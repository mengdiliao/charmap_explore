# Experiment 4 — zipf (profiled call 1)

| Group | Proposal | Positions | Pruning % | Delta vs Bloom (pp) | Delta vs E3 best (pp) |
|---|---|---|---:|---:|---:|
| Oracle |  |  | 99.7420 | +85.2239 | +90.6941 |
| OptimizedBloom |  |  | 14.5181 | +0.0000 | +5.4701 |
| Experiment3BestAI | A1_03 | 0;4;-5;-1 | 9.0480 | -5.4701 | +0.0000 |
| Experiment4ProfiledAI | A01 | 4;5;-6;-5 | 15.5085 | +0.9904 | +6.4605 |
| Experiment4ProfiledAI | A02 | 4;6;-7;-5 | 10.7637 | -3.7543 | +1.7158 |
| Experiment4ProfiledAI | A03 | 5;6;-6;-5 | 8.0316 | -6.4865 | -1.0164 |
| Experiment4ProfiledAI | A04 | 4;5;6;-5 | 14.6027 | +0.0846 | +5.5547 |
| Experiment4ProfiledAI | A05 | 5;7;-7;-6 | 8.1880 | -6.3301 | -0.8600 |
| Experiment4ProfiledAI | A06 | 4;7;-8;-5 | 13.1012 | -1.4169 | +4.0532 |
| Experiment4ProfiledAI | A07 | 6;8;-6;-5 | 11.0018 | -3.5163 | +1.9538 |
| Experiment4ProfiledAI | A08 | 4;5;-9;-5 | 16.8694 | +2.3514 | +7.8215 |
| Experiment4ProfiledAI | A09 | 4;5;-7;-6;-5 | 16.3238 | +1.8057 | +7.2758 |
| Experiment4ProfiledAI | A10 | 4;6;8;-6;-5 | 11.5514 | -2.9667 | +2.5035 |
| Experiment4ProfiledAI | A11 | 4;5;6;-7;-6;-5 | 15.7859 | +1.2678 | +6.7379 |
| Experiment4ProfiledAI | A12 | 4;5;7;-8;-6;-5 | 11.1349 | -3.3832 | +2.0870 |

Profiled best / mean / median: 16.8694% / 12.7386% / 12.3263%.
Above E3 best: 10/12; above Bloom: 5/12.
All results are in-sample. Experiment 3 best is selected post hoc; workload-specific prompting and profile information changed together. No causal attribution to the profile alone.
