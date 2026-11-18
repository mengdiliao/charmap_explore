# Gradle quick start

JDK 21, Python 3.10+; the committed official Gradle 8.14.3 wrapper downloads its pinned distribution on first use. No separate Gradle installation needed. JUnit 5.11.4 runs correctness tests. Production Java sources are organized below src/main/java/charmap in hashing, encoding, data, serialization, statistics, evaluation and experiments; test source is src/test/java/charmap. Existing source data, results, and experiment parameters are unchanged.

    ./gradlew --version
    ./gradlew build
    ./gradlew test
    ./gradlew tasks --group experiments

Run experiments from repo root after preparing the same data files:

    ./gradlew shallaPilot -Pbudget=256
    ./gradlew partitionSensitivity -PpartitionSize=8000 -Pbudget=512
    ./gradlew jointProfile
    ./gradlew positionEvaluator -Pcandidates=runs/experiment3_level1/designs.tsv

Use -PdataDir=/path/to/data/shalla and -PoutputDir=/path/to/results to override paths. Use -Pheap=6g or JAVA_HEAP=6g to change experiment heap (default 4g). positionEvaluator accepts -Pseed=55. The Python Experiment 3 commands prepare, generate, freeze, evaluate, report are unchanged; evaluate uses Gradle directly with absolute paths and records build/source hashes and wrapper/JVM info.

The first build requires network access for the Gradle distribution and JUnit dependency download. No API calls are made by Gradle tests. The full Shalla CI jobs compare with archived C++ CSVs as before. Original upstream C workload generator is preserved.
