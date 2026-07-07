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

"""
tallies.py — flux map for ranking the five control rods.
Run in model/ to write tallies.xml. OpenMC records neutron flux on a
grid; rank_rods.py reads it afterward to find which rod sits in the
highest flux = highest-worth rod.
"""
import openmc
from geometry import PITCH_X, PITCH_Y

mesh = openmc.RegularMesh()
mesh.dimension   = [160, 180, 1]
mesh.lower_left  = [-4.0 * PITCH_X, -4.5 * PITCH_Y, -30.0]
mesh.upper_right = [ 4.0 * PITCH_X,  4.5 * PITCH_Y,  30.0]

flux_tally = openmc.Tally(name='flux_map')
flux_tally.filters = [openmc.MeshFilter(mesh)]
flux_tally.scores  = ['flux']

openmc.Tallies([flux_tally]).export_to_xml()
print("tallies.xml written (flux map).")