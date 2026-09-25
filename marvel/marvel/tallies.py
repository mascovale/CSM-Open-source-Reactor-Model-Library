""" Default tallies of the MARVEL model.

Fission-matrix tallies follow the JSI TRIGA model approach: nu-fission scored
in every fuel cell, filtered by the fuel cell the neutron was born in, gives
the raw fission-matrix elements a_ij.

Classes:
    MarvelTallies: openmc.Tallies built for a Reactor.
"""

import openmc


class MarvelTallies(openmc.Tallies):
    """ Default tallies for a MARVEL reactor model.

    Tally sets (select with `tallies`):
        'fm_raw': nu-fission by [CellFilter(fuel cells), CellBornFilter(fuel
            cells)] - raw fission-matrix elements.
        'nu-fission': nu-fission per fuel cell, plus 'nu-fission-tot' over
            the whole model.

    Attributes:
        fuel_cell_ids (list of int): IDs of the reactor's fuel cells, in
            `reactor.fuel_cells` order (fission-matrix index order).
    """

    DEFAULT_TALLIES = ('fm_raw', 'nu-fission')
    ALLOWED_TALLIES = DEFAULT_TALLIES

    def __init__(self, reactor, tallies=None):
        """
        Args:
            reactor (Reactor): reactor providing `fuel_cells`.
            tallies (list of str, optional): tally sets to create; None for
                `DEFAULT_TALLIES`, [] for none.
        """
        super().__init__()
        names = list(self.DEFAULT_TALLIES if tallies is None else tallies)
        unknown = set(names) - set(self.ALLOWED_TALLIES)
        if unknown:
            raise ValueError(f"Unknown tallies {sorted(unknown)}; allowed: "
                             f"{self.ALLOWED_TALLIES}")
        self.fuel_cell_ids = [cell.id for cell in reactor.fuel_cells]
        builders = {
            'fm_raw': self._add_fm_raw,
            'nu-fission': self._add_nu_fission,
        }
        for name in names:
            builders[name](reactor)

    def _add_fm_raw(self, reactor):
        tally = openmc.Tally(name='fm_raw')
        tally.filters = [openmc.CellFilter(self.fuel_cell_ids),
                         openmc.CellBornFilter(self.fuel_cell_ids)]
        tally.scores = ['nu-fission']
        self.append(tally)

    def _add_nu_fission(self, reactor):
        tally = openmc.Tally(name='nu-fission')
        tally.filters = [openmc.CellFilter(self.fuel_cell_ids)]
        tally.scores = ['nu-fission']
        self.append(tally)
        total = openmc.Tally(name='nu-fission-tot')
        total.scores = ['nu-fission']
        self.append(total)
