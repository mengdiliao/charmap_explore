#!/usr/bin/env python3
"""Four figures for the 23-configuration matched-workload sensitivity sweep."""
from joint_cm_plotting import *
from matplotlib.colors import TwoSlopeNorm

PARTITIONS=(500,2000,8000,32000,128000)
BPKS=(.512,1.024,2.048,4.096)
SUPPLEMENTAL={(8000,256),(32000,256),(128000,256)}
ANCHOR=(8000,512)


def budget(p,bpk):
    return round(p*bpk/8)


def validate(rows):
    config={(p,budget(p,b)) for p in PARTITIONS for b in BPKS}|SUPPLEMENTAL
    expected={(w,m,p,b) for w in WORKLOADS for m in ("Oracle",*METHODS) for p,b in config}
    actual={(r["workload"],r["method"],int(r["partition_size"]),int(r["budget_bytes"])) for r in rows}
    if actual!=expected or len(rows)!=len(expected):
        raise ValueError("Expected complete, unique 276-row matched-workload matrix")
    if any(int(r["false_negatives"])!=0 for r in rows):
        raise ValueError("False negatives in sensitivity data")
    for w in WORKLOADS:
        for m in CANDIDATES:
            rs=subset(rows,workload=w,method=m)
            if len({(r["solution_id"],r["positions"]) for r in rs})!=1:
                raise ValueError(f"Candidate changed during sweep: {w}/{m}")


def record(rows,w,m,p,b):
    return one(rows,workload=w,method=m,partition_size=p,budget_bytes=b)


def rate(rows,w,m,p,b):
    return float(record(rows,w,m,p,b)["pruning_pct"])


def p_label(p):
    return f"{p:,}"


def vs_bpk(rows,args):
    fig,axes=plt.subplots(2,5,figsize=(15,6.1),sharex=True,sharey=True)
    heading(fig,"Pruning rate versus configured bits per key",
            "Frozen workload-specific winners | each column fixes partition size | constant-BPK matrix")
    for i,w in enumerate(WORKLOADS):
        for j,p in enumerate(PARTITIONS):
            ax=axes[i,j]
            for m in METHODS:
                line(ax,BPKS,[rate(rows,w,m,p,budget(p,b)) for b in BPKS],m)
            ax.set(xscale="log",xticks=BPKS,xticklabels=[str(b) for b in BPKS],ylim=(0,100))
            ax.minorticks_off()
            grid(ax)
            if i==0: ax.set_title(f"P = {p_label(p)}")
            if j==0: ax.set_ylabel(f"{w.capitalize()}\nPruning rate (%)")
            if i==1: ax.set_xlabel("Configured BPK")
    fig.legend(handles=handles(),loc="lower center",ncol=3,frameon=False)
    fig.subplots_adjust(top=.85,bottom=.18,wspace=.12,hspace=.20)
    save(fig,args,"pruning_vs_bpk")


def vs_partition(rows,args):
    fig,axes=plt.subplots(2,4,figsize=(13.1,6.1),sharex=True,sharey=True)
    heading(fig,"Pruning rate versus partition size",
            "Frozen workload-specific winners | each column fixes configured BPK")
    for i,w in enumerate(WORKLOADS):
        for j,b in enumerate(BPKS):
            ax=axes[i,j]
            for m in METHODS:
                line(ax,PARTITIONS,[rate(rows,w,m,p,budget(p,b)) for p in PARTITIONS],m)
            ax.set(xscale="log",xticks=PARTITIONS,xticklabels=["500","2k","8k","32k","128k"],ylim=(0,100))
            ax.minorticks_off()
            grid(ax)
            if i==0: ax.set_title(f"{b:g} BPK")
            if j==0: ax.set_ylabel(f"{w.capitalize()}\nPruning rate (%)")
            if i==1: ax.set_xlabel("Partition size")
    fig.legend(handles=handles(),loc="lower center",ncol=3,frameon=False)
    fig.subplots_adjust(top=.85,bottom=.18,wspace=.12,hspace=.20)
    save(fig,args,"pruning_vs_partition_size")


def deltas(rows,args):
    panels=[]
    for w in WORKLOADS:
        for field in ("delta_bloom_pp","delta_ai_no_characteristics_best_pp"):
            matrix=np.array([[float(record(rows,w,"AI_HumanCharacteristics",p,budget(p,b))[field])
                              for b in BPKS] for p in PARTITIONS])
            panels.append(matrix)
    vmax=max(5,5*np.ceil(max(np.abs(a).max() for a in panels)/5))
    norm=TwoSlopeNorm(vmin=-vmax,vcenter=0,vmax=vmax)
    fig,axes=plt.subplots(2,2,figsize=(8.6,7.3),sharex=True,sharey=True)
    heading(fig,"Characteristics-guided pruning advantage",
            "AI with human characteristics minus comparison method | same configuration | percentage points")
    for i,w in enumerate(WORKLOADS):
        for j,base in enumerate(("Optimized Bloom","AI without characteristics")):
            ax=axes[i,j]
            a=panels[i*2+j]
            im=ax.imshow(a,cmap="RdBu",norm=norm,aspect="auto")
            ax.set(xticks=range(4),xticklabels=[str(b) for b in BPKS],
                   yticks=range(5),yticklabels=[p_label(p) for p in PARTITIONS],
                   title=f"{w.capitalize()} vs. {base}")
            for y in range(5):
                for x in range(4):
                    v=a[y,x]
                    ax.text(x,y,f"{v:+.1f}",ha="center",va="center",fontsize=9,
                            color="white" if abs(v)>.62*vmax else "#222222")
            if j==0: ax.set_ylabel("Partition size")
            if i==1: ax.set_xlabel("Configured BPK")
    fig.subplots_adjust(top=.85,bottom=.10,right=.87,hspace=.28,wspace=.16)
    cax=fig.add_axes([.90,.15,.025,.65])
    fig.colorbar(im,cax=cax,label="Pruning advantage (pp)")
    save(fig,args,"performance_delta")


def ceiling(rows,args):
    fig,axes=plt.subplots(1,2,figsize=(9.8,4.7),sharey=True)
    heading(fig,"Actual pruning and collision-free projection ceiling",
            "P = 8,000 | solid: measured pruning | dashed: exact projected-tuple pruning")
    p=ANCHOR[0]
    bpk=(.256,*BPKS)
    methods=CANDIDATES[1:]
    for ax,w in zip(axes,WORKLOADS):
        for m in methods:
            rs=[record(rows,w,m,p,budget(p,b)) for b in bpk]
            a=values(rs,"pruning_pct")
            exact=values(rs,"exact_joint_pruning_pct")
            if not np.allclose(exact,exact[0],rtol=0,atol=1e-7) or np.any(a>exact+1e-7):
                raise ValueError(f"Inconsistent fixed-projection ceiling: {w}/{m}")
            line(ax,bpk,a,m)
            ax.axhline(exact[0],color=COLORS[m],ls="--",lw=1.2)
            ax.fill_between(bpk,a,exact,color=COLORS[m],alpha=.08)
            ax.text(bpk[-1],exact[0]+1.5,f"{exact[0]:.1f}%",ha="right",fontsize=8,color=COLORS[m])
        ax.set(xscale="log",xticks=bpk,xticklabels=[str(b) for b in bpk],ylim=(0,100),
               xlabel="Configured BPK",title=w.capitalize())
        ax.minorticks_off()
        grid(ax)
    axes[0].set_ylabel("Pruning rate (%)")
    legend=handles(methods)+[Line2D([],[],color="#555555",ls="--",label="Exact projection ceiling")]
    fig.legend(handles=legend,loc="lower center",ncol=2,frameon=False)
    fig.subplots_adjust(top=.83,bottom=.24,wspace=.12)
    save(fig,args,"exact_pruning_ceiling")


def main():
    args=arguments("sensitivity")
    rows=read(args.input)
    validate(rows)
    for plot in (vs_bpk,vs_partition,deltas,ceiling):
        plot(rows,args)


if __name__=="__main__":
    main()
