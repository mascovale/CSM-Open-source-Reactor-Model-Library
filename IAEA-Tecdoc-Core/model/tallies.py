"""
tallies.py
----------
Tally definitions for the IAEA TECDOC-643 Appendix A-2
Generic 10 MW LEU Research Reactor Core (Argonne design).

Reference:
    IAEA-TECDOC-643, "Research Reactor Core Conversion Guidebook,
    Volume 2: Analysis (Appendices A-F)," IAEA, Vienna, 1992.
    Appendix A-2: Generic 10 MW Reactor — Argonne National Laboratory.

About this file:
    Tallies are how OpenMC records results during the simulation.
    Every time a neutron does something interesting (crosses a surface,
    causes fission, scatters, etc.) OpenMC can record it.
    
    Think of tallies like sensors placed around the reactor —
    they count and average neutron interactions in specific regions.

Tallies defined here:
    1. keff                — effective multiplication factor (criticality)
    2. Mesh flux tally     — 2D neutron flux map across the core (x-y plane)
    3. Cell flux tally     — average flux in each fuel element
    4. Power tally         — fission power distribution across the core
    5. Energy spectrum     — neutron energy distribution at core center
"""

import openmc
import numpy as np

# =============================================================================
# TALLY 1 — keff (built into OpenMC settings, recorded automatically)
# No extra code needed — OpenMC always computes keff in eigenvalue mode.
# It will appear in the output as:
#   "Combined keff = X.XXXXX +/- 0.XXXXX"
# =============================================================================

tallies = openmc.Tallies()

# =============================================================================
# TALLY 2 — 2D MESH FLUX TALLY
#
# This creates a grid of "pixels" across the core and records the
# average neutron flux in each pixel. The result is a 2D flux map
# you can plot to see where neutrons are most concentrated.
#
# We use a regular mesh covering the active core region.
# Resolution: 80 x 90 pixels (one pixel ≈ one pitch width)
# =============================================================================

# Define the 2D mesh spanning the core (x-y plane at z=0)
core_mesh = openmc.RegularMesh(name='core_mesh')
core_mesh.dimension = [80, 90]          # 80 pixels in x, 90 pixels in y
core_mesh.lower_left  = [-30.8, -36.45] # cm — matches lattice lower left
core_mesh.upper_right = [ 30.8,  36.45] # cm — matches lattice upper right

# Create a mesh filter — tells OpenMC to score this tally on the mesh
mesh_filter = openmc.MeshFilter(core_mesh)

# Create the flux tally using the mesh filter
flux_tally = openmc.Tally(name='2d_flux_map')
flux_tally.filters = [mesh_filter]
flux_tally.scores  = ['flux']   # record neutron flux

tallies.append(flux_tally)

# =============================================================================
# TALLY 3 — POWER (FISSION HEATING) MESH TALLY
#
# Same mesh as above but records fission energy deposition instead of flux.
# This gives us the power distribution — where is the reactor generating
# the most heat? This is critical for thermal-hydraulic safety analysis.
#
# Score 'fission-q-recoverable' = energy released per fission event
# =============================================================================

power_tally = openmc.Tally(name='2d_power_map')
power_tally.filters = [mesh_filter]
power_tally.scores  = ['fission-q-recoverable']  # recoverable fission energy

tallies.append(power_tally)

# =============================================================================
# TALLY 4 — FISSION RATE TALLY
#
# Records the number of fission reactions per unit volume.
# Used to calculate:
#   - Power peaking factors (how much hotter is the hottest fuel?)
#   - Burnup rates (how fast is the fuel being consumed?)
# =============================================================================

fission_tally = openmc.Tally(name='2d_fission_rate')
fission_tally.filters = [mesh_filter]
fission_tally.scores  = ['fission']   # number of fission reactions

tallies.append(fission_tally)

# =============================================================================
# TALLY 5 — ENERGY SPECTRUM TALLY
#
# Records the neutron flux as a function of energy at the core center.
# This tells us the neutron energy distribution — how many fast neutrons
# vs thermal neutrons are present.
#
# Energy groups: 500 log-spaced bins from 1e-5 eV to 20 MeV
# (covers the full range from thermal to fast neutrons)
# =============================================================================

# Energy bin boundaries (in eV)
energy_bins = np.logspace(-5, 7.3, 501)   # 500 bins, 1e-5 eV to ~20 MeV

energy_filter = openmc.EnergyFilter(energy_bins)

# Spatial filter — small box at core center (x=0, y=0)
center_box = openmc.RegularMesh(name='center_mesh')
center_box.dimension   = [1, 1, 1]           # single cell
center_box.lower_left  = [-3.85, -4.05, -30.0]  # one pitch centered at origin
center_box.upper_right = [ 3.85,  4.05,  30.0]

center_filter = openmc.MeshFilter(center_box)

spectrum_tally = openmc.Tally(name='energy_spectrum_center')
spectrum_tally.filters = [center_filter, energy_filter]
spectrum_tally.scores  = ['flux']

tallies.append(spectrum_tally)

# =============================================================================
# TALLY 6 — 3D FLUX MESH
#
# Same as the 2D flux map but adds axial (z) resolution.
# Shows how the flux varies from bottom to top of the core.
# Useful for checking axial power peaking.
#
# Resolution: 40 x 45 x 30 (coarser than 2D to keep file size manageable)
# =============================================================================

mesh_3d = openmc.RegularMesh(name='core_mesh_3d')
mesh_3d.dimension    = [40, 45, 30]
mesh_3d.lower_left   = [-30.8, -36.45, -30.0]
mesh_3d.upper_right  = [ 30.8,  36.45,  30.0]

mesh_3d_filter = openmc.MeshFilter(mesh_3d)

flux_3d_tally = openmc.Tally(name='3d_flux_map')
flux_3d_tally.filters = [mesh_3d_filter]
flux_3d_tally.scores  = ['flux']

tallies.append(flux_3d_tally)

# =============================================================================
# EXPORT TALLIES TO XML
# =============================================================================

if __name__ == '__main__':
    tallies.export_to_xml()
    print("tallies.xml written successfully.")
    print(f"\nTallies defined:")
    for t in tallies:
        print(f"  [{t.id}] {t.name}")
        print(f"        scores : {t.scores}")