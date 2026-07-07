"""
settings.py
-----------
Simulation settings for the IAEA TECDOC-643 Appendix A-2
Generic 10 MW LEU Research Reactor Core (Argonne design).

Reference:
    IAEA-TECDOC-643, "Research Reactor Core Conversion Guidebook,
    Volume 2: Analysis (Appendices A-F)," IAEA, Vienna, 1992.
    Appendix A-2: Generic 10 MW Reactor — Argonne National Laboratory.

About this file:
    This file controls HOW OpenMC runs the simulation — not what
    the reactor looks like (that's geometry.py) or what it's made
    of (that's materials.py). Think of it as the "run instructions".

Key concepts:
    - Criticality (k-eigenvalue) calculation: finds keff
    - Particles: the neutrons OpenMC simulates
    - Batches: groups of neutrons simulated together
    - Inactive batches: early batches discarded while the fission
      source distribution is still settling (not yet converged)
    - Active batches: batches used for actual statistics/results
"""

import openmc
import numpy as np

# =============================================================================
# SIMULATION MODE
# We are running a k-eigenvalue (criticality) calculation.
# This finds keff — the effective neutron multiplication factor.
# keff > 1.0 = supercritical (reaction growing)
# keff = 1.0 = critical (steady state, what we want for 10 MW operation)
# keff < 1.0 = subcritical (reaction dying out)
# =============================================================================

settings = openmc.Settings()
settings.run_mode = 'eigenvalue'   # criticality calculation

# =============================================================================
# PARTICLE STATISTICS
#
# particles: number of neutrons simulated per batch
# batches:   total number of batches to run
# inactive:  number of batches to discard at the start
#
# Rule of thumb:
#   - inactive batches should be ~40-50% of total batches
#   - more particles = more accurate but slower
#   - start small for testing, scale up for final results
#
# For a first test run (fast, less accurate):
#   particles=1000, batches=50, inactive=20
# For a production run (slow, more accurate):
#   particles=10000, batches=200, inactive=50
# =============================================================================

settings.particles  = 50000    # neutrons per batch (increase for production)
settings.batches    = 150      # total batches
settings.inactive   = 50      # discard first 50 batches (source convergence)

# =============================================================================
# INITIAL FISSION SOURCE
#
# OpenMC needs a starting guess for where fission neutrons come from.
# We use a uniform spatial distribution across the active core volume.
#
# The source is a box spanning the active fuel region:
#   x: -3*PITCH_X to +3*PITCH_X  (covers the 5-wide fuel columns)
#   y: -3*PITCH_Y to +3*PITCH_Y  (covers the 6-tall fuel rows)
#   z: -30.0 to +30.0 cm         (active fuel height)
#
# OpenMC will refine this distribution over the inactive batches
# until it converges to the true fission source shape.
# =============================================================================

# Core active region bounds (approximate, matches fuel element positions)
PITCH_X = 7.7   # cm
PITCH_Y = 8.1   # cm

source_box = openmc.stats.Box(
    lower_left  = (-3 * PITCH_X, -3 * PITCH_Y, -30.0),
    upper_right = ( 3 * PITCH_X,  3 * PITCH_Y,  30.0),
    only_fissionable=True   # only place source points in fissionable material
)

settings.source = openmc.IndependentSource(space=source_box)

# =============================================================================
# OUTPUT OPTIONS
#
# Controls what OpenMC writes to disk after the run.
# summary.h5    — geometry and material summary (always useful)
# tallies.out   — tally results in plain text
# =============================================================================

settings.output = {
    'tallies': True,    # write tallies.out
    'summary': True,    # write summary.h5
}

# =============================================================================
# TEMPERATURE SETTINGS
#
# Cross sections are temperature dependent. We specify the default
# temperature for all materials (room temperature / cold zero power).
# Units: Kelvin
#
# 293 K ≈ 20°C — cold zero power condition (all-fresh core validation)
# 350 K ≈ 77°C — approximate operating temperature at 10 MW
# =============================================================================

settings.temperature = {'method': 'interpolation'}

# =============================================================================
# EXPORT SETTINGS TO XML
# =============================================================================

if __name__ == '__main__':
    settings.export_to_xml()
    print("settings.xml written successfully.")
    print(f"\nSimulation summary:")
    print(f"  Run mode       : {settings.run_mode}")
    print(f"  Particles/batch: {settings.particles}")
    print(f"  Total batches  : {settings.batches}")
    print(f"  Inactive       : {settings.inactive}")
    print(f"  Active         : {settings.batches - settings.inactive}")
    print(f"  Temperature    : {settings.temperature['method']} K")