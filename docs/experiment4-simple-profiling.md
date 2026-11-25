# Experiment 4 — AI with Human-selected Characteristics

## Goal

Measure whether adding eight simple dataset/workload characteristics improves AI-guided selection of one Joint Character Map's positions. Uniform and Zipf are separate target-workload experiments, not a single joint objective. This branch prepares inputs and prompts, supports explicit AI generation, and evaluates the profiled candidates on their target workload. The original Experiment 3 two-workload benchmark mode and results are preserved.

## Run

Python 3.10+; no additional Python package is required for this stage. Obtain the pinned ASCII Shalla text files using [data preparation](data-preparation.md). No external classification file is needed:

```bash
python3 scripts/experiment4.py prepare --workload uniform \
  --out runs/experiment4_uniform

python3 scripts/experiment4.py prepare --workload zipf \
  --out runs/experiment4_zipf
```

The default input directory is data/shalla. The workload flag selects queries_uniform.txt or queries_zipf.txt. To explicitly select input files, use --dataset-file and --query-file (and still specify --workload). --data selects a directory instead. Only the selected query file is read; the other is not required. Default checks verify the selected file and dataset against the Experiment 3 pinned SHA-256 values. Use --allow-unpinned only for intentionally different inputs, and --examples with a JSON object of actual stored strings if the original samples are not members of your dataset. The workload label must describe the supplied query file; a checksum cannot verify its distribution.

The entire selected query file is used for profiling, preserving every query occurrence. The pinned official files contain 10 million occurrences each. No query split is created or required. Evaluation uses the same full selected file, consistent with Experiment 3: this is known-workload (in-sample) optimization, not evidence of generalization to unseen queries. Use fresh output paths. The profiler aborts rather than overwrites an existing run, including an incomplete one. Outputs produced under the earlier classification scheme must be regenerated in fresh directories.

## Eight characteristics

| Dataset | Workload (separately per selected file) |
| --- | --- |
| D1: structural category distribution | W1: structural category distribution |
| D2: length distribution plus min/max/mean/median | W2: global positive rate by category |
| D3: top five raw 3-character prefixes | W3: top ten frequent query keys, occurrence shares, membership flags, combined share |
| D4: top five raw 3-character suffixes | W4: length distribution |

Dataset statistics are over unique stored keys (duplicates rejected); workload statistics are weighted by query occurrences, not distinct values. Global membership is exact raw-key equality against the full dataset. Zero-query categories have null positive rates; all percentages are rounded to four decimal places. Top lists use frequency descending, then raw ASCII lexicographic order to break ties. Prefix/suffix counts use exactly three raw characters and all stored keys as denominator; keys shorter than three do not contribute a token.

Length buckets: 4–7, 8–11, 12–15, 16–19, 20–23, 24–31, 32+. If any input used for profiling has lengths below four, rerun **both** experiments with --first-length-bucket 0 so the common first bucket is 0–7. Counts, not rounded percentages, are authoritative.

Classification uses raw character structure, not semantic domain boundaries. A valid dotted IPv4 address is classified first. Remaining host-shaped strings are grouped by the literal, case-sensitive prefix `www.` and total number of raw dots; no suffix list, network lookup or DNS/public-suffix inference is used.

| Category | Rule | Example |
| --- | --- | --- |
| ipv4 | Valid IPv4 address | 192.0.2.1 |
| non_www_single_dot | No leading www., exactly one dot | example.com |
| non_www_multiple_dots | No leading www., at least two dots | example.co.uk, blog.example.com |
| www_simple | Leading www., one or two dots | www.example.com, www.com |
| www_complex | Leading www., at least three dots | www.example.co.uk, www.blog.example.com |
| other (only if present) | Not a host-shaped string or invalid numeric dotted quad | invalid/path |

Host-shaped strings consist of dot-separated, nonempty ASCII letter/digit/hyphen labels, each 1–63 characters, beginning and ending with a letter/digit. No normalization is performed: uppercase WWW. is not the literal lowercase www. prefix, and trailing dots, empty labels, schemes, paths, underscores and IPv6 are Other. This is a lightweight syntactic rule, not validation of DNS registration. Other is included in both tables in a run if encountered on either side. Categories are mutually exclusive. The original representative samples are reused unchanged.

## Outputs per run

```text
runs/experiment4_uniform/   # or experiment4_zipf/
  dataset_profile.json     # counts, percentages, length summary, prefix/suffix lists
  workload_profile.json    # full selected workload counts, membership, hot keys
  prompt_profile.json      # compact percentages and hot keys fed to AI
  examples.json            # preserved representative sample strings
  prompt.md                # workload-specific prompt + profile
  prompt_control.md        # matched workload-specific prompt without profile
  config.json              # input/output hashes, settings, query count, timings
```

The two prompts use the same single-workload objective, original structural samples, model settings, reference positions, budget and candidate constraints; the only textual addition to the profiled arm is the statistical profile and its definitions. Historical scores from the old hashing version are deliberately omitted in both. A matched control matters because Experiment 3 optimized both workloads jointly; a comparison only against its historic AI proposals would confound profiling with the workload-specific objective. The current FNV-1a/mix hashing description is used, not the historical base-257 mapping description.

Preparation makes no API calls. The existing Experiment 3 generate/freeze/evaluate commands assume two workloads and a different config format: do not pass Experiment 4 folders to those commands. This exploratory evaluation compares profiled AI with Oracle, optimized Bloom, and the best historical Experiment 3 AI for the selected workload. Control generation is optional; no new random candidates are generated. Because both workload-specific prompting and profile information changed, do not attribute the entire observed difference to the profile alone.

## AI generation

Use your existing prepared run directories without rerunning prepare. Set ANTHROPIC_API_KEY in your local shell (never commit it). Each command makes one paid Anthropic Messages API request using the stored prompt and default model/effort from config.json:

```bash
python3 scripts/experiment4.py generate --out runs/experiment4_uniform --arm profiled
python3 scripts/experiment4.py generate --out runs/experiment4_zipf --arm profiled
```

The profiled arm uses prompt.md. The optional control arm uses prompt_control.md; it is not required by the current evaluation. Use one fresh conversation per request; do not give evaluator feedback. The generation command verifies the prepared artifact hashes and reuses Experiment 3 candidate validation. Both arms use the same model, effort and candidate constraints. If a model override is needed, use the same --model value for every arm and workload; the actual model returned by the API is also recorded. Optional --call 2 (and subsequent positive numbers) makes an independent repeat. Unpinned runs require explicit --allow-unpinned.

Each request reserves ai/<arm>/call_<n>/ and records request.json before contacting the API. Successful calls also save api_raw.json, response.json, validated_candidates.json and generation.json (actual model, token usage, wall time and hashes). A repeated call number is rejected to prevent accidental paid duplicate requests. Incomplete or invalid responses are preserved, not silently retried; inspect the raw response and use a new call number for any intentional retry, retaining the original attempt. No credentials are written to disk by the script.

## Evaluation (no AI call)

Use the existing generated profiled response. JDK 21 and the Gradle wrapper are required.

```bash
python3 scripts/experiment4.py evaluate --out runs/experiment4_uniform
python3 scripts/experiment4.py evaluate --out runs/experiment4_zipf
```

The evaluate command automatically freezes the 12 existing profiled proposals, selects the maximum pruning_pct among AI rows for the selected workload from runs/experiment3_unified_hashing/proposal_results.csv, and evaluates the historical best, all profiled proposals, Oracle and optimized Bloom. No AI Control response, Random, reference map or API key is required. The Java evaluator reads only the selected full query file. Input hashes, historical settings and the response provenance are checked. Historical best retained counts must match the new replay exactly. Nominal BPK is 0.512, P=8000, budget=512B, seed=55. The four groups produce 15 rows per workload. All AI proposals are preserved even if a profiled combination matches the historical best.

Use --call N for a different existing profiled response. Default input file paths are read from config.json; override relocated files with --dataset-file and --query-file (hashes must match). --historical-run changes the directory containing historical config.json, runtime.json and proposal_results.csv. --heap 8g adjusts the Java heap. --eval-out selects a fresh destination if repeating evaluation; existing outputs are not overwritten. No prepare or generate rerun is needed.

```text
runs/experiment4_uniform/evaluation/profiled/call_1/
  frozen.json
  designs.tsv
  runtime.json
  benchmark/results.csv
  benchmark/*.bin
  results.csv
  summary.json
  report.md
```

results.csv includes all original evaluator metrics, candidate reasons, historical reference score, and deltas versus Bloom and Experiment 3 best. summary.json and report.md summarize best, mean, median, and counts above baselines. Historical best is selected post hoc; the comparison is in-sample and exploratory. The optional control prompt remains available for a later matched experiment.

## Published results

- [Uniform profiled evaluation](../runs/experiment4_uniform/evaluation/profiled/call_1/results.csv)
- [Zipf profiled evaluation](../runs/experiment4_zipf/evaluation/profiled/call_1/results.csv)
- [Consolidated Experiment 3 and 4 comparison](../results/joint_cm_comparison.csv) and [data dictionary](../results/joint_cm_comparison.md)
- [Sensitivity analysis](../results/joint_cm_sensitivity.md) and [figures](../results/figures/README.md)

## Test

```bash
python3 -m unittest discover -s scripts -p 'test_experiment4.py' -v
```

Tests exercise raw structural categories, frequency-weighted statistics, full occurrence counting, independent prompts, output hashes, mocked API generation, and profiled-only evaluation orchestration using synthetic fixtures; the full Shalla files are not required. Full runs retain the dataset membership set and selected full-workload query Counter in memory; no duplicate query files are written. Measure actual runtime and memory on the real data. Generated files are ignored by Git under data/ and runs/.

[Back to project overview](../README.md)
