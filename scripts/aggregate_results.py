#!/usr/bin/env python3
"""Rebuild the thesis-wide Joint CM comparison from published run artifacts."""
import argparse
import csv
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/joint_cm_comparison.csv"
HISTORY = "runs/experiment3_unified_hashing"
WORKLOADS = ("uniform", "zipf")
METHODS = ("Oracle", "OptimizedBloom", "Random", "AI_NoCharacteristics",
           "AI_HumanCharacteristics")
METRICS = (
    "pruning_pct", "positive_pruning_pct", "negative_pruning_pct",
    "exact_joint_pruning_pct", "oracle_capture_pct", "partition_fpr_pct",
    "false_negatives", "retained_rows_pct", "delta_bloom_pp",
    "delta_reference_pp", "delta_ai_no_characteristics_best_pp",
    "mean_token_ndv", "mean_saturation_pct", "collision_excess_pct",
    "bloom_k", "metadata_total_bytes", "payload_used_bytes", "bpk",
    "query_partition_pairs", "oracle_retained", "retained", "false_positive_pairs",
)
SETTINGS = (
    "dataset", "dataset_rows", "unique_stored", "nonascii_rows",
    "partition_size", "partitions", "budget_bytes", "queries",
    "global_positive", "global_negative", "partition_seed", "hash_version",
)
PROVENANCE = (
    "model", "generation_id", "call", "source_proposal_id", "algorithm",
    "components", "source_file",
)
FIELDS = ("method", "solution_id", "workload", "positions", "position_count", "reason",
          *METRICS, *SETTINGS, *PROVENANCE)
DERIVED = {"positive_pruning_pct", "delta_bloom_pp", "delta_reference_pp",
           "delta_ai_no_characteristics_best_pp"}
RAW_METRICS = set(METRICS) - DERIVED
RAW_SETTINGS = set(SETTINGS) - {"dataset", "partition_seed", "hash_version"}
SHARED = RAW_METRICS | RAW_SETTINGS | {"workload", "algorithm", "components", "positions"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(root, name):
    with (root / name).open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        require(rows and all(None not in r and None not in r.values() for r in rows),
                f"Invalid CSV: {name}")
        return rows


def read_json(root, name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def fixed(value):
    """Use consistent decimal precision for derived percentages."""
    return format(value.quantize(Decimal("0.000000001"), rounding=ROUND_HALF_UP), "f")


def positive_pruning(row):
    positive = int(row["global_positive"])
    if positive == 0:
        return ""
    total = int(row["queries"])
    negative = int(row["global_negative"])
    return fixed((Decimal(row["pruning_pct"]) * total
                  - Decimal(row["negative_pruning_pct"]) * negative) / positive)


def verify_row(row, baseline, label):
    for k in RAW_SETTINGS:
        require(row[k] == baseline[k], f"{label}: inconsistent {k}")
    for k in ("query_partition_pairs", "oracle_retained"):
        require(row[k] == baseline[k], f"{label}: inconsistent {k}")
    require(int(row["false_negatives"]) == 0, f"{label}: false negatives")
    pairs, retained, oracle = (int(row[k]) for k in
                               ("query_partition_pairs", "retained", "oracle_retained"))
    require(int(row["queries"]) * int(row["partitions"]) == pairs and
            int(row["global_positive"]) + int(row["global_negative"]) == int(row["queries"]) and
            oracle <= retained <= pairs and int(row["false_positive_pairs"]) == retained - oracle,
            f"{label}: inconsistent counts")


def index_unique(rows, keys, label):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        require(key not in result, f"{label}: duplicate {key}")
        result[key] = row
    return result


def aggregate(root):
    hist_raw = f"{HISTORY}/results.csv"
    hist_props = f"{HISTORY}/proposal_results.csv"
    raw = read_csv(root, hist_raw)
    proposals = read_csv(root, hist_props)
    config = read_json(root, f"{HISTORY}/config.json")
    runtime = read_json(root, f"{HISTORY}/runtime.json")
    raw_index = index_unique(raw, ("workload", "algorithm"), "historical benchmark")
    index_unique(proposals, ("workload", "group", "proposal_id"), "historical proposals")
    counts = Counter((r["group"], r["workload"]) for r in proposals)
    require(counts == Counter({(g,w):12 for g in ("AI","Random") for w in WORKLOADS}),
            "Expected twelve historical AI and random proposals per workload")
    require(config["calls"] == 1 and config["candidates_per_call"] == 12,
            "Unexpected historical generation configuration")
    model = read_json(root, f"{HISTORY}/api_raw_1.json")["model"]
    require(runtime["hash_version"] == "fnv1a-mix-v1", "Unexpected hashing version")
    output = []

    for workload in WORKLOADS:
        baseline = raw_index[(workload, "OptimizedBloom")]
        oracle = raw_index[(workload, "Oracle")]
        ref = raw_index[(workload, "ReferenceJointCM")]
        require(int(baseline["partition_size"]) == config["partition_size"] and
                int(baseline["budget_bytes"]) == config["budget"],
                "Historical benchmark/config settings differ")
        old = [r for r in proposals if r["workload"] == workload]
        for row in old:
            match = raw_index[(workload, row["algorithm"])]
            require(all(row[k] == match[k] for k in SHARED),
                    f"Historical proposal/benchmark mismatch: {row['proposal_id']}")
        old_ai = [r for r in old if r["group"] == "AI"]
        best = min(old_ai, key=lambda r: (-Decimal(r["pruning_pct"]), r["proposal_id"]))
        current = f"runs/experiment4_{workload}"
        folder = f"{current}/evaluation/profiled/call_1"
        path = f"{folder}/results.csv"
        prepared = read_json(root, f"{current}/config.json")
        frozen = read_json(root, f"{folder}/frozen.json")
        gen = frozen["generation"]
        require(prepared["workload"] == frozen["workload"] == gen["workload"] == workload
                and gen["arm"] == "profiled" and gen["call"] == frozen["call"] == 1
                and gen["candidate_count"] == 12 and gen["returned_model"] == model,
                "Unexpected profiled generation or model mismatch")
        require(prepared["input_sha256"]["dataset"] == config["input_sha256"]["dataset.txt"]
                and prepared["input_sha256"]["query"] == config["input_sha256"][f"queries_{workload}.txt"]
                and prepared["partition_size"] == config["partition_size"]
                and prepared["budget_bytes"] == config["budget"]
                and prepared["partition_seed"] == config["partition_seed"]
                and prepared["hash_version"] == runtime["hash_version"]
                and prepared["query_occurrences"] == int(baseline["queries"]),
                "Profiled run is not comparable to historical inputs/settings")
        new = read_csv(root, path)
        new_index = index_unique(new, ("group", "proposal_id"), path)
        require(Counter(r["group"] for r in new) ==
                Counter({"Oracle":1, "OptimizedBloom":1, "Experiment3BestAI":1,
                         "Experiment4ProfiledAI":12}), f"Unexpected row counts: {path}")
        for name, previous in (("Oracle",oracle),("OptimizedBloom",baseline)):
            duplicate = new_index[(name,"")]
            require(all(duplicate[k] == previous[k] for k in SHARED),
                    f"{workload}: duplicate {name} differs")
        replay = next(r for r in new if r["group"] == "Experiment3BestAI")
        require(all(replay[k] == best[k] for k in
                    ("proposal_id","positions","reason","retained","pruning_pct","false_negatives")),
                f"{workload}: historical best replay differs")
        designs = index_unique(frozen["designs"], ("algorithm",), "frozen designs")

        def append(row, method, solution_id, source, *, generation="", ai_model="", call=""):
            verify_row(row, baseline, f"{method}/{solution_id}/{workload}")
            positions = row["positions"]
            if positions:
                p = [int(x) for x in positions.split(";")]
                require(2 <= len(p) <= 6 and len(p) == len(set(p)) and
                        all(-16 <= x <= 15 for x in p), f"Invalid positions: {positions}")
            require(not method.startswith("AI_") or (positions and row.get("reason")),
                    f"Missing AI reason or positions: {solution_id}")
            score = Decimal(row["pruning_pct"])
            result = {k: row[k] for k in RAW_METRICS | RAW_SETTINGS}
            result.update(method=method, solution_id=solution_id, workload=workload,
                          positions=positions, position_count=str(len(positions.split(";"))) if positions else "",
                          reason=row.get("reason",""),
                          positive_pruning_pct=positive_pruning(row),
                          delta_bloom_pp=fixed(score - Decimal(baseline["pruning_pct"])),
                          delta_reference_pp=fixed(score - Decimal(ref["pruning_pct"])),
                          delta_ai_no_characteristics_best_pp=fixed(score - Decimal(best["pruning_pct"])),
                          dataset="Shalla", partition_seed=str(config["partition_seed"]),
                          hash_version=runtime["hash_version"], model=ai_model,
                          generation_id=generation, call=str(call),
                          source_proposal_id=row.get("proposal_id",""), algorithm=row["algorithm"],
                          components=row["components"], source_file=source)
            require(set(result) == set(FIELDS), "Unexpected output schema")
            output.append(result)

        append(oracle, "Oracle", "ORACLE", hist_raw)
        append(baseline, "OptimizedBloom", "BLOOM", hist_raw)
        for group, method, prefix in (("Random","Random","RANDOM"),
                                       ("AI","AI_NoCharacteristics","AI_NC")):
            group_rows = sorted((r for r in old if r["group"] == group),
                                key=lambda r: r["proposal_id"])
            for i,row in enumerate(group_rows,1):
                require(row["call"] == "1", "Unexpected historical call")
                append(row, method, f"{prefix}_{i:02d}", hist_props,
                       generation="AI_NC_call_1" if group=="AI" else "",
                       ai_model=model if group=="AI" else "", call=row["call"])
        short = "U" if workload == "uniform" else "Z"
        for i,row in enumerate(sorted((r for r in new if r["group"]=="Experiment4ProfiledAI"),
                                      key=lambda r:r["proposal_id"]),1):
            design = designs[(row["algorithm"],)]
            require(design["group"] == "Experiment4ProfiledAI" and
                    design["proposal_id"] == row["proposal_id"] and design["reason"] == row["reason"] and
                    ";".join(map(str,design["positions"])) == row["positions"],
                    f"Frozen candidate differs: {row['proposal_id']}")
            append(row,"AI_HumanCharacteristics",f"AI_HC_{short}_{i:02d}",path,
                   generation=f"AI_HC_{short}_call_1",ai_model=gen["returned_model"],call=gen["call"])

    expected = Counter({(m,w):1 if m in METHODS[:2] else 12
                        for m in METHODS for w in WORKLOADS})
    require(Counter((r["method"],r["workload"]) for r in output) == expected,
            "Incorrect aggregated group counts")
    index_unique(output, ("solution_id", "workload"), "master results")
    # A design generated once must retain its positions/reason in every evaluation.
    seen = {}
    for r in output:
        identity = (r["positions"],r["reason"],r["method"],r["generation_id"])
        require(seen.setdefault(r["solution_id"],identity) == identity,
                f"Inconsistent solution identity: {r['solution_id']}")
    return output


def render(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed CSV is not reproducible")
    args = parser.parse_args()
    rows = aggregate(ROOT)
    content = render(rows)
    if args.check:
        require(OUTPUT.is_file() and OUTPUT.read_bytes() == content,
                f"Stale master CSV; run {Path(__file__).name}")
    else:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        OUTPUT.write_bytes(content)
    print(f"{'Verified' if args.check else 'Wrote'} {len(rows)} rows to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
