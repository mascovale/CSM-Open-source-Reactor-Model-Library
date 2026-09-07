"""Run all-in (withdrawn_fraction=0.0) with the taller TECDOC-faithful model."""
import sys, os, pathlib
MODEL_DIR = pathlib.Path(__file__).parent.parent / 'model'
sys.path.insert(0, str(MODEL_DIR))
import openmc

os.environ.setdefault('OPENMC_CROSS_SECTIONS',
    '/home/tmccoy/nuclear-data/endfb-viii.0-hdf5/cross_sections.xml')

from geometry import (PITCH_X, PITCH_Y, CORE_BOTTOM, CORE_TOP,
                      water_univ, graphite_univ, make_flux_trap,
                      make_standard_fuel_element, make_control_fuel_element)

std_elems  = [make_standard_fuel_element(i) for i in range(23)]
ctrl_elems = [make_control_fuel_element(100+i, withdrawn_fraction=0.0) for i in range(5)]
F = make_flux_trap()
W, G, S, C = water_univ, graphite_univ, std_elems, ctrl_elems

lattice = openmc.RectLattice(name='core_lattice')
lattice.pitch      = (PITCH_X, PITCH_Y)
lattice.lower_left = (-4*PITCH_X, -4.5*PITCH_Y)
lattice.universes  = [
    [W, W,     W,     W,     W,     W,     W,     W],
    [W, G,     G,     G,     G,     G,     G,     W],
    [W, S[0],  S[1],  C[0],  S[2],  S[3],  S[4],  W],
    [W, S[5],  S[6],  S[7],  S[8],  C[1],  S[9],  W],
    [W, S[10], C[2],  S[11], F,     S[12], S[13], W],
    [W, S[14], S[15], S[16], S[17], C[3],  S[18], W],
    [W, F,     S[19], C[4],  S[20], S[21], S[22], W],
    [W, G,     G,     G,     G,     G,     G,     W],
    [W, W,     W,     W,     W,     W,     W,     W],
]

core_cell = openmc.Cell(fill=lattice, region=(
    +openmc.XPlane(x0=-4*PITCH_X, boundary_type='vacuum') &
    -openmc.XPlane(x0= 4*PITCH_X, boundary_type='vacuum') &
    +openmc.YPlane(y0=-4.5*PITCH_Y, boundary_type='vacuum') &
    -openmc.YPlane(y0= 4.5*PITCH_Y, boundary_type='vacuum') &
    +openmc.ZPlane(z0=CORE_BOTTOM, boundary_type='vacuum') &
    -openmc.ZPlane(z0=CORE_TOP,   boundary_type='vacuum')))

geometry  = openmc.Geometry(openmc.Universe(cells=[core_cell]))

from materials import materials
from settings  import settings
settings.particles = 70000
settings.batches   = 150
settings.inactive  = 50

run_dir = pathlib.Path(__file__).parent.parent / 'run_results' / 'partC_all_in'
run_dir.mkdir(parents=True, exist_ok=True)

model = openmc.Model(geometry=geometry, materials=materials, settings=settings)
sp_path = model.run(cwd=str(run_dir))

sp   = openmc.StatePoint(sp_path)
keff = sp.keff
print(f"\nall-in  keff = {keff.nominal_value:.5f} +/- {keff.std_dev:.5f}")
print(f"vs TECDOC 1.0296   : {(keff.nominal_value-1.0296)*1e5:+.0f} pcm")
print(f"vs prior baseline  : {(keff.nominal_value-1.01944)*1e5:+.0f} pcm")
print("(taller model + end-box regions shift keff from prior run; f=0 blade z=[-30,+30])")
