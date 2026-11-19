# Shalla data and workloads

The Experiment 3 dataset and query workloads are derived from [How to Train Your Filter](https://arxiv.org/abs/2602.13484), using the authors' [pinned repository](https://github.com/saltsystemslab/How-to-Train-Your-Filter/tree/c970c3436465355e8b13c6d525bcc0dc72620312) and archive data/compressed/shalla.tar.gz (Git blob b1747b1229a5bc4041b7c28b829b0cb05182257a).

The script [prepare_shalla.py](../scripts/prepare_shalla.py) downloads the archive, verifies its Git blob hash and extracts shalla_combined.csv. Rows with label 1 become the stored keys; label 0 rows are nonmembers. The original candidate pool has 3,905,928 rows, of which 2,926,705 are stored and 979,223 are nonmembers. The benchmark uses 2,926,705 unique stored ASCII strings.

| Query workload | Occurrences | Globally positive | Globally negative |
| --- | ---: | ---: | ---: |
| Uniform | 10,000,000 | 7,493,560 (74.94%) | 2,506,440 |
| Zipfian (1.5) | 10,000,000 | 9,442,030 (94.42%) | 557,970 |

The original authors' C generator is compiled unchanged and used to produce the two query index streams locally. Zipf ranks are mapped with the authors' NumPy permutation (seed 0). The workload files are exported as text. These are generated with the authors' method, not newly downloaded query text files. No artificial positive/negative ratio, query subsampling, or loss of multiplicities is introduced. Stored keys are exported in source order; the Java benchmark subsequently uses its pinned seed-55 shuffle rather than sorting keys.

## Obtain the exact inputs

Download the [prepared GitHub Actions artifact](https://github.com/mengdiliao/charmap_explore/actions/runs/44195004791/artifacts/14377239207) if it is still available (requires repo access; artifact retention is limited). Extract at the repository root so the following files exist:

```text
data/shalla/
├── dataset.txt
├── queries_uniform.txt
├── queries_zipf.txt
├── indices_uniform.npy
├── indices_zipf.npy
└── manifest.json
```

Only the three text files are needed for evaluation. If the artifact has expired, regenerate on Linux with Python 3.12+, NumPy, GCC and network access:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/prepare_shalla.py
```

The C generator's rand() is platform-dependent; native macOS regeneration may not produce the pinned hashes. The upstream files are cached under .upstream/shalla. Input data are not tracked in Git.

## Verify inputs

From the repository root:

```bash
python3 -c "from scripts.experiment3 import verify; from pathlib import Path; print(verify(Path('data/shalla')))"
```

Expected SHA-256 (also recorded in the [published config](../runs/experiment3_unified_hashing/config.json)):

| File | SHA-256 |
| --- | --- |
| dataset.txt | `081bf7628046d046533f63ed2e049e4aff6bd21d3151b64a41c8cbfc584a4a2a` |
| queries_uniform.txt | `095d4cbd2cc6091bd6a660ad0826c203b00b8d70c364a0eb8319b86d49529fb8` |
| queries_zipf.txt | `7058cc63df718c76872a6788a35161a2d19156db739c4400f2a548799559cc52` |

Use --data /path/to/shalla on the Python evaluate command if the prepared data live elsewhere.
