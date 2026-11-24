# Experiment 5 — AI-defined characteristics (stage 1 only)

Compare human-defined (Experiment 4) and AI-defined profiling approaches on the same known dataset/workload. The first AI call writes an extractor; a human reviews the source, executes it in isolation and inspects its eight characteristics. The second AI call and all evaluation changes are intentionally out of scope until this review is complete.

## Configuration

Inherit Experiment 4: Shalla, P=8000, 512 bytes/partition, seed 55, fnv1a-mix-v1, the same model default (from experiment3.py), high effort and 16000 max output tokens. Uniform and Zipf (official exponent 1.5) are independent runs. Use the same pinned input files (see [data preparation](data-preparation.md)). The full selected workload is available, duplicates preserved; no holdout. This is in-sample optimization, not evidence of generalization.

The driver passes the original dataset and selected workload directly to the generated extractor as read-only files. It neither shuffles nor copies the dataset. The benchmark still uses its existing MT19937-64/libstdc++-compatible shuffle (seed 55) before partitioning. The model is informed of this layout and may choose whether partition-level analysis is necessary. Consecutive original-file keys are not assumed to represent actual benchmark partitions. Approximate partitioning or sampling must be described as such; exact-layout claims require reproducing the pinned shuffle. No historical experiment results or Experiment 4 characteristic definitions are sent to the model.

The [call-1 prompt](../scripts/prompts/experiment5_call1.txt) requires exactly 4 dataset and 4 workload characteristic types and prohibits candidate search, exact pruning-score computation and direct statistic design. The standard-library-only requirement, provisional 16 KiB output cap, 600-second profiling timeout, 8 GiB memory limit and 2 CPUs are additional stage-1 defaults. Experiment 4 does not enforce this profile cap; report actual profile bytes and token usage for both experiments rather than claiming equal information volume. Adjust the cap before prepare if needed, consistently across runs.

## 1. Prepare (offline)

Python 3.10+, no extra Python dependency. From repository root:

```bash
python3 scripts/experiment5.py prepare --workload uniform --out runs/experiment5_uniform
python3 scripts/experiment5.py prepare --workload zipf --out runs/experiment5_zipf
```

By default reads data/shalla/dataset.txt and only the selected queries_uniform.txt or queries_zipf.txt. Override via --data, --dataset-file or --query-file; nonofficial input requires explicit --allow-unpinned at each stage. The driver verifies SHA-256 checksums, validates unique stored keys, records counts and creates only prompt_call1.txt and config.json. Use a fresh output directory. No shuffled dataset or additional data copy is created. Duplicate checking temporarily uses memory proportional to the number of unique stored keys.

Previously prepared runs with the shuffled-input contract are incompatible with the revised prompt. Keep those runs for provenance; prepare in a new output directory before generating code. The driver rejects old configs rather than silently changing their input semantics.

## 2. Generate (one paid API call per command)

Set ANTHROPIC_API_KEY locally; never commit it. Use the same model as the Experiment 4 runs for a matched comparison (optional --model override). Review the prepared prompt first if desired.

```bash
python3 scripts/experiment5.py generate --out runs/experiment5_uniform
python3 scripts/experiment5.py generate --out runs/experiment5_zipf
```

The command sends only the text prompt, not the dataset or query files. It saves request.json, api_raw.json, response.txt, extract_characteristics.py and generation.json under ai/call_1/. It verifies Python syntax, never runs generated source, and never calls a second model. It prints the source SHA-256. No automatic retries; an intentional independent attempt needs --call 2 (and retain the failed original).

## 3. Review and execute (offline)

Read the entire generated Python source first; check the eight characteristic definitions, absence of candidate search and input handling. Syntax validation is not a security or semantic guarantee. Docker Desktop or Docker Engine must be available. Pull the runtime image once (requires network before execution):

```bash
docker pull python:3.12-slim
```

For each selected workload:

```bash
run=runs/experiment5_uniform
cat "$run/ai/call_1/extract_characteristics.py"
```

Only after reviewing, copy the SHA-256 printed by generate (or calculate it with shasum -a 256 on macOS / sha256sum on Linux). Substitute the reviewed hash:

```bash
python3 scripts/experiment5.py run --out "$run" --approve-sha REVIEWED_SHA256
```

Repeat with run=runs/experiment5_zipf and its own reviewed hash. The driver checks source and original input integrity before and after execution (use --dataset-file and/or --query-file to relocate identical inputs), uses a network-disabled container with a read-only root filesystem, no extra capabilities, no API credentials, separate read-only mounts for source/data/query, and an isolated writable output directory. It never mounts the repository or benchmark. This is defense in depth, not a guarantee against arbitrary code; review remains mandatory. Docker image must be pre-pulled; --image can specify a locally available pinned image digest. The output directory is not disk-quota limited. Stop if the source looks unsafe or violates the research rules. Execution can be repeated with --execution 2 without another paid request. Use --timeout if the default is insufficient, and record deviations.

The generated program's CLI is fixed:
```bash
python3 extract_characteristics.py --dataset dataset.txt --workload queries.txt \
  --partition-size 8000 --budget-bytes 512 --output characteristics.json
```
The driver supplies equivalent container paths; do not execute generated code directly in the repository.

## 4. Inspect outputs and stop

```text
runs/experiment5_uniform/
  config.json
  prompt_call1.txt
  ai/call_1/
    request.json
    api_raw.json
    response.txt
    extract_characteristics.py
    generation.json
    execution_1.log
    execution_1.json
    execution_1/
      characteristics.json
```

The driver validates exact group counts (4+4), unique names, nonempty descriptions, finite JSON values, exact fields and byte cap. Review the profile and script manually for meaning, correct denominators, partition alignment, sampling and forbidden search. A schema-valid profile does not prove correctness or usefulness. Keep the original source and output for reproducibility. The JSON is intended for insertion into the future independent design prompt; no design prompt or benchmark call exists in this stage.

To inspect:
```bash
python3 -m json.tool "$run/ai/call_1/execution_1/characteristics.json"
cat "$run/ai/call_1/execution_1.json"
```

## Tests

```bash
python3 -m unittest discover -s scripts -p 'test_experiment5.py' -v
```

Synthetic fixture tests cover original input preservation and mount paths, rejection of old shuffled-input configurations, input integrity, schema constraints, full query occurrence count, mocked single API request, review hash gate and mocked isolated execution. Real API and Docker execution require local setup and are separate from unit tests. No existing benchmark or Experiment 4 source files are changed.
