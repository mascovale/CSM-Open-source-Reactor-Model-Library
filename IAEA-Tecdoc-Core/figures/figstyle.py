"""
figures/figstyle.py
-------------------
Shared drawing vocabulary for the IAEA-TECDOC-643 A-2 manuscript figures.

Split out of make_figures.py so that check_figures.py consumes the SAME palette,
hatch table, thresholds and pair declarations that the figures are drawn with.
Two copies of a palette is how a legend starts disagreeing with its own figure.

=============================================================================
HOW THE PALETTE WAS DERIVED  (rebuilt 2026-08-13)
=============================================================================
Luminance is solved FIRST as a pure constraint problem; hue and saturation are
assigned afterwards over the fixed values. Rebuilt from scratch when fig3 gained
a second panel and the old palette's per-figure reasoning collapsed.

*** HARD CONSTRAINT -- READ BEFORE ADDING A REGION ***

    EIGHT regions occupy SEVEN luma levels, evenly spaced 0.15333 apart across
    [0.04, 0.96]. The ladder is PINNED. There is no freedom left in it.

    Eight DISTINCT levels are arithmetically impossible: 8 levels at VALUE_MIN
    = 0.15 need 7 * 0.15 = 1.05 of span, and luma is bounded by [0, 1]. No
    palette, no solver and no colour choice can produce it. That is why clad
    and structural_Al are merged onto one level (see EXEMPT_PAIRS below).

    A NINTH REGION CANNOT BE ADDED WITHOUT ANOTHER MERGE. Seven levels already
    consume 6 * 0.15333 = 0.92 of the 0.92 usable span. Adding a level means
    finding two more regions that can honestly share one, or lowering
    VALUE_MIN, which is not a decision to take quietly.

    This is not "no figure contains all eight regions" any more. The previous
    derivation leaned on that, and it stopped being true: co-occurrence is now
    effectively complete across the figure set, so the constraint is global.

WHY [0.04, 0.96] AND NOT [0.05, 0.95]

The natural-looking ladder -- 0.05 to 0.95, exactly 0.15 apart, zero headroom --
DOES NOT SURVIVE 8-BIT QUANTISATION. It was built and measured first, and all
five interior gaps landed short: 0.1485, 0.1499, 0.1485, 0.1499, 0.1499. A
1-LSB step in green moves luma by 0.587/255 = 0.0023, and a ladder with zero
headroom has nothing to absorb it with. It would have looked perfectly correct
written down as a specification and failed every gap when rendered.

[0.04, 0.96] gives 0.15333 nominal spacing, so every achieved gap clears 0.15
with about +0.0017 to spare -- roughly one LSB of green. That margin is the
entire reason the ladder is representable. Do not narrow the band.

THE LADDER, lightest to darkest

    0.9600  pool water 294 K      very light blue; the pool is background and
                                  should recede
    0.8067  clad | structural_Al  ONE level, two hues: clad cool, structural a
                                  faintly warm neutral. See EXEMPT_PAIRS.
    0.6533  end box homogenate    warm grey-tan -- reads as a mixture, neither
                                  metal nor water
    0.5000  U3Si2-Al fuel meat    the only strongly saturated region (S = 0.72);
                                  the subject, and the first thing the eye lands
                                  on in every figure
    0.3467  coolant water 316.8 K mid blue, same hue family as pool water,
                                  separated from it by value alone
    0.1933  B4C absorber          dark teal-green, MTR convention
    0.0400  graphite reflector    WARM near-black, not a neutral one

GRAPHITE IS TINTED, AND IT CANNOT BE LIGHTENED

A dead-neutral #0A0A0A read as a harsh black. It is warmed to #0D0A08 instead:
a warm near-black reads softer than a neutral one at the same luminance, and it
buys hue separation from the teal B4C directly above it.

Warmed, NOT lightened, because it cannot be lightened. Graphite is the darkest
level and the only pair constraining it is B4C, so its ceiling is
0.1930 - 0.15 = 0.0430 -- a total lift of 0.0038 from where it sits, roughly one
8-bit step. A genuine soft charcoal is luma 0.08 to 0.16, which would force B4C
to 0.23+ against its own ceiling of coolant - 0.15 = 0.1968. Infeasible without
moving every level, and shifting the whole ladder up by 0.04 puts pool water at
0.998, which is page white.

If a soft charcoal is ever actually wanted, the ONLY way to get one without
re-solving is to swap graphite and B4C between these two levels: graphite takes
0.193 as a true matte charcoal and B4C takes 0.040 as a near-black green. That
is arguably the more faithful pair -- reactor graphite is matte dark grey and
B4C is black -- and it was offered and declined on 2026-08-13, because it makes
B4C the darkest thing in every figure that carries it.

DESIGN INTENT, in priority order: faithful before pretty (aluminium silver,
water blue, graphite black-grey, fuel warm); the two waters read as one family
split by value, likewise the two aluminiums; fuel meat is the only saturated
warm region; the two darks (B4C, graphite) split by HUE as well as value,
because 0.15 at the dark end is perceptually tighter than 0.15 at the light end.

structural_Al is a faintly warm NEUTRAL (S = 0.05) rather than a tan. At a
definite tan it landed on hue 0.092 against end_box's 0.092 -- the same hue at
the ladder's minimum value gap, which is the weakest pair a palette can have.
Dropping its chroma separates the two by saturation as well as value, and
neutral silver is the more faithful reading of structural aluminium anyway.

Result: every non-exempt pair clears VALUE_MIN by VALUE ALONE, so nothing is
colour-only and the palette survives greyscale conversion. The tightest is
clad/end_box at 0.1517, and it separates on hue too (0.581 vs 0.092).

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
    'pool_water':     '#EDF7FF',   # 0.9605  very light blue -- recedes
    'clad':           '#BED1E3',   # 0.8054  silver-grey, cool cast
    'structural_Al':  '#D2CDC7',   # 0.8071  silver-grey, faintly warm neutral
    'meat':           '#DA5E3D',   # 0.4993  the only saturated warm region
    'coolant':        '#32628C',   # 0.3468  mid blue, pool-water family
    'graphite':       '#0D0A08',   # 0.0418  warm near-black, see below
    'end_box':        '#B5A48F',   # 0.6537  warm grey-tan, a mixture
    'B4C':            '#074635',   # 0.1930  dark teal-green, MTR convention
}

# =============================================================================
# THE ALUMINIUM MERGE -- a DECLARED exemption, listed by the checker, never
# silently skipped.
# =============================================================================
# clad and structural_Al share one luma level and separate by HUE ALONE. In
# greyscale they are one tone, deliberately.
#
# The palette text above this used to exempt them on the grounds that they
# "separate by hatch DIRECTION, not hue". That reasoning does not survive
# contact with these figures: REGION_HATCH belongs to the vector schematic
# path, and figures 2-4 are RASTER OpenMC renders in which no hatch is drawn at
# all. The old palette therefore had them 0.1515 apart -- barely over the line
# -- separating by nothing a reader can actually see, two similar grey-blues
# that neither merged nor distinguished. One honest grey is better than two
# greys pretending to be distinct.
#
# They are the same metal (Al 6061) in two roles, so merging them costs no
# physical distinction. It also buys the one thing that makes this palette
# possible at all -- see the HARD CONSTRAINT below.
EXEMPT_PAIRS = {('clad', 'structural_Al')}


def is_exempt(a, b):
    """True if this pair is a declared same-material merge."""
    return tuple(sorted((a, b))) in EXEMPT_PAIRS

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
        if is_exempt(a, b):
            notes.append(f'{a} and {b} share a luma level ({d:.4f} apart) by '
                         f'DECLARED EXEMPTION -- same metal, two roles; they '
                         f'separate by hue only and merge in greyscale')
            continue
        if d < min_sep:
            notes.append(f'{a} and {b} are {d:.3f} apart in luminance '
                         f'(< {min_sep}); they will be hard to tell apart in '
                         f'greyscale if they appear in the same figure')
    # Levels, not regions: an exempt pair is one level carrying two fills, so
    # counting regions here would demand span the ladder does not need.
    n_levels = len(order) - len(EXEMPT_PAIRS)
    span = lums[0] - lums[-1]
    need = min_sep * (n_levels - 1)
    if span < need:
        notes.append(f'the palette spans {span:.3f} in luminance but '
                     f'{n_levels} levels at {min_sep} apart need {need:.3f}; '
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
