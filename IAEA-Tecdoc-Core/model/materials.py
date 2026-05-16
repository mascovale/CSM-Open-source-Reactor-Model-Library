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

# =============================================================================
# FUEL MATERIAL
# LEU U3Si2-Al fuel, 19.75 w/o enriched uranium
# Fuel meat density: ~4.8 g/cm3 (U3Si2 dispersed in Al matrix)
# =============================================================================

fuel = openmc.Material(name='LEU_U3Si2_Al_fuel')
fuel.set_density('g/cm3', 6.42)
fuel.add_nuclide('U235', 0.1369, 'wo')
fuel.add_nuclide('U238', 0.5562, 'wo')
fuel.add_element('Si', 0.0545, 'wo')
fuel.add_element('Al', 0.2524, 'wo')
fuel.add_s_alpha_beta('c_Al27')  # thermal scattering for Al

# =============================================================================
# CLADDING MATERIAL
# 6061-T6 Aluminum alloy (standard MTR fuel plate cladding)
# Density: 2.70 g/cm3
# =============================================================================

clad = openmc.Material(name='Al_6061_cladding')
clad.set_density('g/cm3', 2.70)
clad.add_element('Al', 1.00, 'wo')
# below is the detailed composition of 6061-T6 aluminum alloy, but for simplicity,
# we will use pure aluminum in the model. The minor alloying elements have negligible effects.
# clad.add_element('Al', 0.9733, 'wo') 
# clad.add_element('Mg', 0.0100, 'wo')
# clad.add_element('Si', 0.0060, 'wo')
# clad.add_element('Cu', 0.0028, 'wo')
# clad.add_element('Cr', 0.0020, 'wo')
# clad.add_element('Zn', 0.0025, 'wo')
# clad.add_element('Ti', 0.0015, 'wo')
# clad.add_element('Fe', 0.0019, 'wo')
# clad.add_s_alpha_beta('c_Al27')

# =============================================================================
# COOLANT / MODERATOR
# Light water (H2O) at ~38°C, atmospheric pressure
# Density: 0.993 g/cm3
# =============================================================================

water = openmc.Material(name='light_water')
water.set_density('g/cm3', 0.993) # density at 38°C
water.add_element('H', 2.0, 'ao')
water.add_element('O', 1.0, 'ao')
water.add_s_alpha_beta('c_H_in_H2O')  # thermal scattering for H in water

# =============================================================================
# CONTROL BLADE MATERIAL
# Hafnium (Hf) — used in IAEA generic 10 MW core control blades
# Density: 13.31 g/cm3
# =============================================================================

hafnium = openmc.Material(name='hafnium_control_blade')
hafnium.set_density('g/cm3', 13.31)
hafnium.add_element('Hf', 1.0, 'ao')

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

# =============================================================================
# REFLECTOR MATERIAL
# Beryllium (Be) reflector blocks surrounding the core
# Density: 1.85 g/cm3
# =============================================================================

graphite = openmc.Material(name='graphite_reflector')
graphite.set_density('g/cm3', 1.70)
graphite.add_element('C', 1.0, 'ao')
graphite.add_s_alpha_beta('c_Graphite')

# =============================================================================
# STRUCTURAL ALUMINUM
# Pure aluminum for grid plates, side plates, core structure
# Density: 2.70 g/cm3
# =============================================================================

aluminum = openmc.Material(name='aluminum_structure')
aluminum.set_density('g/cm3', 2.70)
aluminum.add_element('Al', 1.0, 'ao')
aluminum.add_s_alpha_beta('c_Al27')

# =============================================================================
# VOID / AIR (for dry experimental tubes or gaps)
# =============================================================================

air = openmc.Material(name='air')
air.set_density('g/cm3', 0.001205)
air.add_element('N', 0.784, 'ao')
air.add_element('O', 0.216, 'ao')

# =============================================================================
# Collect all materials into a Materials object for export
# =============================================================================

materials = openmc.Materials([
    fuel,
    clad,
    water,
    hafnium,
    graphite,
    aluminum,
    air,
])

if __name__ == '__main__':
    # Export to XML for verification
    materials.export_to_xml()
    print("materials.xml written successfully.")
    print("\nMaterial summary:")
    for mat in materials:
        print(f"  [{mat.id}] {mat.name}  —  {mat.density} g/cm3")