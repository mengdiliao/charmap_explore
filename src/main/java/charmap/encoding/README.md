# Character encoding

[CharacterEncoding.java](CharacterEncoding.java) handles the character projection shared by joint statistics and their diagnostics.

| Method / field | Responsibility |
| --- | --- |
| REF | Reference positions [0,1,-2,-1]. |
| ch(s,p) | Extract one character; negative positions count from the end, missing positions return 128. |
| extractCharacters(s,positions) | Materialize the ordered sequence of selected symbols, including MISSING. |
| token(s,positions) | Encode a fixed-length tuple losslessly as a base-257 long. |
| pair(s,p,q) | Encode a two-symbol tuple as a base-256 long for the earlier pair diagnostics. |
| decodeToken(token,length,base) | Recover the fixed-length sequence from its integer representation. |

Example: www.example.com with positions [0,1,-2,-1] produces wwom. Actual Joint CM bitmap mapping processes the projected symbols through FNV-1a; it does **not** hash the base-257 integer. The exact integer encoding allows fast comparisons, NDV counting and exact projection pruning without bitmap collisions. Its injectivity requires a fixed tuple length, valid symbols, and no integer overflow; all Experiment 3 tuples (2–6 ASCII/MISSING symbols) meet those conditions.

See [hashing](../hashing/README.md) and [evaluation](../evaluation/README.md).
