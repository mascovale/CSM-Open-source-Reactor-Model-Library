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

DEPLETION ZONE VIEWS (opt-in, new outputs — the default figure above is never
touched or overwritten):
    python tests/plot_core.py --depletion-zones
    python tests/plot_core.py --depletion-zones --color-mode element

These make the per-element, per-axial-zone depletion materials visible so the
zoning can be INSPECTED, not merely asserted. Two colour modes, catching
different failures:

  zone     (default) all elements share N colours, one per axial zone, on a
           perceptually monotonic ramp. Every horizontal band must run unbroken
           across the whole core — a break means one element's zones were built
           from the wrong z-bounds.
  element  hue = element, dark (bottom) -> light (top) within each element.
           Adjacent columns must never share a hue — a repeat means two
           elements share a material, or an element's zones collapsed.

Everything is derived from N_AXIAL_ZONES; changing it needs no edit here.
"""

import argparse
import colorsys
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
    PITCH_X, PITCH_Y, HALF_Z, BLADE_LENGTH, ROD_TRAVEL,
    CORE_BOTTOM, CORE_TOP,
    ENDBOX_ABOVE_TOP, ENDBOX_BELOW_BOT,
    FT_HOLE_RADIUS,
    ELEM_Y, ACTIVE_STACK_X, ABSORBER_THICK,
    CTRL_OUTER_OFFSET, CTRL_AL_PLATE_THICK, CTRL_BLADE_WATER, MEAT_THICK,
    water_univ, graphite_univ, make_flux_trap,
    make_standard_fuel_element, make_control_fuel_element,
    build_core_geometry, CORE_MAP, core_map_label,
    MEAT_BOT_Z, MEAT_TOP_Z, MEAT_ZONE_HEIGHT,
)
from materials import (
    fuel, clad, water, water_core, b4c, graphite, aluminum, end_box_homog,
    N_AXIAL_ZONES, get_zoned_fuels,
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

# Blade withdrawal fraction for the standard figure. f = 0 is fully INSERTED,
# which is the position this figure exists to show.
DEFAULT_PLOT_F = 0.0

# Blade z-extent, DERIVED from DEFAULT_PLOT_F using the same formula the
# geometry itself uses. Previously hardcoded to the f = 0 values while
# build_geometry() was called with f = 0.5, so the annotation silently stopped
# matching the geometry it annotates. Deriving it makes that drift impossible.
BLADE_Z_BOT = -HALF_Z + DEFAULT_PLOT_F * ROD_TRAVEL
BLADE_Z_TOP = BLADE_Z_BOT + BLADE_LENGTH

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


OUT_DIR = os.path.join(REPO_ROOT, 'plots')


# =============================================================================
# Default figure: 2×2 main block  +  tall side column (spans both rows)
# =============================================================================

def build_default_figure():
    """The standard geometry figure — unchanged behaviour, unchanged filename."""
    geometry = build_geometry(f=DEFAULT_PLOT_F)   # blades fully in

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
        f'(control blades fully inserted, f = {DEFAULT_PLOT_F:.0f})\n'
        f'Flux trap: ZCylinder r = {FT_HOLE_RADIUS:.4f} cm, hot water 316.8 K inside   |   '
        f'B4C blade z = [{BLADE_Z_BOT:.0f}, {BLADE_Z_TOP:.0f}] cm ({BLADE_LENGTH:.0f} cm)',
        fontsize=10, y=0.996,
    )

    PLOT_KW = dict(color_by='material', colors=COLORS)

    # ── [0,0]  XY  z = 0 — full core top-down ───────────────────────────────
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

    # ── [0,1]  XY  z = 0 — flux trap 1 zoom ─────────────────────────────────
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

    # ── [1,0]  XZ  y = FT1_Y — flux trap 1 column, cropped ──────────────────
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

    # ── [1,1]  YZ  x = FT1_X — flux trap 1 column, cropped ──────────────────
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

    # ── [:,2]  XZ through control element C2 — full height ──────────────────
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

    # ── Shared material legend ──────────────────────────────────────────────
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

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'core_geometry_plots.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_path}")
    return out_path


# =============================================================================
# DEPLETION ZONE VISUALIZATION
#
# Verification artifact, not decoration: every choice below exists so that a
# specific class of zoning error becomes visually obvious. See the module
# docstring for what each colour mode catches.
# =============================================================================

# Non-fuel materials are muted to greys so the zoning dominates the image.
# EXCEPTION: B4C stays a desaturated dark red — a plot where you cannot tell
# where the absorber sits has lost half its value.
MUTED_COLORS = {
    water:         (238, 238, 238),   # very light — outer pool water
    water_core:    (218, 218, 218),   # very light — core coolant
    clad:          (186, 186, 186),   # light-mid  — Al cladding
    aluminum:      (160, 160, 160),   # light-mid  — structural Al
    end_box_homog: (134, 134, 134),   # mid        — 25 % Al / 75 % H₂O
    graphite:      ( 74,  74,  74),   # dark       — graphite reflector
    b4c:           (122,  46,  46),   # desaturated dark red — absorber blade
}

# Canonical element ordering: row-major over the core map, so the hue stride
# below scatters TRUE lattice neighbours rather than list neighbours.
CANONICAL_ELEMENTS = [core_map_label(i, j)
                      for i, row in enumerate(CORE_MAP)
                      for j, t in enumerate(row) if t in ('S', 'C')]
N_ELEMENTS = len(CANONICAL_ELEMENTS)          # 28

# Hue stride, coprime with 28. Sequential hues would be ~13 deg apart and
# lattice neighbours would be indistinguishable; stride 11 throws adjacent
# positions to opposite sides of the colour wheel.
HUE_STRIDE = 11

# Mode-B zone ramp: dark (bottom zone) -> light (top zone).
SAT_TOP,   SAT_BOT   = 0.53, 0.95
VALUE_BOT, VALUE_TOP = 0.42, 0.95


def _to255(rgb01):
    return tuple(int(round(255 * c)) for c in rgb01[:3])


def zone_ramp():
    """N colours, bottom -> top, sampled at zone centres on viridis."""
    cmap = matplotlib.colormaps['viridis']
    return [_to255(cmap((k + 0.5) / N_AXIAL_ZONES))
            for k in range(N_AXIAL_ZONES)]


def element_hue(idx):
    """Hue in [0,1) for canonical element index idx."""
    return ((idx * HUE_STRIDE) % N_ELEMENTS) / float(N_ELEMENTS)


def element_zone_rgb(idx, k):
    """Mode B: hue from the element, value/saturation ramped by zone."""
    t = k / (N_AXIAL_ZONES - 1) if N_AXIAL_ZONES > 1 else 0.5
    return _to255(colorsys.hsv_to_rgb(
        element_hue(idx),
        SAT_BOT + (SAT_TOP - SAT_BOT) * t,
        VALUE_BOT + (VALUE_TOP - VALUE_BOT) * t,
    ))


def build_zone_colors(mode):
    """(colors_for_openmc, {(element_id, zone_index): rgb}) — deterministic.

    Keyed on (element_id, zone_index), resolved through the material NAME, so
    the mapping never depends on dict ordering or object identity.
    """
    by_name = {m.name: m for m in get_zoned_fuels()}
    colors = dict(MUTED_COLORS)
    key_rgb = {}
    ramp = zone_ramp()

    for idx, elem in enumerate(CANONICAL_ELEMENTS):
        for k in range(N_AXIAL_ZONES):
            name = f'fuel_{elem}_z{k}'
            rgb = ramp[k] if mode == 'zone' else element_zone_rgb(idx, k)
            colors[by_name[name]] = rgb
            key_rgb[(elem, k)] = rgb
    return colors, key_rgb


# ── Slice locations, derived from the core map ───────────────────────────────

_LL_X, _LL_Y = -4.0 * PITCH_X, -4.5 * PITCH_Y
_NROWS = len(CORE_MAP)


def row_center_y(i):
    """Global y of core-map row i. Row 0 is the +y edge (lattice array order)."""
    return _LL_Y + (_NROWS - 1 - i + 0.5) * PITCH_Y


def col_center_x(j):
    """Global x of core-map column j."""
    return _LL_X + (j + 0.5) * PITCH_X


# Row 4 / column C both carry standard AND control elements, and both are
# element centres. Standard elements have 23 plates and control followers 17 —
# both odd — so the middle plate is centred on the element and its meat is
# centred within it. A row/column centre therefore lands inside meat for both
# element types. Probed, not assumed: see probe_slice_locations().
ZONE_XZ_ROW = 4
ZONE_YZ_COL = 3
ZONE_XZ_Y = row_center_y(ZONE_XZ_ROW)    # 0.0 cm
ZONE_YZ_X = col_center_x(ZONE_YZ_COL)    # -3.85 cm


def zone_midplane_z(k):
    """Axial midplane of zone k — computed, never hardcoded."""
    return MEAT_BOT_Z + (k + 0.5) * MEAT_ZONE_HEIGHT


def annotate_depletion_zones(ax, x_half, color='white'):
    """Dashed lines on the N-1 interior zone boundaries, plus z0..z{N-1} labels."""
    for k in range(1, N_AXIAL_ZONES):
        ax.axhline(MEAT_BOT_Z + k * MEAT_ZONE_HEIGHT,
                   color=color, lw=0.8, ls='--', alpha=0.8)
    for z in (MEAT_BOT_Z, MEAT_TOP_Z):
        ax.axhline(z, color=color, lw=1.1, ls='-', alpha=0.65)
    for k in range(N_AXIAL_ZONES):
        ax.text(-x_half + 0.5, zone_midplane_z(k), f'z{k}',
                color=color, fontsize=7.5, va='center', ha='left',
                fontweight='bold',
                bbox=dict(facecolor='black', alpha=0.35, pad=1.5,
                          edgecolor='none'))


def probe_slice_locations(geom):
    """Verify the slice locations land in zoned meat. Returns list of lines."""
    lines, bad = [], []
    std_ok = ctrl_ok = False

    for tag, pts in (
        (f'XZ slice  y = {ZONE_XZ_Y:.3f} (row {ZONE_XZ_ROW})',
         [(core_map_label(ZONE_XZ_ROW, j), CORE_MAP[ZONE_XZ_ROW][j],
           (col_center_x(j), ZONE_XZ_Y, 0.0))
          for j in range(len(CORE_MAP[ZONE_XZ_ROW]))
          if CORE_MAP[ZONE_XZ_ROW][j] in ('S', 'C', 'F')]),
        (f'YZ slice  x = {ZONE_YZ_X:.3f} (col {ZONE_YZ_COL})',
         [(core_map_label(i, ZONE_YZ_COL), CORE_MAP[i][ZONE_YZ_COL],
           (ZONE_YZ_X, row_center_y(i), 0.0))
          for i in range(_NROWS)
          if CORE_MAP[i][ZONE_YZ_COL] in ('S', 'C', 'F')]),
    ):
        lines.append(f'  {tag}')
        for label, token, pt in pts:
            found = geom.find(pt)[-1]
            name = (found.fill.name if isinstance(found.fill, openmc.Material)
                    else '<no material>')
            lines.append(f'    {label} ({token})  {pt[0]:8.3f}, {pt[1]:8.3f} '
                         f' -> {name}')
            zoned = name.startswith('fuel_') and '_z' in name
            if token == 'S':
                std_ok |= zoned
                if not zoned:
                    bad.append((label, name))
            elif token == 'C':
                ctrl_ok |= zoned
                if not zoned:
                    bad.append((label, name))

    if bad or not (std_ok and ctrl_ok):
        raise SystemExit(
            "Slice probe FAILED — the chosen slice does not land in zoned fuel "
            f"meat. Offenders: {bad}\n"
            "That is either a bad slice location or a real geometry surprise; "
            "both are worth knowing. Not plotting.")
    return lines


# ── Views ────────────────────────────────────────────────────────────────────

def _zone_legend_handles():
    ramp = zone_ramp()
    return [mpatches.Patch(
                facecolor=tuple(c / 255.0 for c in ramp[k]),
                edgecolor='#333', lw=0.5,
                label=f'z{k}  [{MEAT_BOT_Z + k * MEAT_ZONE_HEIGHT:+.1f}, '
                      f'{MEAT_BOT_Z + (k + 1) * MEAT_ZONE_HEIGHT:+.1f}] cm'
                      + ('  (bottom)' if k == 0 else
                         '  (top)' if k == N_AXIAL_ZONES - 1 else ''))
            for k in range(N_AXIAL_ZONES)]


def _mode_note(mode):
    return ('all elements share one colour per zone — every horizontal band '
            'must run UNBROKEN across the core'
            if mode == 'zone' else
            'hue = element, dark (bottom) -> light (top) within each element — '
            'adjacent columns must never share a hue')


def plot_axial_view(geom, colors, mode, basis, f, fname):
    """XZ or YZ slice showing the zone bands against the element structure."""
    if basis == 'xz':
        origin, width = (0.0, ZONE_XZ_Y, 0.0), (W_AX_CROP, MAIN_AX_H)
        where = f'y = {ZONE_XZ_Y:.2f} cm  (core-map row {ZONE_XZ_ROW} centre)'
        xlabel, x_half = 'x  (cm)', W_AX_CROP / 2
    else:
        origin, width = (ZONE_YZ_X, 0.0, 0.0), (W_YZ_CROP, MAIN_AX_H)
        where = f'x = {ZONE_YZ_X:.2f} cm  (core-map column {ZONE_YZ_COL} centre)'
        xlabel, x_half = 'y  (cm)', W_YZ_CROP / 2

    fig, ax = plt.subplots(figsize=(13, 9))
    geom.plot(basis=basis, origin=origin, width=width, pixels=(1500, 1700),
              axes=ax, color_by='material', colors=colors)
    ax.set_title(
        f'Depletion zones — {basis.upper()}  {where}\n'
        f'{N_AXIAL_ZONES} axial zones x {MEAT_ZONE_HEIGHT:g} cm, '
        f'blade withdrawn f = {f:.1f}   |   mode "{mode}": {_mode_note(mode)}',
        fontsize=10)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel('z  (cm)', fontsize=9)
    annotate_depletion_zones(ax, x_half=x_half)

    if mode == 'zone':
        ax.legend(handles=_zone_legend_handles(), loc='upper right',
                  fontsize=8, framealpha=0.9, title='Axial depletion zone',
                  title_fontsize=8)

    out = os.path.join(OUT_DIR, fname)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


# XY midplane panels are ZOOMED to a 2x2 element block, not the full core.
# Why: fuel meat is MEAT_THICK = 0.051 cm thick against a 75.9 cm full-core
# field of view — a ratio of 1:1488. At any figure size that fits on a page the
# meat is SUB-PIXEL (0.59 px at the full-core scale), and OpenMC point-samples
# one material per pixel, so it hits some plates and misses others. The
# resulting aliasing looks exactly like "this element is missing its zone" —
# i.e. it mimics the failure mode the view exists to detect. Zoomed to 2x2
# elements the meat spans ~3 px and renders honestly.
# Whole-core "is every element in step" is covered by plot_row_panels() below,
# which is legible because the XZ basis shows meat edge-on.
ZOOM_ROWS = (4, 5)      # core-map rows spanned by the XY zoom
ZOOM_COLS = (2, 3)      # core-map cols — B4 (control) + C4/B5/C5 (standard)


def plot_zone_midplanes(geom, colors, mode, f, fname):
    """One XY panel per zone, at that zone's axial midplane, zoomed to 2x2."""
    cx = 0.5 * (col_center_x(ZOOM_COLS[0]) + col_center_x(ZOOM_COLS[1]))
    cy = 0.5 * (row_center_y(ZOOM_ROWS[0]) + row_center_y(ZOOM_ROWS[1]))
    width = (2 * PITCH_X, 2 * PITCH_Y)
    block = ', '.join(core_map_label(i, j)
                      for i in ZOOM_ROWS for j in ZOOM_COLS)

    fig, axes = plt.subplots(
        1, N_AXIAL_ZONES, figsize=(4.1 * N_AXIAL_ZONES, 5.2))
    axes = [axes] if N_AXIAL_ZONES == 1 else list(axes)

    for k, ax in enumerate(axes):
        zc = zone_midplane_z(k)
        geom.plot(basis='xy', origin=(cx, cy, zc), width=width,
                  pixels=(900, 950), axes=ax, color_by='material', colors=colors)
        ax.set_title(f'z{k}   z = {zc:+.1f} cm', fontsize=10)
        ax.set_xlabel('x  (cm)', fontsize=8)
        ax.set_ylabel('y  (cm)' if k == 0 else '', fontsize=8)
        ax.tick_params(labelsize=7)

    fig.suptitle(
        f'Depletion zones — XY at each zone midplane, zoomed to elements '
        f'{block}\n({N_AXIAL_ZONES} zones x {MEAT_ZONE_HEIGHT:g} cm, '
        f'f = {f:.1f})   |   mode "{mode}": {_mode_note(mode)}\n'
        f'zoomed because meat is {MEAT_THICK} cm against a 75.9 cm core '
        f'(1:1488) — sub-pixel at full-core scale', fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.87))

    out = os.path.join(OUT_DIR, fname)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


def plot_row_panels(geom, colors, mode, f, fname):
    """One XZ panel per fuel row — all 28 elements, zone bands edge-on.

    This is the whole-core "is every element in step" check. XZ works where a
    full-core XY cannot: meat is seen edge-on, so each element reads as a solid
    6.3 cm-wide column of zone colour rather than a sub-pixel sliver.
    """
    fuel_rows = [i for i, row in enumerate(CORE_MAP)
                 if any(t in ('S', 'C') for t in row)]
    z_pad = 4.0
    z_lo, z_hi = MEAT_BOT_Z - z_pad, MEAT_TOP_Z + z_pad

    fig, axes = plt.subplots(1, len(fuel_rows),
                             figsize=(4.0 * len(fuel_rows), 5.0))
    axes = [axes] if len(fuel_rows) == 1 else list(axes)

    for ax, i in zip(axes, fuel_rows):
        y = row_center_y(i)
        geom.plot(basis='xz', origin=(0.0, y, 0.5 * (z_lo + z_hi)),
                  width=(W_XY, z_hi - z_lo), pixels=(900, 800),
                  axes=ax, color_by='material', colors=colors)
        members = ' '.join(core_map_label(i, j)
                           for j, t in enumerate(CORE_MAP[i])
                           if t in ('S', 'C', 'F'))
        ax.set_title(f'row {i}   y = {y:+.2f} cm\n{members}', fontsize=8.5)
        ax.set_xlabel('x  (cm)', fontsize=8)
        ax.set_ylabel('z  (cm)' if i == fuel_rows[0] else '', fontsize=8)
        ax.tick_params(labelsize=7)
        for k in range(1, N_AXIAL_ZONES):
            ax.axhline(MEAT_BOT_Z + k * MEAT_ZONE_HEIGHT,
                       color='white', lw=0.7, ls='--', alpha=0.8)

    fig.suptitle(
        f'Depletion zones — XZ through every fuel row (all 28 elements, '
        f'f = {f:.1f})\nmode "{mode}": {_mode_note(mode)}', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.88))

    out = os.path.join(OUT_DIR, fname)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


def plot_element_hue_map(fname='depletion_zones_element_huemap.png'):
    """Mode-B key: element hues laid out on the core grid (A-F x 1-7).

    140 legend entries is not a legend. This is the readable substitute, and
    doubles as a core map.
    """
    fig, ax = plt.subplots(figsize=(7.6, 8.6))
    mid = (N_AXIAL_ZONES - 1) / 2.0

    for i, row in enumerate(CORE_MAP):
        for j, token in enumerate(row):
            label = core_map_label(i, j)
            if label is None:
                continue
            if token in ('S', 'C'):
                idx = CANONICAL_ELEMENTS.index(label)
                face = tuple(c / 255.0 for c in
                             element_zone_rgb(idx, int(round(mid))))
                txt, tcol = f'{label}\n{token}', 'white'
            else:
                face = {'G': (0.29, 0.29, 0.29),
                        'F': (0.85, 0.85, 0.85),
                        'W': (0.96, 0.96, 0.96)}[token]
                txt = f'{label}\n' + {'G': 'G', 'F': 'FT', 'W': '—'}[token]
                tcol = 'white' if token == 'G' else '#444'

            ax.add_patch(mpatches.Rectangle((j - 0.5, -i - 0.5), 1, 1,
                                            facecolor=face, edgecolor='white',
                                            lw=1.5))
            ax.text(j, -i, txt, ha='center', va='center', fontsize=8.5,
                    color=tcol, fontweight='bold')

    ax.set_xlim(0.5, 6.5)
    ax.set_ylim(-7.5, -0.5)
    ax.set_xticks(range(1, 7))
    ax.set_xticklabels(list('ABCDEF'), fontsize=11)
    ax.set_yticks([-i for i in range(1, 8)])
    ax.set_yticklabels([str(i) for i in range(1, 8)], fontsize=11)
    ax.xaxis.set_ticks_position('top')
    ax.set_aspect('equal')
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(
        'Element hue map — colour-mode "element"\n'
        f'hue = element (stride {HUE_STRIDE} of {N_ELEMENTS}), '
        'shown at the mid zone; row 1 is the +y edge',
        fontsize=10.5, pad=26)

    out = os.path.join(OUT_DIR, fname)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


def plot_depletion_zones(mode):
    """Build the zoned geometry and emit every zone view. Self-verifying."""
    os.makedirs(OUT_DIR, exist_ok=True)

    # Straight through the model package — the local lattice_universes literal
    # in build_geometry() above is NOT used on this path.
    geom = build_core_geometry(withdrawn_fraction=1.0, depletion_zoning=True)
    geom_f0 = build_core_geometry(withdrawn_fraction=0.0, depletion_zoning=True)

    print(f"\nDepletion zone plots — mode '{mode}', "
          f"N_AXIAL_ZONES = {N_AXIAL_ZONES}")
    print("  slice probes:")
    for line in probe_slice_locations(geom):
        print(line)

    colors, key_rgb = build_zone_colors(mode)

    # Self-checks: the artifact verifies itself whenever it is regenerated.
    zoned = get_zoned_fuels()
    expected = N_ELEMENTS * N_AXIAL_ZONES
    assert len(zoned) == expected, \
        f"expected {expected} zoned materials, found {len(zoned)}"
    assert all(m in colors for m in zoned), \
        "colour dict does not cover every zoned material"
    assert len(key_rgb) == expected, \
        f"colour keys {len(key_rgb)} != {expected}"
    if mode == 'element':
        assert len(set(key_rgb.values())) == expected, \
            "two distinct (element, zone) keys share an RGB in mode 'element'"
    print(f"  [OK] {len(zoned)} zoned materials, all coloured"
          + ("; all RGBs distinct" if mode == 'element' else
             f"; {N_AXIAL_ZONES} shared zone colours"))

    written = [
        plot_axial_view(geom, colors, mode, 'xz', 1.0,
                        f'depletion_zones_{mode}_xz.png'),
        plot_axial_view(geom, colors, mode, 'yz', 1.0,
                        f'depletion_zones_{mode}_yz.png'),
        plot_zone_midplanes(geom, colors, mode, 1.0,
                            f'depletion_zones_{mode}_xy_midplanes.png'),
        plot_row_panels(geom, colors, mode, 1.0,
                        f'depletion_zones_{mode}_xz_rows.png'),
        plot_axial_view(geom_f0, colors, mode, 'xz', 0.0,
                        f'depletion_zones_{mode}_xz_f0.png'),
    ]
    if mode == 'element':
        written.append(plot_element_hue_map())

    for p in written:
        size = os.path.getsize(p)
        assert size > 0, f"{p} is empty"
        print(f"  Saved: {p}  ({size / 1024:.0f} KB)")
    return written


# =============================================================================
# CLI
# =============================================================================

def main(argv=None):
    p = argparse.ArgumentParser(
        description='TECDOC-643 10 MW LEU core — geometry cross-section plots')
    p.add_argument('--depletion-zones', action='store_true',
                   help='emit the depletion-zone views instead of the standard '
                        'geometry figure (which is never overwritten)')
    p.add_argument('--color-mode', choices=['zone', 'element'], default='zone',
                   help="'zone' (default): one colour per axial zone, shared by "
                        "all elements. 'element': hue per element, dark->light "
                        "by zone.")
    args = p.parse_args(argv)

    if args.depletion_zones:
        plot_depletion_zones(args.color_mode)
    else:
        build_default_figure()


if __name__ == '__main__':
    main()
