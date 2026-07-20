"""
geometry.py
-----------
Geometry definitions for the IAEA TECDOC-643 Appendix A-2
Generic 10 MW LEU Research Reactor Core (Argonne design).

Reference:
    IAEA-TECDOC-643, "Research Reactor Core Conversion Guidebook,
    Volume 2: Analysis (Appendices A-F)," IAEA, Vienna, 1992.
    Appendix A-2: Generic 10 MW Reactor — Argonne National Laboratory.

Core Layout:
    - 5x6 active core in 8x9 grid
    - 23 standard fuel elements, 5 control fuel elements, 2 flux traps
    - Lattice pitch: 77 mm x 81 mm
    - Active fuel height: 60 cm

Axial model structure (deck-confirmed, symmetric about z=0):
    CORE_BOTTOM = -90 cm  (vacuum)
    [-90, -45]  : 45 cm light water
    [-45, -30]  : 15 cm homogenized end-box (0.25 Al / 0.75 H₂O by volume)
    [-30, +30]  : 60 cm active fuel region
    [+30, +45]  : 15 cm homogenized end-box
    [+45, +90]  : 45 cm light water
    CORE_TOP    = +90 cm  (vacuum) — COINCIDES with the fully-withdrawn (f=1)
                  blade top; no water cap above the withdrawn blade.

Control blade model — fixed-length sliding absorber:
    BLADE_LENGTH = 60 cm (rigid; never changes)
    ROD_TRAVEL   = 60 cm (full stroke)
    withdrawn_fraction f in [0, 1]:
        z_bot = -30 + f * 60   → f=0: -30,  f=1: +30
        z_top = z_bot + 60     → f=0: +30,  f=1: +90 (= CORE_TOP at f=1)
    b4c fills the Hf-slot x/y band for z in [z_bot, z_top]. A 15 cm homogenized
    (end_box_homog) end-box cap is RIGIDLY ATTACHED to the top of the blade and
    translates with it, occupying the blade's own slot footprint over
    z=[z_top, min(z_top+15, CORE_TOP)]; above the cap the slot is water up to
    CORE_TOP. At f=0 the cap sits at [+30,+45], coplanar with the surrounding
    end-boxes. At f=1 the blade top coincides with CORE_TOP (z_top == +90), so
    the cap is pushed entirely out of the model and is NOT created — the blade
    itself fills the slot to the top, exactly as before.
    All other cells (guide plates, fuel, channels, etc.) are restricted
    to the active zone z=[-30, +30]; end-box/water cells cover z outside.

Standard Fuel Element (LEU, U3Si2-Al, heterogeneous build):
    - Envelope:           76 x 80 mm
    - Side plates:        4.8 mm each (aluminum, in x)
    - Active stack:       66.4 mm wide between side plate inner faces
    - 23 plates:          1.27 mm inner, 1.5 mm outer (outer plates clad on
                          both faces of the meat at the outer 0.495 mm
                          thickness, not just the face away from the stack)
    - Fuel meat:          0.51 mm thick x 63 mm wide x 600 mm tall
    - Inner clad:         0.38 mm  |  Outer clad: 0.495 mm

All dimensions in cm.
"""

import openmc
from materials import fuel, clad, water, water_core, b4c, graphite, aluminum, end_box_homog

# =============================================================================
# LATTICE / ELEMENT ENVELOPE
# =============================================================================

PITCH_X = 7.7    # cm  (77 mm)
PITCH_Y = 8.1    # cm  (81 mm)

ELEM_X = 7.6     # cm  (76 mm)
ELEM_Y = 8.0     # cm  (80 mm)
ELEM_Z = 60.0    # cm  (600 mm) — active fuel height

# Inter-element water gap — documentation/tripwire only. Feeds no surface or
# cell directly; every gap cell derives its width from the pitch/envelope
# XPlane/YPlane objects themselves (PITCH_X/Y, ELEM_X/Y above), not from
# these constants. Exists so a future PITCH/ELEM edit that zeroes or inverts
# the gap fails loudly here instead of emitting a zero-width sliver cell.
GAP_X = (PITCH_X - ELEM_X) / 2.0   # cm
GAP_Y = (PITCH_Y - ELEM_Y) / 2.0   # cm
assert GAP_X > 0, "PITCH_X must exceed ELEM_X (zero/negative gap)"
assert GAP_Y > 0, "PITCH_Y must exceed ELEM_Y (zero/negative gap)"

SIDE_PLATE_THICK = 0.48   # cm  (4.8 mm)
ACTIVE_STACK_X   = ELEM_X - 2 * SIDE_PLATE_THICK   # 6.64 cm

# =============================================================================
# PLATE / MEAT / CLAD DIMENSIONS
# =============================================================================

PLATE_THICK_INNER = 0.127    # cm  (1.27 mm)

CLAD_THICK_INNER = 0.038     # cm  (0.38 mm)
CLAD_THICK_OUTER = 0.0495    # cm  (0.495 mm)

MEAT_THICK = 0.051           # cm  (0.51 mm)
MEAT_WIDTH = 6.3             # cm  (63 mm)

# Outer plates (first/last in the stack) are clad at the outer thickness on
# BOTH faces of the meat, not just the face away from the stack — so their
# total thickness is meat + 2*CLAD_THICK_OUTER, not meat + inner + outer.
PLATE_THICK_OUTER = MEAT_THICK + 2 * CLAD_THICK_OUTER   # 0.15 cm  (1.5 mm)

N_PLATES_STD  = 23
N_PLATES_CTRL = 17

WATER_CHAN_THICK = 0.219     # cm  (2.19 mm)

# Standard element plate-stack height and the residual end water gap between
# the outermost plate face and the element envelope edge. [DERIVED]
STD_STACK_HEIGHT = (2 * PLATE_THICK_OUTER
                    + (N_PLATES_STD - 2) * PLATE_THICK_INNER
                    + (N_PLATES_STD - 1) * WATER_CHAN_THICK)   # 7.785 cm
STD_END_WATER = (ELEM_Y - STD_STACK_HEIGHT) / 2.0             # 0.1075 cm  [DERIVED]
assert STD_END_WATER > 0, "standard element end water gap must be positive"

# Flux trap cylindrical water hole radius.
# ASSUMED 2.5 cm (inscribed radius of the 50 mm square hole).
# Area-equivalent radius would be 5/sqrt(pi) ~2.8209 cm.
# VERIFY against Kyle's MCNP deck — if the deck uses a CYL surface
# with a different radius, update FT_HOLE_RADIUS here.
FT_HOLE_RADIUS = 2.5         # cm

HALF_Z = ELEM_Z / 2.0       # 30.0 cm

# =============================================================================
# AXIAL MODEL EXTENTS AND FIXED-LENGTH BLADE PARAMETERS
# =============================================================================

BLADE_LENGTH     = 60.0    # cm — rigid absorber blade (fixed length, translates in z)
ROD_TRAVEL       = 60.0    # cm — full stroke
CORE_TOP         = +90.0   # cm — vacuum boundary; COINCIDES with the fully-withdrawn
                            # (f=1) blade top (z_top = -30 + 60 + 60 = +90). No cap above.
CORE_BOTTOM      = -90.0   # cm — vacuum boundary; symmetric with CORE_TOP
                            # (15 cm end-box + 45 cm water below -30)
ENDBOX_ABOVE_TOP = +45.0   # cm — top of upper end-box  (+30 + 15 cm)
ENDBOX_BELOW_BOT = -45.0   # cm — bottom of lower end-box (-30 - 15 cm)

# Symmetry / height tripwires — deck-confirmed axial stack. Documentation +
# guard only: none of these feed a cell or surface directly.
assert CORE_TOP == -CORE_BOTTOM, "axial model must be symmetric about z=0"
assert (CORE_TOP - CORE_BOTTOM) == 180.0, "total axial height must be 180 cm"
assert (CORE_TOP - ENDBOX_ABOVE_TOP) == 45.0, "upper water region must be 45 cm"
assert (ENDBOX_BELOW_BOT - CORE_BOTTOM) == 45.0, "lower water region must be 45 cm"
assert (ENDBOX_ABOVE_TOP - HALF_Z) == 15.0, "upper end-box must be 15 cm"
assert (-HALF_Z - ENDBOX_BELOW_BOT) == 15.0, "lower end-box must be 15 cm"

# Shared axial ZPlane surfaces — transmission (NOT vacuum boundaries).
# Defined once at module level and reused in every element universe to avoid
# creating redundant surfaces at identical z-values.
_z_fuel_bot     = openmc.ZPlane(z0=-HALF_Z)           # −30.0 cm
_z_fuel_top     = openmc.ZPlane(z0= HALF_Z)           # +30.0 cm
_z_endbox_above = openmc.ZPlane(z0=ENDBOX_ABOVE_TOP)  # +45.0 cm
_z_endbox_below = openmc.ZPlane(z0=ENDBOX_BELOW_BOT)  # −45.0 cm
_z_model_top    = openmc.ZPlane(z0=CORE_TOP)           # +90.0 cm
_z_model_bot    = openmc.ZPlane(z0=CORE_BOTTOM)        # −90.0 cm


# =============================================================================
# END-BOX INTER-ELEMENT GAP HELPER
# Segments the homogenized end-box in x-y using the SAME pitch/envelope
# planes (and therefore the same gap width) as the active-zone gap cells, so
# the end-box plane mirrors the active-core element/gap grid. Takes only
# already-built plane objects from the calling function — builds none.
# =============================================================================

def _endbox_gap_cells(name_prefix, fill_mat, pitch_planes, envelope_planes, z_lo, z_hi):
    """4 water sliver cells (xleft/xright/yfront/yback) between envelope and
    pitch, restricted to [z_lo, z_hi]."""
    pitch_left, pitch_right, pitch_front, pitch_back = pitch_planes
    env_left, env_right, env_front, env_back = envelope_planes
    return [
        openmc.Cell(name=f'{name_prefix}_gap_xleft', fill=fill_mat,
            region=(+pitch_left & -env_left & +pitch_front & -pitch_back & +z_lo & -z_hi)),
        openmc.Cell(name=f'{name_prefix}_gap_xright', fill=fill_mat,
            region=(+env_right & -pitch_right & +pitch_front & -pitch_back & +z_lo & -z_hi)),
        openmc.Cell(name=f'{name_prefix}_gap_yfront', fill=fill_mat,
            region=(+env_left & -env_right & +pitch_front & -env_front & +z_lo & -z_hi)),
        openmc.Cell(name=f'{name_prefix}_gap_yback', fill=fill_mat,
            region=(+env_left & -env_right & +env_back & -pitch_back & +z_lo & -z_hi)),
    ]


# =============================================================================
# STANDARD FUEL ELEMENT
# 23 plates stacked in y, running in x. Plate meat is 60 cm tall (z).
# All structural cells are bounded to the active zone z=[-30, +30].
# End-box and water regions fill the full pitch footprint above/below.
# =============================================================================

def make_standard_fuel_element(elem_id):
    """
    Standard ANL/TECDOC A-2 fuel element.

    X = plate meat width direction (side plates bound this)
    Y = plate/channel stack direction (plates stacked here)
    Z = axial (active fuel from -30 to +30 cm)
    """

    # Pitch cell boundaries
    pitch_left  = openmc.XPlane(x0=-PITCH_X / 2.0)
    pitch_right = openmc.XPlane(x0= PITCH_X / 2.0)
    pitch_front = openmc.YPlane(y0=-PITCH_Y / 2.0)
    pitch_back  = openmc.YPlane(y0= PITCH_Y / 2.0)

    # Element envelope
    box_left  = openmc.XPlane(x0=-ELEM_X / 2.0)
    box_right = openmc.XPlane(x0= ELEM_X / 2.0)
    box_front = openmc.YPlane(y0=-ELEM_Y / 2.0)
    box_back  = openmc.YPlane(y0= ELEM_Y / 2.0)

    # Side plate inner faces
    side_inner_left  = openmc.XPlane(x0=-ELEM_X / 2.0 + SIDE_PLATE_THICK)
    side_inner_right = openmc.XPlane(x0= ELEM_X / 2.0 - SIDE_PLATE_THICK)

    # Fuel meat X boundaries
    meat_left  = openmc.XPlane(x0=-MEAT_WIDTH / 2.0)
    meat_right = openmc.XPlane(x0= MEAT_WIDTH / 2.0)

    # Axial bounds — reuse module-level surfaces (avoids redundant surface IDs)
    meat_zbot = _z_fuel_bot   # −30 cm
    meat_ztop = _z_fuel_top   # +30 cm
    active_z  = +_z_fuel_bot & -_z_fuel_top

    cells = []

    plate_thicks = (
        [PLATE_THICK_OUTER]
        + [PLATE_THICK_INNER] * (N_PLATES_STD - 2)
        + [PLATE_THICK_OUTER]
    )

    stack_height_y = sum(plate_thicks) + (N_PLATES_STD - 1) * WATER_CHAN_THICK
    # Tie the built stack to the module-level derived end-water gap.
    assert abs((ELEM_Y - stack_height_y) / 2.0 - STD_END_WATER) < 1e-9, \
        "standard stack end water gap disagrees with STD_END_WATER"
    y = -stack_height_y / 2.0
    stack_bottom_surf = openmc.YPlane(y0=y)

    for i, plate_thick in enumerate(plate_thicks):
        is_first = (i == 0)
        is_last  = (i == N_PLATES_STD - 1)

        plate_bottom = openmc.YPlane(y0=y)
        plate_top    = openmc.YPlane(y0=y + plate_thick)

        if is_first or is_last:
            # Outer plates: clad at the outer thickness on BOTH faces of the
            # meat (not just the face away from the stack).
            clad_bottom = CLAD_THICK_OUTER
            clad_top    = CLAD_THICK_OUTER
        else:
            clad_bottom = CLAD_THICK_INNER 
            clad_top    = CLAD_THICK_INNER

        meat_bottom = openmc.YPlane(y0=y + clad_bottom)
        meat_top    = openmc.YPlane(y0=y + plate_thick - clad_top)

        # Meat: bounded in x, y, AND z (active zone only)
        meat_region = (
            +meat_left & -meat_right &
            +meat_bottom & -meat_top &
            +meat_zbot & -meat_ztop
        )

        # Plate region bounded to active zone
        plate_region = (
            +side_inner_left & -side_inner_right &
            +plate_bottom & -plate_top &
            active_z
        )

        cells.append(openmc.Cell(
            name=f'std{elem_id}_meat_{i}',
            fill=fuel,
            region=meat_region
        ))
        cells.append(openmc.Cell(
            name=f'std{elem_id}_clad_{i}',
            fill=clad,
            region=plate_region & ~meat_region
        ))

        y += plate_thick

        if not is_last:
            chan_bottom = plate_top
            chan_top    = openmc.YPlane(y0=y + WATER_CHAN_THICK)
            cells.append(openmc.Cell(
                name=f'std{elem_id}_chan_{i}',
                fill=water_core,
                region=(
                    +side_inner_left & -side_inner_right &
                    +chan_bottom & -chan_top &
                    active_z
                )
            ))
            y += WATER_CHAN_THICK

    stack_top_surf = openmc.YPlane(y0=y)

    # Water below and above the plate stack — active zone only
    cells.append(openmc.Cell(
        name=f'std{elem_id}_water_below_stack',
        fill=water_core,
        region=(
            +box_front & -stack_bottom_surf &
            +side_inner_left & -side_inner_right &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_water_above_stack',
        fill=water_core,
        region=(
            +stack_top_surf & -box_back &
            +side_inner_left & -side_inner_right &
            active_z
        )
    ))

    # Side plates — active zone only
    cells.append(openmc.Cell(
        name=f'std{elem_id}_side_left',
        fill=aluminum,
        region=(
            +box_left & -side_inner_left &
            +box_front & -box_back &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_side_right',
        fill=aluminum,
        region=(
            +side_inner_right & -box_right &
            +box_front & -box_back &
            active_z
        )
    ))

    # Inter-element water gaps — active zone only
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_xleft',
        fill=water_core,
        region=(
            +pitch_left & -box_left &
            +pitch_front & -pitch_back &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_xright',
        fill=water_core,
        region=(
            +box_right & -pitch_right &
            +pitch_front & -pitch_back &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_yfront',
        fill=water_core,
        region=(
            +box_left & -box_right &
            +pitch_front & -box_front &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_yback',
        fill=water_core,
        region=(
            +box_left & -box_right &
            +box_back & -pitch_back &
            active_z
        )
    ))

    # ── Axial regions above/below the active fuel ──────────────────────────
    # End-box footprint mirrors the active-core element/gap grid: envelope
    # block (same box_left/right/front/back as the active zone) + thin pitch
    # gaps (same pitch_left/right/front/back), via _endbox_gap_cells, just
    # restricted to the end-box z-band instead of active_z. Water-beyond
    # regions stay full pitch (uniform water, no grid needed).
    full_pitch = +pitch_left & -pitch_right & +pitch_front & -pitch_back
    envelope   = +box_left & -box_right & +box_front & -box_back

    cells.append(openmc.Cell(
        name=f'std{elem_id}_upper_endbox',
        fill=end_box_homog,
        region=envelope & +_z_fuel_top & -_z_endbox_above
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_upper_water',
        fill=water,
        region=full_pitch & +_z_endbox_above & -_z_model_top
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_lower_endbox',
        fill=end_box_homog,
        region=envelope & +_z_endbox_below & -_z_fuel_bot
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_lower_water',
        fill=water,
        region=full_pitch & +_z_model_bot & -_z_endbox_below
    ))

    pitch_planes = (pitch_left, pitch_right, pitch_front, pitch_back)
    box_planes   = (box_left, box_right, box_front, box_back)
    cells.extend(_endbox_gap_cells(f'std{elem_id}_endbox_upper', water_core,
        pitch_planes, box_planes, _z_fuel_top, _z_endbox_above))
    cells.extend(_endbox_gap_cells(f'std{elem_id}_endbox_lower', water_core,
        pitch_planes, box_planes, _z_endbox_below, _z_fuel_bot))

    return openmc.Universe(name=f'std_fuel_elem_{elem_id}', cells=cells)


# =============================================================================
# CONTROL ELEMENT
# Architecture: two end blocks + central 17-plate fuel follower stack, built
# on the SAME standard 0.127 cm plate / 0.219 cm channel pitch as the standard
# fuel element (TECDOC A-2 Table 1: "17 + 4 Al plates").
#
#   Follower fuel stack (17 plates + 16 channels), centered on the element:
#     half-width = (17*PLATE_THICK_INNER + 16*WATER_CHAN_THICK) / 2 = 2.8315 cm
#
#   Each end, from the fuel stack outward to the element wall:
#     [feeder channel 0.219 | Al inner guide 0.150 | blade water g |
#      B4C blade slot 0.310 | blade water g | Al outer guide 0.150 |
#      outer offset water OUTER_OFFSET]
#   The feeder channel is a standard fuel-to-fuel water channel (matches the
#   follower's own plate pitch). The two blade-flanking water gaps are EQUAL
#   (even spacing) and are the residual after every other layer is fixed:
#     g = (END_BLOCK - 2*CTRL_AL_PLATE_THICK - ABSORBER_THICK - CTRL_OUTER_OFFSET
#          - CTRL_FEEDER_CHANNEL) / 2
#   where END_BLOCK = ELEM_Y/2 - CTRL_FUEL_STACK_HALF (1.1685 cm, fixed by the
#   element envelope and the fuel stack half-width above).
#
# Fixed-length sliding blade:
#   The B4C absorber blade is BLADE_LENGTH=60 cm long and translates in z.
#   At fraction f, the blade occupies z=[z_bot, z_top] = [-30+f*60, +30+f*60].
#   b4c fills the Hf-slot x/y band for z in [z_bot, z_top] across the full
#   model height. Below z_bot, water fills the slot (active zone only — the
#   blade never dips below z=-30, so the lower end-box/water are uniform
#   material with no reserved slot at all). Above z_top, the slot's own
#   material is region-appropriate (homo in [+30,+45], water in
#   [+45, CORE_TOP]) rather than a permanently reserved water channel; at
#   f=1, z_top == CORE_TOP so that complement is zero-measure (no cap).
#   All guide/slider/fuel/channel cells are bounded to the active zone
#   z=[-30, +30]; end-box/water cells fill z outside that range.
# =============================================================================

ABSORBER_THICK  = 0.31

CTRL_FUEL_WIDTH_X   = ACTIVE_STACK_X
CTRL_SIDE_PLATE_X   = SIDE_PLATE_THICK
CTRL_AL_PLATE_THICK = 0.127   # cm (1.27 mm) [TECDOC] — was 0.15 (an Argonne
                              # TH-analysis convenience); reverted 2026-07-20.
CTRL_HF_THICK       = ABSORBER_THICK

N_CTRL_FUEL_PLATES  = 17
CTRL_PLATE_PITCH    = PLATE_THICK_INNER + WATER_CHAN_THICK   # 0.346 cm

# Follower fuel stack half-width (standard 0.127/0.219 pitch, symmetric)
CTRL_FUEL_STACK_HALF = (N_CTRL_FUEL_PLATES * PLATE_THICK_INNER
                        + (N_CTRL_FUEL_PLATES - 1) * WATER_CHAN_THICK) / 2.0  # 2.8315 cm

# Feeder channel: the follower's outermost fuel plate to the inner guide
# plate is a standard fuel-to-fuel water channel, same width as every
# plate-to-plate channel in the stack above it.
CTRL_FEEDER_CHANNEL = WATER_CHAN_THICK   # 0.219 cm [DERIVED — standard channel]

# Gap between the outer guide plate and the element wall, likewise set to the
# standard-element end gap.
CTRL_OUTER_OFFSET = STD_END_WATER   # 0.1075 cm [DERIVED, 2026-07-20 meeting]

# End-block budget: everything between the fuel stack edge and the wall.
CTRL_END_BLOCK = ELEM_Y / 2.0 - CTRL_FUEL_STACK_HALF   # 1.1685 cm

# Blade-flanking water gap — residual, split equally on both sides of the
# blade. Recomputes automatically if CTRL_OUTER_OFFSET (or any layer above)
# changes.
CTRL_BLADE_WATER = (CTRL_END_BLOCK - CTRL_FEEDER_CHANNEL
                    - 2.0 * CTRL_AL_PLATE_THICK - ABSORBER_THICK
                    - CTRL_OUTER_OFFSET) / 2.0
# With the 2026-07-20 values this evaluates to exactly:
#   (1.1685 - 0.219 - 2*0.127 - 0.31 - 0.1075) / 2 = 0.139 cm

assert CTRL_BLADE_WATER >= 0.05, (
    f"CTRL_BLADE_WATER={CTRL_BLADE_WATER:.5f} cm is degenerate for "
    f"CTRL_AL_PLATE_THICK={CTRL_AL_PLATE_THICK}, "
    f"CTRL_OUTER_OFFSET={CTRL_OUTER_OFFSET} — check end-block budget")


def make_control_fuel_element(elem_id, withdrawn_fraction=0.0):
    """
    Control fuel element with a fixed-length (60 cm) B4C absorber blade that
    translates in z.

    withdrawn_fraction f in [0, 1]:
        f=0 → blade at z=[-30, +30] (all-in, blade fully within active fuel)
        f=1 → blade at z=[+30, +90] (all-out, blade entirely above active fuel)

    The blade always exists; only its z-position changes.
    """
    f = withdrawn_fraction
    z_bot = -HALF_Z + f * ROD_TRAVEL   # blade bottom
    z_top = z_bot + BLADE_LENGTH        # blade top

    assert z_bot >= CORE_BOTTOM, (
        f"ctrl{elem_id}: blade bottom {z_bot:.2f} < CORE_BOTTOM {CORE_BOTTOM}")
    assert z_top <= CORE_TOP, (
        f"ctrl{elem_id}: blade top {z_top:.2f} > CORE_TOP {CORE_TOP}")
    # These two are the sole justification for (a) merging the lower end-box/
    # water into uniform material with no Hf-slot exclusion, and (b) never
    # needing an "above-active" water-gap cell (the blade always reaches at
    # least the top of the active zone). If travel or geometry parameters
    # ever change so these fail, both simplifications below become wrong.
    assert z_bot >= -HALF_Z, (
        f"ctrl{elem_id}: blade_z_bot={z_bot:.2f} < -HALF_Z ({-HALF_Z}) — "
        "blade would enter the lower end-box/water; lower-side merge is invalid")
    assert z_top >= HALF_Z, (
        f"ctrl{elem_id}: blade_z_top={z_top:.2f} < HALF_Z ({HALF_Z}) — "
        "blade would leave a water gap above it inside the active zone")
    print(f"ctrl{elem_id}: f={f:.3f}  blade z=[{z_bot:.2f}, {z_top:.2f}] cm"
          f"  (within [{CORE_BOTTOM}, {CORE_TOP}] ✓)")

    # Axial surfaces for this blade position
    blade_z_bot = openmc.ZPlane(z0=z_bot)
    blade_z_top = openmc.ZPlane(z0=z_top)
    active_z    = +_z_fuel_bot & -_z_fuel_top

    cells = []

    # Pitch cell boundaries
    pitch_left  = openmc.XPlane(x0=-PITCH_X / 2.0)
    pitch_right = openmc.XPlane(x0= PITCH_X / 2.0)
    pitch_front = openmc.YPlane(y0=-PITCH_Y / 2.0)
    pitch_back  = openmc.YPlane(y0= PITCH_Y / 2.0)

    # Element envelope
    elem_left  = openmc.XPlane(x0=-ELEM_X / 2.0)
    elem_right = openmc.XPlane(x0= ELEM_X / 2.0)
    elem_front = openmc.YPlane(y0=-ELEM_Y / 2.0)
    elem_back  = openmc.YPlane(y0= ELEM_Y / 2.0)

    # X-band for the interior stack (between side plates)
    side_inner_left  = openmc.XPlane(x0=-CTRL_FUEL_WIDTH_X / 2.0)
    side_inner_right = openmc.XPlane(x0= CTRL_FUEL_WIDTH_X / 2.0)

    # Fuel meat x/z bounds
    meat_zbot  = _z_fuel_bot
    meat_ztop  = _z_fuel_top
    meat_left  = openmc.XPlane(x0=-MEAT_WIDTH / 2.0)
    meat_right = openmc.XPlane(x0= MEAT_WIDTH / 2.0)

    # Y-layout — fuel stack is centered, half-width fixed by the standard
    # 0.127/0.219 pitch (CTRL_FUEL_STACK_HALF, module level).
    y_fuel_start = -CTRL_FUEL_STACK_HALF   # −2.8315 cm
    y_fuel_end   =  CTRL_FUEL_STACK_HALF   # +2.8315 cm

    # Bottom end block, built outward from the fuel stack to the wall:
    #   feeder channel (0.219) | inner guide (Al) | blade water (g) |
    #   B4C blade slot | blade water (g) | outer guide (Al) | outer offset water
    bot_slider_top = openmc.YPlane(y0=y_fuel_start - CTRL_FEEDER_CHANNEL)
    bot_slider_bot = openmc.YPlane(y0=bot_slider_top.y0 - CTRL_AL_PLATE_THICK)
    bot_hf_top     = openmc.YPlane(y0=bot_slider_bot.y0 - CTRL_BLADE_WATER)
    bot_hf_bot     = openmc.YPlane(y0=bot_hf_top.y0 - ABSORBER_THICK)
    bot_guide_top  = openmc.YPlane(y0=bot_hf_bot.y0 - CTRL_BLADE_WATER)
    bot_offset_top = openmc.YPlane(y0=bot_guide_top.y0 - CTRL_AL_PLATE_THICK)
    # bot_offset_top should coincide with elem_front + CTRL_OUTER_OFFSET
    assert abs(bot_offset_top.y0 - (-ELEM_Y / 2.0 + CTRL_OUTER_OFFSET)) < 1e-9, \
        "control end-block budget does not reach the element wall (bottom)"

    # Top end block — mirror image, built outward from the fuel stack to the wall.
    top_slider_bot = openmc.YPlane(y0=y_fuel_end + CTRL_FEEDER_CHANNEL)
    top_slider_top = openmc.YPlane(y0=top_slider_bot.y0 + CTRL_AL_PLATE_THICK)
    top_hf_bot     = openmc.YPlane(y0=top_slider_top.y0 + CTRL_BLADE_WATER)
    top_hf_top     = openmc.YPlane(y0=top_hf_bot.y0 + ABSORBER_THICK)
    top_guide_bot  = openmc.YPlane(y0=top_hf_top.y0 + CTRL_BLADE_WATER)
    top_guide_top  = openmc.YPlane(y0=top_guide_bot.y0 + CTRL_AL_PLATE_THICK)
    assert abs(top_guide_top.y0 - (ELEM_Y / 2.0 - CTRL_OUTER_OFFSET)) < 1e-9, \
        "control end-block budget does not reach the element wall (top)"

    # Hf slot x/y footprints (unbounded in z — blade cells own their z-range)
    hf_slot_b = +bot_hf_bot & -bot_hf_top & +side_inner_left & -side_inner_right
    hf_slot_t = +top_hf_bot & -top_hf_top & +side_inner_left & -side_inner_right

    # ── Bottom sandwich structural cells (active zone only) ─────────────────
    # Wall -> fuel: offset water | outer guide | blade water | [blade] |
    #               blade water | inner guide | feeder channel | fuel

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_offset_water_bottom', fill=water_core,
        region=(+elem_front & -bot_offset_top &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_guide_bottom', fill=aluminum,
        region=(+bot_offset_top & -bot_guide_top &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_blade_water_outer_bottom', fill=water_core,
        region=(+bot_guide_top & -bot_hf_bot &
                +side_inner_left & -side_inner_right & active_z)))

    # (Hf slot cells are handled separately below — not bounded to active_z)

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_blade_water_inner_bottom', fill=water_core,
        region=(+bot_hf_top & -bot_slider_bot &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slider_bottom', fill=aluminum,
        region=(+bot_slider_bot & -bot_slider_top &
                +side_inner_left & -side_inner_right & active_z)))

    # ── Top sandwich structural cells (active zone only) ────────────────────
    # Fuel -> wall: feeder channel | inner guide | blade water | [blade] |
    #               blade water | outer guide | offset water

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slider_top', fill=aluminum,
        region=(+top_slider_bot & -top_slider_top &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_blade_water_inner_top', fill=water_core,
        region=(+top_slider_top & -top_hf_bot &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_blade_water_outer_top', fill=water_core,
        region=(+top_hf_top & -top_guide_bot &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_guide_top', fill=aluminum,
        region=(+top_guide_bot & -top_guide_top &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_offset_water_top', fill=water_core,
        region=(+top_guide_top & -elem_back &
                +side_inner_left & -side_inner_right & active_z)))

    # ── Fixed-length B4C blade ───────────────────────────────────────────────
    # B4C occupies [z_bot, z_top] in the Hf-slot band, unbounded by axial
    # region (spans across active/end-box/water boundaries as one piece).
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_absorber_bottom', fill=b4c,
        region=hf_slot_b & +blade_z_bot & -blade_z_top))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_absorber_top', fill=b4c,
        region=hf_slot_t & +blade_z_bot & -blade_z_top))

    # Water gap below the blade, ACTIVE ZONE ONLY (blade withdrawing vacates
    # the bottom of the active zone; blade_z_bot in [-30,+30] per the assert
    # above). There is never a gap above the blade inside the active zone,
    # since blade_z_top is always >= HALF_Z (asserted above).
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slot_b_water_active', fill=water_core,
        region=hf_slot_b & +_z_fuel_bot & -blade_z_bot))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slot_t_water_active', fill=water_core,
        region=hf_slot_t & +_z_fuel_bot & -blade_z_bot))

    # Moving homogenized end-box cap, rigidly attached to the blade top. A
    # 15 cm end_box_homog cap rides on top of the blade in the Hf-slot x/y
    # band, translating with it and clipped at CORE_TOP; above the cap the slot
    # is water (294 K) up to CORE_TOP. At f=0 the cap occupies [+30,+45],
    # coplanar with the surrounding end-boxes. At f=1 the blade top coincides
    # with CORE_TOP, so the cap is pushed entirely out of the model and is not
    # created at all — the blade fills the slot to the top.
    # No lower-side counterpart is needed: blade_z_bot is always >= -HALF_Z
    # (asserted above), so the blade never reaches the lower end-box/water.
    if z_top < CORE_TOP:
        # Cap top is always >= +45 (z_top >= HALF_Z = +30, asserted above), so
        # the water above the cap never encroaches on the end-box band
        # [+30,+45].
        assert z_top + 15.0 >= ENDBOX_ABOVE_TOP, (
            f"ctrl{elem_id}: cap top {z_top + 15.0:.2f} < ENDBOX_ABOVE_TOP "
            f"{ENDBOX_ABOVE_TOP} — cap would not clear the end-box band")
        blade_cap_top = openmc.ZPlane(z0=min(z_top + 15.0, CORE_TOP))
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_blade_cap_slot_b', fill=end_box_homog,
            region=hf_slot_b & +blade_z_top & -blade_cap_top))
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_blade_cap_slot_t', fill=end_box_homog,
            region=hf_slot_t & +blade_z_top & -blade_cap_top))
        if blade_cap_top.z0 < CORE_TOP:
            cells.append(openmc.Cell(
                name=f'ctrl{elem_id}_water_above_cap_slot_b', fill=water,
                region=hf_slot_b & +blade_cap_top & -_z_model_top))
            cells.append(openmc.Cell(
                name=f'ctrl{elem_id}_water_above_cap_slot_t', fill=water,
                region=hf_slot_t & +blade_cap_top & -_z_model_top))

    # ── 17-plate fuel follower (active zone only) ───────────────────────────

    plate_bot_surfs = []
    plate_top_surfs = []

    for i in range(N_CTRL_FUEL_PLATES):
        # Standard 0.127/0.219 pitch, same as the standard fuel element.
        plate_bot = y_fuel_start + i * CTRL_PLATE_PITCH
        plate_top = plate_bot + PLATE_THICK_INNER

        plate_bot_s = openmc.YPlane(y0=plate_bot)
        plate_top_s = openmc.YPlane(y0=plate_top)
        plate_bot_surfs.append(plate_bot_s)
        plate_top_surfs.append(plate_top_s)

        meat_b = openmc.YPlane(y0=plate_bot + CLAD_THICK_INNER)
        meat_t = openmc.YPlane(y0=plate_top - CLAD_THICK_INNER)
        meat_region = (
            +meat_b & -meat_t &
            +meat_left & -meat_right &
            +meat_zbot & -meat_ztop
        )
        clad_region = (
            +plate_bot_s & -plate_top_s &
            +side_inner_left & -side_inner_right &
            active_z &
            ~meat_region
        )
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_meat_{i}', fill=fuel, region=meat_region))
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_clad_{i}', fill=clad, region=clad_region))

    # Water channels (active zone only)
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_chan_bot_half', fill=water_core,
        region=(+bot_slider_top & -plate_bot_surfs[0] &
                +side_inner_left & -side_inner_right & active_z)))
    for i in range(N_CTRL_FUEL_PLATES - 1):
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_chan_{i}', fill=water_core,
            region=(+plate_top_surfs[i] & -plate_bot_surfs[i + 1] &
                    +side_inner_left & -side_inner_right & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_chan_top_half', fill=water_core,
        region=(+plate_top_surfs[-1] & -top_slider_bot &
                +side_inner_left & -side_inner_right & active_z)))

    # Side plates (active zone only)
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_side_left', fill=aluminum,
        region=(+elem_left & -side_inner_left &
                +elem_front & -elem_back & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_side_right', fill=aluminum,
        region=(+side_inner_right & -elem_right &
                +elem_front & -elem_back & active_z)))

    # Inter-element water gaps (active zone only)
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_xleft', fill=water_core,
        region=(+pitch_left & -elem_left &
                +pitch_front & -pitch_back & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_xright', fill=water_core,
        region=(+elem_right & -pitch_right &
                +pitch_front & -pitch_back & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_yfront', fill=water_core,
        region=(+elem_left & -elem_right &
                +pitch_front & -elem_front & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_yback', fill=water_core,
        region=(+elem_left & -elem_right &
                +elem_back & -pitch_back & active_z)))

    # ── Axial regions above/below active fuel ───────────────────────────────
    # Upper end-box/water still exclude the Hf-slot footprint (handled above,
    # since the blade can reach into them). Lower end-box/water need NO such
    # exclusion: the blade never enters z<-HALF_Z (asserted above), so that
    # band is uniform material straight through — no reserved gap. End-box
    # footprint mirrors the active-core element/gap grid (envelope + thin
    # pitch gaps via _endbox_gap_cells); water-beyond stays full pitch.
    full_pitch   = +pitch_left & -pitch_right & +pitch_front & -pitch_back
    envelope     = +elem_left & -elem_right & +elem_front & -elem_back
    not_hf_slots = ~hf_slot_b & ~hf_slot_t   # complement of both Hf slot footprints

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_upper_endbox', fill=end_box_homog,
        region=envelope & +_z_fuel_top & -_z_endbox_above & not_hf_slots))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_upper_water', fill=water,
        region=full_pitch & +_z_endbox_above & -_z_model_top & not_hf_slots))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_lower_endbox', fill=end_box_homog,
        region=envelope & +_z_endbox_below & -_z_fuel_bot))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_lower_water', fill=water,
        region=full_pitch & +_z_model_bot & -_z_endbox_below))

    pitch_planes = (pitch_left, pitch_right, pitch_front, pitch_back)
    elem_planes  = (elem_left, elem_right, elem_front, elem_back)
    cells.extend(_endbox_gap_cells(f'ctrl{elem_id}_endbox_upper', water_core,
        pitch_planes, elem_planes, _z_fuel_top, _z_endbox_above))
    cells.extend(_endbox_gap_cells(f'ctrl{elem_id}_endbox_lower', water_core,
        pitch_planes, elem_planes, _z_endbox_below, _z_fuel_bot))

    return openmc.Universe(name=f'ctrl_fuel_elem_{elem_id}', cells=cells)


# =============================================================================
# FLUX TRAP
# =============================================================================

def make_flux_trap():
    """
    Flux trap: aluminum block with a central cylindrical water hole (water_core
    at 316.8 K, the same core coolant water used throughout the core), matching
    the MCNP deck which models the hole as a ZCylinder rather than the
    originally-commented square.

    The aluminum block itself fills the FULL lattice pitch (PITCH_X x
    PITCH_Y = 7.7 x 8.1 cm) — there is no inter-element water gap around the
    active-zone block. The axial end-box (homogenized water/Al) region above
    and below, however, keeps the SAME ELEM_X x ELEM_Y envelope/pitch grid as
    the fuel and graphite elements — i.e. the core-element separation
    channels continue through the end-box region here too, using core
    coolant water (water_core) rather than the old bulk-water gap fill.

    Cylinder: radius FT_HOLE_RADIUS = 2.5 cm, centered at element origin (x=0, y=0).
    The cylinder is axially unbounded within the active zone (active_z clips it).
    Aluminum fills the annular region between the cylinder and the pitch envelope.
    """
    pitch_left  = openmc.XPlane(x0=-PITCH_X / 2.0)
    pitch_right = openmc.XPlane(x0= PITCH_X / 2.0)
    pitch_front = openmc.YPlane(y0=-PITCH_Y / 2.0)
    pitch_back  = openmc.YPlane(y0= PITCH_Y / 2.0)

    elem_left  = openmc.XPlane(x0=-ELEM_X / 2.0)
    elem_right = openmc.XPlane(x0= ELEM_X / 2.0)
    elem_front = openmc.YPlane(y0=-ELEM_Y / 2.0)
    elem_back  = openmc.YPlane(y0= ELEM_Y / 2.0)

    hole_cyl = openmc.ZCylinder(x0=0.0, y0=0.0, r=FT_HOLE_RADIUS)

    active_z = +_z_fuel_bot & -_z_fuel_top

    cells = []

    # Cylindrical water hole — core coolant water at 316.8 K
    cells.append(openmc.Cell(
        name='flux_trap_water_hole',
        fill=water_core,
        region=-hole_cyl & active_z
    ))
    # Aluminum block: full pitch envelope minus the cylinder, active zone only
    cells.append(openmc.Cell(
        name='flux_trap_aluminum_block',
        fill=aluminum,
        region=(+pitch_left & -pitch_right & +pitch_front & -pitch_back & +hole_cyl & active_z)
    ))

    # Axial regions above/below active fuel. End-box mirrors the active-core
    # element/gap grid (envelope + thin pitch gaps via _endbox_gap_cells,
    # filled with core coolant water); water-beyond stays full pitch.
    full_pitch = +pitch_left & -pitch_right & +pitch_front & -pitch_back
    envelope   = +elem_left & -elem_right & +elem_front & -elem_back

    cells.append(openmc.Cell(
        name='flux_trap_upper_endbox',
        fill=end_box_homog,
        region=envelope & +_z_fuel_top & -_z_endbox_above
    ))
    cells.append(openmc.Cell(
        name='flux_trap_upper_water',
        fill=water,
        region=full_pitch & +_z_endbox_above & -_z_model_top
    ))
    cells.append(openmc.Cell(
        name='flux_trap_lower_endbox',
        fill=end_box_homog,
        region=envelope & +_z_endbox_below & -_z_fuel_bot
    ))
    cells.append(openmc.Cell(
        name='flux_trap_lower_water',
        fill=water,
        region=full_pitch & +_z_model_bot & -_z_endbox_below
    ))

    pitch_planes = (pitch_left, pitch_right, pitch_front, pitch_back)
    elem_planes  = (elem_left, elem_right, elem_front, elem_back)
    cells.extend(_endbox_gap_cells('flux_trap_endbox_upper', water_core,
        pitch_planes, elem_planes, _z_fuel_top, _z_endbox_above))
    cells.extend(_endbox_gap_cells('flux_trap_endbox_lower', water_core,
        pitch_planes, elem_planes, _z_endbox_below, _z_fuel_bot))

    return openmc.Universe(name='flux_trap_universe', cells=cells)


# =============================================================================
# WATER AND GRAPHITE FILL UNIVERSES
# =============================================================================

# Water universe: fully unbounded — bulk water fills whatever space the parent
# lattice boundary provides (used for the outer ring and top/bottom water rows).
water_cell = openmc.Cell(name='water_fill', fill=water)
water_univ = openmc.Universe(name='water_universe', cells=[water_cell])

# Graphite reflector universe.
#
# In-plane: the graphite block itself IS a solid block — each reflector
# element fills its full lattice pitch cell in the active-graphite z-range
# (no inter-element water gaps), so adjacent reflector positions form one
# continuous graphite wall.
#
# Axially: graphite occupies only the active fuel z-range [-30, +30]. Above
# and below, the end-box (homogenized water/Al) region keeps the SAME
# envelope/pitch grid as the fuel elements — i.e. the core-element gaps
# continue through the end-box region for each reflector position, even
# though the graphite wall above/below them is continuous. Water-beyond
# stays full pitch, mirroring the fuel element end-box + water stack so the
# reflector height matches the core height.
def make_graphite_element():
    """Graphite reflector element: continuous wall in-plane, gapped end-box axially."""
    # TODO (2026-07-20 meeting): add small water channels BETWEEN graphite
    # blocks. Dimension is pending — it must come FROM THE MCNP MODEL; do not
    # invent a channel width. Until then the reflector remains a continuous
    # in-plane wall (no inter-block gap).
    pitch_left  = openmc.XPlane(x0=-PITCH_X / 2.0)
    pitch_right = openmc.XPlane(x0= PITCH_X / 2.0)
    pitch_front = openmc.YPlane(y0=-PITCH_Y / 2.0)
    pitch_back  = openmc.YPlane(y0= PITCH_Y / 2.0)

    blk_left  = openmc.XPlane(x0=-ELEM_X / 2.0)
    blk_right = openmc.XPlane(x0= ELEM_X / 2.0)
    blk_front = openmc.YPlane(y0=-ELEM_Y / 2.0)
    blk_back  = openmc.YPlane(y0= ELEM_Y / 2.0)

    active_z   = +_z_fuel_bot & -_z_fuel_top
    full_pitch = +pitch_left & -pitch_right & +pitch_front & -pitch_back
    envelope   = +blk_left & -blk_right & +blk_front & -blk_back

    cells = [
        openmc.Cell(
            name='graphite_block',
            fill=graphite,
            region=active_z,
        ),
        openmc.Cell(
            name='graphite_upper_endbox',
            fill=end_box_homog,
            region=envelope & +_z_fuel_top & -_z_endbox_above,   # +30 → +45 cm
        ),
        openmc.Cell(
            name='graphite_upper_water',
            fill=water,
            region=full_pitch & +_z_endbox_above & -_z_model_top,  # +45 → +90 cm
        ),
        openmc.Cell(
            name='graphite_lower_endbox',
            fill=end_box_homog,
            region=envelope & +_z_endbox_below & -_z_fuel_bot,   # −45 → −30 cm
        ),
        openmc.Cell(
            name='graphite_lower_water',
            fill=water,
            region=full_pitch & +_z_model_bot & -_z_endbox_below,  # −90 → −45 cm
        ),
    ]

    pitch_planes = (pitch_left, pitch_right, pitch_front, pitch_back)
    blk_planes   = (blk_left, blk_right, blk_front, blk_back)
    cells.extend(_endbox_gap_cells('graphite_endbox_upper', water_core,
        pitch_planes, blk_planes, _z_fuel_top, _z_endbox_above))
    cells.extend(_endbox_gap_cells('graphite_endbox_lower', water_core,
        pitch_planes, blk_planes, _z_endbox_below, _z_fuel_bot))

    return openmc.Universe(name='graphite_universe', cells=cells)


graphite_univ = make_graphite_element()


# =============================================================================
# CORE LATTICE — TECDOC-643 Fig. 2.1 (LEU panel)
# =============================================================================

def build_core_geometry(withdrawn_fraction=1.0):
    """Build the full-core openmc.Geometry for a blade WITHDRAWAL fraction f.

    f = 0.0 → blades fully INSERTED  (absorber spans z=[-30, +30])
    f = 1.0 → blades fully WITHDRAWN (absorber spans z=[+30, +90])

    This is the single construction path used by core.build_model() and all
    run/ drivers. Vacuum boundaries at the lattice edge and at
    CORE_BOTTOM=-90 / CORE_TOP=+90 accommodate the full axial stack
    (water/end-box/fuel/end-box/water); the withdrawn (f=1) blade top
    coincides exactly with CORE_TOP, so there is no water cap above it.
    """
    std_elems  = [make_standard_fuel_element(i) for i in range(23)]
    ctrl_elems = [make_control_fuel_element(100 + i,
                                            withdrawn_fraction=withdrawn_fraction)
                  for i in range(5)]

    W = water_univ
    G = graphite_univ
    S = std_elems
    C = ctrl_elems
    F = make_flux_trap()

    lattice_universes = [
        [W, W, W, W, W, W, W, W],
        [W, G, G, G, G, G, G, W],
        [W, S[0],  S[1],  C[0],  S[2],  S[3],  S[4],  W],
        [W, S[5],  S[6],  S[7],  S[8],  C[1],  S[9],  W],
        [W, S[10], C[2],  S[11], F,     S[12], S[13], W],
        [W, S[14], S[15], S[16], S[17], C[3],  S[18], W],
        [W, F,     S[19], C[4],  S[20], S[21], S[22], W],
        [W, G, G, G, G, G, G, W],
        [W, W, W, W, W, W, W, W],
    ]

    core_lattice = openmc.RectLattice(name='core_lattice')
    core_lattice.pitch      = (PITCH_X, PITCH_Y)
    core_lattice.lower_left = (-4 * PITCH_X, -4.5 * PITCH_Y)
    core_lattice.universes  = lattice_universes
    # Guard against edge-case lattice lookups just outside the universe array
    # (floating-point roundoff at the boundary planes) — fill with bulk water
    # instead of losing the particle.
    core_lattice.outer      = water_univ

    core_left   = openmc.XPlane(x0=-4   * PITCH_X, boundary_type='vacuum')
    core_right  = openmc.XPlane(x0= 4   * PITCH_X, boundary_type='vacuum')
    core_front  = openmc.YPlane(y0=-4.5 * PITCH_Y, boundary_type='vacuum')
    core_back   = openmc.YPlane(y0= 4.5 * PITCH_Y, boundary_type='vacuum')
    core_bottom = openmc.ZPlane(z0=CORE_BOTTOM,     boundary_type='vacuum')
    core_top    = openmc.ZPlane(z0=CORE_TOP,        boundary_type='vacuum')

    core_region = (
        +core_left  & -core_right  &
        +core_front & -core_back   &
        +core_bottom & -core_top
    )
    core_cell = openmc.Cell(name='core_cell', fill=core_lattice,
                            region=core_region)

    root_universe = openmc.Universe(name='root', cells=[core_cell])
    return openmc.Geometry(root_universe)


# Module-level default geometry (blades fully inserted) — kept for direct
# `python geometry.py` debug use; drivers should call build_core_geometry().
geometry = build_core_geometry(withdrawn_fraction=0.0)


if __name__ == '__main__':
    geometry.export_to_xml()
    print("geometry.xml written successfully.\n")
    print(f"Lattice pitch:        {PITCH_X} x {PITCH_Y} cm")
    print(f"Element envelope:     {ELEM_X} x {ELEM_Y} x {ELEM_Z} cm")
    print(f"Active fuel z:        [{-HALF_Z}, {+HALF_Z}] cm")
    print(f"End-box above:        [{+HALF_Z}, {ENDBOX_ABOVE_TOP}] cm")
    print(f"End-box below:        [{ENDBOX_BELOW_BOT}, {-HALF_Z}] cm")
    print(f"Core z-bounds:        [{CORE_BOTTOM}, {CORE_TOP}] cm (vacuum)")
    print(f"End-box gap width:    GAP_X={GAP_X:.4f} cm, GAP_Y={GAP_Y:.4f} cm "
          f"(same pitch/envelope surfaces reused for active-zone and "
          f"end-box gap cells — no separate value possible)")
    print(f"\nBlade model:")
    print(f"  BLADE_LENGTH = {BLADE_LENGTH} cm (fixed)")
    print(f"  ROD_TRAVEL   = {ROD_TRAVEL} cm")
    for f_chk in [0.0, 0.5, 1.0]:
        z_b = -HALF_Z + f_chk * ROD_TRAVEL
        z_t = z_b + BLADE_LENGTH
        ok = z_b >= CORE_BOTTOM and z_t <= CORE_TOP
        print(f"  f={f_chk:.1f}: blade z=[{z_b:.1f}, {z_t:.1f}]  "
              f"within [{CORE_BOTTOM},{CORE_TOP}]: {ok}")

    print(f"\nControl element layout:")
    print(f"  Fuel stack half-width (CTRL_FUEL_STACK_HALF): "
          f"{CTRL_FUEL_STACK_HALF:.6f} cm")
    print(f"  Fuel stack:       [{-CTRL_FUEL_STACK_HALF:.6f}, "
          f"{CTRL_FUEL_STACK_HALF:.6f}] cm "
          f"({2*CTRL_FUEL_STACK_HALF:.6f} cm, 17 plates @ pitch "
          f"{CTRL_PLATE_PITCH:.6f} cm)")
    print(f"  End block (each): {CTRL_END_BLOCK:.6f} cm "
          f"(feeder {CTRL_FEEDER_CHANNEL:.5f} + guide {CTRL_AL_PLATE_THICK:.5f} "
          f"+ blade-water {CTRL_BLADE_WATER:.5f} + blade {ABSORBER_THICK:.5f} "
          f"+ blade-water {CTRL_BLADE_WATER:.5f} + guide {CTRL_AL_PLATE_THICK:.5f} "
          f"+ offset {CTRL_OUTER_OFFSET:.5f})")

    end_block_layer_sum = (CTRL_FEEDER_CHANNEL + CTRL_AL_PLATE_THICK
                           + CTRL_BLADE_WATER + ABSORBER_THICK
                           + CTRL_BLADE_WATER + CTRL_AL_PLATE_THICK
                           + CTRL_OUTER_OFFSET)
    print(f"  End-block layer sum: {end_block_layer_sum:.6f} cm "
          f"(should be {CTRL_END_BLOCK:.6f})")
    print(f"  Total (2 ends + fuel stack): "
          f"{2*end_block_layer_sum + 2*CTRL_FUEL_STACK_HALF:.6f} cm (should be {ELEM_Y})")

    assert abs(end_block_layer_sum - CTRL_END_BLOCK) < 1e-9, \
        "control end-block layers do not sum to CTRL_END_BLOCK"
    assert abs(2*end_block_layer_sum + 2*CTRL_FUEL_STACK_HALF - ELEM_Y) < 1e-9, \
        "control element total height != ELEM_Y"

    # Geometry overlap check
    import tempfile
    from materials import materials as _materials
    from settings import settings as _settings

    _settings.particles = 200
    _settings.batches   = 2
    _settings.inactive  = 1

    debug_model = openmc.Model(
        geometry=geometry, materials=_materials, settings=_settings
    )
    with tempfile.TemporaryDirectory() as _debug_dir:
        debug_model.run(geometry_debug=True, cwd=_debug_dir)
    print("\nOverlap check (f=0.0) passed: no cell overlaps detected.")

    # f=1.0 exercises the degenerate case introduced by the axial resize:
    # blade_z_top == CORE_TOP exactly (three coincident ZPlane objects at the
    # withdrawn blade top / upper_water boundary / global vacuum boundary).
    geometry_f1 = build_core_geometry(withdrawn_fraction=1.0)
    debug_model_f1 = openmc.Model(
        geometry=geometry_f1, materials=_materials, settings=_settings
    )
    with tempfile.TemporaryDirectory() as _debug_dir_f1:
        debug_model_f1.run(geometry_debug=True, cwd=_debug_dir_f1)
    print("Overlap check (f=1.0) passed: no cell overlaps detected "
          "(blade top coincident with CORE_TOP vacuum boundary).")
