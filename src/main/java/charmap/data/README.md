# Data loading and partition layout

Reads the already prepared Shalla files. No download or generation is performed by these Java classes.

| File | Responsibility |
| --- | --- |
| [DatasetLoader.java](DatasetLoader.java) | Reads dataset.txt and both query files using ASCII, rejects duplicate stored keys and empty inputs, counts query multiplicities, and invokes the deterministic shuffle. |
| [LoadedData.java](LoadedData.java) | Holds stored keys, the union of stored/query keys, per-workload occurrence counts, global query counts, and partition membership. No file I/O. |
| [PartitionLayout.java](PartitionLayout.java) | Implements the pinned MT19937-64/libstdc++-compatible shuffle and assigns partition IDs from shuffled key indices (index / P). Updates positive-query counts from membership. |

The evaluator uses P=8000 and seed 55. The final partition may be smaller. Queries absent from the whole dataset have partition ID -1. Query multiplicities are preserved, even though repeated keys need only one pruning evaluation.

See [input preparation](../../../../../docs/data-preparation.md) for the raw files and exact provenance.
