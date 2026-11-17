# Experiment 2 — Partition size sensitivity

Full Shalla dataset, 2,926,705 unique keys, and the two unchanged official 10M query workloads. Use shuffle seed 55 and the same permutation for all partition sizes; smaller full partitions nest within larger ones. The final partial partition is retained. Exact frequency-weighted evaluation (no sampling). No AI or learned parameter selection.

Primary: P = 500, 2000, 8000, 32000, 128000; nominal 0.512, 1.024, 2.048, 4.096 bits per row; B=P*BPK/8. Supplement: fixed 256 bytes at all P (reuse overlaps). 23 unique configurations, two workloads each.

Methods: exact Oracle; 32-byte truncated MinMax at every budget as lower-cost reference; theoretically optimized integer-k Bloom (same hash family as pilot, k recomputed for P); fixed prefix and prefix-suffix character maps (128 bits/position, bounded to 64 and 32+32 positions respectively, and to maximum stored length); JointCharacterMap (single hashed tuple of positions 0,1,-2,-1 using full budget); legacy first/last 16B pair map + BF; scaled 4-position joint map (max(16,B/8) bytes) + BF; first/last CM + BF; Length + BF. All components conservative. Fixed maps stop allocating at the documented position cap rather than padding unused capacity. Thus budget is a maximum, not necessarily identical actual metadata. Actual serialized byte count, used bytes and actual BPK reported; shared schema counts separately in total bytes. Oracle is an unbudgeted reference, its zero metadata is a placeholder, not its true storage cost. MinMax and Oracle are repeated at each cap for ease of comparison. The scaled hybrid is a fixed exploratory design, not an optimized winner. Byte positions (Shalla is ASCII). Missing aliases zero only in the legacy single-position bitmap.

Metrics: pruning_pct counts query-partition pairs; partition_fpr_pct conditions on exact nonmembership; oracle_capture_pct = 100 - partition_fpr_pct when FN=0; retained_rows_pct accounts for unequal last partition. Global-negative pruning also reported. FN checks are exact for all observed matching query-partition pairs; fail on any FN. Offline bitset postings are not production latency. All comparison schemes serialize fixed-width payloads with shared schema; results.csv contains actual file sizes.

Run:
    mkdir -p build results
    g++ -std=c++17 -O3 -march=native experiments/partition_sensitivity.cpp -o build/partition_sensitivity
    build/partition_sensitivity data/shalla results/p8000_b1024 8000 1024

GitHub Actions uses the verified artifact from run 44195004791; if expired, rerun data preparation and run locally or update run-id. Only CSV and data manifests are uploaded; summary binaries are produced and measured on runner but can be regenerated locally.
