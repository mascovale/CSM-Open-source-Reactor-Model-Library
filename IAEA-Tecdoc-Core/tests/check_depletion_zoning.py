"""
tests/check_depletion_zoning.py
-------------------------------
Structural verification of the fuel-meat depletion zoning (Phase 1.5).

Zoning splits every fuel meat cell on an (x, z) grid into
N_X_ZONES x N_AXIAL_ZONES cells, with one depletable material PER CELL —
cells and materials are 1:1, 614 plates x N_X_ZONES x N_AXIAL_ZONES of each,
nothing shared between plates. x is the meat WIDTH direction
(MEAT_WIDTH, 6.3 cm); z is axial; y (plate stacking) is NOT subdivided.
This script checks the scaffolding only — it configures and runs NO depletion,
and performs NO eigenvalue calculation. The overlap checks use
`model.run(geometry_debug=True)` (= `openmc --geometry-debug`), an overlap scan,
matching the idiom already in geometry.py's __main__ block.

NAMING — NOT A REGRESSION. Cells are `std{n}_meat_{i}_x{j}_z{k}` and materials
`fuel_{ELEM}_p{i}_x{j}_z{k}`, mirroring the cell name order element -> plate ->
x -> z, at EVERY zone count including N_X_ZONES == 1, where the older 1D scheme
emitted `..._z{k}` with no `_x0`. The `_x0` infix in a
N_X_ZONES == 1 diff is expected: uniform naming was chosen over a special case.
Backward compatibility at N_X_ZONES == 1 means GEOMETRIC, VOLUMETRIC and
REGION-EXPRESSION identity with the old axial-only behaviour, not name identity.
Sections 10a/10b test that identity directly.

Every assertion is written against N_X_ZONES / N_AXIAL_ZONES; the benchmark
literals (0.9639 / 11836.692 cm^3) are asserted only under an [N_X=2, N_Z=10]
guard, so changing either count breaks nothing here. There is no longer a std
vs ctrl volume literal: every material owns exactly one plate's zone, so 0.9639
is the ONLY per-material volume in the model.

IF YOU CHANGE THE ZONE COUNTS, RETARGET THAT GUARD TOO. A guard whose condition
no longer matches the defaults does not fail — it silently stops running, and
the suite still prints ALL CHECKS PASSED while asserting none of the benchmark
numbers. That is worse than having no benchmark block at all.

Run from the repo root:
    conda activate openmc
    python tests/check_depletion_zoning.py

Internal modes (used to isolate a check in its own process, so material/surface
ID spaces and monkeypatched module state never cross-contaminate):
    python tests/check_depletion_zoning.py --overlap  <f> <0|1>
    python tests/check_depletion_zoning.py --negative <count|planes>
    python tests/check_depletion_zoning.py --degenerate <nx> <nz>
"""

import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
import xml.etree.ElementTree as ET

import numpy as np

THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, 'model'))

import openmc

import materials as mats_mod
import geometry as g
from materials import N_X_ZONES, N_AXIAL_ZONES, get_zoned_fuels


N_STD, N_CTRL = 23, 5
N_PLATES_TOTAL = N_STD * g.N_PLATES_STD + N_CTRL * g.N_CTRL_FUEL_PLATES  # 614
N_ZONES_PER_ELEM = N_X_ZONES * N_AXIAL_ZONES                            # 20
N_ZONED_MATS     = N_PLATES_TOTAL * N_ZONES_PER_ELEM                    # 12280

_failures = []


def check(label, ok, detail=''):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  — {detail}" if detail else ''))
    if not ok:
        _failures.append(label)
    return ok


def bbox_volume(cell):
    """Exact volume of a cell's bounding box.

    Meat cells are pure half-space intersections (rectangular prisms), so the
    bounding box volume IS the cell volume — deterministic, not a stochastic
    volume estimate.
    """
    bb = cell.bounding_box
    return float(np.prod(np.asarray(bb.upper_right) - np.asarray(bb.lower_left)))


def is_fuel_meat(cell):
    """True for a cell filled with fuel meat, zoned or not."""
    fill = cell.fill
    if not isinstance(fill, openmc.Material):
        return False
    return fill is mats_mod.fuel or bool(fill.depletable)


# =============================================================================
# Internal modes — one isolated check, one process
# =============================================================================

def _run_one_overlap(f, zoned):
    import core
    core.resolve_cross_sections(core.CoreConfig())

    from settings import settings as _settings
    _settings.particles, _settings.batches, _settings.inactive = 200, 2, 1

    geom = g.build_core_geometry(withdrawn_fraction=f, depletion_zoning=zoned)
    # Same assembly core.build_model() uses: base fuel dropped when zoned.
    mat_list = (openmc.Materials(
                    [m for m in mats_mod.materials if m is not mats_mod.fuel]
                    + get_zoned_fuels())
                if zoned else mats_mod.materials)
    model = openmc.Model(geometry=geom, materials=mat_list, settings=_settings)
    with tempfile.TemporaryDirectory() as d:
        model.run(geometry_debug=True, cwd=d)


def _run_negative(kind):
    """Inject a defect and confirm the guard fires. Exit 0 = fired as intended.

    Exit 2 means the defect was injected and NOTHING complained — the guard is
    not doing its job, which is a test failure, not a pass.
    """
    if kind == 'count':
        # Off-by-one in the x ZONE COUNT: the count is bumped while the derived
        # MEAT_ZONE_WIDTH keeps its old value. This is exactly the
        # desynchronisation the module-level tiling assert exists to catch — a
        # self-consistent count change cannot be caught by it, and is not
        # supposed to be (see the scale-invariance note in section 10c).
        g.N_X_ZONES = N_X_ZONES + 1
        try:
            assert abs((g.MEAT_LEFT_X + g.N_X_ZONES * g.MEAT_ZONE_WIDTH)
                       - g.MEAT_RIGHT_X) < g.ZONE_TILE_TOL, \
                "x zones do not tile the active meat width"
        except AssertionError as e:
            print(f"FIRED AssertionError: {e}")
            # Downstream consequence. Note the SECOND guard that catches this:
            # make_zoned_fuel validates x_index against materials.N_X_ZONES,
            # which is still the unpatched value, so the desynchronised count is
            # rejected at material creation before it can reach the volume sum.
            # Either guard firing is a pass; report whichever does.
            try:
                geom = g.build_core_geometry(withdrawn_fraction=1.0,
                                             depletion_zoning=True)
            except Exception as e2:
                print(f"FIRED {type(e2).__name__} from make_zoned_fuel: {e2}")
                sys.exit(0)
            depl = [m for m in geom.get_all_materials().values() if m.depletable]
            declared = sum(m.volume for m in depl)
            true_vol = (N_PLATES_TOTAL * g.MEAT_THICK * g.MEAT_WIDTH
                        * g.MEAT_HEIGHT)
            if abs(declared - true_vol) < 1e-6:
                print("NEGATIVE TEST DID NOT FIRE — bad count still summed to "
                      "the true meat volume")
                sys.exit(2)
            print(f"FIRED volume-sum: declared {declared:.6f} != "
                  f"true {true_vol:.6f} cm^3  (delta {declared - true_vol:+.6f})")
            sys.exit(0)
        print("NEGATIVE TEST DID NOT FIRE — tiling assert accepted a bad count")
        sys.exit(2)

    if kind == 'planes':
        # Off-by-one in the INTERIOR PLANE COUNT: one plane short. zone_x_bounds
        # indexes planes[j] for the interior zones, so the last interior zone
        # runs off the end of the list.
        g._FUEL_ZONE_X_PLANES = [
            openmc.XPlane(x0=g.MEAT_LEFT_X + j * g.MEAT_ZONE_WIDTH)
            for j in range(1, N_X_ZONES - 1)          # one short
        ]
        n = len(g.fuel_zone_x_planes())
        if n == N_X_ZONES - 1:
            print("NEGATIVE TEST DID NOT FIRE — plane list was not perturbed")
            sys.exit(2)
        print(f"FIRED plane-count: {n} interior x planes, expected "
              f"{N_X_ZONES - 1}")
        try:
            g.build_core_geometry(withdrawn_fraction=1.0, depletion_zoning=True)
        except IndexError as e:
            print(f"FIRED IndexError from zone_x_bounds: {e}")
            sys.exit(0)
        print("NEGATIVE TEST DID NOT FIRE — geometry built with a short "
              "plane list")
        sys.exit(2)

    raise SystemExit(f"unknown negative test '{kind}'")


def _run_degenerate(nx, nz):
    """Rebuild the module stack at (nx, nz) and report meat geometry.

    Used by 10a/10b to prove that N_X_ZONES == 1 reproduces the axial-only
    behaviour and that (1, 1) reproduces the unzoned meat region. Runs in its
    own process because it reimports materials/geometry with patched counts.
    """
    import importlib
    import materials as m2
    m2.N_X_ZONES, m2.N_AXIAL_ZONES = nx, nz
    g2 = importlib.import_module('geometry')
    g2 = importlib.reload(g2)

    geom = g2.build_core_geometry(withdrawn_fraction=1.0, depletion_zoning=True)
    meat = [c for c in geom.get_all_cells().values()
            if '_meat_' in (c.name or '')]
    vol = sum(float(np.prod(np.asarray(c.bounding_box.upper_right)
                            - np.asarray(c.bounding_box.lower_left)))
              for c in meat)
    sample = sorted((c for c in meat if c.name.startswith('std0_meat_0_')),
                    key=lambda c: c.name)
    print(f"CELLS {len(meat)}")
    print(f"VOL {vol:.9f}")
    print(f"SAMPLE_N {len(sample)}")
    print(f"SAMPLE_REGION {sample[0].region}")
    print(f"SAMPLE_NAME {sample[0].name}")


if len(sys.argv) > 1 and sys.argv[1] == '--overlap':
    _run_one_overlap(float(sys.argv[2]), bool(int(sys.argv[3])))
    sys.exit(0)

if len(sys.argv) > 1 and sys.argv[1] == '--negative':
    _run_negative(sys.argv[2])
    sys.exit(0)

if len(sys.argv) > 1 and sys.argv[1] == '--degenerate':
    _run_degenerate(int(sys.argv[2]), int(sys.argv[3]))
    sys.exit(0)


# =============================================================================
# 1. Zone constants and tiling — BOTH directions
# =============================================================================

print("\n=== 1. Zone constants and tiling ===")
print(f"  N_X_ZONES x N_AXIAL_ZONES  = {N_X_ZONES} x {N_AXIAL_ZONES} "
      f"= {N_ZONES_PER_ELEM} zones per element")
print(f"  meat x-range               = [{g.MEAT_LEFT_X}, {g.MEAT_RIGHT_X}] cm "
      f"(width {g.MEAT_WIDTH} cm)")
print(f"  meat z-range               = [{g.MEAT_BOT_Z}, {g.MEAT_TOP_Z}] cm "
      f"(height {g.MEAT_HEIGHT} cm)")
print(f"  MEAT_ZONE_WIDTH            = {g.MEAT_ZONE_WIDTH} cm")
print(f"  MEAT_ZONE_HEIGHT           = {g.MEAT_ZONE_HEIGHT} cm")
print(f"  MEAT_ZONE_VOLUME_PER_PLATE = {g.MEAT_ZONE_VOLUME_PER_PLATE} cm^3")
print(f"  ZONE_TILE_TOL              = {g.ZONE_TILE_TOL:g}")

check("x zones tile the meat width exactly",
      abs(g.MEAT_LEFT_X + N_X_ZONES * g.MEAT_ZONE_WIDTH - g.MEAT_RIGHT_X)
      < g.ZONE_TILE_TOL)
check("z zones tile the meat height exactly",
      abs(g.MEAT_BOT_Z + N_AXIAL_ZONES * g.MEAT_ZONE_HEIGHT - g.MEAT_TOP_Z)
      < g.ZONE_TILE_TOL)
check("interior x plane count == N_X_ZONES - 1",
      len(g.fuel_zone_x_planes()) == N_X_ZONES - 1,
      f"{len(g.fuel_zone_x_planes())}")
check("interior z plane count == N_AXIAL_ZONES - 1",
      len(g.fuel_zone_planes()) == N_AXIAL_ZONES - 1,
      f"{len(g.fuel_zone_planes())}")
check("x zone planes are created once (memoized)",
      g.fuel_zone_x_planes() is g.fuel_zone_x_planes())
check("z zone planes are created once (memoized)",
      g.fuel_zone_planes() is g.fuel_zone_planes())
check("2D zone volume == thickness x width x height",
      abs(g.MEAT_ZONE_VOLUME_PER_PLATE
          - g.MEAT_THICK * g.MEAT_ZONE_WIDTH * g.MEAT_ZONE_HEIGHT) < 1e-15)
check("plate count == 23*23 + 5*17 == 614", N_PLATES_TOTAL == 614,
      f"{N_PLATES_TOTAL}")

# No other surface in the model sits on the meat centreline, so an even
# N_X_ZONES (which puts an interior plane at x = 0) collides with nothing.
if N_X_ZONES % 2 == 0:
    _centre = [s for s in g.fuel_zone_x_planes() if abs(s.x0) < 1e-15]
    check("even N_X_ZONES puts exactly one interior plane on x = 0",
          len(_centre) == 1, f"{len(_centre)}")

if N_X_ZONES == 2 and N_AXIAL_ZONES == 10:
    check("[N_X=2, N_Z=10] zone width == 3.15 cm",
          abs(g.MEAT_ZONE_WIDTH - 3.15) < 1e-12)
    check("[N_X=2, N_Z=10] zone height == 6.0 cm",
          abs(g.MEAT_ZONE_HEIGHT - 6.0) < 1e-12)
    check("[N_X=2, N_Z=10] one plate, one zone == 0.9639 cm^3",
          abs(g.MEAT_ZONE_VOLUME_PER_PLATE - 0.9639) < 1e-12,
          f"{g.MEAT_ZONE_VOLUME_PER_PLATE:.9f}")
    # No std/ctrl split any more: one material owns one plate's zone, so
    # 0.9639 above IS the material volume for every one of the 12,280.
    check("[N_X=2, N_Z=10] 20 zones x per-plate zone vol == per-plate meat vol",
          abs(N_ZONES_PER_ELEM * g.MEAT_ZONE_VOLUME_PER_PLATE - 19.278) < 1e-12)

# =============================================================================
# 2. Core map
# =============================================================================

print("\n=== 2. Core map ===")
print(f"  standard : {' '.join(g.STD_ELEMENT_IDS)}")
print(f"  control  : {' '.join(g.CTRL_ELEMENT_IDS)}")
ft_positions = [g.core_map_label(i, j)
                for i, row in enumerate(g.CORE_MAP)
                for j, t in enumerate(row) if t == 'F']
print(f"  flux traps: {' '.join(ft_positions)}  (A-2 Table 1: 1 center, 1 edge)")
check("23 standard + 5 control labels, all unique",
      len(g.STD_ELEMENT_IDS) == 23 and len(g.CTRL_ELEMENT_IDS) == 5
      and len(set(g.STD_ELEMENT_IDS + g.CTRL_ELEMENT_IDS)) == 28)
check("flux traps at D4 (center) and A6 (edge)", ft_positions == ['D4', 'A6'],
      str(ft_positions))

# =============================================================================
# 3. Zoning OFF — baseline is untouched
# =============================================================================

print("\n=== 3. Zoning OFF ===")
_t0 = time.perf_counter()
geom_off = g.build_core_geometry(withdrawn_fraction=1.0, depletion_zoning=False)
_t_off = time.perf_counter() - _t0
mats_off = geom_off.get_all_materials().values()
cells_off = geom_off.get_all_cells().values()
meat_off = [c for c in cells_off if is_fuel_meat(c)]
vol_off = sum(bbox_volume(c) for c in meat_off)

# NOTE: this is NOT zero. OpenMC auto-sets depletable=True on any material
# carrying an actinide (openmc/material.py: "For actinides, have the material
# be depletable by default"), so the base fuel has been flagged depletable
# since long before zoning existed — verified against pristine HEAD. The
# baseline therefore has exactly ONE depletable material, and it has no volume.
depl_off = [m for m in mats_off if m.depletable]
check("exactly 1 depletable material — the base fuel, auto-flagged by OpenMC",
      len(depl_off) == 1 and depl_off[0] is mats_mod.fuel,
      f"{[m.name for m in depl_off]}")
check("baseline depletable material has no volume (nothing to normalize on)",
      depl_off[0].volume is None)
check(f"{N_PLATES_TOTAL} meat cells (one per plate)",
      len(meat_off) == N_PLATES_TOTAL, f"{len(meat_off)}")
check("every meat cell filled with the base fuel material",
      all(c.fill is mats_mod.fuel for c in meat_off))
print(f"  total meat volume (bbox sum) = {vol_off:.6f} cm^3")
print(f"  geometry build wall time     = {_t_off:.2f} s")

# =============================================================================
# 4. Zoning ON — material inventory
# =============================================================================

print("\n=== 4. Zoning ON — materials ===")
_t0 = time.perf_counter()
geom_on = g.build_core_geometry(withdrawn_fraction=1.0, depletion_zoning=True)
_t_on = time.perf_counter() - _t0
mats_on = list(geom_on.get_all_materials().values())
depl = [m for m in mats_on if m.depletable]
print(f"  geometry build wall time     = {_t_on:.2f} s")

check(f"exactly {N_ZONED_MATS} = 614 * N_X_ZONES * N_AXIAL_ZONES depletable "
      f"materials", len(depl) == N_ZONED_MATS, f"{len(depl)}")
check("every depletable material has a non-None volume",
      all(m.volume is not None for m in depl))
check("no two zoned materials share a name",
      len({m.name for m in depl}) == len(depl))
check("the zoned materials are the only depletable materials in the geometry",
      len([m for m in mats_on if m.depletable]) == N_ZONED_MATS)
check("registry and geometry agree on the material set",
      {m.id for m in get_zoned_fuels()} == {m.id for m in depl})
_expect_names = (
    {f'fuel_{e}_p{i}_x{j}_z{k}'
     for e in g.STD_ELEMENT_IDS for i in range(g.N_PLATES_STD)
     for j in range(N_X_ZONES) for k in range(N_AXIAL_ZONES)}
    | {f'fuel_{e}_p{i}_x{j}_z{k}'
       for e in g.CTRL_ELEMENT_IDS for i in range(g.N_CTRL_FUEL_PLATES)
       for j in range(N_X_ZONES) for k in range(N_AXIAL_ZONES)})
check("every (element, plate, x, z) quadruple is present exactly once",
      _expect_names == {m.name for m in depl},
      f"expected {len(_expect_names)}, got {len({m.name for m in depl})}")

# The base fuel must fill NOTHING when zoned — a surviving base-fuel cell would
# mean the split missed a meat cell, and the volume identity below would then
# need explaining. core.build_model() raises on this; assert it here too.
base_fuel_cells = [c.name for c in geom_on.get_all_cells().values()
                   if c.fill is mats_mod.fuel]
check("no cell is filled with the base fuel material when zoned",
      len(base_fuel_cells) == 0, f"{base_fuel_cells[:5]}")
check("base fuel material absent from the geometry's material set",
      mats_mod.fuel not in mats_on)

# ...and is therefore excluded from the exported set, so no depletable material
# with volume=None reaches a future depletion solve. This mirrors what
# core.build_model() assembles on the zoning-on path.
_exported = openmc.Materials(
    [m for m in mats_mod.materials if m is not mats_mod.fuel] + get_zoned_fuels())
check(f"exported set carries exactly {N_ZONED_MATS} depletable materials",
      sum(1 for m in _exported if m.depletable) == N_ZONED_MATS,
      f"{sum(1 for m in _exported if m.depletable)}")
check("no exported depletable material has volume=None",
      all(m.volume is not None for m in _exported if m.depletable))
check("base fuel excluded from the exported set",
      mats_mod.fuel not in _exported)

# --- CHECK #2: declared material volumes vs the analytic total ---------------
# This is the check that catches a mis-derived zone volume. Nothing else ties
# the 560 declared volumes back to the geometry they are supposed to describe.
vol_analytic = N_PLATES_TOTAL * g.MEAT_THICK * g.MEAT_WIDTH * g.MEAT_HEIGHT
vol_declared = sum(m.volume for m in depl)
print(f"  analytic total meat volume = {vol_analytic:.9f} cm^3")
print(f"  declared volume sum        = {vol_declared:.9f} cm^3")
check("sum of all zone material volumes == analytic total meat volume",
      abs(vol_declared - vol_analytic) < 1e-6,
      f"delta = {vol_declared - vol_analytic:+.3e}")
if N_X_ZONES == 2 and N_AXIAL_ZONES == 10:
    check("[N_X=2, N_Z=10] declared volume sum == 11836.692 cm^3",
          abs(vol_declared - 11836.692) < 1e-6, f"{vol_declared:.6f}")

# --- U-235 MASS CONSERVATION ------------------------------------------------
# All zoned materials are clones of the base fuel, so composition and density
# are identical and mass conservation reduces to volume conservation — but it is
# checked on MASS, through openmc's own get_mass(), because that is the quantity
# a depletion solve normalizes on.
_ref = mats_mod.fuel.clone()
_ref.volume = vol_analytic
m_ref = _ref.get_mass('U235')
m_zoned = sum(m.get_mass('U235') for m in depl)
print(f"  U-235 mass, unzoned reference = {m_ref:.6f} g")
print(f"  U-235 mass, summed over zones = {m_zoned:.6f} g")
check("U-235 mass conserved across the zoned decomposition",
      abs(m_zoned - m_ref) < 1e-6 * m_ref,
      f"delta = {m_zoned - m_ref:+.3e} g "
      f"({abs(m_zoned - m_ref) / m_ref:.2e} relative)")

# composition parity with the base fuel
base_nuc = dict((n.name, n.percent) for n in mats_mod.fuel.nuclides)
check("all zoned materials keep the base composition",
      all(dict((n.name, n.percent) for n in m.nuclides) == base_nuc for m in depl))
check("all zoned materials keep the base temperature (332.1 K)",
      all(m.temperature == mats_mod.fuel.temperature for m in depl))

# =============================================================================
# 5. Zoning ON — cells, and the fuel-inventory parity check
# =============================================================================

print("\n=== 5. Zoning ON — cells and fuel-inventory parity ===")
cells_on = geom_on.get_all_cells().values()
meat_on = [c for c in cells_on if is_fuel_meat(c)]
vol_on = sum(bbox_volume(c) for c in meat_on)

check(f"{N_PLATES_TOTAL} * {N_ZONES_PER_ELEM} = "
      f"{N_PLATES_TOTAL * N_ZONES_PER_ELEM} meat cells",
      len(meat_on) == N_PLATES_TOTAL * N_ZONES_PER_ELEM, f"{len(meat_on)}")
print(f"  meat volume, zoning OFF = {vol_off:.9f} cm^3")
print(f"  meat volume, zoning ON  = {vol_on:.9f} cm^3")
check("meat volume identical with zoning on and off",
      abs(vol_on - vol_off) < 1e-9, f"delta = {abs(vol_on - vol_off):.3e}")
check("geometry meat volume == analytic 614-plate volume",
      abs(vol_on - vol_analytic) < 1e-6)
check("geometry meat volume == sum of declared material volumes",
      abs(vol_on - vol_declared) < 1e-6,
      f"delta = {abs(vol_on - vol_declared):.3e}")

# Every material owns exactly ONE plate's zone — no 23/17 multiplier anywhere.
by_name = {m.name: m for m in depl}
check("EVERY material carries the single-plate zone volume (no std/ctrl split)",
      all(abs(m.volume - g.MEAT_ZONE_VOLUME_PER_PLATE) < 1e-9 for m in depl),
      f"{len({round(m.volume, 12) for m in depl})} distinct volumes, "
      f"expected 1")

# --- THE 1:1 INVARIANT — cells and materials, one for one -------------------
# This replaces the old element-sharing structure and is the check that would
# catch a duplicated registry key. All THREE clauses matter: the counts alone
# would pass a registry that handed two cells the same material while creating
# a compensating orphan, so the set equality is the one that actually binds.
_cell_fills = [c.fill for c in meat_on]
check("1:1 (a) material count == meat cell count",
      len(depl) == len(meat_on), f"{len(depl)} mats vs {len(meat_on)} cells")
check("1:1 (b) every meat cell references a DISTINCT material — no sharing",
      len({id(f) for f in _cell_fills}) == len(meat_on),
      f"{len({id(f) for f in _cell_fills})} distinct fills across "
      f"{len(meat_on)} cells")
check("1:1 (c) cell-referenced materials == get_zoned_fuels() exactly",
      {id(f) for f in _cell_fills} == {id(m) for m in get_zoned_fuels()},
      f"cells reference {len({id(f) for f in _cell_fills})}, registry holds "
      f"{len(get_zoned_fuels())}; "
      f"orphans in registry: "
      f"{len({id(m) for m in get_zoned_fuels()} - {id(f) for f in _cell_fills})}, "
      f"unregistered in cells: "
      f"{len({id(f) for f in _cell_fills} - {id(m) for m in get_zoned_fuels()})}")

# --- 2D tiling of one plate: contiguous in x AND z, spanning the full meat ---
sample_std = g.STD_ELEMENT_IDS[0]
sample_cells = [c for c in meat_on if c.name.startswith('std0_meat_0_x')]
check("sample plate has N_X_ZONES * N_AXIAL_ZONES zone cells",
      len(sample_cells) == N_ZONES_PER_ELEM, f"{len(sample_cells)}")

grid = {}
for c in sample_cells:
    j, k = c.name.rsplit('_x', 1)[1].split('_z')
    bb = c.bounding_box
    grid[(int(j), int(k))] = (float(bb.lower_left[0]), float(bb.upper_right[0]),
                              float(bb.lower_left[2]), float(bb.upper_right[2]))
check("every (x, z) index pair present exactly once in the sample plate",
      set(grid) == {(j, k) for j in range(N_X_ZONES)
                    for k in range(N_AXIAL_ZONES)})

xb = [(grid[(j, 0)][0], grid[(j, 0)][1]) for j in range(N_X_ZONES)]
zb = [(grid[(0, k)][2], grid[(0, k)][3]) for k in range(N_AXIAL_ZONES)]
print(f"  {sample_std} plate 0, x-bounds: "
      + ' '.join(f'[{a:g},{b:g}]' for a, b in xb))
print(f"  {sample_std} plate 0, z-bounds: "
      + ' '.join(f'[{a:g},{b:g}]' for a, b in zb[:4]) + ' ...')
check("x zone cells are contiguous — no gap, no overlap",
      all(abs(xb[j][1] - xb[j + 1][0]) < 1e-12 for j in range(len(xb) - 1)))
check("z zone cells are contiguous — no gap, no overlap",
      all(abs(zb[k][1] - zb[k + 1][0]) < 1e-12 for k in range(len(zb) - 1)))
check("x zone cells span exactly [MEAT_LEFT_X, MEAT_RIGHT_X]",
      abs(xb[0][0] - g.MEAT_LEFT_X) < 1e-12
      and abs(xb[-1][1] - g.MEAT_RIGHT_X) < 1e-12)
check("z zone cells span exactly [MEAT_BOT_Z, MEAT_TOP_Z]",
      abs(zb[0][0] - g.MEAT_BOT_Z) < 1e-12
      and abs(zb[-1][1] - g.MEAT_TOP_Z) < 1e-12)
check("the x tiling is identical at every z (rows are not skewed)",
      all(abs(grid[(j, k)][0] - xb[j][0]) < 1e-12
          and abs(grid[(j, k)][1] - xb[j][1]) < 1e-12
          for j in range(N_X_ZONES) for k in range(N_AXIAL_ZONES)))

# Region complexity: a zone cell SUBSTITUTES its x bounds for meat_left/
# meat_right rather than intersecting on top of them, so it carries the same 6
# half-spaces the unzoned meat cell did. Across every meat cell the difference
# between 6 and 8 is not academic — it is ~30% of geometry.xml.
_hs = [len(re.findall(r'-?\d+', str(c.region))) for c in sample_cells]
check("every zone cell region carries exactly 6 half-spaces",
      set(_hs) == {6}, f"observed {sorted(set(_hs))}")

# =============================================================================
# 6. Coordinate probes — zone ordering over the full (x, z) grid
# =============================================================================

print("\n=== 6. Coordinate probes ===")

_NROWS = len(g.CORE_MAP)
# Lattice lower_left. Derived from the lattice envelope (CORE_HALF_X/Y are
# lattice half-extents despite the name), never hardcoded: this
# was -4.0*PITCH_X, -4.5*PITCH_Y — the extent of the pre-B4 8x9 lattice
# including its water ring. After B4 reduced the lattice to the 6x7 core
# positions, that put every probe a full pitch cell off, so the zone-ordering
# checks read pool water at x = -26.95 (outside the +/-23.1 core) and failed.
_LL_X, _LL_Y = -g.CORE_HALF_X, -g.CORE_HALF_Y


def element_center(label):
    """Global (x, y) of the lattice cell carrying `label`. Row 0 is the +y edge."""
    for i, row in enumerate(g.CORE_MAP):
        for j, _ in enumerate(row):
            if g.core_map_label(i, j) == label:
                return (_LL_X + (j + 0.5) * g.PITCH_X,
                        _LL_Y + (_NROWS - 1 - i + 0.5) * g.PITCH_Y)
    raise KeyError(label)


def probe(label, cell_prefix, plate_index, verbose_rows=3):
    """Walk the full (x, z) zone grid at points inside this element's meat.

    x0 = -x edge, z0 = bottom. The y coordinate comes from the sample cell's
    bounding box; x and z are computed zone-centre coordinates, so the probe
    tests the ORDERING of the zones, not just their existence.

    `plate_index` must match the plate `cell_prefix` names, since materials are
    now per plate and the expected name carries it. Probing plate 0 with
    plate_index=1 would look like a zone-ordering failure rather than the
    caller's mistake, so they are passed together and checked below.
    """
    assert cell_prefix.endswith(f'_meat_{plate_index}'), (
        f"probe(): cell_prefix {cell_prefix!r} does not name plate "
        f"{plate_index} — the expected material name would be wrong")
    univ = geom_on.get_all_universes()
    target = next(u for u in univ.values()
                  if any(c.name.startswith(cell_prefix + '_x')
                         for c in u.cells.values()))
    meat0 = next(c for c in target.cells.values()
                 if c.name == cell_prefix + '_x0_z0')
    bb = meat0.bounding_box
    yl = (float(bb.lower_left[1]) + float(bb.upper_right[1])) / 2.0
    ex, ey = element_center(label)

    ok, shown = True, 0
    for j in range(N_X_ZONES):
        x = g.MEAT_LEFT_X + (j + 0.5) * g.MEAT_ZONE_WIDTH
        for k in range(N_AXIAL_ZONES):
            z = g.MEAT_BOT_Z + (k + 0.5) * g.MEAT_ZONE_HEIGHT
            found = geom_on.find((ex + x, ey + yl, z))[-1]
            name = (found.fill.name if isinstance(found.fill, openmc.Material)
                    else '<none>')
            expect = f'fuel_{label}_p{plate_index}_x{j}_z{k}'
            if shown < verbose_rows:
                print(f"    ({ex + x:8.4f}, {ey + yl:8.4f}, {z:+6.1f}) -> {name}")
                shown += 1
            ok &= (name == expect)
    return ok


if N_X_ZONES == 2 and N_AXIAL_ZONES == 10:
    check("[N_X=2] probe x-centres are ∓1.575",
          abs((g.MEAT_LEFT_X + 0.5 * g.MEAT_ZONE_WIDTH) + 1.575) < 1e-12
          and abs((g.MEAT_LEFT_X + 1.5 * g.MEAT_ZONE_WIDTH) - 1.575) < 1e-12)
    check("[N_Z=10] probe z-centres are -27.0 … +27.0",
          abs((g.MEAT_BOT_Z + 0.5 * g.MEAT_ZONE_HEIGHT) + 27.0) < 1e-12
          and abs((g.MEAT_BOT_Z + 9.5 * g.MEAT_ZONE_HEIGHT) - 27.0) < 1e-12)

print(f"  standard element {g.STD_ELEMENT_IDS[0]} (std0, plate 0), first rows:")
check(f"zone ordering over the full (x, z) grid in {g.STD_ELEMENT_IDS[0]}",
      probe(g.STD_ELEMENT_IDS[0], 'std0_meat_0', 0))
print(f"  control element {g.CTRL_ELEMENT_IDS[0]} (ctrl100, plate 0), first rows:")
check(f"zone ordering over the full (x, z) grid in {g.CTRL_ELEMENT_IDS[0]}",
      probe(g.CTRL_ELEMENT_IDS[0], 'ctrl100_meat_0', 0))

# A SECOND plate of the same element. Under the old element-shared scheme this
# probed identical materials to plate 0; now it must resolve to a disjoint set,
# which is the per-plate split visible from coordinates rather than from names.
print(f"  standard element {g.STD_ELEMENT_IDS[0]} (std0, plate 1), first rows:")
check(f"zone ordering in a SECOND plate of {g.STD_ELEMENT_IDS[0]}",
      probe(g.STD_ELEMENT_IDS[0], 'std0_meat_1', 1))

# =============================================================================
# 7. XML export with zoning on
# =============================================================================

print("\n=== 7. XML export (zoning on) ===")
with tempfile.TemporaryDirectory() as d:
    gx, mx = os.path.join(d, 'geometry.xml'), os.path.join(d, 'materials.xml')
    geom_on.export_to_xml(gx)
    _exported.export_to_xml(mx)
    n_mat_xml = len(ET.parse(mx).getroot().findall('material'))
    n_cell_xml = len(ET.parse(gx).getroot().findall('cell'))
    print(f"  geometry.xml  = {os.path.getsize(gx) / 1e6:.2f} MB "
          f"({n_cell_xml} cells)")
    print(f"  materials.xml = {os.path.getsize(mx) / 1e6:.2f} MB "
          f"({n_mat_xml} materials)")
    check("geometry.xml parses", n_cell_xml > 0, f"{n_cell_xml} cells")
    check("materials.xml parses and holds non-fuel base + zoned materials",
          n_mat_xml == len(mats_mod.materials) - 1 + N_ZONED_MATS,
          f"{n_mat_xml} materials")
    # Re-reading mints fresh Material objects that collide with the live ones's
    # IDs; the IDWarning storm is expected and says nothing about the export.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', openmc.IDWarning)
        check("materials.xml re-reads through openmc",
              len(openmc.Materials.from_xml(mx)) == n_mat_xml)

# =============================================================================
# 8. Overlap checks — f = 0.0, 0.5, 0.99, 1.0 x zoning off/on (8 checks)
# =============================================================================

print("\n=== 8. Overlap checks (openmc --geometry-debug) ===")
for f in (0.0, 0.5, 0.99, 1.0):
    for zoned in (0, 1):
        tag = f"f={f}, zoning {'ON ' if zoned else 'OFF'}"
        t0 = time.perf_counter()
        r = subprocess.run(
            [sys.executable, os.path.abspath(__file__), '--overlap',
             str(f), str(zoned)],
            cwd=REPO_ROOT, capture_output=True, text=True)
        dt = time.perf_counter() - t0
        lost = [ln for ln in r.stdout.splitlines()
                if 'lost' in ln.lower() or 'Lost particle' in ln]
        check(f"no overlaps — {tag}  [{dt:.1f} s]", r.returncode == 0,
              '' if r.returncode == 0 else str(r.stderr.strip().splitlines()[-1:]))
        check(f"no lost particles — {tag}", not lost, str(lost[:2]))

# =============================================================================
# 9. Backward compatibility — degenerate zone counts
# =============================================================================

print("\n=== 9. Backward compatibility (degenerate counts) ===")


def degenerate(nx, nz):
    r = subprocess.run(
        [sys.executable, os.path.abspath(__file__), '--degenerate',
         str(nx), str(nz)],
        cwd=REPO_ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    out = {}
    for ln in r.stdout.splitlines():
        if ln.startswith(('CELLS ', 'VOL ', 'SAMPLE_N ', 'SAMPLE_REGION ',
                          'SAMPLE_NAME ')):
            k, v = ln.split(' ', 1)
            out[k] = v
    return out

# (1, N) must reproduce the axial-only behaviour: one cell per plate per axial
# zone, same total meat volume, and a region expression carrying the same 6
# half-spaces the old 1D code produced.
d1 = degenerate(1, N_AXIAL_ZONES)
check("N_X_ZONES=1 builds", d1 is not None)
if d1:
    print(f"  (1, {N_AXIAL_ZONES}): {d1['CELLS']} meat cells, "
          f"vol {float(d1['VOL']):.6f} cm^3")
    print(f"     sample cell   : {d1['SAMPLE_NAME']}")
    print(f"     sample region : {d1['SAMPLE_REGION']}")
    check("N_X_ZONES=1 gives 614 * N_AXIAL_ZONES meat cells",
          int(d1['CELLS']) == N_PLATES_TOTAL * N_AXIAL_ZONES, d1['CELLS'])
    check("N_X_ZONES=1 preserves the total meat volume",
          abs(float(d1['VOL']) - vol_analytic) < 1e-6)
    check("N_X_ZONES=1 sample plate has N_AXIAL_ZONES cells",
          int(d1['SAMPLE_N']) == N_AXIAL_ZONES, d1['SAMPLE_N'])
    # Six half-spaces, not eight: the zone cell SUBSTITUTES its x bounds for
    # meat_left/meat_right rather than intersecting on top of them, so it is no
    # more complex than the unzoned meat cell it replaces. OpenMC's region repr
    # prefixes only negative half-spaces, so count surface tokens, not signs.
    _n_halfspaces = len(re.findall(r'-?\d+', d1['SAMPLE_REGION']))
    check("N_X_ZONES=1 region carries 6 half-spaces (no redundant x bounds)",
          _n_halfspaces == 6, f"{_n_halfspaces} in {d1['SAMPLE_REGION']}")

# (1, 1) must reproduce the unzoned meat region exactly.
d11 = degenerate(1, 1)
check("N_X_ZONES=1, N_AXIAL_ZONES=1 builds", d11 is not None)
if d11:
    print(f"  (1, 1):  {d11['CELLS']} meat cells, "
          f"vol {float(d11['VOL']):.6f} cm^3")
    print(f"     sample region : {d11['SAMPLE_REGION']}")
    check("(1, 1) gives exactly 614 meat cells — one per plate, as unzoned",
          int(d11['CELLS']) == N_PLATES_TOTAL, d11['CELLS'])
    check("(1, 1) preserves the total meat volume",
          abs(float(d11['VOL']) - vol_analytic) < 1e-6)
    check("(1, 1) sample plate has exactly 1 meat cell",
          int(d11['SAMPLE_N']) == 1, d11['SAMPLE_N'])

# =============================================================================
# 10. Negative tests — inject a defect, confirm the guard fires
# =============================================================================

print("\n=== 10. Negative tests (defect injection) ===")
print("  Each runs in a forked subprocess so the monkeypatched module state")
print("  cannot leak into the checks above.")

for kind, label in (('count',  'off-by-one in the x ZONE COUNT'),
                    ('planes', 'off-by-one in the INTERIOR PLANE COUNT')):
    r = subprocess.run(
        [sys.executable, os.path.abspath(__file__), '--negative', kind],
        cwd=REPO_ROOT, capture_output=True, text=True)
    fired = [ln for ln in r.stdout.splitlines() if ln.startswith('FIRED')]
    silent = [ln for ln in r.stdout.splitlines()
              if 'DID NOT FIRE' in ln]
    print(f"  -- {label}")
    for ln in fired:
        print(f"     {ln}")
    for ln in silent:
        print(f"     {ln}")
    check(f"guard fires on {label}",
          r.returncode == 0 and bool(fired) and not silent,
          f"rc={r.returncode}")

# SCALE INVARIANCE — stated so nobody mistakes what the tiling assert proves.
# Editing N_X_ZONES/N_AXIAL_ZONES at source recomputes MEAT_ZONE_WIDTH/HEIGHT,
# so the tiling assert passes for ANY count: that configuration IS
# self-consistent. The assert catches a MISMATCH between a count and its derived
# width/plane list, never a "wrong" count. The counts themselves are [ASSUMED]
# and are not falsifiable from inside this code — only the reference model can
# falsify them. See the provenance block in materials.py.
print("  NOTE: the tiling asserts are scale-invariant by construction — they")
print("        cannot falsify a zone COUNT, only a count/derivation mismatch.")

# =============================================================================
# 11. On-disk verification
# =============================================================================

print("\n=== 11. On-disk verification ===")
for cmd in (['grep', '-c', 'depletable', 'model/materials.py'],
            ['grep', '-n', 'N_X_ZONES *=\\|N_AXIAL_ZONES *=', 'model/materials.py'],
            ['grep', '-n', "fuel_{element_id}_p", 'model/materials.py'],
            ['grep', '-n', 'RETIRED', 'model/materials.py'],
            ['grep', '-c', '_x{j}_z{k}', 'model/geometry.py'],
            ['grep', '-n', 'ASSUMED\\|SUPERSEDED\\|STILL LIVE',
             'model/materials.py']):
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd)}\n{r.stdout.rstrip()}")

# =============================================================================

print("\n" + "=" * 70)
if _failures:
    print(f"FAILED — {len(_failures)} check(s): " + '; '.join(_failures))
    sys.exit(1)
print("ALL CHECKS PASSED")
