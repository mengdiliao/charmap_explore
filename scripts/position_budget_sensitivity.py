#!/usr/bin/env python3
"""Fixed-position sensitivity sweep for Experiment 3 winners (no new AI calls).

Data and position selections are frozen from the published unified-hashing run.
The complete original 10M Uniform and 10M Zipf query occurrences are evaluated
at each of the 23 partition-size/budget configurations.
"""
import argparse
import csv
import math
import shutil
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "runs/experiment3_unified_hashing"
DESIGNS = ROOT / "experiments/position_budget_sensitivity/selected.tsv"
BUDGETS = {
    500: [32, 64, 128, 256],
    2000: [128, 256, 512, 1024],
    8000: [256, 512, 1024, 2048, 4096],
    32000: [256, 2048, 4096, 8192, 16384],
    128000: [256, 8192, 16384, 32768, 65536],
}
# Method name -> (selection group, source workload, published proposal_id, positions)
CHOSEN = {
    "AI_Uniform": ("AI", "uniform", "A1_04", "0;1;-5;-1"),
    "AI_Zipf": ("AI", "zipf", "A1_03", "0;4;-5;-1"),
    "Random_Uniform": ("Random", "uniform", "R1_02", "1;3;5;11"),
    "Random_Zipf": ("Random", "zipf", "R1_06", "6;7;-10;-5"),
}
METHODS = ("Oracle", "OptimizedBloom", "ReferenceJointCM", *CHOSEN)
EXTRA = ("selection_group", "selection_workload", "source_proposal_id")
BASE_FIELDS = None

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def validate_selections():
    source = read_csv(SRC / "proposal_results.csv")
    entries = {}
    for name, (group, workload, proposal_id, positions) in CHOSEN.items():
        pool = [r for r in source if r["group"] == group and r["workload"] == workload]
        best = max(pool, key=lambda r: float(r["pruning_pct"]))
        if best["proposal_id"] != proposal_id or best["positions"] != positions:
            raise AssertionError(f"Selection no longer matches published best {name}: {best}")
        entries[name] = best
    lines = [line.strip().split("\t") for line in DESIGNS.read_text().splitlines() if line.strip()]
    expected = {"ReferenceJointCM": ("0", "1", "-2", "-1")}
    expected.update({name: tuple(pos.split(";")) for name, (*_, pos) in CHOSEN.items()})
    actual = {fields[0]: tuple(fields[1:]) for fields in lines}
    if actual != expected or len(lines) != 5:
        raise AssertionError(f"Unexpected selected.tsv: {actual}")
    return entries

def annotate(row):
    row = dict(row)
    info = CHOSEN.get(row["algorithm"])
    row.update(zip(EXTRA, info[:3] if info else ("", "", "")))
    return row

def validate_matrix_rows(rows, partition_sizes):
    expected = {(w, p, b, a) for w in ("uniform", "zipf")
                for p in partition_sizes for b in BUDGETS[p] for a in METHODS}
    got = set()
    for r in rows:
        w, p, b, alg = r["workload"], int(r["partition_size"]), int(r["budget_bytes"]), r["algorithm"]
        key = (w, p, b, alg)
        if key in got or key not in expected:
            raise AssertionError(f"Unexpected / duplicated row: {key}")
        got.add(key)
        if int(r["false_negatives"]) != 0:
            raise AssertionError(f"False negatives: {key}")
        rate = float(r["pruning_pct"])
        if not (0 <= rate <= 100):
            raise AssertionError(f"Invalid pruning rate: {key}")
        if alg != "Oracle" and int(r["payload_used_bytes"]) > b:
            raise AssertionError(f"Exceeded bitmap budget: {key}")
        if alg in CHOSEN or alg == "ReferenceJointCM":
            if not float(r["exact_joint_pruning_pct"]) + 1e-7 >= rate:
                raise AssertionError(f"Pruning exceeds collision-free ceiling: {key}")
    if got != expected:
        raise AssertionError(f"Missing {len(expected - got)} expected rows: {sorted(expected - got)[:5]}")
    return True

def verify_anchor(rows):
    """The new sweep must reproduce every selected Experiment 3 metric at P=8000, B=512."""
    source = read_csv(SRC / "results.csv")
    proposals = validate_selections()
    by_source = {(r["workload"], r["algorithm"]): r for r in source}
    names = {"Oracle": "Oracle", "OptimizedBloom": "OptimizedBloom",
             "ReferenceJointCM": "ReferenceJointCM"}
    names.update({name: row["algorithm"] for name, row in proposals.items()})
    for row in rows:
        if int(row["partition_size"]) != 8000 or int(row["budget_bytes"]) != 512:
            continue
        expected = by_source[row["workload"], names[row["algorithm"]]]
        for field in ("pruning_pct", "negative_pruning_pct", "oracle_retained",
                      "retained", "false_negatives", "exact_joint_pruning_pct"):
            a, b = row[field], expected[field]
            if a == "" and b == "":
                continue
            if not math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-7):
                raise AssertionError(f"Anchor discrepancy {row['workload']} {row['algorithm']} {field}: {a} vs {b}")

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0])
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, cols)
        writer.writeheader()
        writer.writerows(rows)

def run_partition(partition_size, output, data):
    validate_selections()
    # The official full dataset and two query files must match the frozen run hashes.
    from experiment3 import verify
    verify(data)
    output.mkdir(parents=True, exist_ok=True)
    combined = []
    for budget in BUDGETS[partition_size]:
        tmp = output / f"tmp_p{partition_size}_b{budget}"
        args = [
            str(ROOT / "gradlew"), "--no-daemon", "--console=plain", "positionEvaluator",
            f"-PdataDir={data.resolve()}", f"-PoutputDir={tmp.resolve()}",
            f"-PpartitionSize={partition_size}", f"-Pbudget={budget}",
            f"-Pcandidates={DESIGNS.resolve()}", "-Pseed=55",
        ]
        print(f"Running P={partition_size}, B={budget}", flush=True)
        subprocess.run(args, cwd=ROOT, check=True)
        combined.extend(annotate(r) for r in read_csv(tmp / "results.csv"))
        shutil.rmtree(tmp)  # do not retain large bitmap binaries in the artifact
    validate_matrix_rows(combined, [partition_size])
    if partition_size == 8000:
        verify_anchor(combined)
    path = output / f"p{partition_size}.csv"
    write_csv(path, combined)
    print(f"Validated {len(combined)} rows in {path}", flush=True)

def merge(source_dir, output):
    validate_selections()
    rows = []
    for p in BUDGETS:
        f = source_dir / f"p{p}.csv"
        if not f.is_file():
            raise FileNotFoundError(f)
        rows += read_csv(f)
    validate_matrix_rows(rows, list(BUDGETS))
    verify_anchor(rows)
    method_order = {m: i for i, m in enumerate(METHODS)}
    rows.sort(key=lambda x: (("uniform", "zipf").index(x["workload"]),
                              int(x["partition_size"]), int(x["budget_bytes"]),
                              method_order[x["algorithm"]]))
    write_csv(output, rows)
    # Compact source-backed summary at the same time as the full CSV.
    indexed = {(r["workload"], int(r["partition_size"]), int(r["budget_bytes"]), r["algorithm"]): r for r in rows}
    summary = [
        "# Selected position combinations — budget and partition sensitivity",
        "",
        "Full Shalla; 2,926,705 stored keys; full official 10M-query Uniform and Zipf workloads;",
        "partition seed 55; fnv1a-mix-v1; all methods use the same bitmap budget at each setting.",
        "Candidates are selected **post hoc** using Experiment 3 at P=8000, B=512B.",
        "This is a sensitivity analysis, **not** an independent validation of AI superiority.",
        "",
        "| Method | Origin | Selected positions |",
        "|---|---|---|",
        "| ReferenceJointCM | Fixed baseline | (0,1,-2,-1) |",
    ]
    for name, (group, workload, proposal, positions) in CHOSEN.items():
        summary.append(f"| {name} | {group}, best {workload} ({proposal}) | ({positions.replace(';', ',')}) |")
    summary += ["", "## Wins against OptimizedBloom across 23 settings", "",
                "| Method | Uniform wins | Zipf wins |", "|---|---:|---:|"]
    for name in ("ReferenceJointCM", *CHOSEN):
        wins = [sum(float(indexed[w,p,b,name]["pruning_pct"]) >
                    float(indexed[w,p,b,"OptimizedBloom"]["pruning_pct"])
                    for p, budgets in BUDGETS.items() for b in budgets)
                for w in ("uniform", "zipf")]
        summary.append(f"| {name} | {wins[0]}/23 | {wins[1]}/23 |")
    summary += ["", "## Pruning at the original selection point (P=8000, B=512B)", "",
                "| Method | Uniform % | Zipf % |", "|---|---:|---:|"]
    for name in METHODS:
        vals = [float(indexed[w,8000,512,name]["pruning_pct"]) for w in ("uniform", "zipf")]
        summary.append(f"| {name} | {vals[0]:.4f} | {vals[1]:.4f} |")
    summary += ["", "See CSV for all 322 method/workload/configuration rows, actual metadata,",
                "false negatives, saturation, collisions and per-design collision-free ceilings.",
                "The collision-free ceiling belongs to each individual position combination;",
                "it is not a universal bound for character maps.", ""]
    report = output.with_suffix(".md")
    report.write_text("\n".join(summary), encoding="utf-8")
    print(f"Validated {len(rows)} rows: {output}, {report}", flush=True)

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--partition-size", type=int, choices=list(BUDGETS), required=True)
    r.add_argument("--data", type=Path, default=ROOT / "data/shalla")
    r.add_argument("--out", type=Path, required=True)
    m = sub.add_parser("merge")
    m.add_argument("--source-dir", type=Path, required=True)
    m.add_argument("--output", type=Path, required=True)
    v = sub.add_parser("validate")
    args = parser.parse_args()
    if args.cmd == "run":
        run_partition(args.partition_size, args.out, args.data)
    elif args.cmd == "merge":
        merge(args.source_dir, args.output)
    else:
        entries = validate_selections()
        print({name: (r["proposal_id"], r["positions"], r["pruning_pct"]) for name, r in entries.items()})

if __name__ == "__main__":
    main()
