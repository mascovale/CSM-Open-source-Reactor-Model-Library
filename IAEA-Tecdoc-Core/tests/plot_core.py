"""
tests/plot_core.py
------------------
2D cross-section plots of the IAEA TECDOC-643 10 MW LEU reactor geometry.

TECDOC-faithful axial model (control blade at f=1, all-out):
  CORE_BOTTOM = -65 cm  (vacuum)
  [-65, -45]  : 20 cm light water
  [-45, -30]  : 15 cm homogenized end-box  (25 % Al / 75 % H₂O by vol.)
  [-30, +30]  : 60 cm active fuel
  [+30, +45]  : 15 cm homogenized end-box
  [+45, +95]  : 50 cm light water  (Hf blade tip reaches +90 at f=1)
  CORE_TOP    = +95 cm  (vacuum)

Four views:
  [top-left]     XY at z = 0      full core top-down (fuel midplane)
  [top-right]    XZ at y = 0      full 160 cm height — axial zone stack
  [bottom-left]  YZ at x = C2_x  full height through control rod C2
  [bottom-right] XY at z = +60   blade cross-section plane (Hf visible)

Run from the repo root:
    conda activate openmc
    python tests/plot_core.py
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, 'model'))

from geometry import (
    geometry,
    PITCH_X, PITCH_Y, HALF_Z,
    CORE_BOTTOM, CORE_TOP,
    ENDBOX_ABOVE_TOP, ENDBOX_BELOW_BOT,
)
from materials import (
    fuel, clad, water, b4c, graphite, aluminum, end_box_homog,
)

# =============================================================================
# Colour map
# =============================================================================

COLORS = {
    fuel:          (210,  55,  55),   # red         — U₃Si₂-Al fuel meat
    clad:          (200, 200, 200),   # light gray  — Al cladding
    water:         ( 85, 175, 235),   # sky blue    — moderator / coolant
    graphite:      ( 65,  65,  65),   # dark gray   — reflector
    aluminum:      (165, 165, 200),   # silver-blue — structural Al
    b4c:       ( 25, 120,  55),   # dark green  — Hf absorber blade
    end_box_homog: (215, 165,  75),   # amber       — 25 % Al / 75 % H₂O
}

def _rgb(mat):
    return tuple(c / 255.0 for c in COLORS[mat])

# =============================================================================
# Derived geometry constants
# =============================================================================

CORE_Z_CTR    = 0.5 * (CORE_TOP + CORE_BOTTOM)   # +15.0 cm
CORE_Z_HEIGHT = CORE_TOP - CORE_BOTTOM             # 160.0 cm
CORE_X_HALF   = 4.0 * PITCH_X                      # 30.8 cm
CORE_Y_HALF   = 4.5 * PITCH_Y                      # 36.45 cm

# Control rod C2 sits at lattice row 4, col 2  (0-indexed from bottom-left).
# Centre: x = lower_left_x + 2.5*PITCH_X = -4*PITCH_X + 2.5*PITCH_X = -1.5*PITCH_X
#         y = lower_left_y + 4.5*PITCH_Y = -4.5*PITCH_Y + 4.5*PITCH_Y = 0
C2_X = -1.5 * PITCH_X   # ≈ −11.55 cm
C2_Y =  0.0             # cm

# View widths — add a small margin so core edges are visible
_PAD   = 3.0                      # cm padding each side
W_XY   = 2 * CORE_X_HALF + _PAD  # ≈ 64.6 cm
H_XY   = 2 * CORE_Y_HALF + _PAD  # ≈ 75.9 cm
W_AX   = W_XY                     # axial-view x-width (same as XY)
H_AX   = CORE_Z_HEIGHT + _PAD     # ≈ 163 cm  (full height + margin)
W_YZ   = H_XY                     # y-axis width for YZ view

# Axial zone boundaries (z values of the four internal transitions)
ZONE_BOUNDS = [
    (CORE_BOTTOM,      ENDBOX_BELOW_BOT, 'lower\nwater',   '+'),
    (ENDBOX_BELOW_BOT, -HALF_Z,          'lower\nend-box', '×'),
    (-HALF_Z,           HALF_Z,          'active\nfuel',   ''),
    ( HALF_Z,          ENDBOX_ABOVE_TOP, 'upper\nend-box', '×'),
    (ENDBOX_ABOVE_TOP, CORE_TOP,         'upper\nwater',   '+'),
]

Z_LINES = [ENDBOX_BELOW_BOT, -HALF_Z, HALF_Z, ENDBOX_ABOVE_TOP]  # dashed lines at these z


def annotate_axial_zones(ax, x_half, color='white'):
    """Draw dashed horizontal lines + right-margin labels for axial zones."""
    for z in Z_LINES:
        ax.axhline(z, color=color, lw=0.8, ls='--', alpha=0.55)
    for (z_lo, z_hi, label, _) in ZONE_BOUNDS:
        ax.text(
            x_half - 0.4, 0.5 * (z_lo + z_hi),
            label,
            color=color, fontsize=6.5, va='center', ha='right',
            bbox=dict(facecolor='black', alpha=0.30, pad=1.5, edgecolor='none'),
        )


# =============================================================================
# Figure layout  (2 × 2)
# =============================================================================

fig, axes = plt.subplots(
    2, 2,
    figsize=(16, 20),
    gridspec_kw={'hspace': 0.10, 'wspace': 0.08},
)

fig.suptitle(
    'IAEA TECDOC-643  Generic 10 MW LEU Research Reactor — Geometry  '
    '(control blades all-out, f = 1)\n'
    'Axial stack (cm):  '
    '[-65, -45] water  |  [-45, -30] end-box  |  '
    '[-30, +30] active fuel  |  [+30, +45] end-box  |  [+45, +95] water',
    fontsize=9.5,
    y=0.998,
)

PLOT_KW = dict(color_by='material', colors=COLORS)

# ── [0, 0]  XY at z = 0 — full core top-down ────────────────────────────────
geometry.plot(
    basis='xy', origin=(0.0, 0.0, 0.0),
    width=(W_XY, H_XY), pixels=(1200, 1400),
    axes=axes[0, 0], **PLOT_KW,
)
axes[0, 0].set_title('XY  z = 0 cm  (fuel midplane, top-down)', fontsize=10)
axes[0, 0].set_xlabel('x  (cm)', fontsize=9)
axes[0, 0].set_ylabel('y  (cm)', fontsize=9)

# ── [0, 1]  XZ at y = 0 — full 160 cm height ────────────────────────────────
geometry.plot(
    basis='xz', origin=(0.0, 0.0, CORE_Z_CTR),
    width=(W_AX, H_AX), pixels=(1200, 1800),
    axes=axes[0, 1], **PLOT_KW,
)
axes[0, 1].set_title('XZ  y = 0 cm  (full height)', fontsize=10)
axes[0, 1].set_xlabel('x  (cm)', fontsize=9)
axes[0, 1].set_ylabel('z  (cm)', fontsize=9)
annotate_axial_zones(axes[0, 1], x_half=W_AX / 2)

# ── [1, 0]  YZ at x = C2_x — full height through control rod C2 ─────────────
geometry.plot(
    basis='yz', origin=(C2_X, 0.0, CORE_Z_CTR),
    width=(W_YZ, H_AX), pixels=(1200, 1800),
    axes=axes[1, 0], **PLOT_KW,
)
axes[1, 0].set_title(
    f'YZ  x = {C2_X:.1f} cm  (through C2 — full height)', fontsize=10)
axes[1, 0].set_xlabel('y  (cm)', fontsize=9)
axes[1, 0].set_ylabel('z  (cm)', fontsize=9)
annotate_axial_zones(axes[1, 0], x_half=W_YZ / 2)

# ── [1, 1]  XY at z = +60 — blade cross-section plane ───────────────────────
# At f=1 the Hf blade occupies z = [+30, +90]; z = +60 cuts through the blade
# above the fuel, clearly showing absorber positions against a water background.
geometry.plot(
    basis='xy', origin=(0.0, 0.0, 60.0),
    width=(W_XY, H_XY), pixels=(1200, 1400),
    axes=axes[1, 1], **PLOT_KW,
)
axes[1, 1].set_title(
    'XY  z = +60 cm  (blade cross-section, all-out)\n'
    'Hf blade at [+30, +90] cm — green stripes are absorber', fontsize=9.5)
axes[1, 1].set_xlabel('x  (cm)', fontsize=9)
axes[1, 1].set_ylabel('y  (cm)', fontsize=9)

# =============================================================================
# Shared material legend  (one row below the subplots)
# =============================================================================

legend_handles = [
    mpatches.Patch(
        facecolor=_rgb(mat),
        edgecolor='#555',
        linewidth=0.5,
        label=mat.name,
    )
    for mat in COLORS
]

fig.legend(
    handles=legend_handles,
    loc='lower center',
    bbox_to_anchor=(0.5, -0.025),
    ncol=len(legend_handles),
    frameon=True,
    fontsize=9,
    title='Materials',
    title_fontsize=9,
)

plt.tight_layout(rect=(0, 0.03, 1, 0.997))

# =============================================================================
# Save
# =============================================================================

out_dir  = os.path.join(REPO_ROOT, 'plots')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'core_geometry_plots.png')
fig.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"Saved: {out_path}")

plt.show()
