"""Shared plotting conventions for Joint CM thesis figures."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORKLOADS = ("uniform", "zipf")
CANDIDATES = ("Random", "AI_NoCharacteristics", "AI_HumanCharacteristics")
METHODS = ("OptimizedBloom", "ReferenceJointCM", *CANDIDATES)
LABELS = {"Oracle": "Oracle", "OptimizedBloom": "Optimized Bloom",
          "ReferenceJointCM": "Reference Joint CM", "Random": "Random",
          "AI_NoCharacteristics": "AI without characteristics",
          "AI_HumanCharacteristics": "AI with human characteristics"}
SHORT = {"Random": "Random", "AI_NoCharacteristics": "AI without\ncharacteristics",
         "AI_HumanCharacteristics": "AI with human\ncharacteristics"}
COLORS = {"Oracle": "#999999", "OptimizedBloom": "#343434",
          "ReferenceJointCM": "#888888", "Random": "#D55E00",
          "AI_NoCharacteristics": "#0072B2", "AI_HumanCharacteristics": "#009E73"}
MARKERS = {"OptimizedBloom": "s", "ReferenceJointCM": "x", "Random": "^",
           "AI_NoCharacteristics": "o", "AI_HumanCharacteristics": "D"}
FORMATS = ("svg", "pdf", "png")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.titlesize": 10, "axes.labelsize": 10,
                     "legend.fontsize": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.axisbelow": True,
                     "grid.alpha": 0.25, "grid.linewidth": 0.6,
                     "svg.hashsalt": "joint-cm-v1", "svg.fonttype": "none",
                     "pdf.fonttype": 42, "savefig.facecolor": "white"})


def arguments(name):
    p = argparse.ArgumentParser(description=f"Plot {name} figures from the published CSV.")
    p.add_argument("--input", type=Path, default=ROOT / "results" / f"joint_cm_{name}.csv")
    p.add_argument("--out", type=Path, default=ROOT / "results/figures" / name)
    p.add_argument("--formats", nargs="+", choices=FORMATS, default=list(FORMATS))
    return p.parse_args()


def read(path):
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or any(None in r or None in r.values() for r in rows):
        raise ValueError(f"Empty or malformed CSV: {path}")
    return rows


def subset(rows, **filters):
    return [r for r in rows if all(r[k] == str(v) for k, v in filters.items())]


def one(rows, **filters):
    matches = subset(rows, **filters)
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {filters}; got {len(matches)}")
    return matches[0]


def values(rows, field):
    a = np.asarray([float(r[field]) for r in rows])
    if not len(a) or not np.isfinite(a).all():
        raise ValueError(f"Missing or nonfinite metric: {field}")
    return a


def handles(methods=METHODS):
    return [Line2D([], [], color=COLORS[m], marker=MARKERS[m],
                   linestyle="--" if m == "ReferenceJointCM" else "-",
                   label=LABELS[m], linewidth=1.5, markersize=4) for m in methods]


def line(ax, x, y, method):
    ax.plot(x, y, color=COLORS[method], marker=MARKERS[method],
            linestyle="--" if method == "ReferenceJointCM" else "-",
            linewidth=2.0 if method == "AI_HumanCharacteristics" else 1.4,
            markersize=4)


def grid(ax):
    ax.grid(axis="y")


def save(fig, args, stem):
    args.out.mkdir(parents=True, exist_ok=True)
    for ext in dict.fromkeys(args.formats):
        path = args.out / f"{stem}.{ext}"
        meta = {"Date": None} if ext == "svg" else (
            {"CreationDate": None, "ModDate": None} if ext == "pdf" else {})
        fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.12, metadata=meta)
        print(path)
    plt.close(fig)


def heading(fig, title, subtitle):
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.985)
    fig.text(0.5, 0.94, subtitle, ha="center", fontsize=9, color="#555555")
