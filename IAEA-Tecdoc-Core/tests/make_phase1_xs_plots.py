"""
make_phase1_xs_plots.py
-----------------------
Regenerates the Phase 1 geometry-finalization cross-section plots in plots/.

These are VERIFICATION plots for the B1-B4 geometry changes, not manuscript
figures — the manuscript figures live in figures/ and are built by
figures/make_figures.py under a different set of typographic constraints.

Written as a script rather than by hand so the committed PNGs in plots/ can be
reproduced and diffed against a later geometry. Every bound is taken from
geometry.py constants; nothing here restates a dimension.

    python tests/make_phase1_xs_plots.py

Panels, all at f = 0.0 (blades fully INSERTED — the case the A4 resolution
governs):

  phase1_xs1_xy_full_z0     XY at z=0, the whole model including the 38.5 cm
                            pool and the vacuum boundary (B4).
  phase1_xs2_xy_zoom_meat   XY over one standard element's pitch cell, at a
                            resolution that resolves the 0.051 cm meat. The
                            full-core view above cannot.
  phase1_xs3_xz_ctrl_full   XZ through a control element, cut through the
                            absorber slot rather than y=0 — an axial slice of a
                            control element that misses the blade is the wrong
                            slice.
  phase1_xs4_xz_clad_endbox XZ zoom on the +30 / +31 / +45 interfaces: the 1 cm
                            unfueled clad extension, the 14 cm end-box, and the
                            A4 coolant band in the slot (B1).
"""
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, 'model'))

import openmc
import geometry as g
from materials import materials

OUT_DIR = os.path.join(REPO_ROOT, 'plots')

# Distinct in colour AND in luminance, so the panels survive greyscale print.
COLORS = {
    g.fuel:          (200,  60,  60),
    g.clad:          (150, 150, 160),
    g.water:         (120, 170, 235),   # 294 K pool / bulk
    g.water_core:    ( 60, 110, 200),   # 316.8 K core coolant
    g.b4c:           ( 30,  30,  30),
    g.graphite:      (110, 110, 110),
    g.aluminum:      (205, 205, 210),
    g.end_box_homog: (170, 190, 170),
}

WITHDRAWN_FRACTION = 0.0


def _plot(name, basis, origin, width, px):
    p = openmc.Plot()
    p.filename = name
    p.basis    = basis
    p.origin   = origin
    p.width    = width
    p.pixels   = px
    p.color_by = 'material'
    p.colors   = COLORS
    return p


def build_plots():
    """The four verification panels, all bounds derived from geometry.py."""
    # 1. Whole model in XY, pool included.
    w_full = (2 * g.POOL_HALF_X, 2 * g.POOL_HALF_Y)
    p1 = _plot('phase1_xs1_xy_full_z0', 'xy', (0.0, 0.0, 0.0), w_full,
               (1400, int(1400 * w_full[1] / w_full[0])))

    # 2. One standard element's pitch cell, fine enough for the 0.051 cm meat.
    row, col = g._first_position('S')
    ex, ey = g._lattice_center(row, col)
    p2 = _plot('phase1_xs2_xy_zoom_meat', 'xy', (ex, ey, 0.0),
               (g.PITCH_X, g.PITCH_Y), (2400, 2400))

    # 3. XZ through a control element, cut through the absorber slot. The slot
    #    offset is built outward from the follower stack exactly as
    #    make_control_fuel_element lays the end block out.
    row, col = g._first_position('C')
    cx, cy = g._lattice_center(row, col)
    slot_y = cy - (g.CTRL_FUEL_STACK_HALF + g.CTRL_FEEDER_CHANNEL
                   + g.CTRL_AL_PLATE_THICK + g.CTRL_BLADE_WATER
                   + g.ABSORBER_THICK / 2.0)
    z_span = g.CORE_TOP - g.CORE_BOTTOM
    p3 = _plot('phase1_xs3_xz_ctrl_full', 'xz', (cx, slot_y, 0.0),
               (2 * g.PITCH_X, z_span), (700, int(700 * z_span / (2 * g.PITCH_X))))

    # 4. Zoom on the clad extension / end-box interfaces. Centred between the
    #    meat top and the end-box top so both +30->+31 and +31->+45 are in frame.
    z_centre = (g.HALF_Z + g.ENDBOX_ABOVE_TOP) / 2.0
    z_height = 22.0
    p4 = _plot('phase1_xs4_xz_clad_endbox', 'xz', (cx, slot_y, z_centre),
               (2 * g.PITCH_X, z_height),
               (2000, int(2000 * z_height / (2 * g.PITCH_X))))

    return openmc.Plots([p1, p2, p3, p4])


def stamp(png_path, text):
    """Burn a provenance line into the bottom-left corner of a PNG.

    plots/ is no longer tracked (4a76220), so a PNG on disk has no version
    control and no way to say which geometry it depicts. That is exactly how
    twelve plots of a superseded model sat in the repository for four days and
    became finding #2 of the Phase 1 audit. A SHA in the corner makes staleness
    self-evident to anyone looking at the file, with no repository access.

    Verification plots only. figures/make_figures.py output is NOT stamped —
    manuscript figures keep clean margins.
    """
    from PIL import Image, ImageDraw, ImageFont
    with Image.open(png_path) as im:
        im = im.convert('RGB')
        d = ImageDraw.Draw(im)
        # Font scales with the image: these panels run from 700 px to 2400 px
        # wide, and a fixed 11 px default would be invisible on the large ones.
        size = max(11, im.width // 60)
        try:
            font = ImageFont.load_default(size=size)
        except TypeError:          # Pillow < 9.2 has no size argument
            font = ImageFont.load_default()
        pad = max(6, im.width // 100)
        halo = max(1, size // 8)
        x, y = pad, im.height - pad - size
        # Two passes: white halo then black text, so the stamp stays legible
        # over either the dark B4C or the light aluminium.
        for dx in (-halo, 0, halo):
            for dy in (-halo, 0, halo):
                if dx or dy:
                    d.text((x + dx, y + dy), text, font=font, fill=(255, 255, 255))
        d.text((x, y), text, font=font, fill=(0, 0, 0))
        im.save(png_path)


if __name__ == '__main__':
    from settings import run_provenance

    # Primed at run start, before the build — same rule as core.build_model().
    prov = run_provenance()
    stamp_text = (f"{prov['git']} | openmc {prov['openmc_version']} | "
                  f"{prov['utc'][:10]} | f={WITHDRAWN_FRACTION}")

    geom = g.build_core_geometry(withdrawn_fraction=WITHDRAWN_FRACTION)
    model = openmc.Model(geometry=geom, materials=materials,
                         plots=build_plots())
    model.plot_geometry(cwd=OUT_DIR)

    for p in build_plots():
        stamp(os.path.join(OUT_DIR, f'{p.filename}.png'), stamp_text)

    print(f"\nWrote 4 verification plots to {OUT_DIR} "
          f"(f = {WITHDRAWN_FRACTION}, blades "
          f"{'inserted' if WITHDRAWN_FRACTION == 0.0 else 'withdrawn'})")
    print(f"  stamped: {stamp_text}")
