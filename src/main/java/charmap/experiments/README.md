# Experiment entry points

The primary entry point for the reported stage result is PositionEvaluator.java.

| File | Responsibility |
| --- | --- |
| [PositionEvaluator.java](PositionEvaluator.java) | Experiment 3: loads prepared data, reads frozen candidate positions, evaluates all Joint CMs, optimized Bloom and Oracle in position mode. |
| [JointProfile.java](JointProfile.java) | Standalone reference pair/four-position diagnostics across partition sizes and budgets. Supports full-data verification; does not evaluate the 24 AI/random proposals. |
| [PartitionSensitivity.java](PartitionSensitivity.java) | Earlier partition-size/budget benchmark entry point; retained for reproducibility. |
| [ShallaPilot.java](ShallaPilot.java) | Earlier fixed-P baseline pilot entry point; retained for reproducibility. |

The published run is reproduced with the [root instructions](../../../../../README.md#reproduce-the-published-result). Python orchestrates the Gradle positionEvaluator task, passing dataDir, outputDir, candidates, partitionSize, budget and seed. Its candidates file is generated from the frozen designs. The other entry points are not required to reproduce the published Experiment 3 results.
