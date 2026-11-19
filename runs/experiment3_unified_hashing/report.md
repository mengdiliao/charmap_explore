# Experiment 3 — Level 1 results

Hash version: fnv1a-mix-v1.
Full Shalla workload.
Unique joint maps: 25; proposal count: 24.

| Workload | Group | Call | N | Best % | Median % | Mean % | Above Bloom |
|---|---|---:|---:|---:|---:|---:|---:|
| uniform | AI | 1 | 12 | 18.3266 | 15.0514 | 14.8116 | 6 |
| uniform | Random | 1 | 12 | 19.0296 | 15.2104 | 14.9342 | 9 |

uniform: Bloom 14.1506%, reference 14.4001%.

| zipf | AI | 1 | 12 | 9.0480 | 5.7864 | 6.0322 | 0 |
| zipf | Random | 1 | 12 | 22.0971 | 11.0700 | 11.3581 | 2 |

zipf: Bloom 14.5181%, reference 4.6455%.


Replayed the original frozen AI and Random designs; no new AI calls. Original prompt is preserved for provenance.

Full workload exploration, no held-out test. Best is selected post hoc, not independently validated. All repeated proposals retained in proposal_results.csv.
