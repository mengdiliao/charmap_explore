# Experiment 4 — Simple Statistical Profiling (preparation only)

## Goal

Measure whether adding eight simple dataset/workload characteristics improves AI-guided selection of one Joint Character Map's positions. Uniform and Zipf are separate target-workload experiments, not a single joint objective. This branch only prepares inputs and prompts; it does not invoke AI, freeze candidates, evaluate candidates, or modify Experiment 3's Java implementation/results.

## Run

Python 3.10+; no additional Python package is required for this stage. Obtain the pinned ASCII Shalla text files using [data preparation](data-preparation.md). Download a Public Suffix List snapshot once and use the identical local file for both experiments (do not refresh it between runs):

```bash
mkdir -p data/shalla
curl --fail --location https://publicsuffix.org/list/public_suffix_list.dat -o data/shalla/public_suffix_list.dat

python3 scripts/experiment4.py prepare --workload uniform \
  --psl data/shalla/public_suffix_list.dat --out runs/experiment4_uniform

python3 scripts/experiment4.py prepare --workload zipf \
  --psl data/shalla/public_suffix_list.dat --out runs/experiment4_zipf
```

The default input directory is data/shalla. The workload flag selects queries_uniform.txt or queries_zipf.txt. To explicitly select input files, use --dataset-file and --query-file (and still specify --workload). --data selects a directory instead. Only the selected query file is read; the other is not required. Default checks verify the selected file and dataset against the Experiment 3 pinned SHA-256 values. Use --allow-unpinned only for intentionally different inputs, and --examples with a JSON object of actual stored strings if the original samples are not members of your dataset. The workload label must describe the supplied query file; a checksum cannot verify its distribution.

By default, a seeded Bernoulli split (seed 155, holdout probability 0.2) produces approximately 80% training and 20% holdout occurrences, preserving relative order. Counts and all query characteristics in the prompt use training occurrences only. Both files are saved for subsequent evaluation; repeated keys may appear in both splits, intentionally testing the same query distribution, not unseen-key generalization. --split-seed and --holdout-fraction configure the split. For an explicitly in-sample exploratory profile or an externally prepared training file, use --holdout-fraction 0 (empty generated holdout); do not claim out-of-sample evaluation without independent queries. Use fresh output paths. The profiler aborts rather than overwrites an existing run, including an incomplete one.

## Eight characteristics

| Dataset | Workload (separately per selected file) |
| --- | --- |
| D1: structural category distribution | W1: structural category distribution |
| D2: length distribution plus min/max/mean/median | W2: global positive rate by category |
| D3: top five raw 3-character prefixes | W3: top ten frequent query keys, occurrence shares, membership flags, combined share |
| D4: top five raw 3-character suffixes | W4: length distribution |

Dataset statistics are over unique stored keys (duplicates rejected); workload statistics are weighted by query occurrences, not distinct values. Global membership is exact raw-key equality against the full dataset. Zero-query categories have null positive rates; all percentages are rounded to four decimal places. Top lists use frequency descending, then raw ASCII lexicographic order to break ties. Prefix/suffix counts use exactly three raw characters and all stored keys as denominator; keys shorter than three do not contribute a token.

Length buckets: 4–7, 8–11, 12–15, 16–19, 20–23, 24–31, 32+. If any input used for profiling has lengths below four, rerun **both** experiments with --first-length-bucket 0 so the common first bucket is 0–7. Counts, not rounded percentages, are authoritative.

Classification: use a local Public Suffix List ICANN section, including wildcard/exception rules and the default wildcard rule for unknown suffixes. Private suffixes (e.g. blogspot.com) are deliberately excluded so hosting-service labels remain visible as subdomains. Classification is case-insensitive and removes one final DNS root dot; no normalization is applied to stored keys, membership, lengths, prefix/suffix or hot-key statistics. Only raw syntactically valid hostname-like strings or IPv4 are classified; URLs with schemes/paths, IPv6, malformed/non-DNS hosts or suffix-only names are Other. No network lookups or URL parsing.

| Category | Example |
| --- | --- |
| ipv4 | 192.0.2.1 |
| plain_domain | example.co.uk |
| www_domain | www.example.com |
| subdomain_without_www | blog.example.com |
| subdomain_with_www | www.blog.example.com |
| other (only if present) | invalid/path |

WWW means the first extra label preceding the registrable domain is exactly www, not a generic prefix. Other is included in both tables in a run if encountered on either side. Categories are mutually exclusive. The original representative samples are reused unchanged.

## Outputs per run

```text
runs/experiment4_uniform/   # or experiment4_zipf/
  dataset_profile.json     # counts, percentages, length summary, prefix/suffix lists
  workload_profile.json    # training-only counts, membership, hot keys
  prompt_profile.json      # compact percentages and hot keys fed to AI
  examples.json            # preserved representative sample strings
  prompt.md                # workload-specific prompt + profile
  prompt_control.md        # matched workload-specific prompt without profile
  queries_train.txt        # exact training split
  queries_holdout.txt      # exact held-out split
  public_suffix_list.dat   # exact PSL snapshot
  config.json              # input/output hashes, settings, split sizes, timings
```

The two prompts use the same single-workload objective, original structural samples, model settings, reference positions, budget and candidate constraints; the only textual addition to the profiled arm is the statistical profile and its definitions. Historical scores from the old hashing version are deliberately omitted in both. A matched control matters because Experiment 3 optimized both workloads jointly; a comparison only against its historic AI proposals would confound profiling with the workload-specific objective. The current FNV-1a/mix hashing description is used, not the historical base-257 mapping description.

No API calls are performed. The existing Experiment 3 generate/freeze/evaluate commands assume two workloads and a different config format: do not pass Experiment 4 folders to those commands. Later integration should evaluate both arms and random controls on the same saved holdout for the selected workload, with P=8000, 512B, seed 55, zero false negatives, and matched candidate length distributions. Keep full-data Experiment 3 results as historical reference only.

## Test

```bash
python3 -m unittest discover -s scripts -p 'test_experiment4.py' -v
```

Tests exercise PSL boundaries, wildcard/exception handling, frequency-weighted statistics, deterministic split, independent prompts, and output hashes using synthetic fixtures; the full Shalla files are not required. Full runs retain the dataset membership set and selected training query Counter in memory and write split files to disk. Measure actual runtime and memory on the real data. Generated files are ignored by Git under data/ and runs/.
