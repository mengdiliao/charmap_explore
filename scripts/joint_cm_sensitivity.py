#!/usr/bin/env python3
"""Sensitivity of frozen workload-specific winners; no AI calls or cross-workload evaluation."""
import argparse
import csv
from collections import Counter
from decimal import Decimal
import io
import json
from pathlib import Path
import shutil
import subprocess

from aggregate_results import (ROOT, FIELDS, RAW_METRICS, RAW_SETTINGS, fixed,
                               positive_pruning, require, index_unique)
from experiment3 import EXPECTED, HASH_VERSION, digest
from position_budget_sensitivity import BUDGETS

MASTER = ROOT / "results/joint_cm_comparison.csv"
OLD = ROOT / "results/non_character/position_budget_sensitivity.csv"
PLAN = ROOT / "experiments/joint_cm_sensitivity/config.json"
RAW = ROOT / "runs/joint_cm_sensitivity/evaluations.csv"
OUT = ROOT / "results/joint_cm_sensitivity.csv"
REPORT = OUT.with_suffix(".md")
WORKLOADS = ("uniform","zipf")
GROUPS = ("Oracle","OptimizedBloom","ReferenceJointCM","Random",
          "AI_NoCharacteristics","AI_HumanCharacteristics")
WINNERS = GROUPS[3:]
ANCHOR = (8000,512)
SEED = 55
# The original algorithm names are retained in old rows. New rows reuse their
# original E4 evaluator names so serialized metadata is comparable at the anchor.
LEGACY = {
    "uniform": {"Random":"Random_Uniform","AI_NoCharacteristics":"AI_Uniform"},
    "zipf": {"Random":"Random_Zipf","AI_NoCharacteristics":"AI_Zipf"},
}
KEY = ("workload","partition_size","budget_bytes","algorithm")
CORE = RAW_METRICS | RAW_SETTINGS | {"positions"}
# A renamed statistic can change only metadata size/BPK, not its pruning metrics.
PARITY = CORE - {"metadata_total_bytes","bpk"}


def read(path):
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    require(rows and all(None not in r and None not in r.values() for r in rows),
            f"Invalid CSV: {path}")
    return rows


def write(path, rows, fields=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream,fieldnames=fields or list(rows[0]),lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_bytes(stream.getvalue().encode("utf-8"))


def key(w,p,b,a):
    return (w,str(p),str(b),a)


def configurations(partition=None):
    return [(p,b) for p,bs in BUDGETS.items() if partition is None or p==partition for b in bs]


def make_plan():
    master = read(MASTER)
    chosen = {}
    for w in WORKLOADS:
        chosen[w] = {}
        for method in WINNERS:
            pool = [r for r in master if r["workload"]==w and r["method"]==method
                    and (int(r["partition_size"]),int(r["budget_bytes"]))==ANCHOR]
            require(len(pool)==12,f"Expected 12 anchor candidates: {w}/{method}")
            best = min(pool,key=lambda r:(-Decimal(r["pruning_pct"]),r["solution_id"]))
            require(best["hash_version"]==HASH_VERSION and int(best["partition_seed"])==SEED
                    and best["false_negatives"]=="0", "Invalid anchor settings")
            chosen[w][method] = {k:best[k] for k in ("solution_id","source_proposal_id",
                "positions","reason","pruning_pct","algorithm","generation_id","model","call")}
    return {"selection_point":{"partition_size":ANCHOR[0],"budget_bytes":ANCHOR[1]},
            "partition_seed":SEED,"hash_version":HASH_VERSION,"input_sha256":EXPECTED,
            "master_sha256":digest(MASTER),"historical_sweep_sha256":digest(OLD),
            "budgets":{str(p):bs for p,bs in BUDGETS.items()},"selected":chosen,
            "evaluation_scope":"matching_workload_only","selection":"fixed_post_hoc_best_at_anchor"}


def load_plan():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    require(plan==make_plan(),"Frozen plan differs from published source; do not silently reselect")
    return plan


def equal(a,b,fields,label):
    for field in fields:
        require(a[field]==b[field],f"{label}: mismatch {field}: {a[field]} vs {b[field]}")


def old_index(plan):
    rows = read(OLD)
    idx = index_unique(rows,KEY,"historical sweep")
    historical_methods = ("Oracle","OptimizedBloom","ReferenceJointCM",
                          "Random_Uniform","Random_Zipf","AI_Uniform","AI_Zipf")
    expected = {key(w,p,b,a) for w in WORKLOADS for p,b in configurations()
                for a in historical_methods}
    require(set(idx)==expected,"Incomplete historical 322-row matrix")
    anchor = {(r["workload"],r["solution_id"]):r for r in read(MASTER)}
    for w in WORKLOADS:
        for method in WINNERS[:2]:
            info=plan["selected"][w][method]
            alg=LEGACY[w][method]
            for p,b in configurations():
                row=idx[key(w,p,b,alg)]
                require(row["positions"]==info["positions"] and row["selection_workload"]==w
                        and row["source_proposal_id"]==info["source_proposal_id"],
                        f"Historical winner mismatch: {w}/{method}")
            equal(idx[key(w,*ANCHOR,alg)],anchor[w,info["solution_id"]],PARITY,
                  f"Historical anchor {w}/{method}")
        for method,sid in (("Oracle","ORACLE"),("OptimizedBloom","BLOOM")):
            equal(idx[key(w,*ANCHOR,method)],anchor[w,sid],CORE,f"Baseline anchor {w}/{method}")
    return idx


def validate_row(row,baseline):
    label=f"{row['workload']}/{row['partition_size']}/{row['budget_bytes']}/{row['algorithm']}"
    equal(row,baseline,RAW_SETTINGS | {"query_partition_pairs","oracle_retained"},label)
    pairs,ret,oracle=(int(row[k]) for k in ("query_partition_pairs","retained","oracle_retained"))
    require(int(row["false_negatives"])==0 and oracle<=ret<=pairs and
            int(row["false_positive_pairs"])==ret-oracle and
            pairs==int(row["queries"])*int(row["partitions"]) and
            int(row["global_positive"])+int(row["global_negative"])==int(row["queries"]) and
            0<=Decimal(row["pruning_pct"])<=100 and
            int(row["payload_used_bytes"])<=int(row["budget_bytes"]),f"Invalid metrics: {label}")
    if row["positions"]:
        require(Decimal(row["pruning_pct"])<=Decimal(row["exact_joint_pruning_pct"])+Decimal("0.0000001"),
                f"Exceeds exact projection ceiling: {label}")


def validate_new(rows,plan,old,workloads=WORKLOADS,partition=None):
    idx=index_unique(rows,KEY,"new evaluations")
    expected={key(w,p,b,a) for w in workloads for p,b in configurations(partition)
              for a in ("Oracle","OptimizedBloom",plan["selected"][w][WINNERS[2]]["algorithm"])}
    require(set(idx)==expected,"Unexpected or incomplete new evaluation matrix")
    anchor={(r["workload"],r["solution_id"]):r for r in read(MASTER)}
    for w in workloads:
        info=plan["selected"][w][WINNERS[2]]
        for p,b in configurations(partition):
            baseline=old[key(w,p,b,"OptimizedBloom")]
            for a in ("Oracle","OptimizedBloom"):
                equal(idx[key(w,p,b,a)],old[key(w,p,b,a)],CORE,f"Baseline parity {w}/{p}/{b}/{a}")
            row=idx[key(w,p,b,info["algorithm"])]
            validate_row(row,baseline)
            require(row["positions"]==info["positions"],"New candidate positions changed")
            if (p,b)==ANCHOR:
                equal(row,anchor[w,info["solution_id"]],CORE,f"Profiled anchor {w}")
    return idx


def run(w,p,data,out,heap):
    plan=load_plan()
    old=old_index(plan)
    data=data.resolve()
    for name in ("dataset.txt",f"queries_{w}.txt"):
        require(digest(data/name)==EXPECTED[name],f"Wrong pinned input: {name}")
    out.mkdir(parents=True,exist_ok=True)
    info=plan["selected"][w][WINNERS[2]]
    tsv=out/f"{w}_p{p}.tsv"
    tsv.write_text(info["algorithm"]+"\t"+info["positions"].replace(";","\t")+"\n",encoding="utf-8")
    rows=[]
    for _,b in configurations(p):
        tmp=out/f"raw_{w}_p{p}_b{b}"
        require(not tmp.exists(),f"Refusing to overwrite {tmp}")
        command=[str(ROOT/"gradlew"),"--no-daemon","--console=plain","experiment4Evaluator",
                 f"-PdatasetFile={data/'dataset.txt'}",f"-PqueryFile={data/f'queries_{w}.txt'}",
                 f"-Pworkload={w}",f"-PpartitionSize={p}",f"-Pbudget={b}",
                 f"-Pseed={SEED}",f"-Pheap={heap}",f"-Pcandidates={tsv.resolve()}",
                 f"-PoutputDir={tmp.resolve()}"]
        print(f"Running {w}, P={p}, B={b}",flush=True)
        subprocess.run(command,cwd=ROOT,check=True)
        rows.extend(read(tmp/"results.csv"))
        shutil.rmtree(tmp)
    validate_new(rows,plan,old,(w,),p)
    write(out/f"{w}_p{p}.csv",rows)
    print(f"Validated {len(rows)} rows for {w}, P={p}",flush=True)


def merge(source_dir,output=OUT,raw_path=RAW):
    plan=load_plan()
    old=old_index(plan)
    fresh=[]
    for w in WORKLOADS:
        for p in BUDGETS:
            fresh.extend(read(source_dir/f"{w}_p{p}.csv"))
    new=validate_new(fresh,plan,old)
    write(raw_path,fresh)
    results=combine(plan,old,new)
    write(output,results,FIELDS)
    output.with_suffix(".md").write_text(report(plan,results),encoding="utf-8")
    print(f"Published {len(results)} validated rows: {output}",flush=True)


def combine(plan,old,new):
    result=[]
    for w in WORKLOADS:
        for p,b in configurations():
            baselines={a:old[key(w,p,b,a)] for a in GROUPS[:3]}
            selected={m:plan["selected"][w][m] for m in WINNERS}
            nochar=old[key(w,p,b,LEGACY[w]["AI_NoCharacteristics"])]
            for method in GROUPS:
                info=selected.get(method,{})
                if method==WINNERS[2]:
                    row=new[key(w,p,b,info["algorithm"])]
                    source=str(RAW.relative_to(ROOT))
                else:
                    row=old[key(w,p,b,LEGACY[w].get(method,method))]
                    source=str(OLD.relative_to(ROOT))
                validate_row(row,baselines["OptimizedBloom"])
                rate=Decimal(row["pruning_pct"])
                record={k:row[k] for k in RAW_METRICS | RAW_SETTINGS}
                sid={"Oracle":"ORACLE","OptimizedBloom":"BLOOM","ReferenceJointCM":"REFERENCE"}.get(method)
                record.update(method=method,solution_id=sid or info["solution_id"],workload=w,
                    positions=row["positions"],position_count=str(len(row["positions"].split(";"))) if row["positions"] else "",
                    reason=info.get("reason",""),positive_pruning_pct=positive_pruning(row),
                    delta_bloom_pp=fixed(rate-Decimal(baselines["OptimizedBloom"]["pruning_pct"])),
                    delta_reference_pp=fixed(rate-Decimal(baselines["ReferenceJointCM"]["pruning_pct"])),
                    delta_ai_no_characteristics_best_pp=fixed(rate-Decimal(nochar["pruning_pct"])),
                    dataset="Shalla",partition_seed=str(SEED),hash_version=HASH_VERSION,
                    model=info.get("model",""),generation_id=info.get("generation_id",""),call=info.get("call",""),
                    source_proposal_id=info.get("source_proposal_id",""),algorithm=row["algorithm"],
                    components=row["components"],source_file=source)
                require(set(record)==set(FIELDS),"Output schema mismatch")
                result.append(record)
    require(len(result)==276 and len(index_unique(result,("workload","partition_size","budget_bytes","method"),"output"))==276,
            "Expected 276 rows")
    return result


def report(plan,rows):
    ix=index_unique(rows,("workload","partition_size","budget_bytes","method"),"report")
    lines=["# Joint CM sensitivity — selected workload-specific winners","",
           "Full Shalla, pinned 10M query occurrences per workload; seed 55, fnv1a-mix-v1.",
           "23 configurations per workload: 20 constant-BPK cases and 3 supplemental fixed-256B cases.",
           "All six winners were selected post hoc at P=8000, B=512B and frozen; each is evaluated only on its matching workload.",
           "230 historical rows reused; 46 new profiled rows. All 276 results have zero observed false negatives.",
           "The raw new evaluations include Oracle and Bloom solely for exact baseline parity checks.",
           "This measures configuration robustness of selected maps, not causal effects of profiling or generalization.","",
           "| Workload | Method | Solution | Positions | Anchor pruning (%) |","|---|---|---|---|---:|"]
    for w in WORKLOADS:
        for m in WINNERS:
            r=plan["selected"][w][m]
            lines.append(f"| {w} | {m} | {r['solution_id']} | {r['positions']} | {float(r['pruning_pct']):.4f} |")
    for w in WORKLOADS:
        lines.extend(["",f"## {w.capitalize()}","",
                      "| Partition size | Budget B | BPK | Oracle | Bloom | Reference | Random best | AI no characteristics | AI human characteristics |",
                      "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for p,b in configurations():
            scores=[float(ix[key(w,p,b,m)]["pruning_pct"]) for m in GROUPS]
            lines.append(f"| {p} | {b} | {8*b/p:.3f} | "+" | ".join(f"{s:.4f}" for s in scores)+" |")
        lines.extend(["","### Wins vs. Bloom (constant-BPK configurations only)","",
                      "| Method | 0.512 | 1.024 | 2.048 | 4.096 |","|---|---:|---:|---:|---:|"])
        for m in GROUPS[2:]:
            wins=[]
            for factor in (1,2,4,8):
                cases=[(p,b) for p,b in configurations() if b*8000==512*p*factor]
                wins.append(str(sum(Decimal(ix[key(w,p,b,m)]["pruning_pct"])>
                                    Decimal(ix[key(w,p,b,"OptimizedBloom")]["pruning_pct"]) for p,b in cases))+"/5")
            lines.append(f"| {m} | "+" | ".join(wins)+" |")
        cases=configurations()
        hc=max(cases,key=lambda pb:Decimal(ix[key(w,*pb,WINNERS[2])]["delta_bloom_pp"]))
        hcrow=ix[key(w,*hc,WINNERS[2])]
        lines.extend(["",f"Best profiled-vs-Bloom delta across the 23 settings: {float(hcrow['delta_bloom_pp']):+.4f} pp at P={hc[0]}, budget={hc[1]}B.",
                      "The fixed-256B supplemental cases can have negligible absolute pruning even when one method wins."])
    lines.extend(["","The CSV retains actual serialized BPK; configured BPK is 8 × budget_bytes / partition_size. The exact projection ceiling varies with positions and partition size.",""])
    return "\n".join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="cmd",required=True)
    sub.add_parser("freeze",help="Create the immutable selected-candidate plan")
    sub.add_parser("validate",help="Check source and frozen selections")
    r=sub.add_parser("run")
    r.add_argument("--workload",choices=WORKLOADS,required=True)
    r.add_argument("--partition-size",type=int,choices=list(BUDGETS),required=True)
    r.add_argument("--data",type=Path,default=ROOT/"data/shalla")
    r.add_argument("--out",type=Path,required=True)
    r.add_argument("--heap",default="4g")
    m=sub.add_parser("merge")
    m.add_argument("--source-dir",type=Path,required=True)
    sub.add_parser("check",help="Rebuild and verify published CSV from archived raw evaluations")
    args=parser.parse_args()
    if args.cmd=="freeze":
        PLAN.parent.mkdir(parents=True,exist_ok=True)
        with PLAN.open("x",encoding="utf-8") as f:
            json.dump(make_plan(),f,indent=2)
            f.write("\n")
    elif args.cmd=="validate":
        old_index(load_plan())
        print("Validated frozen winners and historical matrix")
    elif args.cmd=="run":
        run(args.workload,args.partition_size,args.data,args.out,args.heap)
    elif args.cmd=="merge":
        merge(args.source_dir)
    else:
        plan=load_plan()
        old=old_index(plan)
        new=validate_new(read(RAW),plan,old)
        rows=combine(plan,old,new)
        require(read(OUT)==rows and REPORT.read_text(encoding="utf-8")==report(plan,rows),
                "Published results or report differ from reproducible output")
        print("Verified all 276 published rows and report")


if __name__=="__main__":
    main()
