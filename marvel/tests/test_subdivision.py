""" Tests for marvel.subdivision: pieces tile the annulus with equal volumes. """

import numpy as np
import openmc

from marvel.subdivision import ring_radii, subdivide_annulus


def _check_tiling(r_in, r_out, n_rad, n_azi, n_ax, n_points=20000, seed=1):
    planes = [openmc.ZPlane(z0=z) for z in np.linspace(0.0, 10.0, n_ax + 1)]
    pieces = subdivide_annulus(r_in, r_out, planes, n_rad, n_azi)
    assert len(pieces) == n_rad * n_azi * n_ax

    rng = np.random.default_rng(seed)
    counts = np.zeros(len(pieces), dtype=int)
    for _ in range(n_points):
        # Uniform in area over the annulus, uniform in z.
        r = np.sqrt(rng.uniform(r_in**2, r_out**2))
        phi = rng.uniform(0.0, 2 * np.pi)
        point = (r * np.cos(phi), r * np.sin(phi), rng.uniform(0.0, 10.0))
        hits = [i for i, (region, _) in enumerate(pieces) if point in region]
        assert len(hits) == 1, f"point {point} in {len(hits)} pieces"
        counts[hits[0]] += 1

    expected = n_points / len(pieces)
    # Equal-volume pieces: every count within 5 sigma of the mean.
    assert np.all(np.abs(counts - expected) < 5 * np.sqrt(expected)), counts


def test_ring_radii_equal_area():
    radii = ring_radii(0.3, 1.7, 4)
    areas = np.diff(np.square(radii))
    assert np.allclose(areas, areas[0])
    assert radii[0] == 0.3 and np.isclose(radii[-1], 1.7)


def test_default_split():
    _check_tiling(0.3, 1.7, 1, 1, 10)


def test_solid_cylinder_split():
    _check_tiling(0.0, 1.7, 3, 1, 2)


def test_two_sectors():
    _check_tiling(0.3, 1.7, 1, 2, 1)


def test_general_split():
    _check_tiling(0.3, 1.7, 2, 6, 3)


if __name__ == '__main__':
    for name, func in list(globals().items()):
        if name.startswith('test_'):
            func()
            print(f'{name}: ok')
