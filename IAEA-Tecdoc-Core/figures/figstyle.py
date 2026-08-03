"""
figures/figstyle.py
-------------------
Shared drawing vocabulary for the IAEA-TECDOC-643 A-2 manuscript figures.

Split out of make_figures.py so that check_figures.py consumes the SAME palette,
hatch table, thresholds and pair declarations that the figures are drawn with.
Two copies of a palette is how a legend starts disagreeing with its own figure.

=============================================================================
HOW THE PALETTE WAS DERIVED
=============================================================================
Luminance was solved FIRST, as a pure constraint problem, with hue and
saturation assigned afterwards over the fixed values.

The constraint set is PER FIGURE, not global: no figure contains all eight
regions, and regions that never co-occur need not separate at all. Co-occurrence
is derived by sampling the built geometry (see check_figures.derive_cooccurrence),
never hand-declared. fig2 binds with 7 regions; end_box and graphite never share
a figure, so the effective level count is 7 and the even-spacing ceiling is
0.910 / 6 = 0.1517.

An LP over every ordering maximises the all-pairs floor subject to each
co-occurring adjacent pair clearing VALUE_MIN. Among the 18720 solutions that
reach the optimum, the one closest to a semantic target (water light, metals
mid, absorber dark) was chosen. Those semantics came back on their own: they
were NOT constraints. Solving one global 8-region ramp instead gives only
0.1245, because it forces regions apart that never meet.

Result: every pair in every figure clears 0.15 by VALUE alone, so nothing is
colour-only and the palette survives greyscale conversion. Fuel meat is the only
strongly saturated region, so it reads as the subject wherever it sits in the
value ramp.

=============================================================================
LUMINANCE METRIC
=============================================================================
Region separation is measured with gamma-encoded luma,

    Y' = 0.299 R' + 0.587 G' + 0.114 B'        (ITU-R BT.601, on sRGB values
                                                as stored, NOT linearised)

and NOT with linear-light relative luminance Y (CIE / WCAG).

The two disagree sharply at the dark end: fuel meat #A32A20 against B4C #171717
is 0.21 in encoded luma and 0.09 in linear-light Y. Encoded luma is the correct
space for this question for two reasons:

  1. The sRGB transfer function is approximately perceptually uniform, so equal
     steps in Y' are approximately equal steps in apparent lightness. Linear
     light Y is proportional to radiance, not to perceived lightness, and
     compresses the entire dark half of the range into a few hundredths — which
     is why a red/near-black pair that is plainly separable on paper scores 0.09
     there.
  2. Every grayscale conversion in the reproduction path — desaturating for a
     mono print stream, or a reviewer printing the PDF on a mono device —
     operates on the encoded values. The number we test is therefore the number
     the reproduction path acts on.

Linear-light Y is still reported for the dark pairs, but as a CONTRAST RATIO
(Y+0.05)/(Y+0.05), not as a difference: a fixed difference threshold is
meaningless in a space that is not perceptually uniform.

All dimensions in cm. Every dimension originates in model/geometry.py.
"""

import os
import sys

import matplotlib.colors as mcolors

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'model'))
from materials import (fuel, clad, water, water_core, b4c, graphite, aluminum,
                       end_box_homog)

# =============================================================================
# UNITS
#
# Three different "points" collide in this pipeline and mixing them silently
# breaks the scale-1.0 invariant the width constant exists to protect:
#
#   TeX point   1/72.27 in   what \the\textwidth reports
#   PostScript  1/72    in   what a PDF MediaBox counts, and matplotlib's
#               point            font sizes and line widths
#
# A 0.375% slip is 0.024 in on a 6.5 in figure. Convert once, here, and never
# open-code either divisor anywhere else.
# =============================================================================

TEX_PT_PER_IN = 72.27
PDF_PT_PER_IN = 72.0


def tex_pt_to_in(tex_pt):
    """\\the\\textwidth (TeX points) -> inches."""
    return tex_pt / TEX_PT_PER_IN


def in_to_pdf_pt(inches):
    """inches -> PDF/PostScript points (MediaBox units)."""
    return inches * PDF_PT_PER_IN


# =============================================================================
# TEXT WIDTH — the ONE constant that sets every figure's native width.
#
# PROVENANCE: MEASURED. \the\textwidth reported by the manuscript's own compile,
# Elsevier CAS single column, a4paper, 2026-07-29.
#
#     \the\textwidth = 468.3324 pt (TeX)  ->  468.3324 / 72.27 = 6.480315 in
#
# Deliberately \textwidth and NOT \linewidth: inside the
# center/minipage/captionof pattern the manuscript uses, \linewidth resolves to
# the enclosing minipage width, not the text measure.
#
# RE-MEASURE if the class options change (paper size, single/double column, or
# any margin/geometry package). Every figure width in this project derives from
# this one number, so a stale value silently breaks the scale-1.0 invariant it
# exists to protect.
# =============================================================================

TEXTWIDTH_PT = 468.3324           # TeX points; = 6.480315 in
TEXTWIDTH_MEASURED = True

# fig1 is portrait and stays at the fraction it was designed for; fig3/fig4 take
# the full measure. Derived from the one constant so all three move together.
FIG1_WIDTH_FRAC = 0.6


def textwidth_in():
    return tex_pt_to_in(TEXTWIDTH_PT)


# =============================================================================
# LINE WEIGHT VOCABULARY — exactly three, no others.
# =============================================================================

LW_ENVELOPE = 1.00      # outer envelope of a part assembly
LW_PART = 0.55          # part boundary: plate, side plate, guide, absorber
LW_DIM = 0.35           # dimension, extension, leader, construction lines

INK = '#000000'

# A part boundary is only drawn when the band it bounds can survive it: below
# 4 x LW_PART the stroke pair eats the fill and a 23-plate stack goes solid
# black. An interface line between two bands requires BOTH to clear it.
STROKE_MIN_PT = 4.0 * LW_PART       # 2.2 pt

# Hatch is suppressed below this band width. matplotlib renders a hatch inside a
# sub-point band as aliased noise, not as a pattern, so a narrow band is drawn as
# flat tint. This is why Al cladding is flat in the at-scale and x6 panels and
# hatched only at x20 — the same material legitimately changes appearance with
# scale, which is stated in every figure note so it does not read as an error.
#
# It also DERIVES the mechanism classification: because clad renders flat
# wherever it meets coolant at scale, that pair cannot be texture-encoded and
# must separate by value. Nothing about clad/coolant is asserted by hand.
HATCH_MIN_PT = 4.5

# =============================================================================
# TYPE — single serif family, sizes are final printed sizes (scale 1.0).
# =============================================================================

FS_LABEL = 8.0          # axis labels, legend text, cell letters
FS_DIM = 7.5            # dimension values, notes. All values one size, none bold
FS_PANEL = 9.0          # panel letters, bold
FS_TICK = 7.0
FS_FLOOR = 7.0          # nothing below this


def check_type_sizes():
    for n, v in [('FS_LABEL', FS_LABEL), ('FS_DIM', FS_DIM),
                 ('FS_PANEL', FS_PANEL), ('FS_TICK', FS_TICK)]:
        assert v >= FS_FLOOR, f'{n}={v} is below the {FS_FLOOR} pt floor'


# =============================================================================
# PALETTE
#
# Anchors: coolant water is the lightest region, B4C the darkest, fuel meat is
# the visual subject and separates by value from both cladding and B4C. Cladding
# and structural Al are the SAME material in different roles, so they sit within
# 0.15 of each other deliberately and separate by hatch DIRECTION, not hue.
#
# Four orthogonal hatch directions are in play, one per material that needs one:
#   meat horizontal | clad 45 | structural Al 135 | graphite vertical
# plus dots (pool water) and blank (coolant) for the two waters.
# =============================================================================

REGION_FILL = {
    'pool_water':     '#007BFF',
    'clad':           '#C8D8EE',
    'structural_Al':  '#A1B2C5',
    'meat':           '#EC6053',
    'coolant':        '#000080',
    'graphite':       "#030303",
    'end_box':        '#0D4870',
    'B4C':            '#2E8B57',
}

REGION_HATCH = {
    'coolant':       None,
    'pool_water':    '..',
    'graphite':      '||',
    'clad':          '//',
    'structural_Al': '\\\\',
    # Homogenised end-box: no hatch. All four hatch directions are already
    # committed (meat horizontal, clad 45, structural Al 135, graphite vertical)
    # and dots are pool water, but end_box needs none -- it clears 0.15 by VALUE
    # against every region it can touch in an axial elevation.
    'end_box':       None,
    'meat':          '--',
    'B4C':           None,
}

REGION_LABEL = {
    'coolant':       'coolant water, 316.8 K',
    'pool_water':    'pool water, 294 K',
    'graphite':      'graphite reflector',
    'clad':          'Al cladding',
    'structural_Al': 'structural Al',
    'end_box':       'end box, homogenised Al/H$_2$O',
    'meat':          r'U$_3$Si$_2$-Al fuel meat',
    'B4C':           r'B$_4$C absorber',
}

HATCH_LW = 0.5          # hatch stroke weight; part of the fill, not the outline

# Hatch ink colour. Black everywhere except pool water: at fig1's cell size a
# black dot stipple reads louder than the fuel it surrounds, which inverts the
# "water is the quietest thing on the page" rule. A mid grey keeps the dots
# detectable -- the texture test still separates them from blank coolant and
# from graphite's vertical hatch at 150 dpi -- while dropping their weight.
HATCH_COLOR = {k: INK for k in REGION_FILL}
HATCH_COLOR['pool_water'] = '#9AA3AC'

# =============================================================================
# EDITING THE PALETTE
# =============================================================================
# Change REGION_FILL above. That is the whole procedure.
#
# Everything else is DERIVED from it: the light-to-dark ordering, the colour map
# handed to OpenMC, every legend swatch, and the SolidWorks appearance table.
# There is no second copy to keep in sync and no ordering list to update.
#
# Nothing here rejects a colour you chose. The figures will build. Only two
# things are hard errors, because they break the machinery rather than the
# aesthetics:
#   * a value matplotlib cannot parse as a colour;
#   * two regions sharing the exact same colour -- the renders are mapped back
#     to materials BY pixel colour, so identical fills make two materials
#     indistinguishable to the legend builder as well as to the reader.
#
# Everything else -- how well regions separate, whether the figure survives
# greyscale -- is REPORTED, not enforced. palette_issues() lists what your
# choice gives up; make_figures prints it as a warning and carries on, and
# check_figures.py is where it counts as a failure. So you can try a colour,
# look at the figure, and decide.
#
# Historical note: this file used to assert a specific solved palette -- that
# pool water held the near-white slot, that end box and graphite shared a level,
# that luminance had not drifted from a stored reference. Those encoded one
# particular solution, not an invariant, so any hand edit tripped them. They are
# gone.
# =============================================================================


def luma601(hex_color):
    """Gamma-encoded luma Y' (ITU-R BT.601). The normative metric.

    Gamma-encoded, not linear-light: the sRGB transfer function is roughly
    perceptually uniform, and every greyscale conversion in the reproduction
    path operates on the encoded values.
    """
    r, g, b = mcolors.to_rgb(hex_color)
    return 0.299 * r + 0.587 * g + 0.114 * b


def linear_Y(hex_color):
    """Linear-light relative luminance Y (CIE/WCAG). Reported, never thresholded."""
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in mcolors.to_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(h1, h2):
    """WCAG contrast ratio, for reporting dark pairs."""
    a, b = linear_Y(h1), linear_Y(h2)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def flat_luma(kind):
    return luma601(REGION_FILL[kind])


def lum_order():
    """Region kinds, lightest to darkest. Derived, never maintained by hand."""
    return sorted(REGION_FILL, key=lambda k: -flat_luma(k))


# Snapshot for convenience; recompute with lum_order() if REGION_FILL is
# changed at runtime rather than in the source.
LUM_ORDER = lum_order()


def check_palette():
    """Hard errors only -- the two things that break the machinery.

    Deliberately does NOT judge your colour choices. See palette_issues().
    """
    for k, v in REGION_FILL.items():
        try:
            mcolors.to_rgb(v)
        except ValueError:
            raise ValueError(
                f"REGION_FILL['{k}'] = {v!r} is not a colour matplotlib can "
                f"parse. Use a hex string like '#RRGGBB'.")
    seen = {}
    for k in REGION_FILL:
        rgb = rgb255(k)
        if rgb in seen:
            raise ValueError(
                f"REGION_FILL['{k}'] and REGION_FILL['{seen[rgb]}'] are the "
                f"same colour {REGION_FILL[k]}. Renders are mapped back to "
                f"materials by pixel colour, so two regions cannot share one.")
        seen[rgb] = k


def palette_issues(min_sep=None):
    """Review the palette without rejecting it. Returns a list of notes.

    Reports adjacent-luminance crowding across the whole palette. It does not
    know which regions actually share a figure -- check_figures.py does that
    properly, per figure, from the rendered pixels.
    """
    if min_sep is None:
        min_sep = VALUE_MIN
    notes = []
    order = lum_order()
    lums = [flat_luma(k) for k in order]
    for a, b, la, lb in zip(order, order[1:], lums, lums[1:]):
        d = la - lb
        if d < min_sep:
            notes.append(f'{a} and {b} are {d:.3f} apart in luminance '
                         f'(< {min_sep}); they will be hard to tell apart in '
                         f'greyscale if they appear in the same figure')
    span = lums[0] - lums[-1]
    need = min_sep * (len(order) - 1)
    if span < need:
        notes.append(f'the palette spans {span:.3f} in luminance but '
                     f'{len(order)} regions at {min_sep} apart need {need:.3f}; '
                     f'some pairs must overlap unless they never share a figure')
    return notes


# =============================================================================
# SEPARATION MECHANISMS
#
# Declared, never inferred. A test that is free to decide which bucket a pair
# belongs to can launder a value failure into "texture-encoded", so the table is
# authoritative and any adjacent pair absent from it fails by default.
#
# LABEL is available in fig1 only: every fig1 cell carries a letter and a
# LW_PART outline, which is a real third mechanism and is declared rather than
# left implicit. fig3/fig4 regions carry no letters, so they have VALUE and
# TEXTURE only.
# =============================================================================

VALUE, TEXTURE, LABEL = 'VALUE', 'TEXTURE', 'LABEL'

MECHANISMS_BY_FIGURE = {
    'fig1': {VALUE, TEXTURE, LABEL},   # every cell carries a letter + outline
    'fig2': {VALUE, TEXTURE},
    'fig3': {VALUE, TEXTURE},
}

VALUE_MIN = 0.15

# (a, b) -> (mechanisms, note). Pairs are sorted tuples.
PAIR_TABLE = {
    ('clad', 'meat'):              ((VALUE,), 'plate face to its own meat'),
    ('coolant', 'meat'):           ((VALUE,), 'not a shared boundary; meat is enclosed by clad. Defensive'),
    ('meat', 'structural_Al'):     ((VALUE,), 'not a shared boundary; 0.17 cm of clad intervenes. Defensive'),
    ('B4C', 'meat'):               ((VALUE,), 'not adjacent, but co-occur in fig4 and are the two darkest regions'),
    ('B4C', 'coolant'):            ((VALUE,), 'absorber to blade water'),
    ('B4C', 'clad'):               ((VALUE,), 'not a shared boundary; blade water and guide intervene. Defensive'),
    ('B4C', 'structural_Al'):      ((VALUE,), 'absorber band abuts the side plate in x'),
    ('clad', 'coolant'):           ((VALUE,), 'channel to plate face, 23x per element. VALUE is FORCED: clad renders '
                                              'flat below HATCH_MIN_PT at the scales where this pair appears'),
    ('coolant', 'structural_Al'):  ((VALUE,), 'channel to side plate'),
    ('pool_water', 'structural_Al'): ((VALUE,), 'the A6 flux trap fills its cell with Al and borders the pool ring'),
    ('graphite', 'structural_Al'): ((VALUE,), 'reflector to the A6 flux-trap cell'),
    ('clad', 'structural_Al'):     ((TEXTURE,), 'same material, different role: 45 vs 135 deg'),
    ('coolant', 'pool_water'):     ((TEXTURE,), 'blank vs sparse dots'),
    ('coolant', 'graphite'):       ((TEXTURE, LABEL), 'vertical vs blank; fig1 only, letters also present'),
    ('graphite', 'pool_water'):    ((TEXTURE, LABEL), 'vertical vs dots; 0.015 apart, fig1 only, letters also present'),
    # fig2 axial elevation only: the homogenised end box against everything it
    # stacks against in z.
    ('end_box', 'pool_water'):     ((VALUE,), 'end box to the water above/below it'),
    ('coolant', 'end_box'):        ((VALUE,), 'end box to the active-zone coolant'),
    ('clad', 'end_box'):           ((VALUE,), 'end box to the plate end'),
    ('end_box', 'meat'):           ((VALUE,), 'end box to the meat end when no cladding extension is modelled'),
    ('end_box', 'structural_Al'):  ((VALUE,), 'end box to the side plate end'),
    ('B4C', 'end_box'):            ((VALUE,), 'blade top to the end-box cap rigidly attached above it'),
}


def pair_key(a, b):
    return tuple(sorted((a, b)))


# =============================================================================
# LEGEND DISPLAY NAMES, keyed by material ID
#
# materials.py is a production file and its `name` fields are IDENTIFIERS -- they
# may be referenced by tallies, the depletion-zoning scaffold, or the
# cross-validation spreadsheet. Renaming them for legend cosmetics is out of
# scope for a figures change, so the figures carry their own presentation names
# here and build the legend by hand rather than relying on plot(legend=True),
# which would print the raw identifiers.
#
# Keyed by ID, and the IDs are read off the imported material objects, so this
# cannot go stale if materials.py is reordered.
# =============================================================================

DISPLAY_NAMES = {
    fuel.id:          r'U$_3$Si$_2$-Al fuel meat',
    clad.id:          'Al 6061 cladding',
    aluminum.id:      'Structural aluminium',
    water.id:         'Pool water, 294 K',
    water_core.id:    'Coolant water, 316.8 K',
    graphite.id:      'Graphite reflector',
    b4c.id:           r'B$_4$C absorber',
    end_box_homog.id: r'End box, homogenised Al/H$_2$O',
}

# region kind -> material object, the one place the two vocabularies meet
KIND_MATERIAL = {
    'coolant': water_core, 'pool_water': water, 'graphite': graphite,
    'clad': clad, 'structural_Al': aluminum, 'meat': fuel, 'B4C': b4c,
    'end_box': end_box_homog,
}


def rgb255(kind):
    """0-255 tuple, the form openmc's plotter requires (it rejects hex)."""
    return tuple(int(round(255 * c))
                 for c in mcolors.to_rgb(REGION_FILL[kind]))


def openmc_colors():
    """{material: rgb} for plot(colors=...), straight from the palette."""
    return {KIND_MATERIAL[k]: rgb255(k) for k in REGION_FILL}


def display_name(kind):
    return DISPLAY_NAMES[KIND_MATERIAL[kind].id]
