# Experiment 4 — uniform (profiled call 1)

| Group | Proposal | Positions | Pruning % | Delta vs Bloom (pp) | Delta vs E3 best (pp) |
|---|---|---|---:|---:|---:|
| Oracle |  |  | 99.7953 | +85.6447 | +81.4686 |
| OptimizedBloom |  |  | 14.1506 | +0.0000 | -4.1761 |
| Experiment3BestAI | A1_04 | 0;1;-5;-1 | 18.3266 | +4.1761 | +0.0000 |
| Experiment4ProfiledAI | A01 | 4;5;-6;-5 | 14.8827 | +0.7322 | -3.4439 |
| Experiment4ProfiledAI | A02 | 4;6;-7;-5 | 14.5709 | +0.4203 | -3.7558 |
| Experiment4ProfiledAI | A03 | 5;6;-6;-5 | 15.1006 | +0.9500 | -3.2261 |
| Experiment4ProfiledAI | A04 | 4;5;6;-5 | 15.1495 | +0.9989 | -3.1771 |
| Experiment4ProfiledAI | A05 | 4;7;-6;-5 | 14.6687 | +0.5181 | -3.6580 |
| Experiment4ProfiledAI | A06 | 0;5;-6;-5 | 16.3943 | +2.2438 | -1.9323 |
| Experiment4ProfiledAI | A07 | 4;5;-8;-5 | 14.5975 | +0.4470 | -3.7291 |
| Experiment4ProfiledAI | A08 | 5;7;-7;-6 | 14.7475 | +0.5969 | -3.5792 |
| Experiment4ProfiledAI | A09 | 4;5;6;-7;-6;-5 | 14.3818 | +0.2312 | -3.9449 |
| Experiment4ProfiledAI | A10 | 4;5;-6;-5;-1 | 14.5822 | +0.4316 | -3.7445 |
| Experiment4ProfiledAI | A11 | 0;4;5;-6;-5 | 14.6655 | +0.5149 | -3.6612 |
| Experiment4ProfiledAI | A12 | 4;6;-5 | 14.0877 | -0.0629 | -4.2390 |

Profiled best / mean / median: 16.3943% / 14.8191% / 14.6671%.
Above E3 best: 0/12; above Bloom: 11/12.
All results are in-sample. Experiment 3 best is selected post hoc; workload-specific prompting and profile information changed together. No causal attribution to the profile alone.
