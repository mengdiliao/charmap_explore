#!/usr/bin/env python3
"""Check all common archived CSV fields; exact discrete counts, 1e-8 floating tolerance."""
import csv, math, sys
from pathlib import Path
def load(p):
    with p.open() as f: return list(csv.DictReader(f))
def key(r):
    if "algorithm" in r: return tuple(r[k] for k in ("workload","algorithm","partition_size","budget_bytes"))
    if "rank" in r: return tuple(r[k] for k in ("tuple","source","rank"))
    if "source" in r: return (r["tuple"],r["source"])
    return (r["tuple"],r["partition_size"],r.get("budget_bytes",""))
def compare(new,old):
    a,b=load(new),load(old); ref={key(r):r for r in b}
    assert len(a)==len({key(r) for r in a}),"duplicate keys"
    # In a matrix job the archived file contains all configurations. Limit to the current P/B (pilot Oracle stores budget=0).
    if "algorithm" in a[0]:
        configs={(r["partition_size"],r["budget_bytes"]) for r in a if r["algorithm"]!="Oracle"}
        expect={key(r) for r in b if (r["partition_size"],r["budget_bytes"]) in configs or (r["algorithm"]=="Oracle" and r["budget_bytes"]=="0" and r["partition_size"] in {p for p,_ in configs})}
        # Pilot CSV repeats Oracle once per budget; comparison uses identical last value.
        assert set(map(key,a))==expect,(new,"missing or extra algorithms")
    else: assert set(map(key,a))==set(ref),(new,"missing/extra rows")
    for r in a:
        oldrow=ref[key(r)]
        for k,v in r.items():
            if k not in oldrow: continue
            x=oldrow[k]
            if v==x: continue
            if "." in v and "." in x:
                try:
                    if math.isclose(float(v),float(x),rel_tol=0,abs_tol=1e-8): continue
                except ValueError: pass
            raise AssertionError((new,key(r),k,v,x))
    print(f"Parity passed: {new}: {len(a)} rows")
a,b=map(Path,sys.argv[1:])
if a.is_dir():
    for p in sorted(b.glob("*.csv")):compare(a/p.name,p)
else:compare(a,b)
