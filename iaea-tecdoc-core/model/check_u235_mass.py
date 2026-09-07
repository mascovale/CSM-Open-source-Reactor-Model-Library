# ~/iaea-tecdoc643-openmc/model/check_u235_mass.py
#
# FISSILE INVENTORY CHECK — the only validation in this repository that does
# NOT route through the cross-validation spreadsheet.
#
# Why that matters. Every [MCNP] and [TECDOC] tag in this codebase is checked
# against model_cross_validation.xlsx, which is not under version control (Phase
# 1 audit, finding #4). This script is the exception: it compares the model
# against a PUBLISHED DOCUMENT.
#
#   * The U-235 atom density (2.251800E-03) is already MATCH between OpenMC and
#     the reference MCNP model, so the material side is independently confirmed.
#     TECDOC-643 is a third, independent source.
#   * ASSERT 1 therefore validates the GEOMETRY — meat volume, plate counts,
#     plate and clad thicknesses — against a published document.
#   * ASSERTS 2 and 3 validate the fuel COMPOSITION against the same document.
#
# This is the direct answer to Phase 1 audit Section I, question 2 ("what is the
# reference model, exactly, and can I see it?").
#
# EXITS NON-ZERO on any failure. It printed and exited 0 unconditionally until
# 2026-08-03, which made it a calculator rather than a check.
#
# WHAT FEEDS WHAT — so a failure is diagnosable rather than just red:
#   assert 1 (mass)        geometry: MEAT_WIDTH, MEAT_HEIGHT, PLATE_THICK_INNER,
#                          PLATE_THICK_OUTER, CLAD_THICK_INNER, CLAD_THICK_OUTER,
#                          N_PLATES_STD   +   material: U-235 atom density
#   assert 2 (U density)   material only: U-235 and U-238 atom densities
#   assert 3 (enrichment)  material only: same two atom densities
# A failure of 1 alone points at geometry. A failure of 2 or 3 points at
# materials.py and should take assert 1 down with it.

import sys

import materials
import geometry as g
from openmc.data import atomic_mass, AVOGADRO
from settings import format_provenance

fuel = materials.fuel
# Meat z-extent comes from geometry.MEAT_HEIGHT (60.0 cm, meat planes at
# -30/+30). It was a local ACTIVE_H = 60.0 literal until 2026-07-31 — a
# duplication of a geometry constant in a file that already imports geometry.

# =============================================================================
# REFERENCE VALUES — TECDOC-643 Appendix A-2, Table 1, "IAEA Generic 10 MW
# Reactor and Fuel Element Design Descriptions with HEU and LEU Fuels".
#
# ALL FROM THE **LEU (U3Si2-Al)** COLUMN. This matters: the HEU column of the
# same table gives 280 g / 207 g per element and 0.68 g/cm3 uranium density.
# Reading the wrong column produces a failure that looks like a geometry error —
# a wrong MEAT_WIDTH or a wrong plate count — and would be debugged in entirely
# the wrong place.
# =============================================================================

TECDOC_U235_STD    = 390.0    # g U-235 per standard element   [TECDOC A-2 Table 1]
TECDOC_U235_CTRL   = 288.0    # g U-235 per control follower   [TECDOC A-2 Table 1]
TECDOC_U_DENSITY   = 4.45     # g/cm3 uranium in the meat      [TECDOC A-2 Table 1]
TECDOC_ENRICHMENT  = 19.75    # w/o U-235                      [TECDOC A-2 Table 1]

# Tolerances track the REFERENCE's precision, not the model's. A tolerance
# tighter than the source's own significant figures fails on rounding; one much
# looser stops catching real errors.
TOL_MASS       = 0.5      # g — Table 1 is quoted to the nearest gram (the HEU
                          # column gives 207 g for its control element, so the
                          # figures are not rounded to tens). Half-ULP = 0.5 g.
TOL_U_DENSITY  = 0.005    # g/cm3 — half-ULP at 3 s.f. (4.45)
TOL_ENRICHMENT = 0.005    # w/o   — half-ULP at 4 s.f. (19.75)


def u235_mass(volume_cm3):
    """Clone the shared fuel object so its .volume stays clean, return g U-235."""
    m = fuel.clone()
    m.volume = volume_cm3
    return m.get_mass(nuclide='U235')


def report(label, computed, reference, tol, unit):
    """Print a check line with the fraction of tolerance budget consumed."""
    delta = computed - reference
    print(f"  {label:<34} {computed:10.4f} vs {reference:8.4f} {unit:<6} "
          f"delta {delta:+8.4f}  ({abs(delta) / tol * 100:5.1f}% of +/-{tol} budget)")


print("Run provenance:")
print(format_provenance())
print()

# ------------------------------------------------------------------
# STANDARD element: 23 plates, outer(0,22) + inner(1..21)
#   meat thickness_y = plate_thick - 2*clad
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
    v_plate = g.MEAT_WIDTH * meat_h * g.MEAT_HEIGHT
    v_std += v_plate
    if i < 2 or i == g.N_PLATES_STD - 1:   # show first two + last to spot-check
        tag = "outer" if is_outer else "inner"
        print(f"  plate {i:2d} ({tag}): meat_h={meat_h:.5f}  v={v_plate:.5f} cm^3")
m_std = u235_mass(v_std)
print(f"  meat volume, one std element = {v_std:.5f} cm^3  [DERIVED]")
print(f"  U-235 per std element       = {m_std:.4f} g  [DERIVED]\n")

# ------------------------------------------------------------------
# CONTROL follower: 17 plates, ALL inner-clad (no outer special case)
# ------------------------------------------------------------------
print("=== CONTROL follower (17 plates) ===")
ctrl_meat_h = g.PLATE_THICK_INNER - 2 * g.CLAD_THICK_INNER
v_ctrl_plate = g.MEAT_WIDTH * ctrl_meat_h * g.MEAT_HEIGHT
v_ctrl = v_ctrl_plate * g.N_PLATES_CTRL
m_ctrl = u235_mass(v_ctrl)
print(f"  per-plate: {g.MEAT_WIDTH} x {ctrl_meat_h:.5f} x {g.MEAT_HEIGHT} "
      f"= {v_ctrl_plate:.5f} cm^3")
print(f"  meat volume, one ctrl follower = {v_ctrl:.5f} cm^3  [DERIVED]")
print(f"  U-235 per ctrl follower        = {m_ctrl:.4f} g  [DERIVED]\n")

# ------------------------------------------------------------------
# Fuel composition, computed from the material's own atom densities.
# ------------------------------------------------------------------
ad = fuel.get_nuclide_atom_densities()
u_mass_density = {n: ad[n] * 1e24 * atomic_mass(n) / AVOGADRO
                  for n in ('U235', 'U238')}
u_density_total = sum(u_mass_density.values())
enrichment = 100.0 * u_mass_density['U235'] / u_density_total

# ==================================================================
# CHECKS — against TECDOC-643 A-2 Table 1, LEU column
# ==================================================================
print("=== CHECKS vs TECDOC-643 A-2 Table 1 (LEU / U3Si2-Al column) ===")

report("1. U-235 per standard element", m_std, TECDOC_U235_STD, TOL_MASS, "g")
report("2. uranium density in meat", u_density_total, TECDOC_U_DENSITY,
       TOL_U_DENSITY, "g/cm3")
report("3. enrichment", enrichment, TECDOC_ENRICHMENT, TOL_ENRICHMENT, "w/o")

assert abs(m_std - TECDOC_U235_STD) < TOL_MASS, (
    f"U-235 per standard element is {m_std:.4f} g, outside "
    f"{TECDOC_U235_STD} +/- {TOL_MASS} g [TECDOC A-2 Table 1, LEU column]. "
    f"This assert covers GEOMETRY (meat volume, plate counts, plate and clad "
    f"thicknesses) as well as the U-235 atom density — check asserts 2 and 3 "
    f"first: if they pass, the fault is geometric.")

assert abs(u_density_total - TECDOC_U_DENSITY) < TOL_U_DENSITY, (
    f"uranium density is {u_density_total:.4f} g/cm3, outside "
    f"{TECDOC_U_DENSITY} +/- {TOL_U_DENSITY} [TECDOC A-2 Table 1, LEU column]. "
    f"Depends only on the U-235/U-238 atom densities in materials.py.")

assert abs(enrichment - TECDOC_ENRICHMENT) < TOL_ENRICHMENT, (
    f"enrichment is {enrichment:.4f} w/o, outside {TECDOC_ENRICHMENT} +/- "
    f"{TOL_ENRICHMENT} [TECDOC A-2 Table 1, LEU column]. Depends only on the "
    f"U-235/U-238 atom densities in materials.py.")

# ------------------------------------------------------------------
# The control follower is NOT a fourth assert.
#
# Both element types use the SAME fuel material at the same per-plate areal
# loading, so m_ctrl/m_std is exactly N_CTRL_FUEL_PLATES/N_PLATES_STD = 17/23 by
# construction. Asserting 288 g separately would re-test assert 1 with a
# different constant and double-count it as independent evidence. What IS worth
# checking is that the construction holds — that the two element types really do
# share a material and differ only in plate count:
# ------------------------------------------------------------------
ratio_computed = m_ctrl / m_std
ratio_expected = g.N_PLATES_CTRL / g.N_PLATES_STD
print(f"\n  control/standard mass ratio  {ratio_computed:.9f} vs "
      f"{g.N_PLATES_CTRL}/{g.N_PLATES_STD} = {ratio_expected:.9f}")
assert abs(ratio_computed - ratio_expected) < 1e-9, (
    f"control/standard U-235 ratio is {ratio_computed:.9f}, not the "
    f"{g.N_PLATES_CTRL}/{g.N_PLATES_STD} = {ratio_expected:.9f} the shared fuel "
    f"material requires — the two element types no longer differ by plate count "
    f"alone.")

# TECDOC's OWN two figures are not in exact 23:17 ratio: 390 x 17/23 = 288.26,
# and the table quotes 288. They are independently rounded to the nearest gram.
# The MODEL's ratio is exact. Do NOT "correct" either side to make them agree —
# the discrepancy is rounding in the source, not an error in the model.
_tecdoc_implied_ctrl = TECDOC_U235_STD * g.N_PLATES_CTRL / g.N_PLATES_STD
print(f"  (TECDOC quotes {TECDOC_U235_CTRL:.0f} g for the control element; "
      f"{TECDOC_U235_STD:.0f} x {g.N_PLATES_CTRL}/{g.N_PLATES_STD} = "
      f"{_tecdoc_implied_ctrl:.2f}.")
print(f"   Both TECDOC figures are rounded to the nearest gram independently; "
      f"the model's ratio is exact. Neither side is wrong.)")

print("\nALL CHECKS PASSED — model agrees with TECDOC-643 A-2 Table 1 (LEU) on")
print("fissile inventory, uranium density and enrichment.")
sys.exit(0)
