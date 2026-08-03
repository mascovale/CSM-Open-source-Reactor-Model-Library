"""
tests/check_depletion_zoning.py
-------------------------------
Structural verification of the fuel-meat depletion zoning (Phase 1.5).

Zoning splits every fuel meat cell into N_AXIAL_ZONES axial cells, with one
depletable material per element per zone shared across all plates of that
element (28 elements x N zones). This script checks the scaffolding only — it
configures and runs NO depletion, and performs NO eigenvalue calculation. The
overlap checks use `model.run(geometry_debug=True)` (= `openmc --geometry-debug`),
an overlap scan, matching the idiom already in geometry.py's __main__ block.

Every assertion is written against N_AXIAL_ZONES; the benchmark literals
(3.8556 / 88.6788 / 65.5452 / 11836.692 cm^3) are asserted only under an
N_AXIAL_ZONES == 5 guard, so changing the zone count breaks nothing here.

Run from the repo root:
    conda activate openmc
    python tests/check_depletion_zoning.py

Internal mode (used to isolate each overlap check in its own process, so
material/surface ID spaces never cross-contaminate):
    python tests/check_depletion_zoning.py --overlap <f> <0|1>
"""

import os
import subprocess
import sys
import tempfile
import warnings
import xml.etree.ElementTree as ET

import numpy as np

THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, 'model'))

import openmc

import materials as mats_mod
import geometry as g
from materials import N_AXIAL_ZONES, get_zoned_fuels


N_STD, N_CTRL = 23, 5
N_PLATES_TOTAL = N_STD * g.N_PLATES_STD + N_CTRL * g.N_CTRL_FUEL_PLATES  # 614
N_ZONED_MATS   = (N_STD + N_CTRL) * N_AXIAL_ZONES                        # 140

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
# Internal mode — one overlap check, one process
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


if len(sys.argv) > 1 and sys.argv[1] == '--overlap':
    _run_one_overlap(float(sys.argv[2]), bool(int(sys.argv[3])))
    sys.exit(0)


# =============================================================================
# 1. Zone constants and tiling
# =============================================================================

print("\n=== 1. Zone constants and tiling ===")
print(f"  N_AXIAL_ZONES              = {N_AXIAL_ZONES}")
print(f"  meat z-range               = [{g.MEAT_BOT_Z}, {g.MEAT_TOP_Z}] cm "
      f"(height {g.MEAT_HEIGHT} cm)")
print(f"  MEAT_ZONE_HEIGHT           = {g.MEAT_ZONE_HEIGHT} cm")
print(f"  MEAT_ZONE_VOLUME_PER_PLATE = {g.MEAT_ZONE_VOLUME_PER_PLATE} cm^3")

check("zones tile the meat height exactly",
      abs(g.MEAT_BOT_Z + N_AXIAL_ZONES * g.MEAT_ZONE_HEIGHT - g.MEAT_TOP_Z) < 1e-12)
check("interior zone plane count == N_AXIAL_ZONES - 1",
      len(g.fuel_zone_planes()) == N_AXIAL_ZONES - 1)
check("zone planes are created once (memoized)",
      g.fuel_zone_planes() is g.fuel_zone_planes())
check("plate count == 23*23 + 5*17 == 614", N_PLATES_TOTAL == 614,
      f"{N_PLATES_TOTAL}")

if N_AXIAL_ZONES == 5:
    check("[N=5] zone height == 12.0 cm", abs(g.MEAT_ZONE_HEIGHT - 12.0) < 1e-12)
    check("[N=5] one plate, one zone == 3.8556 cm^3",
          abs(g.MEAT_ZONE_VOLUME_PER_PLATE - 3.8556) < 1e-9,
          f"{g.MEAT_ZONE_VOLUME_PER_PLATE:.6f}")
    check("[N=5] std element zone (23 plates) == 88.6788 cm^3",
          abs(g.N_PLATES_STD * g.MEAT_ZONE_VOLUME_PER_PLATE - 88.6788) < 1e-9)
    check("[N=5] ctrl element zone (17 plates) == 65.5452 cm^3",
          abs(g.N_CTRL_FUEL_PLATES * g.MEAT_ZONE_VOLUME_PER_PLATE - 65.5452) < 1e-9)

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
geom_off = g.build_core_geometry(withdrawn_fraction=1.0, depletion_zoning=False)
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

# =============================================================================
# 4. Zoning ON — material inventory
# =============================================================================

print("\n=== 4. Zoning ON — materials ===")
geom_on = g.build_core_geometry(withdrawn_fraction=1.0, depletion_zoning=True)
mats_on = list(geom_on.get_all_materials().values())
depl = [m for m in mats_on if m.depletable]

check(f"exactly {N_ZONED_MATS} = 28 * N_AXIAL_ZONES depletable materials",
      len(depl) == N_ZONED_MATS, f"{len(depl)}")
check("every depletable material has a non-None volume",
      all(m.volume is not None for m in depl))
check("no two zoned materials share a name",
      len({m.name for m in depl}) == len(depl))
check("the zoned materials are the only depletable materials in the geometry",
      len([m for m in mats_on if m.depletable]) == N_ZONED_MATS)
check("registry and geometry agree on the material set",
      {m.id for m in get_zoned_fuels()} == {m.id for m in depl})

# The base fuel must fill NOTHING when zoned — a surviving base-fuel cell would
# mean the axial split missed a meat cell, and the volume identity below would
# then need explaining. core.build_model() raises on this; assert it here too.
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

vol_declared = sum(m.volume for m in depl)
print(f"  declared volume sum = {vol_declared:.6f} cm^3")
check("declared volume sum == 614 * MEAT_THICK * MEAT_WIDTH * MEAT_HEIGHT",
      abs(vol_declared - N_PLATES_TOTAL * g.MEAT_THICK * g.MEAT_WIDTH
          * g.MEAT_HEIGHT) < 1e-6)
if N_AXIAL_ZONES == 5:
    check("[N=5] declared volume sum == 11836.692 cm^3",
          abs(vol_declared - 11836.692) < 1e-6, f"{vol_declared:.6f}")

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

check(f"{N_PLATES_TOTAL} * {N_AXIAL_ZONES} = {N_PLATES_TOTAL * N_AXIAL_ZONES} "
      f"meat cells", len(meat_on) == N_PLATES_TOTAL * N_AXIAL_ZONES,
      f"{len(meat_on)}")
print(f"  meat volume, zoning OFF = {vol_off:.9f} cm^3")
print(f"  meat volume, zoning ON  = {vol_on:.9f} cm^3")
check("meat volume identical with zoning on and off",
      abs(vol_on - vol_off) < 1e-9, f"delta = {abs(vol_on - vol_off):.3e}")
check("geometry meat volume == analytic 614-plate volume",
      abs(vol_on - N_PLATES_TOTAL * g.MEAT_THICK * g.MEAT_WIDTH
          * g.MEAT_HEIGHT) < 1e-6)
check("geometry meat volume == sum of declared material volumes",
      abs(vol_on - vol_declared) < 1e-6,
      f"delta = {abs(vol_on - vol_declared):.3e}")

# each element's materials carry the right per-element plate count
_std_zone_vol  = g.N_PLATES_STD * g.MEAT_ZONE_VOLUME_PER_PLATE
_ctrl_zone_vol = g.N_CTRL_FUEL_PLATES * g.MEAT_ZONE_VOLUME_PER_PLATE
by_name = {m.name: m for m in depl}
check("standard-element materials carry the 23-plate zone volume",
      all(abs(by_name[f'fuel_{e}_z{k}'].volume - _std_zone_vol) < 1e-9
          for e in g.STD_ELEMENT_IDS for k in range(N_AXIAL_ZONES)))
check("control-element materials carry the 17-plate zone volume",
      all(abs(by_name[f'fuel_{e}_z{k}'].volume - _ctrl_zone_vol) < 1e-9
          for e in g.CTRL_ELEMENT_IDS for k in range(N_AXIAL_ZONES)))

# zone cells of one plate are contiguous and span exactly the meat height
sample_std = g.STD_ELEMENT_IDS[0]
sample_cells = sorted(
    [c for c in meat_on
     if c.name.startswith('std0_meat_0_z')],
    key=lambda c: c.bounding_box.lower_left[2])
zbounds = [(float(c.bounding_box.lower_left[2]),
            float(c.bounding_box.upper_right[2])) for c in sample_cells]
print(f"  {sample_std} plate 0 zone z-bounds: "
      + ' '.join(f'[{a:g},{b:g}]' for a, b in zbounds))
check("sample plate has N_AXIAL_ZONES zone cells",
      len(zbounds) == N_AXIAL_ZONES, f"{len(zbounds)}")
check("zone cells are contiguous — no gap, no overlap",
      all(abs(zbounds[k][1] - zbounds[k + 1][0]) < 1e-12
          for k in range(len(zbounds) - 1)))
check("zone cells span exactly [MEAT_BOT_Z, MEAT_TOP_Z]",
      abs(zbounds[0][0] - g.MEAT_BOT_Z) < 1e-12
      and abs(zbounds[-1][1] - g.MEAT_TOP_Z) < 1e-12)

# =============================================================================
# 6. Coordinate probes — zone ordering, bottom-up
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


def probe(label, cell_prefix):
    """Walk z through every zone at a point inside this element's meat."""
    univ = geom_on.get_all_universes()
    target = next(u for u in univ.values()
                  if any(c.name.startswith(cell_prefix + '_z')
                         for c in u.cells.values()))
    meat0 = next(c for c in target.cells.values()
                 if c.name == cell_prefix + '_z0')
    bb = meat0.bounding_box
    xl, yl = ((float(bb.lower_left[0]) + float(bb.upper_right[0])) / 2.0,
              (float(bb.lower_left[1]) + float(bb.upper_right[1])) / 2.0)
    ex, ey = element_center(label)

    ok = True
    for k in range(N_AXIAL_ZONES):
        z = g.MEAT_BOT_Z + (k + 0.5) * g.MEAT_ZONE_HEIGHT
        found = geom_on.find((ex + xl, ey + yl, z))[-1]
        name = found.fill.name if isinstance(found.fill, openmc.Material) else '<none>'
        expect = f'fuel_{label}_z{k}'
        print(f"    ({ex + xl:8.4f}, {ey + yl:8.4f}, {z:+6.1f}) -> {name}")
        ok &= (name == expect)
    return ok


if N_AXIAL_ZONES == 5:
    check("[N=5] probe z-values are -24, -12, 0, +12, +24",
          [g.MEAT_BOT_Z + (k + 0.5) * g.MEAT_ZONE_HEIGHT
           for k in range(5)] == [-24.0, -12.0, 0.0, 12.0, 24.0])

print(f"  standard element {g.STD_ELEMENT_IDS[0]} (std0, plate 0):")
check(f"zone ordering bottom-up in {g.STD_ELEMENT_IDS[0]}",
      probe(g.STD_ELEMENT_IDS[0], 'std0_meat_0'))
print(f"  control element {g.CTRL_ELEMENT_IDS[0]} (ctrl100, plate 0):")
check(f"zone ordering bottom-up in {g.CTRL_ELEMENT_IDS[0]}",
      probe(g.CTRL_ELEMENT_IDS[0], 'ctrl100_meat_0'))

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
# 8. Overlap checks — f = 0.0, 0.5, 1.0 x zoning off/on (6 checks)
# =============================================================================

print("\n=== 8. Overlap checks (openmc --geometry-debug) ===")
for f in (0.0, 0.5, 1.0):
    for zoned in (0, 1):
        tag = f"f={f}, zoning {'ON ' if zoned else 'OFF'}"
        r = subprocess.run(
            [sys.executable, os.path.abspath(__file__), '--overlap',
             str(f), str(zoned)],
            cwd=REPO_ROOT, capture_output=True, text=True)
        ok = r.returncode == 0 and 'overlap' not in r.stdout.lower().replace(
            'overlap-checking', '').replace('check overlaps', '')
        check(f"no overlaps — {tag}", r.returncode == 0,
              '' if r.returncode == 0 else r.stderr.strip().splitlines()[-1:])

# =============================================================================
# 9. On-disk verification
# =============================================================================

print("\n=== 9. On-disk verification ===")
for cmd in (['grep', '-c', 'depletable', 'model/materials.py'],
            ['grep', '-rn', 'fuel_.*_z', 'model/materials.py'],
            ['grep', '-rc', '_z{k}', 'model/geometry.py']):
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd)}\n{r.stdout.rstrip()}")

# =============================================================================

print("\n" + "=" * 70)
if _failures:
    print(f"FAILED — {len(_failures)} check(s): " + '; '.join(_failures))
    sys.exit(1)
print("ALL CHECKS PASSED")
