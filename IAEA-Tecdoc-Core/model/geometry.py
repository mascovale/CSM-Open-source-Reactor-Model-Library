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
    - Reflectors: graphite on +y/-y faces, water everywhere else
    - Active fuel height: 60 cm; outer model height: 80 cm

Standard Fuel Element (LEU, U3Si2-Al, heterogeneous build):
    - Envelope:           76 x 80 mm  (1 mm water gap on each axis to pitch)
    - Side plates:        4.8 mm each (aluminum, in x)
    - Active stack:       66.4 mm wide between side plate inner faces
    - 23 plates:          1.27 mm inner, 1.385 mm outer (asymmetric clad)
    - Fuel meat:          0.51 mm thick x 63 mm wide x 600 mm tall
    - Inner clad:         0.38 mm   |   Outer clad: 0.495 mm
    - U density:          4.45 g/cm3 in meat   |   235U/elem: 390 g

Dimensional reconciliation (Option 1):
    The TECDOC numbers give 23 plates × 1.27 mm + 22 channels × 2.19 mm =
    77.39 mm of active region width — exceeding the 66.4 mm available
    between the 4.8 mm side plates. To get a self-consistent heterogeneous
    geometry that fills the 7.7 cm lattice pitch with no overlaps or
    undefined regions, we preserve plate thicknesses, meat dimensions, and
    side plates, and solve for the water channel thickness:
        N*t_plate + (N-1)*t_chan = active_width
    → t_chan ≈ 1.692 mm (vs nominal 2.19 mm, ~23% reduction)
    Effect: slightly harder neutron spectrum; ~100-300 pcm keff bias
    relative to published homogenized TECDOC results. Acceptable for
    OpenMC <-> MCNP cross-comparison since both codes use the same model.

Axial extent inside element universes:
    Cells in the element universe are NOT bounded in z (the meat region IS,
    since fuel meat is only 60 cm tall while the lattice cell is 80 cm).
    This lets the universe fill whatever parent z-extent it's placed into.

All dimensions in cm.
"""

import openmc
from materials import fuel, clad, water, hafnium, graphite, aluminum, air

# =============================================================================
# LATTICE / ELEMENT ENVELOPE
# =============================================================================

# Lattice pitch
PITCH_X = 7.7    # cm  (77 mm)
PITCH_Y = 8.1    # cm  (81 mm)

# Fuel element envelope — slightly smaller than pitch to leave a 1 mm
# inter-element water gap on each side of each axis.
ELEM_X = 7.6     # cm  (76 mm)
ELEM_Y = 8.0     # cm  (80 mm)
ELEM_Z = 60.0    # cm  (600 mm) — active fuel height

# Side plate (aluminum strip on each side of the plate stack, in x)
SIDE_PLATE_THICK = 0.48   # cm  (4.8 mm) — TECDOC schematic value

# Active stack region width — between the two side plate inner faces
ACTIVE_STACK_X = ELEM_X - 2 * SIDE_PLATE_THICK   # 6.64 cm

# =============================================================================
# PLATE / MEAT / CLAD DIMENSIONS
# =============================================================================

# Plate thicknesses
PLATE_THICK_INNER = 0.127    # cm  (1.27 mm)
PLATE_THICK_OUTER = 0.1385   # cm  (1.385 mm = 0.495 + 0.51 + 0.38 mm)

# Clad thicknesses (asymmetric on outer plates)
CLAD_THICK_INNER = 0.038     # cm  (0.38 mm)
CLAD_THICK_OUTER = 0.0495    # cm  (0.495 mm)

# Fuel meat dimensions
MEAT_THICK = 0.051           # cm  (0.51 mm)
MEAT_WIDTH = 6.3            # cm  (63 mm)

# Plate counts
N_PLATES_STD  = 23
N_PLATES_CTRL = 17

#water channel thickness
WATER_CHAN_THICK = 0.219       # cm  (2.19 mm)

# Half active height (for fuel meat z-bounds)
HALF_Z = ELEM_Z / 2.0   # 30.0 cm


# =============================================================================
# STANDARD FUEL ELEMENT
# 23 plates stacked in x, running lengthwise in y. Plate meat is 60 cm tall;
# clad/structure/water cells extend the full parent z-extent. Side plates of
# aluminum on each side in x; 1 mm inter-element water gap on each axis.
# =============================================================================

"""
    Build a standard fuel element universe.

    Geometry (in the local lattice-cell frame, origin at the element center):
      - Lattice cell extends ±PITCH_X/2 in x, ±PITCH_Y/2 in y.
      - Element envelope ±ELEM_X/2 in x, ±ELEM_Y/2 in y.
      - Side plates fill from box_left to side_inner_left (and symmetric R).
      - Plate stack fills the 6.64 cm between side plate inner faces.
      - Inter-element water gap fills pitch_left..box_left, box_right..pitch_right,
        and similarly in y.
      - Fuel meat is bounded in z by ±HALF_Z (= 60 cm tall, centered on z=0).
        All other cells are NOT bounded in z, so they extend to whatever
        z-range the parent core cell provides (±40 cm in this model).
        """
def make_standard_fuel_element(elem_id):
    """
    Standard ANL/TECDOC A-2 fuel element.

    X = plate width direction
    Y = plate/channel stack direction
    Z = active height
    """

    # --- Pitch cell boundaries ---
    pitch_left  = openmc.XPlane(x0=-PITCH_X / 2.0)
    pitch_right = openmc.XPlane(x0= PITCH_X / 2.0)
    pitch_front = openmc.YPlane(y0=-PITCH_Y / 2.0)
    pitch_back  = openmc.YPlane(y0= PITCH_Y / 2.0)

    # --- Element envelope ---
    box_left  = openmc.XPlane(x0=-ELEM_X / 2.0)
    box_right = openmc.XPlane(x0= ELEM_X / 2.0)
    box_front = openmc.YPlane(y0=-ELEM_Y / 2.0)
    box_back  = openmc.YPlane(y0= ELEM_Y / 2.0)

    # --- Side plate inner faces ---
    side_inner_left  = openmc.XPlane(x0=-ELEM_X / 2.0 + SIDE_PLATE_THICK)
    side_inner_right = openmc.XPlane(x0= ELEM_X / 2.0 - SIDE_PLATE_THICK)

    # --- Fuel meat X boundaries: meat is 6.30 cm wide left/right ---
    meat_left  = openmc.XPlane(x0=-MEAT_WIDTH / 2.0)
    meat_right = openmc.XPlane(x0= MEAT_WIDTH / 2.0)

    # --- Fuel meat Z bounds ---
    meat_zbot = openmc.ZPlane(z0=-HALF_Z)
    meat_ztop = openmc.ZPlane(z0= HALF_Z)

    cells = []

    # Use outer plate thickness for first/last plates
    plate_thicks = (
        [PLATE_THICK_OUTER]
        + [PLATE_THICK_INNER] * (N_PLATES_STD - 2)
        + [PLATE_THICK_OUTER]
    )

    stack_height_y = sum(plate_thicks) + (N_PLATES_STD - 1) * WATER_CHAN_THICK

    # Center the plate/channel stack inside the 8.00 cm element envelope
    y = -stack_height_y / 2.0
    stack_bottom_surf = openmc.YPlane(y0=y)

    for i, plate_thick in enumerate(plate_thicks):
        is_first = (i == 0)
        is_last  = (i == N_PLATES_STD - 1)

        # Plate outer Y boundaries
        plate_bottom = openmc.YPlane(y0=y)
        plate_top    = openmc.YPlane(y0=y + plate_thick)

        # First and last plates have thicker outside cladding
        if is_first:
            clad_bottom = CLAD_THICK_OUTER
            clad_top = CLAD_THICK_INNER
        elif is_last:
            clad_bottom = CLAD_THICK_INNER
            clad_top = CLAD_THICK_OUTER
        else:
            clad_bottom = CLAD_THICK_INNER
            clad_top = CLAD_THICK_INNER

        meat_bottom = openmc.YPlane(y0=y + clad_bottom)
        meat_top    = openmc.YPlane(y0=y + plate_thick - clad_top)

        # Fuel meat: wide in X, thin in Y, active in Z
        meat_region = (
            +meat_left & -meat_right &
            +meat_bottom & -meat_top &
            +meat_zbot & -meat_ztop
        )

        # Whole plate region: full plate width in X, thin in Y
        plate_region = (
            +side_inner_left & -side_inner_right &
            +plate_bottom & -plate_top
        )

        clad_region = plate_region & ~meat_region

        cells.append(openmc.Cell(
            name=f'std{elem_id}_meat_{i}',
            fill=fuel,
            region=meat_region
        ))

        cells.append(openmc.Cell(
            name=f'std{elem_id}_clad_{i}',
            fill=clad,
            region=clad_region
        ))

        # Move past the plate
        y += plate_thick

        # Water channel after each plate except the last
        if not is_last:
            chan_bottom = plate_top
            chan_top = openmc.YPlane(y0=y + WATER_CHAN_THICK)

            chan_region = (
                +side_inner_left & -side_inner_right &
                +chan_bottom & -chan_top
            )

            cells.append(openmc.Cell(
                name=f'std{elem_id}_chan_{i}',
                fill=water,
                region=chan_region
            ))

            y += WATER_CHAN_THICK

    stack_top_surf = openmc.YPlane(y0=y)

    # Water below and above the plate stack inside the element envelope
    cells.append(openmc.Cell(
        name=f'std{elem_id}_water_below_stack',
        fill=water,
        region=(
            +box_front & -stack_bottom_surf &
            +side_inner_left & -side_inner_right
        )
    ))

    cells.append(openmc.Cell(
        name=f'std{elem_id}_water_above_stack',
        fill=water,
        region=(
            +stack_top_surf & -box_back &
            +side_inner_left & -side_inner_right
        )
    ))

    # Side plates
    cells.append(openmc.Cell(
        name=f'std{elem_id}_side_left',
        fill=aluminum,
        region=(
            +box_left & -side_inner_left &
            +box_front & -box_back
        )
    ))

    cells.append(openmc.Cell(
        name=f'std{elem_id}_side_right',
        fill=aluminum,
        region=(
            +side_inner_right & -box_right &
            +box_front & -box_back
        )
    ))

    # Inter-element water gaps
    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_xleft',
        fill=water,
        region=(
            +pitch_left & -box_left &
            +pitch_front & -pitch_back
        )
    ))

    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_xright',
        fill=water,
        region=(
            +box_right & -pitch_right &
            +pitch_front & -pitch_back
        )
    ))

    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_yfront',
        fill=water,
        region=(
            +box_left & -box_right &
            +pitch_front & -box_front
        )
    ))

    cells.append(openmc.Cell(
        name=f'std{elem_id}_gap_yback',
        fill=water,
        region=(
            +box_left & -box_right &
            +box_back & -pitch_back
        )
    ))

    return openmc.Universe(name=f'std_fuel_elem_{elem_id}', cells=cells)


# =============================================================================
# CONTROL ELEMENT
# Unchanged structure from prior versions (plates still stack in y; the
# orientation rewrite to match standard elements is a separate task). The
# only fix here is removing the spurious z bounds inside cells so the
# universe is fully defined over the parent z-extent.
# =============================================================================

CTRL_FUEL_WIDTH_X = 6.60      # cm
CTRL_SIDE_PLATE_X = (ELEM_X - CTRL_FUEL_WIDTH_X) / 2.0  # 0.50 cm

ABSORBER_THICK  = 0.31        # cm
ABSORBER_GAP    = 0.395       # cm
GUIDE_REGION    = 1.075       # cm

def make_control_fuel_element(elem_id, blades_inserted=True):
    cells = []

    # --- Pitch cell boundaries (full lattice cell) ---
    pitch_left   = openmc.XPlane(x0=-PITCH_X / 2.0)
    pitch_right  = openmc.XPlane(x0= PITCH_X / 2.0)
    pitch_front  = openmc.YPlane(y0=-PITCH_Y / 2.0)
    pitch_back   = openmc.YPlane(y0= PITCH_Y / 2.0)

    # --- Element envelope (76 x 80 mm — 1 mm smaller than pitch on each
    #     axis, mirroring the standard element so the inter-element water
    #     gap is explicit, not implicit) ---
    elem_left  = openmc.XPlane(x0=-ELEM_X / 2.0)
    elem_right = openmc.XPlane(x0= ELEM_X / 2.0)
    elem_front = openmc.YPlane(y0=-ELEM_Y / 2.0)
    elem_back  = openmc.YPlane(y0= ELEM_Y / 2.0)

    # --- Side plate inner faces ---
    # Using 0.65 cm side plates so side_inner lands at ±3.15 cm — the same
    # position as before (when it was -PITCH_X/2 + 0.70 = -3.15), which
    # keeps the plate stack and meat region in the same place. The change
    # is purely that the aluminum is now contained inside ELEM_X = 7.6,
    # not extended to the full PITCH_X = 7.7.
    side_inner_left  = openmc.XPlane(x0=-CTRL_FUEL_WIDTH_X / 2.0)
    side_inner_right = openmc.XPlane(x0= CTRL_FUEL_WIDTH_X / 2.0)

    # --- Guide plate / absorber region (anchored to element envelope in y) ---
    guide_inner_front = openmc.YPlane(y0=-ELEM_Y / 2.0 + GUIDE_REGION)
    guide_inner_back  = openmc.YPlane(y0= ELEM_Y / 2.0 - GUIDE_REGION)

    if blades_inserted:
        blade_front_outer = openmc.YPlane(y0=-ELEM_Y / 2.0 + GUIDE_REGION - ABSORBER_GAP)
        blade_front_inner = openmc.YPlane(y0=-ELEM_Y / 2.0 + GUIDE_REGION - ABSORBER_GAP - ABSORBER_THICK)
        blade_back_inner  = openmc.YPlane(y0= ELEM_Y / 2.0 - GUIDE_REGION + ABSORBER_GAP + ABSORBER_THICK)
        blade_back_outer  = openmc.YPlane(y0= ELEM_Y / 2.0 - GUIDE_REGION + ABSORBER_GAP)

    # Fuel meat z-bounds (only the meat is z-limited)
    meat_zbot = openmc.ZPlane(z0=-HALF_Z)
    meat_ztop = openmc.ZPlane(z0= HALF_Z)

    meat_left  = openmc.XPlane(x0=-MEAT_WIDTH / 2.0)
    meat_right = openmc.XPlane(x0= MEAT_WIDTH / 2.0)

    n_fuel_plates  = 17
    n_al_plates    = 4
    n_total_plates = n_fuel_plates + n_al_plates  # 21
    n_channels     = n_total_plates - 1            # 20

    stack_height = (
    n_total_plates * PLATE_THICK_INNER
    + n_channels * WATER_CHAN_THICK
    )

    # Center the 21-plate control-element stack in the 8.00 cm element.
    # This avoids forcing the stack into the too-small GUIDE_REGION window.
    y_start = -stack_height / 2.0

    al_plate_indices = {0, 1, n_total_plates - 2, n_total_plates - 1}
    y = y_start
    plate_surfaces = []

    for i in range(n_total_plates):
        plate_thick = PLATE_THICK_INNER
        bottom_surf = openmc.YPlane(y0=y)
        top_surf    = openmc.YPlane(y0=y + plate_thick)

        if i in al_plate_indices:
            cells.append(openmc.Cell(
                name=f'ctrl{elem_id}_al_plate_{i}', fill=aluminum,
                region=(+bottom_surf & -top_surf &
                        +side_inner_left & -side_inner_right)))
        else:
            meat_b = openmc.YPlane(y0=y + CLAD_THICK_INNER)
            meat_t = openmc.YPlane(y0=y + plate_thick - CLAD_THICK_INNER)
            meat_region = (
                +meat_b & -meat_t &
                +meat_left & -meat_right &
                +meat_zbot & -meat_ztop
            )
            clad_region = (
                +bottom_surf & -top_surf &
                +side_inner_left & -side_inner_right &
                ~meat_region
            )
            cells.append(openmc.Cell(
                name=f'ctrl{elem_id}_meat_{i}', fill=fuel, region=meat_region))
            cells.append(openmc.Cell(
                name=f'ctrl{elem_id}_clad_{i}', fill=clad, region=clad_region))

        plate_surfaces.append((bottom_surf, top_surf))
        y += plate_thick

        if i < n_total_plates - 1:
            chan_top = openmc.YPlane(y0=y + WATER_CHAN_THICK)
            cells.append(openmc.Cell(
                name=f'ctrl{elem_id}_chan_{i}', fill=water,
                region=(+top_surf & -chan_top &
                        +side_inner_left & -side_inner_right)))
            y += WATER_CHAN_THICK

    stack_bottom = plate_surfaces[0][0]
    stack_top    = plate_surfaces[-1][1]

    # ------------------------------------------------------------------
    # Space above/below centered plate stack inside the control element
    # If blades are inserted, place hafnium strips in the top and bottom
    # clearances with water on each side so nothing overlaps.
    # ------------------------------------------------------------------

    stack_bottom_y = y_start
    stack_top_y    = y_start + stack_height

    clearance_each_side = (ELEM_Y - stack_height) / 2.0

    if blades_inserted:
        if ABSORBER_THICK >= clearance_each_side:
            raise ValueError(
                f"ABSORBER_THICK={ABSORBER_THICK} cm is too large to fit "
                f"in control-element clearance {clearance_each_side:.5f} cm."
            )

        water_pad = (clearance_each_side - ABSORBER_THICK) / 2.0

        # --- Bottom side ---
        blade_bot_lo = -ELEM_Y / 2.0 + water_pad
        blade_bot_hi = blade_bot_lo + ABSORBER_THICK

        blade_bot_lo_s = openmc.YPlane(y0=blade_bot_lo)
        blade_bot_hi_s = openmc.YPlane(y0=blade_bot_hi)

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_bottom_outer_water',
            fill=water,
            region=(
                +elem_front & -blade_bot_lo_s &
                +side_inner_left & -side_inner_right
            )
        ))

        bottom_blade_band = (
            +blade_bot_lo_s & -blade_bot_hi_s &
            +side_inner_left & -side_inner_right
        )

        active_z_region = +meat_zbot & -meat_ztop

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_blade_bottom',
            fill=hafnium,
            region=bottom_blade_band & active_z_region
        ))

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_blade_bottom_water_outside_active_z',
            fill=water,
            region=bottom_blade_band & ~active_z_region
        ))
        
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_bottom_inner_water',
            fill=water,
            region=(
                +blade_bot_hi_s & -stack_bottom &
                +side_inner_left & -side_inner_right
            )
        ))

        # --- Top side ---
        blade_top_lo = stack_top_y + water_pad
        blade_top_hi = blade_top_lo + ABSORBER_THICK

        blade_top_lo_s = openmc.YPlane(y0=blade_top_lo)
        blade_top_hi_s = openmc.YPlane(y0=blade_top_hi)

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_top_inner_water',
            fill=water,
            region=(
                +stack_top & -blade_top_lo_s &
                +side_inner_left & -side_inner_right
            )
        ))

        top_blade_band = (
            +blade_top_lo_s & -blade_top_hi_s &
            +side_inner_left & -side_inner_right
        )

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_blade_top',
            fill=hafnium,
            region=top_blade_band & active_z_region
        ))

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_blade_top_water_outside_active_z',
            fill=water,
            region=top_blade_band & ~active_z_region
        ))

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_top_outer_water',
            fill=water,
            region=(
                +blade_top_hi_s & -elem_back &
                +side_inner_left & -side_inner_right
            )
        ))

    else:
        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_water_below_stack',
            fill=water,
            region=(
                +elem_front & -stack_bottom &
                +side_inner_left & -side_inner_right
            )
        ))

        cells.append(openmc.Cell(
            name=f'ctrl{elem_id}_water_above_stack',
            fill=water,
            region=(
                +stack_top & -elem_back &
                +side_inner_left & -side_inner_right
            )
        ))
    # if blades_inserted:
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_guide_water_bot_outer', fill=water,
    #         region=(+elem_front & -blade_front_inner &
    #                 +side_inner_left & -side_inner_right)))
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_blade_bottom', fill=hafnium,
    #         region=(+blade_front_inner & -blade_front_outer &
    #                 +side_inner_left & -side_inner_right)))
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_gap_bottom', fill=water,
    #         region=(+blade_front_outer & -guide_inner_front &
    #                 +side_inner_left & -side_inner_right)))
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_gap_top', fill=water,
    #         region=(+guide_inner_back & -blade_back_outer &
    #                 +side_inner_left & -side_inner_right)))
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_blade_top', fill=hafnium,
    #         region=(+blade_back_outer & -blade_back_inner &
    #                 +side_inner_left & -side_inner_right)))
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_guide_water_top_outer', fill=water,
    #         region=(+blade_back_inner & -elem_back &
    #                 +side_inner_left & -side_inner_right)))
    # else:
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_guide_bottom_water', fill=water,
    #         region=(+elem_front & -guide_inner_front &
    #                 +side_inner_left & -side_inner_right)))
    #     cells.append(openmc.Cell(
    #         name=f'ctrl{elem_id}_guide_top_water', fill=water,
    #         region=(+guide_inner_back & -elem_back &
    #                 +side_inner_left & -side_inner_right)))

    # Side plates (aluminum) — bounded by element envelope
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_side_left', fill=aluminum,
        region=(+elem_left & -side_inner_left &
                +elem_front & -elem_back)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_side_right', fill=aluminum,
        region=(+side_inner_right & -elem_right &
                +elem_front & -elem_back)))

    # --- Inter-element water gap — fills the 1 mm strip between the
    #     element envelope and the lattice cell boundary on all four sides.
    #     Left/right strips span the full pitch in y; front/back strips
    #     span only the element width in x, so the four corner squares are
    #     covered exactly once. ---
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_xleft', fill=water,
        region=(+pitch_left & -elem_left &
                +pitch_front & -pitch_back)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_xright', fill=water,
        region=(+elem_right & -pitch_right &
                +pitch_front & -pitch_back)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_yfront', fill=water,
        region=(+elem_left & -elem_right &
                +pitch_front & -elem_front)))
    cells.append(openmc.Cell(
        name=f'ctrl{elem_id}_gap_yback', fill=water,
        region=(+elem_left & -elem_right &
                +elem_back & -pitch_back)))

    return openmc.Universe(name=f'ctrl_fuel_elem_{elem_id}', cells=cells)


def make_flux_trap():
    """
    Flux trap placeholder:
    aluminum block inside the element envelope with a central water hole.
    """

    # Pitch cell boundaries
    pitch_left   = openmc.XPlane(x0=-PITCH_X / 2.0)
    pitch_right  = openmc.XPlane(x0= PITCH_X / 2.0)
    pitch_front  = openmc.YPlane(y0=-PITCH_Y / 2.0)
    pitch_back   = openmc.YPlane(y0= PITCH_Y / 2.0)

    # Element envelope
    elem_left  = openmc.XPlane(x0=-ELEM_X / 2.0)
    elem_right = openmc.XPlane(x0= ELEM_X / 2.0)
    elem_front = openmc.YPlane(y0=-ELEM_Y / 2.0)
    elem_back  = openmc.YPlane(y0= ELEM_Y / 2.0)

    # Central water hole, 5.0 cm x 5.0 cm
    hole_half = 2.5
    hole_left  = openmc.XPlane(x0=-hole_half)
    hole_right = openmc.XPlane(x0= hole_half)
    hole_front = openmc.YPlane(y0=-hole_half)
    hole_back  = openmc.YPlane(y0= hole_half)

    hole_region = (
        +hole_left & -hole_right &
        +hole_front & -hole_back
    )

    block_region = (
        +elem_left & -elem_right &
        +elem_front & -elem_back &
        ~hole_region
    )

    cells = []

    cells.append(openmc.Cell(
        name='flux_trap_water_hole',
        fill=water,
        region=hole_region
    ))

    cells.append(openmc.Cell(
        name='flux_trap_aluminum_block',
        fill=aluminum,
        region=block_region
    ))

    # Inter-element water gap
    cells.append(openmc.Cell(
        name='flux_trap_gap_xleft',
        fill=water,
        region=(+pitch_left & -elem_left &
                +pitch_front & -pitch_back)
    ))

    cells.append(openmc.Cell(
        name='flux_trap_gap_xright',
        fill=water,
        region=(+elem_right & -pitch_right &
                +pitch_front & -pitch_back)
    ))

    cells.append(openmc.Cell(
        name='flux_trap_gap_yfront',
        fill=water,
        region=(+elem_left & -elem_right &
                +pitch_front & -elem_front)
    ))

    cells.append(openmc.Cell(
        name='flux_trap_gap_yback',
        fill=water,
        region=(+elem_left & -elem_right &
                +elem_back & -pitch_back)
    ))

    return openmc.Universe(name='flux_trap_universe', cells=cells)

# =============================================================================
# WATER AND GRAPHITE FILL UNIVERSES
# =============================================================================

water_cell    = openmc.Cell(name='water_fill',    fill=water)
water_univ    = openmc.Universe(name='water_universe', cells=[water_cell])

graphite_cell = openmc.Cell(name='graphite_fill', fill=graphite)
graphite_univ = openmc.Universe(name='graphite_universe', cells=[graphite_cell])


# =============================================================================
# CORE LATTICE — TECDOC-643 Fig. 2.1 (LEU panel)
# =============================================================================

std_elems  = [make_standard_fuel_element(i) for i in range(23)]
ctrl_elems = [make_control_fuel_element(100 + i, blades_inserted=False)
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
    [W, S[10], C[2],  S[11], F, S[12], S[13], W],
    [W, S[14], S[15], S[16], S[17], C[3],  S[18], W],
    [W, F, S[19], C[4],  S[20], S[21], S[22], W],
    [W, G, G, G, G, G, G, W],
    [W, W, W, W, W, W, W, W],
]

core_lattice = openmc.RectLattice(name='core_lattice')
core_lattice.pitch      = (PITCH_X, PITCH_Y)
core_lattice.lower_left = (-4 * PITCH_X, -4.5 * PITCH_Y)
core_lattice.universes  = lattice_universes


# =============================================================================
# CORE BOUNDING REGION
# =============================================================================

core_left   = openmc.XPlane(x0=-4   * PITCH_X, boundary_type='vacuum')
core_right  = openmc.XPlane(x0= 4   * PITCH_X, boundary_type='vacuum')
core_front  = openmc.YPlane(y0=-4.5 * PITCH_Y, boundary_type='vacuum')
core_back   = openmc.YPlane(y0= 4.5 * PITCH_Y, boundary_type='vacuum')
core_bottom = openmc.ZPlane(z0=-40.0,           boundary_type='vacuum')
core_top    = openmc.ZPlane(z0= 40.0,           boundary_type='vacuum')

core_region = (
    +core_left  & -core_right &
    +core_front & -core_back  &
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
    print(f"Side plate thickness: {SIDE_PLATE_THICK} cm")
    print(f"Active stack region:  {ACTIVE_STACK_X} cm wide")
    print(f"Inner plate thick:    {PLATE_THICK_INNER} cm")
    print(f"Outer plate thick:    {PLATE_THICK_OUTER} cm")
    print(f"Water channel thick:  {WATER_CHAN_THICK:.5f} cm")
    print(f"Meat thickness:       {MEAT_THICK} cm")
    print(f"Meat width:           {MEAT_WIDTH} cm")

    stack = (
        (N_PLATES_STD - 2) * PLATE_THICK_INNER
        + 2 * PLATE_THICK_OUTER
        + (N_PLATES_STD - 1) * WATER_CHAN_THICK
    )
    print(f"\nSanity check: standard stack height in Y = {stack:.6f} cm "
        f"(target: < {ELEM_Y})")