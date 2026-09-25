""" Shared building blocks for MARVEL model components.

Classes:
    FuelCellInfo: where a single fuel cell sits in the core and its extent.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FuelCellInfo:
    """ Location and extent of one fuel cell (one radial ring x azimuthal
    sector x axial segment of one fuel rod), in global coordinates.

    Attributes:
        rod (int): fuel rod index in the core (0-based).
        radial (int): radial ring index, 0 innermost.
        azimuthal (int): azimuthal sector index, 0 starting at +x.
        axial (int): axial segment index, 0 at the bottom.
        x (float): rod axis x position [cm].
        y (float): rod axis y position [cm].
        z_bot (float): cell bottom elevation [cm].
        z_top (float): cell top elevation [cm].
        r_out (float): outer radius of the rod's fuel [cm] (bounds the cell).
    """
    rod: int
    radial: int
    azimuthal: int
    axial: int
    x: float
    y: float
    z_bot: float
    z_top: float
    r_out: float
