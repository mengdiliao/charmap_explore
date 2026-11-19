# Evaluation

Builds partition statistics, evaluates equality pruning and reports exact diagnostics.

| File | Responsibility |
| --- | --- |
| [Evaluator.java](Evaluator.java) | Creates Bloom and candidate Joint CMs in position mode, builds their bitmaps, writes metadata, evaluates frequency-weighted query–partition pairs, checks false negatives and produces results.csv. Also implements exact full-key Oracle membership and earlier evaluation modes. |
| [JointDiagnostics.java](JointDiagnostics.java) | Counts exact projected token NDVs per partition using lossless base-257 longs and calculates exact projection pruning using query frequencies. Also counts occupied bitmap bits. |
| [ResultWriter.java](ResultWriter.java) | Shared CSV formatting, percentage calculation, output writer and position formatting. |

The benchmark evaluates each distinct query key once, then weights its result by its occurrences in each workload. Oracle retains only the partition containing a stored key, or none for a globally absent key. The evaluator aborts on false negatives or a reported joint pruning rate above its exact projection ceiling.

Diagnostics distinguish projection loss (different full keys share a token) from bitmap collision loss (different tokens share a bit). The exact token sets are offline analysis data, not part of the 512-byte payload.

See [metric definitions](../../../../../docs/experiment3-level1.md#5-evaluation) and [serialization](../serialization/README.md).
