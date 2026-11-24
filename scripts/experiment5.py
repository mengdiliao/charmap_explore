#!/usr/bin/env python3
"""Experiment 5, stage 1 only: prepare, generate source, review, run and validate."""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
from string import Template
import time
import uuid
from urllib.request import Request, urlopen

from experiment3 import EXPECTED, HASH_VERSION, MODEL, ROOT, digest, save

P, BUDGET, SEED = 8000, 512, 55
INPUT_LAYOUT = "original_dataset_v1"
PROMPT = ROOT / "scripts/prompts/experiment5_call1.txt"


def read_keys(path):
    with path.open("r", encoding="ascii", newline=None) as f:
        for line in f:
            yield line.removesuffix("\n")


def prepare(args):
    start = time.perf_counter()
    data = (args.dataset_file or args.data / "dataset.txt").resolve()
    query = (args.query_file or args.data / f"queries_{args.workload}.txt").resolve()
    hashes = {"dataset": digest(data), "workload": digest(query)}
    pinned = (hashes["dataset"] == EXPECTED["dataset.txt"] and
              hashes["workload"] == EXPECTED[f"queries_{args.workload}.txt"])
    if not pinned and not args.allow_unpinned:
        raise ValueError("Input hashes differ from pinned Shalla; use --allow-unpinned for fixtures")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    seen = set()
    for key in read_keys(data):
        if key in seen:
            raise ValueError("Duplicate stored keys")
        seen.add(key)
    n_keys = len(seen)
    del seen
    if not n_keys:
        raise ValueError("Empty dataset")
    n_queries = sum(1 for _ in read_keys(query))
    if not n_queries:
        raise ValueError("Empty workload")
    prompt = Template(PROMPT.read_text(encoding="utf-8")).substitute(
        dataset_count=f"{n_keys:,}", query_count=f"{n_queries:,}",
        workload_label="Uniform" if args.workload == "uniform" else "Zipfian (official exponent 1.5)",
        partition_size=P, budget_bytes=BUDGET,
        bitmap_bits=BUDGET*8, max_profile_bytes=args.max_profile_bytes)
    (out / "prompt_call1.txt").write_text(prompt, encoding="utf-8")
    # Detect changes during preparation.
    if digest(data) != hashes["dataset"] or digest(query) != hashes["workload"]:
        raise ValueError("Input changed during preparation")
    save(out / "config.json", {
        "experiment": 5, "stage": "call1_only", "input_layout": INPUT_LAYOUT,
        "workload": args.workload,
        "model": MODEL, "effort": "high", "max_tokens": 16000,
        "partition_size": P, "budget_bytes": BUDGET, "partition_seed": SEED,
        "hash_version": HASH_VERSION, "dataset_count": n_keys, "query_count": n_queries,
        "evaluation_scope": "full_selected_workload_in_sample",
        "official_input_hashes_match": pinned, "max_profile_bytes": args.max_profile_bytes,
        "input_paths": {"dataset": str(data), "workload": str(query)},
        "input_sha256": hashes,
        "prompt_sha256": digest(out / "prompt_call1.txt"),
        "prepare_seconds": round(time.perf_counter()-start, 3),
    })
    print(f"Prepared {out}; no API call made.")


def config(out, allow_unpinned=False):
    cfg = json.loads((out / "config.json").read_text(encoding="utf-8"))
    if (cfg["experiment"], cfg["stage"], cfg["partition_size"], cfg["budget_bytes"],
        cfg["partition_seed"], cfg["hash_version"]) != (5, "call1_only", P, BUDGET, SEED, HASH_VERSION):
        raise ValueError("Not an Experiment 5 stage-1 run")
    if not cfg["official_input_hashes_match"] and not allow_unpinned:
        raise ValueError("Unpinned inputs require --allow-unpinned")
    if cfg.get("input_layout") != INPUT_LAYOUT:
        raise ValueError("Old shuffled-input run; prepare again in a fresh --out directory")
    if digest(out / "prompt_call1.txt") != cfg["prompt_sha256"]:
        raise ValueError("Prepared artifact changed: prompt_call1.txt")
    return cfg


def verified_inputs(cfg, dataset_file=None, query_file=None):
    data = (dataset_file or Path(cfg["input_paths"]["dataset"])).resolve()
    query = (query_file or Path(cfg["input_paths"]["workload"])).resolve()
    for name, path in (("dataset", data), ("workload", query)):
        if digest(path) != cfg["input_sha256"][name]:
            raise ValueError(f"Input changed: {name}")
    return data, query


def generate(args):
    out = args.out.resolve()
    cfg = config(out, args.allow_unpinned)
    verified_inputs(cfg)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY in your shell")
    model = args.model or cfg["model"]
    dest = out / "ai" / f"call_{args.call}"
    dest.mkdir(parents=True, exist_ok=False)
    request = {"model": model, "effort": cfg["effort"], "max_tokens": cfg["max_tokens"],
               "prompt_sha256": cfg["prompt_sha256"], "config_sha256": digest(out / "config.json")}
    save(dest / "request.json", request)
    body = {"model": model, "max_tokens": cfg["max_tokens"],
            "output_config": {"effort": cfg["effort"]},
            "messages": [{"role": "user", "content": (out / "prompt_call1.txt").read_text(encoding="utf-8")}]}
    req = Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode("utf-8"),
                  headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                           "content-type": "application/json"}, method="POST")
    start = time.perf_counter()
    with urlopen(req, timeout=600) as response:
        raw = json.load(response)
    elapsed = time.perf_counter()-start
    save(dest / "api_raw.json", raw)
    source = "".join(b["text"] for b in raw["content"] if b["type"] == "text")
    (dest / "response.txt").write_text(source, encoding="utf-8")
    if raw.get("stop_reason") != "end_turn":
        raise ValueError("Incomplete response; inspect preserved raw response")
    if not source.strip() or source.lstrip().startswith(chr(96)*3):
        raise ValueError("Expected raw Python source, no Markdown")
    ast.parse(source, filename="extract_characteristics.py")
    path = dest / "extract_characteristics.py"
    path.write_text(source, encoding="utf-8")
    save(dest / "generation.json", {
        **request, "returned_model": raw.get("model"), "usage": raw.get("usage"),
        "elapsed_seconds": round(elapsed, 3), "source_sha256": digest(path),
    })
    print(f"Source saved for manual review: {path}")
    print(f"SHA-256: {digest(path)}")
    print("No generated code executed; no second AI call.")


def reject_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def validate_profile(path, limit):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError(f"Expected regular JSON file within {limit} bytes")
    obj = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant,
                     object_pairs_hook=unique_object)
    # Also reject numeric exponent overflow (e.g. 1e999).
    json.dumps(obj, allow_nan=False)
    groups = ("dataset_characteristics", "workload_characteristics")
    if not isinstance(obj, dict) or set(obj) != set(groups):
        raise ValueError("Expected exactly two characteristic groups")
    names = set()
    for group in groups:
        rows = obj[group]
        if not isinstance(rows, list) or len(rows) != 4:
            raise ValueError(f"{group}: expected exactly 4 characteristics")
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"name", "description", "values"}:
                raise ValueError("Expected name, description, values")
            for field in ("name", "description"):
                if not isinstance(row[field], str) or not row[field].strip():
                    raise ValueError(f"Invalid {field}")
            name = row["name"].strip().casefold()
            if name in names:
                raise ValueError(f"Duplicate characteristic name: {name}")
            names.add(name)
            if row["values"] is None or row["values"] == {} or row["values"] == []:
                raise ValueError(f"Missing values for {name}")
    return obj


def run(args):
    out = args.out.resolve()
    cfg = config(out, args.allow_unpinned)
    dest = out / "ai" / f"call_{args.call}"
    generation = json.loads((dest / "generation.json").read_text(encoding="utf-8"))
    source = dest / "extract_characteristics.py"
    if generation["config_sha256"] != digest(out / "config.json"):
        raise ValueError("Run config changed")
    if digest(source) != generation["source_sha256"] or args.approve_sha != digest(source):
        raise ValueError("Review the exact generated source and supply its SHA-256")
    data, query = verified_inputs(cfg, args.dataset_file, args.query_file)
    result = dest / f"execution_{args.execution}"
    result.mkdir(exist_ok=False)
    output = result / "characteristics.json"
    name = "charmap-exp5-" + uuid.uuid4().hex
    # Do not pass API credentials, repository, benchmark, or other runs.
    # Docker must already have the image available; no implicit image pull.
    image = args.image
    cmd = ["docker", "run", "--rm", "--pull=never", "--name", name,
           "--network=none", "--read-only", "--cap-drop=ALL",
           "--security-opt=no-new-privileges", "--memory=8g", "--cpus=2",
           "--pids-limit=64", "--user", f"{os.getuid()}:{os.getgid()}",
           "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
           "-e", "PYTHONHASHSEED=0", "-e", "PYTHONDONTWRITEBYTECODE=1",
           "--mount", f"type=bind,src={source},dst=/extract_characteristics.py,readonly",
           "--mount", f"type=bind,src={data},dst=/dataset.txt,readonly",
           "--mount", f"type=bind,src={query},dst=/queries.txt,readonly",
           "--mount", f"type=bind,src={result},dst=/output",
           image, "python3", "/extract_characteristics.py",
           "--dataset", "/dataset.txt", "--workload", "/queries.txt",
           "--partition-size", str(P), "--budget-bytes", str(BUDGET),
           "--output", "/output/characteristics.json"]
    # Keep logs and provenance outside the generated program's writable mount.
    log = dest / f"execution_{args.execution}.log"
    meta = dest / f"execution_{args.execution}.json"
    start = time.perf_counter()
    status = "failed"
    try:
        with log.open("w", encoding="utf-8") as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True, timeout=args.timeout)
        validate_profile(output, cfg["max_profile_bytes"])
        if sorted(p.name for p in result.iterdir()) != ["characteristics.json"]:
            raise ValueError("Unexpected files produced by extractor")
        verified_inputs(cfg, data, query)
        if digest(source) != generation["source_sha256"]:
            raise ValueError("Source changed during execution")
        status = "schema_validated"
    finally:
        if status != "schema_validated":
            try:
                subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=15, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        save(meta, {"status": status, "command": cmd, "source_sha256": generation["source_sha256"],
                    "config_sha256": digest(out / "config.json"), "timeout_seconds": args.timeout,
                    "elapsed_seconds": round(time.perf_counter()-start, 3),
                    "profile_bytes": output.stat().st_size if status == "schema_validated" else None,
                    "profile_sha256": digest(output) if status == "schema_validated" else None})
    print(f"Schema-valid profile: {output}")
    print("Review semantic correctness and absence of candidate search manually. Stage 1 ends here.")


def positive_int(value):
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("positive integer required")
    return n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Offline prompt and original input validation")
    prep.add_argument("--workload", choices=["uniform", "zipf"], required=True)
    prep.add_argument("--data", type=Path, default=ROOT / "data/shalla")
    prep.add_argument("--dataset-file", type=Path)
    prep.add_argument("--query-file", type=Path)
    prep.add_argument("--max-profile-bytes", type=positive_int, default=16384)
    gen = sub.add_parser("generate", help="One paid AI call; save source only")
    gen.add_argument("--model")
    gen.add_argument("--call", type=positive_int, default=1)
    exe = sub.add_parser("run", help="Run reviewed source in isolated Docker container, offline")
    exe.add_argument("--call", type=positive_int, default=1)
    exe.add_argument("--execution", type=positive_int, default=1)
    exe.add_argument("--approve-sha", required=True, help="SHA-256 of the manually reviewed source")
    exe.add_argument("--dataset-file", type=Path)
    exe.add_argument("--query-file", type=Path)
    exe.add_argument("--timeout", type=positive_int, default=600)
    exe.add_argument("--image", default="python:3.12-slim", help="Pre-pulled Python image")
    for p in (prep, gen, exe):
        p.add_argument("--out", type=Path, required=True)
        p.add_argument("--allow-unpinned", action="store_true")
    args = parser.parse_args()
    {"prepare": prepare, "generate": generate, "run": run}[args.command](args)


if __name__ == "__main__":
    main()
