#!/usr/bin/env python3
"""Four descriptive figures for all candidates at P=8000, budget=512B."""
from joint_cm_plotting import *


def validate(rows):
    if len(rows) != 76 or {r["workload"] for r in rows} != set(WORKLOADS):
        raise ValueError("Expected the published 76-row comparison")
    for w in WORKLOADS:
        for m in ("Oracle", "OptimizedBloom"):
            one(rows, workload=w, method=m)
        for m in CANDIDATES:
            group = subset(rows, workload=w, method=m)
            if len(group) != 12 or len({r["solution_id"] for r in group}) != 12:
                raise ValueError(f"Expected 12 distinct candidates: {w}/{m}")
    if any(r["partition_size"] != "8000" or r["budget_bytes"] != "512"
           or int(r["false_negatives"]) != 0 for r in rows):
        raise ValueError("Unexpected comparison configuration or false negatives")


def distribution(rows, args):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4), sharey=True)
    heading(fig, "Pruning performance distribution", "Shalla | P = 8,000 | budget = 512 B | 12 candidates per group")
    rng = np.random.default_rng(55)
    for ax, w in zip(axes, WORKLOADS):
        groups = [values(subset(rows, workload=w, method=m), "pruning_pct") for m in CANDIDATES]
        bp = ax.boxplot(groups, widths=.48, patch_artist=True, whis=(0,100), showfliers=False,
                        medianprops={"color": "#222222", "linewidth": 1.5})
        for i, (m, data, box) in enumerate(zip(CANDIDATES, groups, bp["boxes"]), 1):
            box.set(facecolor=COLORS[m], alpha=.22, edgecolor=COLORS[m])
            ax.scatter(i+rng.uniform(-.13,.13,len(data)),data,color=COLORS[m],
                       s=24,alpha=.8,zorder=3,edgecolors="white",linewidths=.35)
        bloom = float(one(rows, workload=w, method="OptimizedBloom")["pruning_pct"])
        ax.axhline(bloom, color=COLORS["OptimizedBloom"], ls="--", lw=1.2,
                   label=f"Bloom: {bloom:.2f}%")
        ax.set(xticks=[1,2,3],xticklabels=[SHORT[m] for m in CANDIDATES],
               ylim=(0,25),title=w.capitalize())
        grid(ax)
        ax.legend(loc="upper left",frameon=False)
    axes[0].set_ylabel("Pruning rate (%)")
    fig.text(.5,.035,"Boxes: IQR and median; whiskers: full range; dots: individual candidates (not independent AI calls).",
             ha="center",fontsize=8)
    fig.subplots_adjust(top=.83,bottom=.21,wspace=.12)
    save(fig,args,"pruning_distribution")


def membership(rows,args):
    fig,axes=plt.subplots(1,2,figsize=(9.6,4.3),sharey=True)
    heading(fig,"Pruning by query membership","Mean pruning rate across 12 candidates per selection method")
    x=np.arange(3)
    for ax,w in zip(axes,WORKLOADS):
        groups=[subset(rows,workload=w,method=m) for m in CANDIDATES]
        rate=100*int(groups[0][0]["global_positive"])/int(groups[0][0]["queries"])
        for j,(field,label,color) in enumerate([
            ("positive_pruning_pct","Globally positive","#0072B2"),
            ("negative_pruning_pct","Globally negative","#E69F00")]):
            v=[values(g,field).mean() for g in groups]
            bars=ax.bar(x+(j-.5)*.32,v,.31,color=color,label=label)
            ax.bar_label(bars,fmt="%.1f",padding=2,fontsize=8)
        ax.set(xticks=x,xticklabels=[SHORT[m] for m in CANDIDATES],
               title=f"{w.capitalize()} ({rate:.2f}% positive)",ylim=(0,26))
        grid(ax)
    axes[0].set_ylabel("Pruning rate (%)")
    fig.legend(*axes[0].get_legend_handles_labels(),loc="lower center",ncol=2,frameon=False)
    fig.subplots_adjust(top=.82,bottom=.25,wspace=.12)
    save(fig,args,"positive_negative_pruning")


def tradeoff(rows,args):
    fig,axes=plt.subplots(2,2,figsize=(8.7,6.6),sharex=True,sharey="row")
    heading(fig,"Discrimination and bitmap saturation","Each marker is one candidate; fixed P = 8,000 and budget = 512 B")
    for col,w in enumerate(WORKLOADS):
        for row,field in enumerate(("exact_joint_pruning_pct","pruning_pct")):
            ax=axes[row,col]
            for m in CANDIDATES:
                group=subset(rows,workload=w,method=m)
                ax.scatter(values(group,"mean_saturation_pct"),values(group,field),
                           color=COLORS[m],marker=MARKERS[m],s=31,alpha=.85,
                           edgecolors="white",linewidths=.35)
            if row==1:
                bloom=float(one(rows,workload=w,method="OptimizedBloom")["pruning_pct"])
                ax.axhline(bloom,color=COLORS["OptimizedBloom"],ls="--",lw=1)
                ax.set_xlabel("Mean bitmap saturation (%)")
            ax.set(xlim=(30,92),ylim=(0,100 if row==0 else 25))
            ax.grid()
            if row==0: ax.set_title(w.capitalize())
            if col==0: ax.set_ylabel("Exact joint pruning (%)" if row==0 else "Actual pruning (%)")
    legend=[Line2D([],[],color=COLORS[m],marker=MARKERS[m],linestyle="none",label=LABELS[m])
            for m in CANDIDATES]
    legend.append(Line2D([],[],color=COLORS["OptimizedBloom"],ls="--",label="Bloom (actual)"))
    fig.legend(handles=legend,loc="lower center",ncol=2,frameon=False)
    fig.subplots_adjust(top=.85,bottom=.16,hspace=.20,wspace=.16)
    save(fig,args,"discrimination_saturation")


def position_frequency(rows,args):
    positions=list(range(16))+list(range(-16,0))
    specs=[("Random","uniform","Random (shared)"),
           ("AI_NoCharacteristics","uniform","AI without characteristics (shared)"),
           ("AI_HumanCharacteristics","uniform","AI with human characteristics — Uniform"),
           ("AI_HumanCharacteristics","zipf","AI with human characteristics — Zipf")]
    counts=[]
    for m,w,_ in specs:
        group=subset(rows,workload=w,method=m)
        if m!="AI_HumanCharacteristics":
            other=subset(rows,workload="zipf",method=m)
            if {(r["solution_id"],r["positions"]) for r in group}!={(r["solution_id"],r["positions"]) for r in other}:
                raise ValueError(f"Expected shared positions for {m}")
        selections=[set(map(int,r["positions"].split(";"))) for r in group]
        if any(not s.issubset(positions) for s in selections):
            raise ValueError("Position outside search space")
        counts.append([sum(p in s for s in selections) for p in positions])
    fig,ax=plt.subplots(figsize=(13,3.3))
    heading(fig,"Character position selection frequency","Full 32-position search space | counts out of 12 candidates")
    image=ax.imshow(counts,cmap="Blues",vmin=0,vmax=12,aspect="auto")
    ax.set(xticks=np.arange(32),xticklabels=positions,yticks=np.arange(4),
           yticklabels=[s[2] for s in specs],xlabel="Character position (negative indices count from the end)")
    ax.axvline(15.5,color="#222222",lw=1.3)
    for i,row in enumerate(counts):
        for j,v in enumerate(row):
            ax.text(j,i,str(v),ha="center",va="center",fontsize=8,color="white" if v>=7 else "#222222")
    fig.colorbar(image,ax=ax,ticks=[0,3,6,9,12],label="Selection count",pad=.015)
    fig.subplots_adjust(left=.28,right=.96,top=.77,bottom=.23)
    save(fig,args,"position_frequency")


def main():
    args=arguments("comparison")
    rows=read(args.input)
    validate(rows)
    for plot in (distribution,membership,tradeoff,position_frequency):
        plot(rows,args)


if __name__=="__main__":
    main()
