""" Radial, azimuthal and axial subdivision of cylindrical fuel regions.

Every fuel cell of the MARVEL model is one piece of a fuel annulus split into
`n_radial` equal-area rings, `n_azimuthal` equal-angle sectors and one cell
per axial segment. Regions are built in the local (rod universe) frame, with
the rod axis along z through the origin.

Functions:
    ring_radii: equal-area ring boundary radii of an annulus.
    sector_regions: equal-angle azimuthal sector regions about the z axis.
    subdivide_annulus: cells-to-be (region + index) of a subdivided annulus.
"""

import math

import openmc

# Angle (degrees, counterclockwise from +x) of the first azimuthal sector
# boundary. 0 puts the first boundary on the +x axis.
DEFAULT_AZIMUTHAL_OFFSET = 0.0


def ring_radii(r_in, r_out, n_radial):
    """ Boundary radii splitting an annulus into equal-area rings.

    Args:
        r_in (float): inner radius [cm] (0 for a solid cylinder).
        r_out (float): outer radius [cm].
        n_radial (int): number of rings (>= 1).

    Returns:
        list of float: `n_radial + 1` radii from `r_in` to `r_out`.
    """
    if n_radial < 1:
        raise ValueError(f"n_radial must be >= 1 (got {n_radial})")
    if not 0.0 <= r_in < r_out:
        raise ValueError(f"Need 0 <= r_in < r_out (got {r_in}, {r_out})")
    area = r_out**2 - r_in**2
    return [math.sqrt(r_in**2 + area * k / n_radial) for k in range(n_radial + 1)]


def _radial_plane(theta_deg):
    """ Plane through the z axis at angle `theta_deg`, with its positive side
    counterclockwise of that angle. """
    theta = math.radians(theta_deg)
    return openmc.Plane(a=-math.sin(theta), b=math.cos(theta), c=0.0, d=0.0)


def sector_regions(n_azimuthal, offset=DEFAULT_AZIMUTHAL_OFFSET):
    """ Equal-angle azimuthal sectors about the z axis.

    Sector j spans [offset + j*360/n, offset + (j+1)*360/n) degrees,
    counterclockwise from +x.

    Args:
        n_azimuthal (int): number of sectors (>= 1).
        offset (float, optional): angle of the first boundary [deg].

    Returns:
        list: `n_azimuthal` openmc.Region objects, or [None] for a single
        (unsplit) sector.
    """
    if n_azimuthal < 1:
        raise ValueError(f"n_azimuthal must be >= 1 (got {n_azimuthal})")
    if n_azimuthal == 1:
        return [None]
    width = 360.0 / n_azimuthal
    planes = [_radial_plane(offset + j * width) for j in range(n_azimuthal)]
    if n_azimuthal == 2:
        return [+planes[0], -planes[0]]
    # Sectors narrower than 180 degrees are the intersection of two
    # half-spaces: counterclockwise of their start, clockwise of their end.
    return [+planes[j] & -planes[(j + 1) % n_azimuthal] for j in range(n_azimuthal)]


def subdivide_annulus(r_in, r_out, z_planes, n_radial=1, n_azimuthal=1,
                      azimuthal_offset=DEFAULT_AZIMUTHAL_OFFSET):
    """ Splits a (possibly solid) cylindrical annulus into cell regions.

    Args:
        r_in (float): inner radius [cm]; 0 for a solid cylinder.
        r_out (float): outer radius [cm].
        z_planes (list of openmc.ZPlane): ordered axial boundaries, bottom to
            top; one axial segment per consecutive pair.
        n_radial (int, optional): equal-area radial rings (default 1).
        n_azimuthal (int, optional): equal-angle sectors (default 1).
        azimuthal_offset (float, optional): first sector boundary [deg].

    Returns:
        list of tuple: (region, (i_radial, i_azimuthal, i_axial)) for every
        piece, indices starting at 0, ordered axial-major then radial then
        azimuthal. Ring 0 is the innermost; axial 0 is the bottom segment.
    """
    radii = ring_radii(r_in, r_out, n_radial)
    cylinders = [openmc.ZCylinder(r=r) if r > 0 else None for r in radii]
    sectors = sector_regions(n_azimuthal, azimuthal_offset)

    pieces = []
    for i_ax, (z_bot, z_top) in enumerate(zip(z_planes[:-1], z_planes[1:])):
        axial = +z_bot & -z_top
        for i_rad in range(n_radial):
            ring = -cylinders[i_rad + 1] & axial
            if cylinders[i_rad] is not None:
                ring = +cylinders[i_rad] & ring
            for i_azi, sector in enumerate(sectors):
                region = ring if sector is None else ring & sector
                pieces.append((region, (i_rad, i_azi, i_ax)))
    return pieces
