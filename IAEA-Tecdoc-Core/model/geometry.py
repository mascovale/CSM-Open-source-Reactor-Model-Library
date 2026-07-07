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

Axial model structure (TECDOC ANL appendix faithful):
    CORE_BOTTOM = -65 cm  (vacuum)
    [-65, -45]  : 20 cm light water
    [-45, -30]  : 15 cm homogenized end-box (0.25 Al / 0.75 H₂O by volume)
    [-30, +30]  : 60 cm active fuel region
    [+30, +45]  : 15 cm homogenized end-box
    [+45, +95]  : 50 cm light water (blade fully-out reaches z=+90)
    CORE_TOP    = +95 cm  (vacuum)

Control blade model — fixed-length sliding absorber:
    BLADE_LENGTH = 60 cm (rigid; never changes)
    ROD_TRAVEL   = 60 cm (full stroke)
    withdrawn_fraction f in [0, 1]:
        z_bot = -30 + f * 60   → f=0: -30,  f=1: +30
        z_top = z_bot + 60     → f=0: +30,  f=1: +90
    b4c fills the Hf-slot x/y band for z in [z_bot, z_top].
    Water fills the slot outside that range (below z_bot and above z_top).
    All other cells (guide plates, fuel, channels, etc.) are restricted
    to the active zone z=[-30, +30]; end-box/water cells cover z outside.

Standard Fuel Element (LEU, U3Si2-Al, heterogeneous build):
    - Envelope:           76 x 80 mm
    - Side plates:        4.8 mm each (aluminum, in x)
    - Active stack:       66.4 mm wide between side plate inner faces
    - 23 plates:          1.27 mm inner, 1.385 mm outer
    - Fuel meat:          0.51 mm thick x 63 mm wide x 600 mm tall
    - Inner clad:         0.38 mm  |  Outer clad: 0.495 mm

All dimensions in cm.
"""

import openmc
from materials import fuel, clad, water, water_flux_trap, b4c, graphite, aluminum, air, end_box_homog

# =============================================================================
# LATTICE / ELEMENT ENVELOPE
# =============================================================================

PITCH_X = 7.7    # cm  (77 mm)
PITCH_Y = 8.1    # cm  (81 mm)

ELEM_X = 7.6     # cm  (76 mm)
ELEM_Y = 8.0     # cm  (80 mm)
ELEM_Z = 60.0    # cm  (600 mm) — active fuel height

SIDE_PLATE_THICK = 0.48   # cm  (4.8 mm)
ACTIVE_STACK_X   = ELEM_X - 2 * SIDE_PLATE_THICK   # 6.64 cm

# =============================================================================
# PLATE / MEAT / CLAD DIMENSIONS
# =============================================================================

PLATE_THICK_INNER = 0.127    # cm  (1.27 mm)
PLATE_THICK_OUTER = 0.1385   # cm  (1.385 mm)

CLAD_THICK_INNER = 0.038     # cm  (0.38 mm)
CLAD_THICK_OUTER = 0.0495    # cm  (0.495 mm)

MEAT_THICK = 0.051           # cm  (0.51 mm)
MEAT_WIDTH = 6.3             # cm  (63 mm)

N_PLATES_STD  = 23
N_PLATES_CTRL = 17

WATER_CHAN_THICK = 0.219     # cm  (2.19 mm)

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
CORE_TOP         = +95.0   # cm — vacuum boundary (5 cm above fully-withdrawn blade top)
CORE_BOTTOM      = -65.0   # cm — vacuum boundary (15 cm end-box + 20 cm water below -30)
ENDBOX_ABOVE_TOP = +45.0   # cm — top of upper end-box  (+30 + 15 cm)
ENDBOX_BELOW_BOT = -45.0   # cm — bottom of lower end-box (-30 - 15 cm)

# Shared axial ZPlane surfaces — transmission (NOT vacuum boundaries).
# Defined once at module level and reused in every element universe to avoid
# creating redundant surfaces at identical z-values.
_z_fuel_bot     = openmc.ZPlane(z0=-HALF_Z)           # −30.0 cm
_z_fuel_top     = openmc.ZPlane(z0= HALF_Z)           # +30.0 cm
_z_endbox_above = openmc.ZPlane(z0=ENDBOX_ABOVE_TOP)  # +45.0 cm
_z_endbox_below = openmc.ZPlane(z0=ENDBOX_BELOW_BOT)  # −45.0 cm
_z_model_top    = openmc.ZPlane(z0=CORE_TOP)           # +95.0 cm
_z_model_bot    = openmc.ZPlane(z0=CORE_BOTTOM)        # −65.0 cm


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
    y = -stack_height_y / 2.0
    stack_bottom_surf = openmc.YPlane(y0=y)

    for i, plate_thick in enumerate(plate_thicks):
        is_first = (i == 0)
        is_last  = (i == N_PLATES_STD - 1)

        plate_bottom = openmc.YPlane(y0=y)
        plate_top    = openmc.YPlane(y0=y + plate_thick)

        if is_first:
            clad_bottom = CLAD_THICK_OUTER
            clad_top    = CLAD_THICK_INNER
        elif is_last:
            clad_bottom = CLAD_THICK_INNER
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
                fill=water,
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
        fill=water,
        region=(
            +box_front & -stack_bottom_surf &
            +side_inner_left & -side_inner_right &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_water_above_stack',
        fill=water,
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
        fill=water,
        region=(
            +pitch_left & -box_left &
            +pitch_front & -pitch_back &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_xright',
        fill=water,
        region=(
            +box_right & -pitch_right &
            +pitch_front & -pitch_back &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_yfront',
        fill=water,
        region=(
            +box_left & -box_right &
            +pitch_front & -box_front &
            active_z
        )
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_yback',
        fill=water,
        region=(
            +box_left & -box_right &
            +box_back & -pitch_back &
            active_z
        )
    ))

    # ── Axial regions above/below the active fuel ──────────────────────────
    # Fill the full pitch footprint; structural detail homogenized per TECDOC.
    full_pitch = +pitch_left & -pitch_right & +pitch_front & -pitch_back

    cells.append(openmc.Cell(
        name=f'std{elem_id}_upper_endbox',
        fill=end_box_homog,
        region=full_pitch & +_z_fuel_top & -_z_endbox_above
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_upper_water',
        fill=water,
        region=full_pitch & +_z_endbox_above & -_z_model_top
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_lower_endbox',
        fill=end_box_homog,
        region=full_pitch & +_z_endbox_below & -_z_fuel_bot
    ))
    cells.append(openmc.Cell(
        name=f'std{elem_id}_lower_water',
        fill=water,
        region=full_pitch & +_z_model_bot & -_z_endbox_below
    ))

    return openmc.Universe(name=f'std_fuel_elem_{elem_id}', cells=cells)


# =============================================================================
# CONTROL ELEMENT
# Architecture: two end sandwiches + central 17-plate fuel follower stack.
#   Each end (from element face inward, per TECDOC-643 v2 p.32 Fig.2 + Table 1):
#     [Al guide 0.127 | H₂O 0.268 | Hf/H₂O 0.310 | H₂O 0.243 | Al slider 0.127]
#     = 1.075 cm per end  (GUIDE_REGION)
#   Fuel region: ELEM_Y - 2×1.075 = 5.85 cm; 17 plates at pitch 5.85/17.
#
# Fixed-length sliding blade:
#   The Hf absorber blade is BLADE_LENGTH=60 cm long and translates in z.
#   At fraction f, the blade occupies z=[z_bot, z_top] = [-30+f*60, +30+f*60].
#   b4c fills the Hf-slot x/y band for z in [z_bot, z_top] across the
#   full model height. Water fills the slot below z_bot and above z_top.
#   All guide/slider/fuel/channel cells are bounded to the active zone
#   z=[-30, +30]; end-box/water cells fill z outside that range.
# =============================================================================

ABSORBER_THICK  = 0.31
ABSORBER_GAP    = 0.395
GUIDE_REGION    = 1.075

CTRL_FUEL_WIDTH_X   = ACTIVE_STACK_X
CTRL_SIDE_PLATE_X   = SIDE_PLATE_THICK
CTRL_AL_PLATE_THICK = .15
CTRL_HF_THICK       = ABSORBER_THICK

CTRL_INNER_WATER = ABSORBER_GAP - CTRL_AL_PLATE_THICK
CTRL_OUTER_WATER = GUIDE_REGION - ABSORBER_GAP - ABSORBER_THICK - CTRL_AL_PLATE_THICK

N_CTRL_FUEL_PLATES = 17


def make_control_fuel_element(elem_id, withdrawn_fraction=0.0):
    """
    Control fuel element with a fixed-length (60 cm) Hf absorber blade that
    translates in z.

    withdrawn_fraction f in [0, 1]:
        f=0 → blade at z=[-30, +30] (all-in, blade fully within active fuel)
        f=1 → blade at z=[+30, +90] (all-out, blade entirely above active fuel)

    The Hf blade always exists; only its z-position changes.
    """
    f = withdrawn_fraction
    z_bot = -HALF_Z + f * ROD_TRAVEL   # blade bottom
    z_top = z_bot + BLADE_LENGTH        # blade top

    assert z_bot >= CORE_BOTTOM, (
        f"ctrl{elem_id}: blade bottom {z_bot:.2f} < CORE_BOTTOM {CORE_BOTTOM}")
    assert z_top <= CORE_TOP, (
        f"ctrl{elem_id}: blade top {z_top:.2f} > CORE_TOP {CORE_TOP}")
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

    # Y-layout
    sandwich_per_end = GUIDE_REGION
    fuel_height  = ELEM_Y - 2.0 * sandwich_per_end   # 5.85 cm
    plate_pitch  = fuel_height / N_CTRL_FUEL_PLATES
    half_chan     = (plate_pitch - PLATE_THICK_INNER) / 2.0

    y_fuel_start = -ELEM_Y / 2.0 + sandwich_per_end   # −2.925 cm
    y_fuel_end   =  ELEM_Y / 2.0 - sandwich_per_end   # +2.925 cm

    # Bottom sandwich surfaces (from elem_front going +y)
    bot_guide_top  = openmc.YPlane(y0=-ELEM_Y/2 + CTRL_AL_PLATE_THICK)
    bot_hf_bot     = openmc.YPlane(y0=-ELEM_Y/2 + ABSORBER_GAP)
    bot_hf_top     = openmc.YPlane(y0=-ELEM_Y/2 + ABSORBER_GAP + ABSORBER_THICK)
    bot_slider_bot = openmc.YPlane(y0=y_fuel_start - CTRL_AL_PLATE_THICK)
    bot_slider_top = openmc.YPlane(y0=y_fuel_start)

    # Top sandwich surfaces (from y_fuel_end going +y to elem_back)
    top_slider_bot = openmc.YPlane(y0=y_fuel_end)
    top_slider_top = openmc.YPlane(y0=y_fuel_end + CTRL_AL_PLATE_THICK)
    top_hf_bot     = openmc.YPlane(y0=y_fuel_end + CTRL_AL_PLATE_THICK + CTRL_OUTER_WATER)
    top_hf_top     = openmc.YPlane(y0=y_fuel_end + CTRL_AL_PLATE_THICK + CTRL_OUTER_WATER
                                                  + ABSORBER_THICK)
    top_guide_bot  = openmc.YPlane(y0=y_fuel_end + CTRL_AL_PLATE_THICK + CTRL_OUTER_WATER
                                                  + ABSORBER_THICK + CTRL_INNER_WATER)

    # Hf slot x/y footprints (unbounded in z — blade cells own their z-range)
    hf_slot_b = +bot_hf_bot & -bot_hf_top & +side_inner_left & -side_inner_right
    hf_slot_t = +top_hf_bot & -top_hf_top & +side_inner_left & -side_inner_right

    # ── Bottom sandwich structural cells (active zone only) ─────────────────

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_guide_bottom', fill=aluminum,
        region=(+elem_front & -bot_guide_top &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_inner_water_bottom', fill=water,
        region=(+bot_guide_top & -bot_hf_bot &
                +side_inner_left & -side_inner_right & active_z)))

    # (Hf slot cells are handled separately below — not bounded to active_z)

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_outer_water_bottom', fill=water,
        region=(+bot_hf_top & -bot_slider_bot &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slider_bottom', fill=aluminum,
        region=(+bot_slider_bot & -bot_slider_top &
                +side_inner_left & -side_inner_right & active_z)))

    # ── Top sandwich structural cells (active zone only) ────────────────────

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slider_top', fill=aluminum,
        region=(+top_slider_bot & -top_slider_top &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_outer_water_top', fill=water,
        region=(+top_slider_top & -top_hf_bot &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_inner_water_top', fill=water,
        region=(+top_hf_top & -top_guide_bot &
                +side_inner_left & -side_inner_right & active_z)))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_guide_top', fill=aluminum,
        region=(+top_guide_bot & -elem_back &
                +side_inner_left & -side_inner_right & active_z)))

    # ── Fixed-length Hf blade — spans full model height in 3 pieces ─────────
    # Hf:          [z_bot, z_top]   (blade body)
    # Water below: [CORE_BOTTOM, z_bot]
    # Water above: [z_top, CORE_TOP]

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_absorber_bottom', fill=b4c,
        region=hf_slot_b & +blade_z_bot & -blade_z_top))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_absorber_top', fill=b4c,
        region=hf_slot_t & +blade_z_bot & -blade_z_top))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slot_b_water_below', fill=water,
        region=hf_slot_b & +_z_model_bot & -blade_z_bot))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slot_t_water_below', fill=water,
        region=hf_slot_t & +_z_model_bot & -blade_z_bot))

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slot_b_water_above', fill=water,
        region=hf_slot_b & +blade_z_top & -_z_model_top))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_slot_t_water_above', fill=water,
        region=hf_slot_t & +blade_z_top & -_z_model_top))

    # ── 17-plate fuel follower (active zone only) ───────────────────────────

    plate_bot_surfs = []
    plate_top_surfs = []

    for i in range(N_CTRL_FUEL_PLATES):
        plate_bot = y_fuel_start + i * plate_pitch + half_chan
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
        name=f'ctrl{elem_id}_chan_bot_half', fill=water,
        region=(+bot_slider_top & -plate_bot_surfs[0] &
                +side_inner_left & -side_inner_right & active_z)))
    for i in range(N_CTRL_FUEL_PLATES - 1):
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_chan_{i}', fill=water,
            region=(+plate_top_surfs[i] & -plate_bot_surfs[i + 1] &
                    +side_inner_left & -side_inner_right & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_chan_top_half', fill=water,
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
        name=f'ctrl{elem_id}_gap_xleft', fill=water,
        region=(+pitch_left & -elem_left &
                +pitch_front & -pitch_back & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_xright', fill=water,
        region=(+elem_right & -pitch_right &
                +pitch_front & -pitch_back & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_yfront', fill=water,
        region=(+elem_left & -elem_right &
                +pitch_front & -elem_front & active_z)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_yback', fill=water,
        region=(+elem_left & -elem_right &
                +elem_back & -pitch_back & active_z)))

    # ── Axial regions above/below active fuel ───────────────────────────────
    # The Hf slot has its own cells (above). Everything else in the pitch cell
    # becomes homogenized end-box (15 cm) or water (beyond that).
    full_pitch   = +pitch_left & -pitch_right & +pitch_front & -pitch_back
    not_hf_slots = ~hf_slot_b & ~hf_slot_t   # complement of both Hf slot footprints

    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_upper_endbox', fill=end_box_homog,
        region=full_pitch & +_z_fuel_top & -_z_endbox_above & not_hf_slots))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_upper_water', fill=water,
        region=full_pitch & +_z_endbox_above & -_z_model_top & not_hf_slots))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_lower_endbox', fill=end_box_homog,
        region=full_pitch & +_z_endbox_below & -_z_fuel_bot & not_hf_slots))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_lower_water', fill=water,
        region=full_pitch & +_z_model_bot & -_z_endbox_below & not_hf_slots))

    return openmc.Universe(name=f'ctrl_fuel_elem_{elem_id}', cells=cells)


# =============================================================================
# FLUX TRAP
# =============================================================================

def make_flux_trap():
    """
    Flux trap: aluminum block with a central cylindrical water hole (water_flux_trap
    at 316.8 K), matching the MCNP deck which models the hole as a ZCylinder rather
    than the originally-commented square.

    Cylinder: radius FT_HOLE_RADIUS = 2.5 cm, centered at element origin (x=0, y=0).
    The cylinder is axially unbounded within the active zone (active_z clips it).
    Aluminum fills the annular region between the cylinder and the element envelope.
    Inter-element gaps and all axial regions use bulk water (294 K).
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

    # Cylindrical water hole — hot flux trap water at 316.8 K
    cells.append(openmc.Cell(
        name='flux_trap_water_hole',
        fill=water_flux_trap,
        region=-hole_cyl & active_z
    ))
    # Aluminum block: element envelope minus the cylinder, active zone only
    cells.append(openmc.Cell(
        name='flux_trap_aluminum_block',
        fill=aluminum,
        region=(+elem_left & -elem_right & +elem_front & -elem_back & +hole_cyl & active_z)
    ))

    # Inter-element water gaps (bulk water, active zone only)
    cells.append(openmc.Cell(
        name='flux_trap_gap_xleft',
        fill=water,
        region=(+pitch_left & -elem_left & +pitch_front & -pitch_back & active_z)
    ))
    cells.append(openmc.Cell(
        name='flux_trap_gap_xright',
        fill=water,
        region=(+elem_right & -pitch_right & +pitch_front & -pitch_back & active_z)
    ))
    cells.append(openmc.Cell(
        name='flux_trap_gap_yfront',
        fill=water,
        region=(+elem_left & -elem_right & +pitch_front & -elem_front & active_z)
    ))
    cells.append(openmc.Cell(
        name='flux_trap_gap_yback',
        fill=water,
        region=(+elem_left & -elem_right & +elem_back & -pitch_back & active_z)
    ))

    # Axial regions above/below active fuel — full pitch footprint, bulk water
    full_pitch = +pitch_left & -pitch_right & +pitch_front & -pitch_back

    cells.append(openmc.Cell(
        name='flux_trap_upper_endbox',
        fill=end_box_homog,
        region=full_pitch & +_z_fuel_top & -_z_endbox_above
    ))
    cells.append(openmc.Cell(
        name='flux_trap_upper_water',
        fill=water,
        region=full_pitch & +_z_endbox_above & -_z_model_top
    ))
    cells.append(openmc.Cell(
        name='flux_trap_lower_endbox',
        fill=end_box_homog,
        region=full_pitch & +_z_endbox_below & -_z_fuel_bot
    ))
    cells.append(openmc.Cell(
        name='flux_trap_lower_water',
        fill=water,
        region=full_pitch & +_z_model_bot & -_z_endbox_below
    ))

    return openmc.Universe(name='flux_trap_universe', cells=cells)


# =============================================================================
# WATER AND GRAPHITE FILL UNIVERSES
# =============================================================================

# Water universe: fully unbounded — bulk water fills whatever space the parent
# lattice boundary provides (used for the outer ring and top/bottom water rows).
water_cell = openmc.Cell(name='water_fill', fill=water)
water_univ = openmc.Universe(name='water_universe', cells=[water_cell])

# Graphite reflector universe: bounded axially to match the fuel element pattern.
# Graphite occupies only the active fuel z-range [-30, +30]; above and below it
# mirrors the fuel element end-box + water stack so the reflector height matches
# the core height without contributing graphite outside the active zone.
graphite_univ = openmc.Universe(
    name='graphite_universe',
    cells=[
        openmc.Cell(
            name='graphite_active',
            fill=graphite,
            region=+_z_fuel_bot & -_z_fuel_top,              # −30 → +30 cm
        ),
        openmc.Cell(
            name='graphite_upper_endbox',
            fill=end_box_homog,
            region=+_z_fuel_top & -_z_endbox_above,           # +30 → +45 cm
        ),
        openmc.Cell(
            name='graphite_upper_water',
            fill=water,
            region=+_z_endbox_above & -_z_model_top,          # +45 → +95 cm
        ),
        openmc.Cell(
            name='graphite_lower_endbox',
            fill=end_box_homog,
            region=+_z_endbox_below & -_z_fuel_bot,           # −45 → −30 cm
        ),
        openmc.Cell(
            name='graphite_lower_water',
            fill=water,
            region=+_z_model_bot & -_z_endbox_below,          # −65 → −45 cm
        ),
    ],
)


# =============================================================================
# CORE LATTICE — TECDOC-643 Fig. 2.1 (LEU panel)
# =============================================================================

std_elems  = [make_standard_fuel_element(i) for i in range(23)]
ctrl_elems = [make_control_fuel_element(100 + i, withdrawn_fraction=0.0)
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


# =============================================================================
# CORE BOUNDING REGION
# Vacuum boundaries at CORE_BOTTOM=-65 and CORE_TOP=+95 to accommodate
# the full axial model stack (water/end-box/fuel/end-box/water) plus the
# control blade travel range (blade top reaches +90 at f=1).
# =============================================================================

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
core_cell = openmc.Cell(name='core_cell', fill=core_lattice, region=core_region)


# =============================================================================
# ROOT UNIVERSE AND GEOMETRY EXPORT
# =============================================================================

root_universe = openmc.Universe(name='root', cells=[core_cell])
geometry      = openmc.Geometry(root_universe)


if __name__ == '__main__':
    geometry.export_to_xml()
    print("geometry.xml written successfully.\n")
    print(f"Lattice pitch:        {PITCH_X} x {PITCH_Y} cm")
    print(f"Element envelope:     {ELEM_X} x {ELEM_Y} x {ELEM_Z} cm")
    print(f"Active fuel z:        [{-HALF_Z}, {+HALF_Z}] cm")
    print(f"End-box above:        [{+HALF_Z}, {ENDBOX_ABOVE_TOP}] cm")
    print(f"End-box below:        [{ENDBOX_BELOW_BOT}, {-HALF_Z}] cm")
    print(f"Core z-bounds:        [{CORE_BOTTOM}, {CORE_TOP}] cm (vacuum)")
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
    sandwich_v   = GUIDE_REGION
    fuel_h_v     = ELEM_Y - 2.0 * sandwich_v
    plate_pitch_v = fuel_h_v / N_CTRL_FUEL_PLATES
    y_fs_v = -ELEM_Y / 2.0 + sandwich_v
    y_fe_v =  ELEM_Y / 2.0 - sandwich_v
    layer_sum = (CTRL_AL_PLATE_THICK + CTRL_INNER_WATER + ABSORBER_THICK
                 + CTRL_OUTER_WATER + CTRL_AL_PLATE_THICK)
    print(f"  Sandwich per end: {sandwich_v:.6f} cm")
    print(f"  Fuel region:      [{y_fs_v:.6f}, {y_fe_v:.6f}] cm ({fuel_h_v:.6f} cm)")
    print(f"  Plate pitch:      {plate_pitch_v:.8f} cm")
    print(f"  Layer sum:        {layer_sum:.6f} cm (should be {GUIDE_REGION})")

    assert abs(layer_sum - GUIDE_REGION) < 1e-12, "guide-region layers do not sum"
    assert abs(plate_pitch_v * N_CTRL_FUEL_PLATES - fuel_h_v) < 1e-12, \
        "plate_pitch * N_plates != fuel_height"

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
    print("\nOverlap check passed: no cell overlaps detected.")
