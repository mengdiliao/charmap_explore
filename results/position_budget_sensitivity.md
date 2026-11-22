# Selected position combinations — budget and partition sensitivity

Full Shalla; 2,926,705 stored keys; full official 10M-query Uniform and Zipf workloads;
partition seed 55; fnv1a-mix-v1; all methods use the same bitmap budget at each setting.
Candidates are selected **post hoc** using Experiment 3 at P=8000, B=512B.
This is a sensitivity analysis, **not** an independent validation of AI superiority.

| Method | Origin | Selected positions |
|---|---|---|
| ReferenceJointCM | Fixed baseline | (0,1,-2,-1) |
| AI_Uniform | AI, best uniform (A1_04) | (0,1,-5,-1) |
| AI_Zipf | AI, best zipf (A1_03) | (0,4,-5,-1) |
| Random_Uniform | Random, best uniform (R1_02) | (1,3,5,11) |
| Random_Zipf | Random, best zipf (R1_06) | (6,7,-10,-5) |

## Wins against OptimizedBloom across 23 settings

| Method | Uniform wins | Zipf wins |
|---|---:|---:|
| ReferenceJointCM | 6/23 | 3/23 |
| AI_Uniform | 6/23 | 2/23 |
| AI_Zipf | 6/23 | 2/23 |
| Random_Uniform | 7/23 | 2/23 |
| Random_Zipf | 7/23 | 10/23 |

## Pruning at the original selection point (P=8000, B=512B)

| Method | Uniform % | Zipf % |
|---|---:|---:|
| Oracle | 99.7953 | 99.7420 |
| OptimizedBloom | 14.1506 | 14.5181 |
| ReferenceJointCM | 14.4001 | 4.6455 |
| AI_Uniform | 18.3266 | 6.1549 |
| AI_Zipf | 16.3150 | 9.0480 |
| Random_Uniform | 19.0296 | 12.9448 |
| Random_Zipf | 14.5168 | 22.0971 |

See CSV for all 322 method/workload/configuration rows, actual metadata,
false negatives, saturation, collisions and per-design collision-free ceilings.
The collision-free ceiling belongs to each individual position combination;
it is not a universal bound for character maps.
