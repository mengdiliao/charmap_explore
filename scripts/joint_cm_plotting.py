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
FORMATS = ("png",)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.titlesize": 10, "axes.labelsize": 10,
                     "legend.fontsize": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.axisbelow": True,
                     "grid.alpha": 0.25, "grid.linewidth": 0.6,
                     "savefig.facecolor": "white"})


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


def layout_heading(fig):
    """Place the subtitle below the measured title, using physical point gaps.

    Check the rendered header and subplot decorations at the export DPI,
    rather than relying on a fixed fraction of the figure's height.
    """
    title, subtitle = fig._joint_cm_heading
    fig.set_dpi(300)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px_per_pt = fig.dpi / 72
    height = fig.bbox.height
    title_box = title.get_window_extent(renderer)
    subtitle.set_y((title_box.y0 - 7 * px_per_pt) / height)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    subtitle_box = subtitle.get_window_extent(renderer)
    # Include axes titles and colorbars in the clearance check.
    for _ in range(4):
        boxes = [ax.get_tightbbox(renderer) for ax in fig.axes if ax.get_visible()]
        axes_top = max(b.y1 for b in boxes if b is not None)
        deficit = axes_top + 10 * px_per_pt - subtitle_box.y0
        if deficit <= 0.25 * px_per_pt:
            break
        new_top = fig.subplotpars.top - (deficit + 2 * px_per_pt) / height
        if new_top <= fig.subplotpars.bottom + .15:
            raise ValueError("Insufficient space for figure header")
        fig.subplots_adjust(top=new_top)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    else:
        raise ValueError("Figure heading overlaps subplot decorations")

    title_box = title.get_window_extent(renderer)
    subtitle_box = subtitle.get_window_extent(renderer)
    gap_pt = (title_box.y0 - subtitle_box.y1) / px_per_pt
    axes_gap_pt = (subtitle_box.y0 - axes_top) / px_per_pt
    if gap_pt < 6 or axes_gap_pt < 9:
        raise ValueError("Figure title/subtitle or subplot spacing is too small")
    for box in (title_box, subtitle_box):
        if box.x0 < 0 or box.x1 > fig.bbox.width or box.y0 < 0 or box.y1 > height:
            raise ValueError("Figure heading extends outside the canvas")
    return gap_pt, axes_gap_pt


def save(fig, args, stem):
    args.out.mkdir(parents=True, exist_ok=True)
    gap, axes_gap = layout_heading(fig)
    path = args.out / f"{stem}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.12)
    print(f"{path} | title/subtitle gap: {gap:.1f} pt | subtitle/axes gap: {axes_gap:.1f} pt")
    plt.close(fig)


def heading(fig, title, subtitle):
    title_artist = fig.suptitle(title, fontsize=13, fontweight="bold",
                               y=0.98, va="top")
    subtitle_artist = fig.text(0.5, 0.9, subtitle, ha="center", va="top",
                               fontsize=9, color="#555555")
    fig._joint_cm_heading = (title_artist, subtitle_artist)
