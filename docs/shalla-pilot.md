# Shalla non-AI pilot

Use the full prepared Shalla dataset (2,926,705 stored rows) and both original 10M-query workloads, unchanged. The evaluation aggregates duplicate queries by exact string and weights by their original multiplicity, so every query-partition pair is counted. No resampling or change of positive fraction.

- P=500, fixed random shuffle seed 55 for partition layout. Original dataset and query files are not altered. This layout targets unclustered data, not the original source order.
- 32/64/128/256-byte per-partition payloads, with actual serialized summary size including its global schema and header. MinMax32 only uses 32B payload; Oracle has no budget.
- Original fixed position maps use 128-bit maps per position (byte modulo 128; missing aliases zero). This is conservative even for non-ASCII bytes, with possible extra false positives. A joint first/last map hashes tuples into 128 bits. Length map uses 64 buckets with saturated final bucket. All character positions are byte positions.
- Bloom k chosen by minimizing textbook FPR for 500 distinct keys. Hashes use FNV-1a and splitmix-style mixing by index, shared between baseline and hybrids. This is not an exhaustive empirical tuning of Bloom parameters.
- Equal payload sizes, small differing global schema sizes reported separately in metadata_total_bytes and BPK.
- Full exact membership check for every queried matching partition; fail on any observed FN. MinMax uses conservative fixed 16-byte zero-padded prefixes.
- Offline posting intersections accelerate exact metrics; not production query time. This is a preliminary comparison with fixed designs, not AI or tuned mappings.
- Both workloads share the same partition layout; no holdout needed for these fixed designs. Future selection/AI must separate evolution and holdout by key.

Run locally after preparing Shalla:

    mkdir -p build results
    g++ -std=c++17 -O3 -march=native experiments/shalla_pilot.cpp -o build/shalla_pilot
    for b in 32 64 128 256; do
      build/shalla_pilot data/shalla results/b$b $b
    done

GitHub Actions uses the verified Shalla artifact from run 44195004791, which expires after 30 days. Regenerate or run locally if expired. Results include CSV and physical summary binaries.
