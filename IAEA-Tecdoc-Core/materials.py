"""
materials.py
------------
Material definitions for the IAEA TECDOC-643 Appendix A-2
Generic 10 MW LEU Research Reactor Core (Argonne design).

Reference:
    IAEA-TECDOC-643, "Research Reactor Core Conversion Guidebook,
    Volume 2: Analysis (Appendices A-F)," IAEA, Vienna, 1992.
    Appendix A-2: Generic 10 MW Reactor — Argonne National Laboratory.

Units:
    All densities in g/cm^3.
    All enrichments in weight percent unless noted.
"""

import openmc

# Natural-carbon (C0, ZAID 6000) vs. explicit C12/C13 isotopic split — the
# deck specifies natural carbon for both B4C and graphite, matching b4c's
# C0 choice below.
USE_NATURAL_CARBON = False

# Al metal thermal scattering S(a,b) (c_Al27). Enabled per the 2026-07-20
# meeting decision ("We will add Al-27 SaB libraries"). The active
# ENDF/B-VIII.0 library ($OPENMC_CROSS_SECTIONS) provides c_Al27; ENDF/B-VII.0
# does not, so this must revert to False if the library is switched back.
USE_AL_SAB = True

# =============================================================================
# FUEL MATERIAL
# LEU U3Si2-Al fuel, 19.75 w/o enriched uranium
# Atom densities (atom/b-cm) taken directly from the reference MCNP deck.
# NO thermal scattering table on the fuel (deck has no mt card for it).
# =============================================================================

fuel = openmc.Material(name='LEU_U3Si2_Al_fuel')
fuel.add_nuclide('U235', 2.251800e-03)   # atom/b-cm
fuel.add_nuclide('U238', 9.034100e-03)
fuel.add_nuclide('Al27', 3.256300e-02)
fuel.add_nuclide('Si28', 6.938766e-03)
fuel.add_nuclide('Si29', 3.524947e-04)
fuel.add_nuclide('Si30', 2.326390e-04)
fuel.set_density('sum')

# =============================================================================
# CLADDING MATERIAL
# 6061-T6 Aluminum alloy (standard MTR fuel plate cladding)
# Density: 2.70 g/cm3
# =============================================================================

clad = openmc.Material(name='Al_6061_cladding')
clad.set_density('g/cm3', 2.70)
clad.add_element('Al', 1.00, 'ao')
# Pure aluminum stands in for 6061-T6; the minor alloying elements (Mg, Si, Cu,
# Cr, Zn, Ti, Fe — ~2.7 w/o total) have negligible reactivity effect here.
# Al metal S(a,b) (c_Al27) added per the 2026-07-20 meeting decision, gated on
# USE_AL_SAB (ENDF/B-VIII.0 provides c_Al27; VII.0 does not).
if USE_AL_SAB:
    clad.add_s_alpha_beta('c_Al27')

# =============================================================================
# COOLANT / MODERATOR
# Two water materials per MCNP deck cross-section assignments:
#   - Outer pool water: 0.9975 g/cm³ at 294 K   (H1 = 6.66909e-2 atom/b-cm)
#     Only the water OUTSIDE the core lattice footprint (the reflector-side
#     boundary ring) uses this — it is not core coolant.
#   - Core water:       0.9909 g/cm³ at 316.8 K (H1 = 6.625423e-2 atom/b-cm)
#     Every water feature INSIDE the core (inter-element gaps, plate/channel
#     water, end-box water, graphite channels, flux-trap holes, etc.) uses
#     this — it is the coolant water throughout the core, not a flux-trap-
#     specific material.
# (Mass densities print ~0.02% lower than the nominal values because the
# O-16-only basis has a slightly lower molar mass than natural oxygen; the
# H1/O16 atom densities above are the deck-authoritative quantities.)
# =============================================================================

# Water is H-1 + O-16 ONLY (no H-2/O-17/O-18), matching the deck's O-16 basis.
water = openmc.Material(name='light_water_294K')
water.temperature = 294.0
water.add_nuclide('H1', 6.66909e-02)
water.add_nuclide('O16', 6.66909e-02 / 2.0)
water.set_density('sum')
water.add_s_alpha_beta('c_H_in_H2O')

water_core = openmc.Material(name='light_water_core_316K')
water_core.temperature = 316.8
water_core.add_nuclide('H1', 6.625423e-02)
water_core.add_nuclide('O16', 6.625423e-02 / 2.0)
water_core.set_density('sum')
water_core.add_s_alpha_beta('c_H_in_H2O')

# =============================================================================
# CONTROL BLADE MATERIAL
# Hafnium (Hf) — used in IAEA generic 10 MW core control blades
# Density: 13.31 g/cm3
# =============================================================================

# hafnium = openmc.Material(name='hafnium_control_blade')
# hafnium.set_density('g/cm3', 13.31)
# hafnium.add_element('Hf', 1.0, 'ao')

# --- Alternative: Ag-In-Cd absorber (80-15-5 w/o) ---
# ag_in_cd = openmc.Material(name='AgInCd_control_blade')
# ag_in_cd.set_density('g/cm3', 10.17)
# ag_in_cd.add_element('Ag', 0.80, 'wo')
# ag_in_cd.add_element('In', 0.15, 'wo')
# ag_in_cd.add_element('Cd', 0.05, 'wo')

# --- Alternative: B4C absorber (natural boron) ---
# b4c = openmc.Material(name='B4C_control_blade')
# b4c.set_density('g/cm3', 2.52)
# b4c.add_element('B', 4.0, 'ao')
# b4c.add_element('C', 1.0, 'ao')

b4c = openmc.Material(name='B4C control absorber')
b4c.temperature = 294.0
b4c.add_nuclide('B10', 1.914973e-02)
b4c.add_nuclide('B11', 7.010412e-02)
b4c.add_nuclide('C12', 2.005592e-02 * 0.9893)
b4c.add_nuclide('C13', 2.005592e-02 * 0.0107)
# b4c.add_nuclide('C0',  2.005592e-02)
b4c.set_density('sum')

# b4c.add_nuclide('C12', 2.005592e-02 * 0.9893)
# b4c.add_nuclide('C13', 2.005592e-02 * 0.0107)

# NO S(a,b) on B4C carbon (deck has no mt card for it).
# b4c.add_nuclide('B10', 1.914973e-02)   # atom/b-cm
# b4c.add_nuclide('B11', 7.010412e-02)

# b4c.set_density('sum')                 # = 1.093098e-01 atom/b-cm


# =============================================================================
# REFLECTOR MATERIAL
# Graphite reflector blocks surrounding the core.
# Density: [TECDOC] 1.7000 g/cm3 per the 2026-07-20 meeting decision (replaces
# the deck-implied ~1.740 g/cm3 that the prior atom-density spec produced).
# =============================================================================

graphite = openmc.Material(name='graphite_reflector')
graphite.temperature = 294.0                      # deck: $ 294.0
if USE_NATURAL_CARBON:
    graphite.add_nuclide('C0', 1.0)
else:
    graphite.add_nuclide('C12', 0.9893)
    graphite.add_nuclide('C13', 0.0107)
graphite.set_density('g/cm3', 1.7000)
graphite.add_s_alpha_beta('c_Graphite')

# =============================================================================
# STRUCTURAL ALUMINUM
# Pure aluminum for grid plates, side plates, core structure
# Density: 2.70 g/cm3
# =============================================================================

aluminum = openmc.Material(name='aluminum_structure')
aluminum.set_density('g/cm3', 2.70)
aluminum.add_element('Al', 1.0, 'ao')
# Al metal S(a,b) (c_Al27) added per the 2026-07-20 meeting decision, gated on
# USE_AL_SAB.
if USE_AL_SAB:
    aluminum.add_s_alpha_beta('c_Al27')

# =============================================================================
# END-BOX HOMOGENIZED MATERIAL
# 25 v/o Al (2.70 g/cm³) / 75 v/o H₂O (0.993 g/cm³) per TECDOC-643 ANL appendix.
# Used in the 15 cm end-box regions immediately above and below the active fuel.
# Density = 0.25*2.70 + 0.75*0.993 = 1.41975 g/cm³
# =============================================================================

# _vf_al  = 0.25
# _vf_h2o = 0.75
# _rho_al  = 2.70    # g/cm³
# _rho_h2o = 0.993   # g/cm³ (at 38°C)

# # Atom densities proportional to (v_fraction * rho) / M_mol
# _n_al  = _vf_al  * _rho_al  / 26.982           # Al
# _n_h   = _vf_h2o * _rho_h2o / 18.015 * 2.0    # H  (2 atoms per H₂O)
# _n_o   = _vf_h2o * _rho_h2o / 18.015 * 1.0    # O
# _n_tot = _n_al + _n_h + _n_o

end_box_homog = openmc.Material(name='end_box_homogenized')
end_box_homog.temperature = 316.8                      # deck m00004: $ 316.8
end_box_homog.add_nuclide('Al27', 1.506565e-02)        # deck 13027
end_box_homog.add_nuclide('H1',   4.969068e-02)        # deck 1001
end_box_homog.add_nuclide('O16',  2.484534e-02)        # deck 8016
end_box_homog.set_density('sum')                       # -> 1.41806 g/cm3
end_box_homog.add_s_alpha_beta('c_H_in_H2O')
# Al metal S(a,b) (c_Al27) on the aluminum component, added per the 2026-07-20
# meeting decision, gated on USE_AL_SAB.
if USE_AL_SAB:
    end_box_homog.add_s_alpha_beta('c_Al27')

# Water component is H-1 + O-16 ONLY (no H-2/O-17/O-18) per the deck.
# end_box_homog = openmc.Material(name='end_box_homogenized')
# end_box_homog.set_density('g/cm3', _vf_al * _rho_al + _vf_h2o * _rho_h2o)  # 1.41975
# end_box_homog.add_nuclide('Al27', _n_al / _n_tot)
# end_box_homog.add_nuclide('H1',   _n_h  / _n_tot)
# end_box_homog.add_nuclide('O16',  _n_o  / _n_tot)
# end_box_homog.add_s_alpha_beta('c_H_in_H2O')
# Al metal S(a,b) on the aluminum component now added (gated on USE_AL_SAB),
# per the 2026-07-20 meeting decision.

# =============================================================================
# Collect all materials into a Materials object for export
# =============================================================================

materials = openmc.Materials([
    fuel,
    clad,
    water,
    water_core,
    b4c,
    graphite,
    aluminum,
    end_box_homog,
])

if __name__ == '__main__':
    materials.export_to_xml()
    print("materials.xml written successfully.")
    print("\nMaterial summary:")
    for mat in materials:
        t = f"  T={mat.temperature} K" if mat.temperature is not None else ""
        print(f"  [{mat.id}] {mat.name}  —  {mat.density} g/cm3{t}")