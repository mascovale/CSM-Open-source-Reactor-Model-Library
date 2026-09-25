""" Tests for the fission-matrix tallies and fixed-source run generator on a
toy two-rod model standing in for the MARVEL Reactor interface. """

import os
import subprocess
import tempfile

import numpy as np
import openmc

from marvel import FissionMatrixRuns, FuelCellInfo, MarvelTallies, subdivide_annulus


class ToyReactor:
    """ Two bare fuel rods in water, fuel split 2 radial x 2 azimuthal x 2 axial. """

    R_FUEL, Z_TOP, PITCH = 1.5, 20.0, 4.0

    def __init__(self):
        fuel = openmc.Material(name='fuel')
        fuel.add_nuclide('U235', 0.2)
        fuel.add_nuclide('U238', 0.8)
        fuel.add_element('O', 2.0)
        fuel.set_density('g/cm3', 10.0)
        water = openmc.Material(name='water')
        water.add_nuclide('H1', 2.0)
        water.add_nuclide('O16', 1.0)
        water.set_density('g/cm3', 1.0)

        planes = [openmc.ZPlane(z0=z) for z in (0.0, 10.0, self.Z_TOP)]
        self.fuel_cells, self._info = [], {}
        rod_cells = []
        mid = openmc.XPlane(0.0)
        for rod, x in enumerate((-self.PITCH / 2, self.PITCH / 2)):
            cells = []
            for region, (i_rad, i_azi, i_ax) in subdivide_annulus(0.0, self.R_FUEL, planes, 2, 2):
                cell = openmc.Cell(fill=fuel, region=region)
                cells.append(cell)
                self.fuel_cells.append(cell)
                self._info[cell.id] = FuelCellInfo(
                    rod, i_rad, i_azi, i_ax, x, 0.0,
                    planes[i_ax].z0, planes[i_ax + 1].z0, self.R_FUEL)
            outside = ~openmc.Union([c.region for c in cells])
            cells.append(openmc.Cell(fill=water, region=outside))
            universe = openmc.Universe(cells=cells)
            box = -mid if rod == 0 else +mid
            rod_cell = openmc.Cell(fill=universe, region=box)
            rod_cell.translation = (x, 0, 0)
            rod_cells.append(rod_cell)

        boundary = openmc.model.RectangularParallelepiped(
            -self.PITCH, self.PITCH, -self.PITCH / 2, self.PITCH / 2, -1.0, self.Z_TOP + 1,
            boundary_type='vacuum')
        for cell in rod_cells:
            cell.region &= -boundary
        root = openmc.Universe(cells=rod_cells)
        self.model = openmc.Model(geometry=openmc.Geometry(root),
                                  materials=openmc.Materials([fuel, water]))
        self.model.tallies = MarvelTallies(self)

    def fuel_cell_info(self, cell):
        return self._info[cell.id]


def test_tallies():
    reactor = ToyReactor()
    names = [t.name for t in reactor.model.tallies]
    assert names == ['fm_raw', 'nu-fission', 'nu-fission-tot']
    fm = reactor.model.tallies[0]
    assert len(fm.filters[0].bins) == len(fm.filters[1].bins) == 16


def test_generate_and_sample():
    reactor = ToyReactor()
    with tempfile.TemporaryDirectory() as tmp:
        local_dir = FissionMatrixRuns(reactor).generate('local', os.path.join(tmp, 'local'))
        assert len([d for d in os.listdir(local_dir) if d.startswith('source_')]) == 16
        assert os.path.exists(os.path.join(local_dir, 'submit_fm_local.sh'))

        global_dir = FissionMatrixRuns(reactor).generate(
            'global', os.path.join(tmp, 'global'), particles=1600, batches=2, slurm=False)
        # Tiny run to prove every per-cell source samples inside its own cell.
        subprocess.run(['openmc', '-s', '2'], cwd=global_dir, check=True,
                       capture_output=True)
        with openmc.StatePoint(os.path.join(global_dir, 'statepoint.2.h5')) as sp:
            fm = sp.get_tally(name='fm_raw').mean.reshape(16, 16)
        # Every source cell must produce fissions (columns = born cell).
        assert np.all(fm.sum(axis=0) > 0), fm.sum(axis=0)


if __name__ == '__main__':
    for name, func in list(globals().items()):
        if name.startswith('test_'):
            func()
            print(f'{name}: ok')
