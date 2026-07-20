"""
tallies.py
----------
Tally definitions for the IAEA TECDOC-643 Appendix A-2
Generic 10 MW LEU Research Reactor Core (Argonne design).

Reference:
    IAEA-TECDOC-643, "Research Reactor Core Conversion Guidebook,
    Volume 2: Analysis (Appendices A-F)," IAEA, Vienna, 1992.
    Appendix A-2: Generic 10 MW Reactor — Argonne National Laboratory.

Exposes build_tallies() -> openmc.Tallies so drivers (core.build_model) can
attach the tallies to an openmc.Model. Nothing is written to disk at import
time; run this file directly only if you want a standalone tallies.xml.

Tallies:
    flux_map — 2D neutron flux map over the core footprint (160 x 180 x 1 mesh,
        z in [-30, +30]). rank_rods.py reads it from the statepoint to find
        which control rod sits in the highest flux (= highest-worth rod).
"""
import openmc
from geometry import PITCH_X, PITCH_Y


def build_tallies():
    """Return the openmc.Tallies for a production run (flux map)."""
    mesh = openmc.RegularMesh()
    mesh.dimension   = [160, 180, 1]
    mesh.lower_left  = [-4.0 * PITCH_X, -4.5 * PITCH_Y, -30.0]
    mesh.upper_right = [ 4.0 * PITCH_X,  4.5 * PITCH_Y,  30.0]

    flux_tally = openmc.Tally(name='flux_map')
    flux_tally.filters = [openmc.MeshFilter(mesh)]
    flux_tally.scores  = ['flux']

    return openmc.Tallies([flux_tally])


if __name__ == '__main__':
    build_tallies().export_to_xml()
    print("tallies.xml written (flux map).")
