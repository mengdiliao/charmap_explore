# Experiment 3 — Level 1: one-shot AI joint position selection

P=8000, B=512 bytes, seed55; all 2,926,705 Shalla stored keys and both 10M official query files, verified SHA256. No holdout, no evaluator feedback, no detailed profiling. Uniform primary, Zipf secondary. One Claude Opus 5.5 response, 12 proposals (8 four-position; 4 variable-length 2/3/5/6), 12 length-matched seeded random controls; duplicate designs evaluated once but all proposals preserved. Reference [0,1,-2,-1], optimized full-key Bloom (same theoretical integer k as Experiment 2), Oracle. All positions canonicalized, one tuple and same base257/mix mapping, missing code 128, no OTHER or hybrid. Fixed 512B payload, actual serialized bytes incl. shared schema measured; no false negatives. Exact projection ceiling is computed, but not used in AI prompt. All data and workloads used; no claim of independent generalization. Prompt includes prior full-workload baseline scores, not candidate scores.

## Local quick start (macOS/Linux)

Install Python 3.10+ and JDK 21 (on macOS: brew install openjdk@21, then configure JAVA_HOME and PATH). No Python third-party package needed for Experiment 3 itself. Gradle Wrapper 8.14.3 is committed; no separate Gradle installation is required. First run downloads Gradle and test dependencies if running tests.
Use the already prepared data artifact at https://github.com/mengdiliao/charmap_explore/actions/runs/44195004791/artifacts/14377239207 (requires repository access; expires after 30 days). Extract at repository root, such that data/shalla/dataset.txt, queries_uniform.txt, queries_zipf.txt exist. If expired, regenerate with scripts/prepare_shalla.py on Linux with Python3.12, GCC and pinned requirements; C rand() is platform dependent, so macOS regeneration may fail expected hashes. Use exact artifact wherever possible.

    python3 scripts/experiment3.py prepare

Open runs/experiment3_level1/prompt.md and review real examples. Missing example categories are omitted. Prompt is frozen via SHA256. If a previous three-call configuration was prepared, use a fresh directory (e.g. --out runs/experiment3_level1_onecall on every command); existing data and runs are not deleted. No full dataset/workload is transmitted.

## Option A: API (preferred for reproducibility)

Visit https://platform.claude.com/ and create an API key, enable billing/credits (separate from Claude chat subscription). Never commit your key.

    read -s "ANTHROPIC_API_KEY?Anthropic API key: "
    export ANTHROPIC_API_KEY
    python3 scripts/experiment3.py generate
    unset ANTHROPIC_API_KEY

The read example is zsh (macOS). Bash use read -s -p "Anthropic API key: " ANTHROPIC_API_KEY then export. One independent call, no tools; model claude-opus-5-5, output_config.effort high, max_tokens 16000. Adaptive thinking always on for this model; no separate thinking field. Uses stdlib HTTPS, no SDK. Saves api_raw_1.json with model, usage, stop reason, and response_1.json. No automatic retries; if interrupted, inspect saved output and rerun generate only if no response/raw file exists. Invalid output is preserved; do not manually edit positions or give feedback. For a fresh independent retry preserve original failed response elsewhere and disclose failure/retry.

## Option B: Claude chat

At https://claude.ai/ start one new chat, select Opus 5.5 if available, turn on extended thinking / high effort if UI offers it, no web/tools. Paste prompt.md into the chat. Save the JSON text unedited under runs/experiment3_level1/response_1.json. Record displayed model, settings, dates and any limitations in a local manual_notes.txt. UI may not expose exact model ID, effort, usage; API is preferred for thesis.

## Run and read

    python3 scripts/experiment3.py freeze
    python3 scripts/experiment3.py evaluate

Both workloads evaluated in one run. No API used in freeze/evaluate. Python validates combinations, fixes tuple order, generates seeded controls, writes frozen.json before benchmark. To repeat use another --out path on every command. Java uses a pinned port of the original libstdc++ mt19937_64 shuffle instead of Collections.shuffle, ensuring a platform-independent layout subject to the archived-result parity gate. The Python runner invokes ./gradlew positionEvaluator automatically. Set JAVA_HEAP (default 4g) if needed. The retired C++ implementation is available in Git history at commit b948c10b57aa84857d0ba9a00d9f66ea1742fc5b; it is no longer present in the main working tree. Memory and run time depend on machine; no production latency claims.

Output under runs/experiment3_level1 (gitignored):
- prompt.md, config.json, examples.json, response_N.json, api_raw_N.json, frozen.json
- runtime.json (Gradle/JVM version info, build and source hashes, frozen design hash)
- benchmark/results.csv, physical summary binaries
- proposal_results.csv: all AI/random proposals, both workloads, deltas
- report.md: best, median, mean, counts above Bloom by group/call.

No real AI response is provided in the repository. Test fixtures are explicitly synthetic. No API spend occurs until you run generate.
