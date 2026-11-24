#!/usr/bin/env python3
"""Experiment 5, stage 1 only: prepare, generate source, review, run and validate."""
import argparse
import ast
import hashlib
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
    max_tokens = getattr(args, "max_tokens", None) or cfg["max_tokens"]
    request = {"model": model, "effort": cfg["effort"], "max_tokens": max_tokens,
               "prompt_sha256": cfg["prompt_sha256"], "config_sha256": digest(out / "config.json")}
    save(dest / "request.json", request)
    body = {"model": model, "max_tokens": max_tokens,
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
    save(dest / "attempt.json", {"stop_reason": raw.get("stop_reason"), "usage": raw.get("usage"),
                                 "elapsed_seconds": round(elapsed, 3)})
    if raw.get("stop_reason") != "end_turn":
        if raw.get("stop_reason") == "max_tokens":
            raise ValueError(f"Token limit reached; use resume --out {out} --call {args.call}")
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



def response_text(raw):
    return "".join(b["text"] for b in raw["content"] if b["type"] == "text")


def continuation_anchor(source):
    """Rewind only the incomplete last line and require an exact overlap."""
    prefix = source[:source.rfind("\n") + 1]
    if not prefix.strip():
        raise ValueError("No complete source line to resume; use a fresh generate --call N")
    lines = prefix.splitlines(keepends=True)
    # Include the last nonblank line and any trailing blank lines.
    i = len(lines) - 1
    while i > 0 and not lines[i].strip():
        i -= 1
    anchor = "".join(lines[max(0, i-2):])
    return prefix, anchor


def resume(args):
    """One explicit continuation of a max_tokens-truncated first-call response."""
    out = args.out.resolve()
    cfg = config(out, args.allow_unpinned)
    verified_inputs(cfg)
    dest = out / "ai" / f"call_{args.call}"
    if (dest / "generation.json").exists() or (dest / "extract_characteristics.py").exists():
        raise ValueError("This call already has a generated source; do not resume it")
    original = json.loads((dest / "request.json").read_text(encoding="utf-8"))
    if (original["config_sha256"] != digest(out / "config.json") or
            original["prompt_sha256"] != cfg["prompt_sha256"]):
        raise ValueError("Original request does not match prepared config/prompt")
    raw = json.loads((dest / "api_raw.json").read_text(encoding="utf-8"))
    source = (dest / "response.txt").read_text(encoding="utf-8")
    if raw.get("stop_reason") != "max_tokens" or source != response_text(raw):
        raise ValueError("Resume requires an unchanged response stopped by max_tokens")
    if not source.strip() or source.lstrip().startswith(chr(96)*3):
        raise ValueError("Expected partial raw Python source; inspect original response")
    # Follow only successfully joined, still-truncated attempts. Failed joins
    # are preserved but never used as a prefix for subsequent requests.
    attempts = sorted((p for p in dest.glob("resume_*") if p.is_dir()
                       and p.name.removeprefix("resume_").isdigit()),
                      key=lambda p: int(p.name.removeprefix("resume_")))
    accepted = []
    for p in attempts:
        meta_path = p / "attempt.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") == "joined_truncated":
            combined = p / "combined.py"
            if meta["previous_source_sha256"] != text_sha256(source) or digest(combined) != meta["combined_sha256"]:
                raise ValueError("Continuation chain was modified")
            source = combined.read_text(encoding="utf-8")
            accepted.append(p.name)
    prefix, anchor = continuation_anchor(source)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY in your shell")
    n = int(attempts[-1].name.removeprefix("resume_")) + 1 if attempts else 1
    part = dest / f"resume_{n}"
    part.mkdir(exist_ok=False)
    max_tokens = args.max_tokens or original["max_tokens"]
    request = {**original, "max_tokens": max_tokens, "resume_number": n,
               "previous_source_sha256": text_sha256(source),
               "accepted_prior_resumes": accepted}
    save(part / "request.json", request)
    (part / "prefix.py").write_text(prefix, encoding="utf-8")
    # A new user turn, not a final assistant prefill. The original text is
    # provided as context; no hidden reasoning blocks are fabricated.
    instruction = (
        "Your previous Python source was truncated by the output token limit. "
        "Continue the SAME program, with the same eight characteristics and methods. "
        "Do not redesign, restart, summarize, add Markdown fences or repeat earlier code. "
        "The last incomplete line will be discarded. Begin your response with the following "
        "exact overlap, including indentation and newlines, then complete the rest of the program. "
        "The overlap below is JSON-encoded only to identify its exact characters; output raw Python, "
        "not JSON. Exact overlap: " + json.dumps(anchor, ensure_ascii=True) +
        "\nFinish all remaining implementation, including the CLI and JSON output. "
        "Keep reasoning and code concise."
    )
    (part / "continuation_prompt.txt").write_text(instruction, encoding="utf-8")
    body = {"model": original["model"], "max_tokens": max_tokens,
            "output_config": {"effort": original["effort"]},
            "messages": [{"role": "user", "content": (out / "prompt_call1.txt").read_text(encoding="utf-8")},
                         {"role": "assistant", "content": source},
                         {"role": "user", "content": instruction}]}
    req = Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode("utf-8"),
                  headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                           "content-type": "application/json"}, method="POST")
    start = time.perf_counter()
    with urlopen(req, timeout=600) as response:
        continued = json.load(response)
    elapsed = round(time.perf_counter()-start, 3)
    save(part / "api_raw.json", continued)
    suffix = response_text(continued)
    (part / "response.txt").write_text(suffix, encoding="utf-8")
    meta = {"stop_reason": continued.get("stop_reason"), "usage": continued.get("usage"),
            "elapsed_seconds": elapsed, "previous_source_sha256": text_sha256(source),
            "status": "not_joined"}
    save(part / "attempt.json", meta)
    if continued.get("model") != raw.get("model"):
        raise ValueError(f"Returned model changed; inspect {part}")
    if not suffix.startswith(anchor) or len(suffix) <= len(anchor):
        raise ValueError(f"Continuation did not reproduce exact overlap; inspect {part}. "
                         "Run resume again to retry from the last accepted prefix.")
    combined = prefix[:-len(anchor)] + suffix
    combined_path = part / "combined.py"
    combined_path.write_text(combined, encoding="utf-8")
    meta["combined_sha256"] = digest(combined_path)
    if continued.get("stop_reason") == "max_tokens":
        meta["status"] = "joined_truncated"
        save(part / "attempt.json", meta)
        raise ValueError("Continuation also reached token limit; run resume again")
    if continued.get("stop_reason") != "end_turn":
        save(part / "attempt.json", meta)
        raise ValueError(f"Incomplete continuation; inspect {part}")
    # Compile without executing; syntax alone does not establish semantic correctness.
    compile(combined, "extract_characteristics.py", "exec")
    meta["status"] = "joined_complete"
    save(part / "attempt.json", meta)
    path = dest / "extract_characteristics.py"
    path.write_text(combined, encoding="utf-8")
    # Count every returned API response, including unsuccessful joins.
    records = [{"attempt": "original", "usage": raw.get("usage"),
                "stop_reason": raw.get("stop_reason"),
                "elapsed_seconds": (json.loads((dest / "attempt.json").read_text())["elapsed_seconds"]
                                    if (dest / "attempt.json").exists() else None)}]
    for p in attempts + [part]:
        ap = p / "api_raw.json"
        if ap.exists():
            ar = json.loads(ap.read_text(encoding="utf-8"))
            am = p / "attempt.json"
            records.append({"attempt": p.name, "usage": ar.get("usage"),
                            "stop_reason": ar.get("stop_reason"),
                            "elapsed_seconds": (json.loads(am.read_text()).get("elapsed_seconds")
                                                if am.exists() else None)})
    fields = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    usage = {k: sum((v["usage"] or {}).get(k, 0) for v in records) for k in fields}
    elapsed_total = (sum(v["elapsed_seconds"] for v in records)
                     if all(v["elapsed_seconds"] is not None for v in records) else None)
    save(dest / "generation.json", {
        **original, "returned_model": continued.get("model"), "usage": usage,
        "elapsed_seconds": elapsed_total, "source_sha256": digest(path),
        "resumed": True, "api_responses": len(records), "attempts": records,
        "accepted_resumes": accepted + [part.name],
    })
    print(f"Completed source saved for manual review: {path}")
    print(f"SHA-256: {digest(path)}")
    print("No generated code executed; no statistic-design AI call.")


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    gen.add_argument("--max-tokens", type=positive_int, help="Override output token limit for this request")
    gen.add_argument("--call", type=positive_int, default=1)
    cont = sub.add_parser("resume", help="One paid continuation of a truncated first call")
    cont.add_argument("--call", type=positive_int, default=1)
    cont.add_argument("--max-tokens", type=positive_int, help="Override continuation output limit")
    exe = sub.add_parser("run", help="Run reviewed source in isolated Docker container, offline")
    exe.add_argument("--call", type=positive_int, default=1)
    exe.add_argument("--execution", type=positive_int, default=1)
    exe.add_argument("--approve-sha", required=True, help="SHA-256 of the manually reviewed source")
    exe.add_argument("--dataset-file", type=Path)
    exe.add_argument("--query-file", type=Path)
    exe.add_argument("--timeout", type=positive_int, default=600)
    exe.add_argument("--image", default="python:3.12-slim", help="Pre-pulled Python image")
    for p in (prep, gen, cont, exe):
        p.add_argument("--out", type=Path, required=True)
        p.add_argument("--allow-unpinned", action="store_true")
    args = parser.parse_args()
    {"prepare": prepare, "generate": generate, "resume": resume, "run": run}[args.command](args)


if __name__ == "__main__":
    main()
