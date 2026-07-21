# ~/iaea-tecdoc643-openmc/model/check_u235_mass.py
# Standalone — does NOT modify the five production files.
# U-235 grams per STANDARD and per CONTROL fuel element via OpenMC get_mass(),
# using analytic meat volumes reconstructed from geometry.py constants.

import materials
import geometry as g

fuel = materials.fuel
ACTIVE_H = 60.0   # meat z-extent, cm (meat_zbot=-30 .. meat_ztop=+30)

def u235_mass(volume_cm3):
    """Clone the shared fuel object so its .volume stays clean, return g U-235."""
    m = fuel.clone()
    m.volume = volume_cm3
    return m.get_mass(nuclide='U235')

# ------------------------------------------------------------------
# STANDARD element: 23 plates, outer(0,22) + inner(1..21)
#   meat thickness_y = plate_thick - 2*clad   (lines 254-255)
# ------------------------------------------------------------------
print("=== STANDARD element (23 plates) ===")
std_plate_thicks = (
    [g.PLATE_THICK_OUTER]
    + [g.PLATE_THICK_INNER] * (g.N_PLATES_STD - 2)
    + [g.PLATE_THICK_OUTER]
)
v_std = 0.0
for i, pt in enumerate(std_plate_thicks):
    is_outer = (i == 0 or i == g.N_PLATES_STD - 1)
    clad = g.CLAD_THICK_OUTER if is_outer else g.CLAD_THICK_INNER
    meat_h = pt - 2 * clad
    v_plate = g.MEAT_WIDTH * meat_h * ACTIVE_H
    v_std += v_plate
    if i < 2 or i == g.N_PLATES_STD - 1:   # show first two + last to spot-check
        tag = "outer" if is_outer else "inner"
        print(f"  plate {i:2d} ({tag}): meat_h={meat_h:.5f}  v={v_plate:.5f} cm^3")
print(f"  meat volume, one std element = {v_std:.5f} cm^3  [DERIVED]")
print(f"  U-235 per std element       = {u235_mass(v_std):.4f} g  [DERIVED]\n")

# ------------------------------------------------------------------
# CONTROL follower: 17 plates, ALL inner-clad (no outer special case)
#   meat thickness_y = PLATE_THICK_INNER - 2*CLAD_THICK_INNER  (lines 215,222-223)
# ------------------------------------------------------------------
print("=== CONTROL follower (17 plates) ===")
ctrl_meat_h = g.PLATE_THICK_INNER - 2 * g.CLAD_THICK_INNER
v_ctrl_plate = g.MEAT_WIDTH * ctrl_meat_h * ACTIVE_H
v_ctrl = v_ctrl_plate * g.N_PLATES_CTRL
print(f"  per-plate: {g.MEAT_WIDTH} x {ctrl_meat_h:.5f} x {ACTIVE_H} = {v_ctrl_plate:.5f} cm^3")
print(f"  meat volume, one ctrl follower = {v_ctrl:.5f} cm^3  [DERIVED]")
print(f"  U-235 per ctrl follower        = {u235_mass(v_ctrl):.4f} g  [DERIVED]\n")

# ------------------------------------------------------------------
print(f"density input provenance UNVERIFIED against deck — do not tag [DECK]")
print(f"control follower shares the SAME fuel material as standard elements,")
print(f"so the per-plate U-235 areal loading is identical; only plate count differs.")