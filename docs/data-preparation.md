# P0 data and workload preparation

## Rules
- No artificial positive/negative ratio, no query subsampling, no deduplication of queries.
- Retain the full author dataset. No sorting of the exported stored keys; partition layout is a separate future benchmark step.
- Raw and generated files are ignored by Git (large, may have redistribution restrictions). Each run writes hashes and counts.
- These scripts have not yet been run end-to-end on the full datasets in this environment.

| Dataset | Source | Stored keys | Workload status |
|---|---|---:|---|
| Shalla | How to Train Your Filter | 2,926,705 | official C generator: 10M uniform, 10M Zipf(1.5) |
| Reddit usernames | LITS | ~26M | official dataset; exact 2024 generator not found |
| GeoNames | LITS | ~7M | same |
| US addresses | LITS | ~34M | same |

## Shalla
Paper: https://arxiv.org/abs/2602.13484
Upstream: https://github.com/saltsystemslab/How-to-Train-Your-Filter/tree/c970c3436465355e8b13c6d525bcc0dc72620312
The pinned repository contains the exact prepared Shalla CSV in data/compressed/shalla.tar.gz (53,971,021 bytes). The Python wrapper compiles the unchanged official C generator, runs its original 10M queries for each distribution, maps Zipf ranks exactly as the authors' convert_query_binaries.py does (NumPy permutation seed 0), and exports the keys from the CSV in index order. The binary generator's uniform rand() implementation is platform dependent; use Linux/GCC for reproducibility. The manifest records actual positive/negative query counts. No one-pass workload is included in this initial preparation.

Requires Python 3.12+, NumPy, GCC and Internet access.

    python3 -m pip install -r requirements.txt
    python3 scripts/prepare_shalla.py

Outputs: data/shalla/dataset.txt, queries_uniform.txt, queries_zipf.txt, indices_uniform.npy, indices_zipf.npy, manifest.json. Original archive, CSV and C sources are cached in .upstream/shalla.

## LITS datasets
Paper: https://arxiv.org/html/2407.11556v1 (Table 1, section 4.1)
Official archive: https://pan.baidu.com/s/1ZyA6YsdZoO4Pt6t2suKoMw?pwd=m5dl (code m5dl).
Download the authors' prepared reddit, geoname and address files from this folder and extract them; actual archive filenames could not be inspected here. Do not substitute newer datasets or apply new cleaning. Paper's cited original sources, for reference only:
- https://www.kaggle.com/datasets/colinmorris/reddit-usernames
- https://www.kaggle.com/datasets/geonames/geonames-database
- https://v2.openaddresses.io/batch-prod/collection-us-west.zip

The 2024 paper uses 20M point lookups, all stored keys loaded, uniform random or Zipf exponent 1. The public original LITS/testbench.cpp is a reduced synthetic-only benchmark. No exact original real-data 2024 query file or generator has been found. If present in the author archive, use those files instead. Do not describe the following as exact LITS 2024 workloads.

### Optional official LITS+ (2026) generator
Pinned upstream: https://github.com/schencoding/lits/tree/ce211d7c0aa15f833eaba5e342951ed49c3b81ba
The later author implementation has YCSB_C and generateQueriesZipf_YCSB_C in LITS+/LIT+/microbench/bench.cpp. The wrapper uses those routines without changing the sampling logic. It only adapts the Entry type and exports the queue. Note the official non-Zipf routine cycles through sorted keys then shuffles the read list, rather than independently drawing uniform indices; with more than 20M keys it selects only the first 20M lexicographic keys. We explicitly name it uniform_cycle and do not claim it is the 2024 uniform workload. Zipf ranks are likewise assigned to the original code's lexicographically sorted temporary list. Neither sorts the exported dataset used for partitioning.

After downloading the authors' cleaned text files (requires a C++17 compiler and substantial RAM/disk):

    python3 scripts/prepare_lits.py reddit /path/to/reddit.txt --acknowledge-litsplus
    python3 scripts/prepare_lits.py geonames /path/to/geoname.txt --acknowledge-litsplus
    python3 scripts/prepare_lits.py us_addresses /path/to/address.txt --acknowledge-litsplus

Each directory under data/ has dataset.txt, queries_litsplus_uniform_cycle.txt, queries_litsplus_zipf.txt and manifest.json. Every query is globally positive; no artificially constructed misses.
