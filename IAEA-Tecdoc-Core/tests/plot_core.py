"""
tests/plot_core.py
------------------
2D cross-section plots of the IAEA TECDOC-643 10 MW LEU reactor geometry.

The geometry here is rebuilt with the control blades FULLY INSERTED
(withdrawn_fraction = 0.0) so the B4C absorber sits exactly in the active zone
z = [-30, +30] with no extension above the fuel.  Production runs set the blade
position through core.CoreConfig; this file only rebuilds a fresh f = 0
geometry for a clean plot.

Panel layout:
  [0,0] XY  z = 0      Full core top-down at fuel midplane (both flux traps marked).
  [0,1] XY  z = 0      Flux trap 1 detail — cylinder boundary annotated.
  [1,0] XZ  y = FT1_Y  Flux trap 1 column, cropped to the main components
                       (fuel + end boxes).
  [1,1] YZ  x = FT1_X  Flux trap 1 column, orthogonal cropped slice.
  [:,2] XZ  through C2 Full 160 cm height through a control element, spanning the
                       full figure height, for control-blade height reference.

Run from the repo root:
    conda activate openmc
    python tests/plot_core.py
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, 'model'))

import openmc
from geometry import (
    PITCH_X, PITCH_Y, HALF_Z, BLADE_LENGTH,
    CORE_BOTTOM, CORE_TOP,
    ENDBOX_ABOVE_TOP, ENDBOX_BELOW_BOT,
    FT_HOLE_RADIUS,
    ELEM_Y, ACTIVE_STACK_X, ABSORBER_THICK,
    CTRL_OUTER_OFFSET, CTRL_AL_PLATE_THICK, CTRL_BLADE_WATER,
    water_univ, graphite_univ, make_flux_trap,
    make_standard_fuel_element, make_control_fuel_element,
)
from materials import (
    fuel, clad, water, water_core, b4c, graphite, aluminum, end_box_homog,
)

# =============================================================================
# Rebuild geometry with control blades FULLY INSERTED (f = 0.0)
# =============================================================================

def build_geometry(f=1.0):
    """Fresh OpenMC geometry for blade withdrawn_fraction f (mirrors run scripts)."""
    std_elems  = [make_standard_fuel_element(i) for i in range(23)]
    ctrl_elems = [make_control_fuel_element(100 + i, withdrawn_fraction=f)
                  for i in range(5)]
    flux_trap  = make_flux_trap()

    W, G, S, C, F = water_univ, graphite_univ, std_elems, ctrl_elems, flux_trap

    lattice = openmc.RectLattice(name='core_lattice')
    lattice.pitch      = (PITCH_X, PITCH_Y)
    lattice.lower_left = (-4 * PITCH_X, -4.5 * PITCH_Y)
    lattice.universes  = [
        [W, W,     W,     W,     W,     W,     W,     W],
        [W, G,     G,     G,     G,     G,     G,     W],
        [W, S[0],  S[1],  C[0],  S[2],  S[3],  S[4],  W],
        [W, S[5],  S[6],  S[7],  S[8],  C[1],  S[9],  W],
        [W, S[10], C[2],  S[11], F,     S[12], S[13], W],
        [W, S[14], S[15], S[16], S[17], C[3],  S[18], W],
        [W, F,     S[19], C[4],  S[20], S[21], S[22], W],
        [W, G,     G,     G,     G,     G,     G,     W],
        [W, W,     W,     W,     W,     W,     W,     W],
    ]

    core_cell = openmc.Cell(
        name='core_cell', fill=lattice,
        region=(
            +openmc.XPlane(x0=-4   * PITCH_X, boundary_type='vacuum') &
            -openmc.XPlane(x0= 4   * PITCH_X, boundary_type='vacuum') &
            +openmc.YPlane(y0=-4.5 * PITCH_Y, boundary_type='vacuum') &
            -openmc.YPlane(y0= 4.5 * PITCH_Y, boundary_type='vacuum') &
            +openmc.ZPlane(z0=CORE_BOTTOM,     boundary_type='vacuum') &
            -openmc.ZPlane(z0=CORE_TOP,        boundary_type='vacuum')
        ),
    )
    return openmc.Geometry(openmc.Universe(cells=[core_cell]))


geometry = build_geometry(f=0.5)   # blades fully in

# =============================================================================
# Colour map
# =============================================================================

COLORS = {
    fuel:            (210,  55,  55),   # red          — U₃Si₂-Al fuel meat
    clad:            (200, 200, 200),   # light gray   — Al cladding
    water:           ( 85, 175, 235),   # sky blue     — outer pool water 294 K
    water_core:      ( 11,  34, 117),   # deep navy    — core coolant water 316.8 K
    graphite:        ( 65,  65,  65),   # dark gray    — graphite reflector
    aluminum:        (165, 165, 200),   # silver-blue  — structural Al
    b4c:             ( 25, 120,  55),   # dark green   — B₄C absorber blade
    end_box_homog:   (215, 165,  75),   # amber        — 25 % Al / 75 % H₂O
}

def _rgb(mat):
    return tuple(c / 255.0 for c in COLORS[mat])

# =============================================================================
# Geometry constants / slice locations
# =============================================================================

CORE_Z_CTR    = 0.5 * (CORE_TOP + CORE_BOTTOM)   # +15.0 cm
CORE_Z_HEIGHT = CORE_TOP - CORE_BOTTOM             # 160.0 cm
CORE_X_HALF   = 4.0 * PITCH_X                      # 30.8 cm
CORE_Y_HALF   = 4.5 * PITCH_Y                      # 36.45 cm

# Flux trap 1 — lattice universes[4][4]
FT1_X = 0.5  * PITCH_X    # ≈  3.85 cm
FT1_Y = 0.0               # cm

# Flux trap 2 — lattice universes[6][1]
FT2_X = -2.5 * PITCH_X    # ≈ -19.25 cm
FT2_Y = -2.0 * PITCH_Y    # ≈ -16.2 cm

# Control element C2 — lattice universes[4][2], centre (x, y)
C2_X = -1.5 * PITCH_X     # ≈ -11.55 cm
C2_Y =  0.0               # cm  (row 4 centre)
# XZ through the blade: slice at the bottom B4C-slot y (relative to the
# element centre) so the absorber band is captured in the constant-y plane.
# Wall -> fuel: offset water | outer guide | blade water | [B4C slot, here].
C2_BLADE_Y = C2_Y + (-ELEM_Y / 2.0 + CTRL_OUTER_OFFSET + CTRL_AL_PLATE_THICK
                     + CTRL_BLADE_WATER + ABSORBER_THICK / 2.0)  # ≈ -3.5003

# Blade z-extent at f = 0 (fully inserted)
BLADE_Z_BOT = -HALF_Z                 # -30 cm
BLADE_Z_TOP = -HALF_Z + BLADE_LENGTH  # +30 cm

# Full-core view extents
_PAD  = 3.0
W_XY  = 2 * CORE_X_HALF + _PAD   # ≈ 64.6 cm
H_XY  = 2 * CORE_Y_HALF + _PAD   # ≈ 75.9 cm

# Cropped axial views — "just the main components": fuel + both end boxes
MAIN_AX_HALF_Z = ENDBOX_ABOVE_TOP + 3.0   # ±48 cm  (fuel + end boxes + margin)
MAIN_AX_H      = 2 * MAIN_AX_HALF_Z         # ≈ 96 cm
W_AX_CROP      = W_XY                        # x-width for cropped XZ
W_YZ_CROP      = H_XY                        # y-width for cropped YZ

# Full-height side view (control blade reference)
H_AX_FULL = CORE_Z_HEIGHT + _PAD   # ≈ 163 cm
SIDE_W    = 3.0 * PITCH_X           # ≈ 23.1 cm x-window centred on C2

# Flux trap zoom (3×3 pitch cells)
FT_ZOOM_W = 3.0 * PITCH_X
FT_ZOOM_H = 3.0 * PITCH_Y

# Axial-zone annotation
ZONE_BOUNDS = [
    (CORE_BOTTOM,      ENDBOX_BELOW_BOT, 'lower\nwater'),
    (ENDBOX_BELOW_BOT, -HALF_Z,          'lower\nend-box'),
    (-HALF_Z,           HALF_Z,          'active\nfuel'),
    ( HALF_Z,          ENDBOX_ABOVE_TOP, 'upper\nend-box'),
    (ENDBOX_ABOVE_TOP, CORE_TOP,         'upper\nwater'),
]
Z_LINES = [ENDBOX_BELOW_BOT, -HALF_Z, HALF_Z, ENDBOX_ABOVE_TOP]


def annotate_axial_zones(ax, x_half, z_lo=CORE_BOTTOM, z_hi=CORE_TOP, color='white'):
    """Dashed z-lines + labels for whichever zones fall inside [z_lo, z_hi]."""
    for z in Z_LINES:
        if z_lo < z < z_hi:
            ax.axhline(z, color=color, lw=0.8, ls='--', alpha=0.55)
    for zb_lo, zb_hi, label in ZONE_BOUNDS:
        zc = 0.5 * (zb_lo + zb_hi)
        if z_lo < zc < z_hi:
            ax.text(
                x_half - 0.4, zc, label,
                color=color, fontsize=6.5, va='center', ha='right',
                bbox=dict(facecolor='black', alpha=0.30, pad=1.5, edgecolor='none'),
            )


# =============================================================================
# Figure layout: 2×2 main block  +  tall side column (spans both rows)
# =============================================================================

fig = plt.figure(figsize=(20, 17))
gs  = gridspec.GridSpec(
    2, 3, figure=fig,
    width_ratios=[1.0, 1.0, 0.5],
    height_ratios=[1.0, 1.25],
    hspace=0.16, wspace=0.14,
)
ax_xy   = fig.add_subplot(gs[0, 0])   # XY full core
ax_ft   = fig.add_subplot(gs[0, 1])   # XY flux trap zoom
ax_xz   = fig.add_subplot(gs[1, 0])   # XZ through FT1 (cropped)
ax_yz   = fig.add_subplot(gs[1, 1])   # YZ through FT1 (cropped)
ax_side = fig.add_subplot(gs[:, 2])   # XZ through C2 (full height)

fig.suptitle(
    'IAEA TECDOC-643  Generic 10 MW LEU Research Reactor — Geometry  '
    '(control blades fully inserted, f = 0)\n'
    f'Flux trap: ZCylinder r = {FT_HOLE_RADIUS:.4f} cm, hot water 316.8 K inside   |   '
    f'B4C blade z = [{BLADE_Z_BOT:.0f}, {BLADE_Z_TOP:.0f}] cm ({BLADE_LENGTH:.0f} cm)',
    fontsize=10, y=0.996,
)

PLOT_KW = dict(color_by='material', colors=COLORS)

# ── [0,0]  XY  z = 0 — full core top-down ───────────────────────────────────
geometry.plot(
    basis='xy', origin=(0.0, 0.0, 0.0),
    width=(W_XY, H_XY), pixels=(1100, 1300),
    axes=ax_xy, **PLOT_KW,
)
ax_xy.set_title('XY  z = 0 cm  (fuel midplane, full core)', fontsize=10)
ax_xy.set_xlabel('x  (cm)', fontsize=9)
ax_xy.set_ylabel('y  (cm)', fontsize=9)
for fx, fy, label in [(FT1_X, FT1_Y, 'FT1'), (FT2_X, FT2_Y, 'FT2')]:
    ax_xy.add_patch(plt.Circle((fx, fy), FT_HOLE_RADIUS,
                    fill=False, edgecolor='white', lw=1.2, ls='--'))
    ax_xy.text(fx, fy, label, color='white', fontsize=7,
               ha='center', va='center', fontweight='bold')

# ── [0,1]  XY  z = 0 — flux trap 1 zoom ─────────────────────────────────────
geometry.plot(
    basis='xy', origin=(FT1_X, FT1_Y, 0.0),
    width=(FT_ZOOM_W, FT_ZOOM_H), pixels=(900, 950),
    axes=ax_ft, **PLOT_KW,
)
ax_ft.set_title(
    f'XY  z = 0 cm  (flux trap 1 detail)\n'
    f'cylinder r = {FT_HOLE_RADIUS:.4f} cm  (white dashed)', fontsize=9.5)
ax_ft.set_xlabel('x  (cm)', fontsize=9)
ax_ft.set_ylabel('y  (cm)', fontsize=9)
ax_ft.add_patch(plt.Circle((FT1_X, FT1_Y), FT_HOLE_RADIUS,
                fill=False, edgecolor='white', lw=1.5, ls='--'))
ax_ft.plot(FT1_X, FT1_Y, '+', color='white', markersize=8, markeredgewidth=1.2)

# ── [1,0]  XZ  y = FT1_Y — flux trap 1 column, cropped to main components ────
geometry.plot(
    basis='xz', origin=(FT1_X, FT1_Y, 0.0),
    width=(W_AX_CROP, MAIN_AX_H), pixels=(1100, 1400),
    axes=ax_xz, **PLOT_KW,
)
ax_xz.set_title(
    f'XZ  y = {FT1_Y:.1f} cm  (flux trap 1 — fuel + end boxes)', fontsize=9.5)
ax_xz.set_xlabel('x  (cm)', fontsize=9)
ax_xz.set_ylabel('z  (cm)', fontsize=9)
annotate_axial_zones(ax_xz, x_half=W_AX_CROP / 2,
                     z_lo=-MAIN_AX_HALF_Z, z_hi=MAIN_AX_HALF_Z)

# ── [1,1]  YZ  x = FT1_X — flux trap 1 column, cropped ───────────────────────
geometry.plot(
    basis='yz', origin=(FT1_X, FT1_Y, 0.0),
    width=(W_YZ_CROP, MAIN_AX_H), pixels=(1100, 1400),
    axes=ax_yz, **PLOT_KW,
)
ax_yz.set_title(
    f'YZ  x = {FT1_X:.2f} cm  (flux trap 1 — fuel + end boxes)', fontsize=9.5)
ax_yz.set_xlabel('y  (cm)', fontsize=9)
ax_yz.set_ylabel('z  (cm)', fontsize=9)
annotate_axial_zones(ax_yz, x_half=W_YZ_CROP / 2,
                     z_lo=-MAIN_AX_HALF_Z, z_hi=MAIN_AX_HALF_Z)

# ── [:,2]  XZ through control element C2 — full height, blade reference ──────
geometry.plot(
    basis='xz', origin=(C2_X, C2_BLADE_Y, CORE_Z_CTR),
    width=(SIDE_W, H_AX_FULL), pixels=(600, 1900),
    axes=ax_side, **PLOT_KW,
)
ax_side.set_title(
    'XZ through C2  (full height)\n'
    f'B4C blade z=[{BLADE_Z_BOT:.0f}, {BLADE_Z_TOP:.0f}] cm', fontsize=9.5)
ax_side.set_xlabel('x  (cm)', fontsize=9)
ax_side.set_ylabel('z  (cm)', fontsize=9)
annotate_axial_zones(ax_side, x_half=SIDE_W / 2)
# Bracket the blade z-extent
ax_side.axhline(BLADE_Z_BOT, color='lime', lw=1.0, ls='-', alpha=0.7)
ax_side.axhline(BLADE_Z_TOP, color='lime', lw=1.0, ls='-', alpha=0.7)

# =============================================================================
# Shared material legend
# =============================================================================

legend_handles = [
    mpatches.Patch(facecolor=_rgb(mat), edgecolor='#555', lw=0.5, label=mat.name)
    for mat in COLORS
]
fig.legend(
    handles=legend_handles, loc='lower center', bbox_to_anchor=(0.5, -0.005),
    ncol=len(legend_handles), frameon=True, fontsize=8.5,
    title='Materials', title_fontsize=8.5,
)

plt.subplots_adjust(left=0.05, right=0.98, top=0.94, bottom=0.06)

# =============================================================================
# Save
# =============================================================================

out_dir  = os.path.join(REPO_ROOT, 'plots')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'core_geometry_plots.png')
fig.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"Saved: {out_path}")
