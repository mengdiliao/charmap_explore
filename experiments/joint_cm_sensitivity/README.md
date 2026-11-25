# Selected Joint CM configuration sensitivity

This analysis freezes the best Random, AI_NoCharacteristics and AI_HumanCharacteristics candidate separately for each workload at P=8000/B=512B from the published master CSV. The selected positions and source-file hashes are pinned in [config.json](config.json). Each candidate is evaluated **only on its matching workload**. No cross-workload evaluation, new AI calls, or candidate reselection is performed.

The original 23 settings are reused unchanged: P=500/2000/8000/32000/128000, configured BPK=0.512/1.024/2.048/4.096, plus 256B at P=8000/32000/128000. Oracle, OptimizedBloom, ReferenceJointCM and two historical winners are reused from results/non_character/position_budget_sensitivity.csv (230 rows). Only the two profiled winners need new sweeps (46 rows); the evaluator also recomputes Oracle and Bloom at each setting to check exact parity. The same pinned Shalla inputs, partition seed and hash function are used.

## Run locally

From the repository root, with JDK 21 and the three pinned files in data/shalla:

```bash
python3 scripts/joint_cm_sensitivity.py validate
for w in uniform zipf; do
  for p in 500 2000 8000 32000 128000; do
    python3 scripts/joint_cm_sensitivity.py run --workload "$w" --partition-size "$p" --out runs/joint_cm_sensitivity_parts
  done
done
python3 scripts/joint_cm_sensitivity.py merge --source-dir runs/joint_cm_sensitivity_parts
python3 scripts/joint_cm_sensitivity.py check
```

The same steps run in the GitHub Actions workflow. The final CSV and Markdown report are published only after all 10 workload/partition-size jobs pass, together with the raw newly measured rows (including duplicate baselines used for validation). The final comparison contains 276 rows and uses the master CSV's column schema. Actual serialized metadata sizes are preserved; older selected maps were serialized using the original sensitivity names, which can produce small name-related overhead differences from the master CSV. The anchor parity check excludes these name-related size differences for reused maps.

The fixed winners were selected post hoc on the original workloads. This is configuration robustness, not a claim of generalization to unseen workloads or a causal effect of the statistical profile alone.
