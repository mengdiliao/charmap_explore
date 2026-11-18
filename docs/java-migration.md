# Java 21 migration

All four experiments now use shared Java code under src/charmap. Python still orchestrates the Claude experiment; Shalla's original upstream C query generator is unchanged. The retired C++ implementation is available in Git history at commit b948c10b57aa84857d0ba9a00d9f66ea1742fc5b; it is no longer present in the main working tree. 

Compile once: 
    mkdir -p build/classes
    javac --release 21 -d build/classes src/charmap/*.java

Run with java -Xmx4g -cp build/classes followed by charmap.ShallaPilot, charmap.PartitionSensitivity, charmap.JointProfile, or charmap.PositionEvaluator and the original arguments (see individual experiment documentation). Experiment 3 Python runner compiles and runs Java automatically.

Hash uses Java long wraparound, unsigned right shifts and remainder. Core.MT64 ports the original libstdc++ paired Fisher-Yates shuffle with exact unsigned multiplication, so no external layout or compiler-dependent shuffle is needed. ASCII input and unique stored keys required, consistent with validated Shalla data. Metrics retain frequency weights, physical summary serialization and last-partition row correction. Runtime/heap are distinct from physical summary metadata. Cross-language parity workflows compare historical results without overwriting them. No Claude API calls in CI.
