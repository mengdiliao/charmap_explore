# Shalla joint character diagnostic

Full source dataset and both 10M query files, identical shuffle (std::mt19937_64 seed 55) and token encoding/hash to partition_sensitivity.cpp. All source rows asserted ASCII, no sampling. Pair = (0,-1) encoded base 256; four = (0,1,-2,-1) encoded base 257. Missing value 128 encoded distinctly, no OTHER. A one-bit hashed tuple summary is evaluated on its own, not combined with full-key Bloom.

- global.csv: distinct tokens, missing-row counts, tokens/queries unseen in the stored data, top token concentration.
- top_tokens.csv: top ten by occurrence count (query frequency includes repeats), with all three frequencies; ties ordered by numeric token.
- partitions.csv: actual per-block distinct tokens min/mean/median/p95/max; exact, collision-free token-pruning ceiling (full query-partition pairs, including members).
- bitmaps.csv: hash modulo B*8, per-partition occupancy, saturation and collisions. Global excess collision fraction = (global distinct tokens - occupied global buckets) / global distinct tokens. Partition collision fraction = sum(NDV - occupied buckets)/sum(NDV); not probability of a colliding pair. Saturation is average occupied bits / capacity. Hash collision loss = exact projection pruning minus hashed projection pruning in percentage points. Query weights and final partial partition retained; comparing pruning of unweighted partition pairs, not row read cost. Exact ceiling assumes collision-free direct tuple encoding, not that mapping overhead is free. Fixed byte budgets, previous fixed BPK sizes, and scaled joint-hybrid tuple capacities included.

Run locally with prepared data:
    mkdir -p build/classes
    javac --release 21 -d build/classes src/charmap/*.java
    java -Xmx4g -cp build/classes charmap.JointProfile data/shalla results/java_joint_profile

No parameter fitting, holdout required for any subsequent selection. Results are diagnostic on the full workloads.
