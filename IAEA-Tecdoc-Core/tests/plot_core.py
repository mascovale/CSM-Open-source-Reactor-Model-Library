"""
plot_core.py
------------
Generate 2D cross-section plots of the IAEA 10 MW reactor geometry
in the XY, XZ, and YZ planes for visual verification.

Uses OpenMC's Python plotting API (Geometry.plot) — no separate
'openmc' binary call needed. Plots open interactively if you have
a display, and are saved to ./plots/ either way.

Run from the repo root with the OpenMC conda env active:
    conda activate openmc
    python tests/plot_core.py
"""

import os
import sys

import matplotlib.pyplot as plt

# Path setup — must come AFTER os/sys imports, BEFORE geometry import
THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, 'model'))

from geometry import geometry, PITCH_X, PITCH_Y
from materials import (
    fuel, clad, water, hafnium, graphite, aluminum, air,
)

# =============================================================================
# Color assignments — passed to Geometry.plot() so each material gets a
# consistent, meaningful color across all four views.
# =============================================================================

colors = {
    fuel:      (220,  60,  60),   # red
    clad:      (200, 200, 200),   # light gray
    water:     (135, 206, 250),   # light blue
    graphite:  ( 80,  80,  80),   # dark gray
    aluminum:  (180, 180, 200),   # silver-blue
    hafnium:   ( 30, 100,  60),   # dark green
    air:       (255, 255, 255),   # white
}

# =============================================================================
# Control element centers
# =============================================================================
# Based on the 8-column x 9-row core lattice.
# These are global coordinates in cm.

CONTROL_CENTERS = {
    "C0": (-0.5 * PITCH_X,  2.0 * PITCH_Y),
    "C1": ( 1.5 * PITCH_X,  1.0 * PITCH_Y),
    "C2": (-1.5 * PITCH_X,  0.0 * PITCH_Y),
    "C3": ( 1.5 * PITCH_X, -1.0 * PITCH_Y),
    "C4": (-0.5 * PITCH_X, -2.0 * PITCH_Y),
}

CTRL_NAME = "C0"
CTRL_X, CTRL_Y = CONTROL_CENTERS[CTRL_NAME]

# =============================================================================
# Build a 2x2 figure with one subplot per view.
# Geometry.plot() takes a matplotlib Axes via `axes=` and draws into it.
# =============================================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 14))

# --- XY midplane (top-down at z=0) ---
geometry.plot(
    basis='xy',
    origin=(0.0, 0.0, 0.0),
    width=(70.0, 80.0),
    pixels=(1400, 1600),
    color_by='material',
    colors=colors,
    axes=axes[0, 0],
)
axes[0, 0].set_title('XY midplane (z = 0)')

# --- XZ slice through y=0 ---
geometry.plot(
    basis='xz',
    origin=(0.0, 0.0, 0.0),
    width=(70.0, 90.0),
    pixels=(1400, 1800),
    color_by='material',
    colors=colors,
    axes=axes[0, 1],
)
axes[0, 1].set_title('XZ side (y = 0)')

# --- YZ slice through x=0 ---
geometry.plot(
    basis='yz',
    origin=(-PITCH_X / 2.0, 0.0, 0.0),   # land on element center, not gap
    width=(80.0, 90.0),
    pixels=(1600, 1800),
    color_by='material',
    colors=colors,
    axes=axes[1, 0],
)
axes[1, 0].set_title('YZ front (x = 0)')

# --- XY zoom on a single fuel element ---
# Lattice has 8 columns (even) -> origin x=0 falls between elements;
# offset by half a pitch to land on a real element center.
# --- XY zoom on a single control element ---
geometry.plot(
    basis='xy',
    origin=(CTRL_X, CTRL_Y, 0.0),
    width=(7.65, 8.05),
    pixels=(1700, 1800),
    color_by='material',
    colors=colors,
    axes=axes[1, 1],
)
axes[1, 1].set_title(f'XY zoom — control element {CTRL_NAME}')

plt.tight_layout()

# =============================================================================
# Save and (if possible) show
# =============================================================================

from matplotlib.patches import Patch

# Build legend handles from the same colors dict used for the plots.
# Convert the (R,G,B) 0-255 tuples into matplotlib's 0-1 range.
legend_handles = [
    Patch(facecolor=tuple(c / 255 for c in rgb),
          edgecolor='black',
          label=mat.name)
    for mat, rgb in colors.items()
]

# Place a single legend at the top of the figure, spanning all subplots.
fig.legend(
    handles=legend_handles,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.5),   # tweak Y if it overlaps the top titles
    ncol=len(legend_handles),     # one row of swatches
    frameon=True,
    fontsize=10,
    title='Materials',
)

# Make room at the top so the legend doesn't overlap subplot titles
plt.tight_layout(rect=(0, 0, 1, 0.95))

out_dir = os.path.join(REPO_ROOT, 'plots')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'core_geometry_plots.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"Saved: {out_path}")

# plt.show() will pop up an interactive window if a display is available
# (e.g. WSLg on Windows 11, or X-forwarding). Harmless if it can't.
plt.show()
