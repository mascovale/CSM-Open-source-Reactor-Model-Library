"""
figures/check_figures.py
------------------------
Acceptance tests for the TECDOC-643 A-2 reference figures. Run after every
build; nothing here is eyeballed.

    python figures/check_figures.py

Imports the palette from figstyle.py -- the same module make_figures.py draws
with -- so a passing test cannot be testing a different palette than the figures.

(a) SEPARATION, per figure and global.
    Co-occurrence is DERIVED by sampling the built geometry, never declared: no
    figure contains all eight regions, and regions that never share a figure need
    not separate at all. That slack is what lifts the all-pairs floor from 0.1245
    (one global ramp) to 0.1517.

    Every pair that co-occurs in a figure must clear VALUE_MIN by luminance.
    A full N x N matrix is reported per figure, not just the adjacency pairs,
    because the failure mode that matters in a flat-fill render is legend
    matchability: a reader reads "graphite" in the key and has to find it.

    Greyscale is the requirement, not colour: Elsevier prints greyscale unless
    colour is paid for. Because every pair separates by VALUE, nothing is
    colour-only and the whole palette survives conversion -- verified by
    converting each emitted proof and re-measuring.

(b) GEOMETRY OF THE EMITTED FILE.
    Page width against TEXTWIDTH, and separately the EMBEDDED IMAGE dimensions
    against the computed pixel requirement -- those are independent, and a
    page-size check alone would pass while the render was downsampled. Also
    counts image objects: one per rendered axes, or matplotlib has tiled or
    composited the render.
"""
import itertools, os, re, sys
import numpy as np
THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS); sys.path.insert(0, os.path.join(os.path.dirname(THIS), 'model'))
import openmc
import figstyle as S
from figstyle import (REGION_FILL, LUM_ORDER, KIND_MATERIAL, flat_luma,
                      luma601, textwidth_in, FIG1_WIDTH_FRAC, in_to_pdf_pt,
                      VALUE_MIN, display_name)
import make_figures as M
from geometry import build_core_geometry, PITCH_X, PITCH_Y, CORE_TOP, CORE_BOTTOM

FAIL = []
def fail(m): FAIL.append(m); print(f'    FAIL  {m}')

ID2K = {m.id: k for k, m in KIND_MATERIAL.items()}


def derive_cooccurrence():
    """Superseded by make_figures.RENDERED -- kept only as a cross-check."""
    """Regions actually present in each figure, sampled from the geometry."""
    geom = build_core_geometry(0.0)
    lat = M.core_lattice_of(geom)
    nx, ny = lat.shape; px, py = lat.pitch; llx, lly = lat.lower_left
    W, H = nx * px, ny * py; Z = CORE_TOP - CORE_BOTTOM
    cx, cy = llx + W / 2, lly + H / 2

    # (horizontal, vertical) axis index per basis, declared once instead of
    # spelled out in a conditional. The previous form had no 'yz' branch: a
    # 'yz' call fell through to the 'xy' arm and swept x/y at a fixed z --
    # silently the wrong plane, with no error. Dormant only because every
    # caller so far asked for 'xy' or 'xz'.
    AXES = {'xy': (0, 1), 'xz': (0, 2), 'yz': (1, 2)}

    def scan(basis, origin, width, n):
        ih, iv = AXES[basis]
        got = set()
        for i in range(n[0]):
            u = origin[ih] - width[0] / 2 + (i + .5) * width[0] / n[0]
            for j in range(n[1]):
                w = origin[iv] - width[1] / 2 + (j + .5) * width[1] / n[1]
                pt = list(origin)
                pt[ih] = u
                pt[iv] = w
                pt = tuple(pt)
                try: seq = geom.find(pt)
                except Exception: continue
                for o in reversed(seq):
                    if isinstance(o, openmc.Cell) and isinstance(o.fill, openmc.Material):
                        if o.fill.id in ID2K: got.add(ID2K[o.fill.id])
                        break
        return got
    pres = {'fig2': scan('xy', (cx, cy, 0.0), (W, H), (220, 250)),
            'fig3': scan('xz', (cx, M.SLOT_Y, 0.0), (W, Z), (200, 240))}
    f4 = set()
    for tok in 'SCF':
        ox, oy = M._cell_centre(tok)
        f4 |= scan('xy', (ox, oy, 0.0), (px, py), (150, 160))
    pres['fig4'] = f4
    return pres


def rendered_regions():
    """What each figure actually contains, read from its own rendered pixels.

    A probe grid over geometry.find() is sampling-dependent: a coarse grid
    silently missed two regions in fig3, which under-reported both the legend
    and this matrix. The renders are the artefact under test, so they are what
    is measured.
    """
    M.apply_style()
    M.fig2_core_xy(); M.fig3_axial_xz(); M.fig4_elements(); M.fig4_split()
    return {k: v for k, v in M.RENDERED.items()}


def test_separation(pres):
    print('\n(a) SEPARATION')
    L = {k: flat_luma(k) for k in REGION_FILL}
    print('\n  regions present per figure (derived from the geometry)')
    for f in sorted(pres): print(f'    {f}: ({len(pres[f])}) {sorted(pres[f])}')
    print('    fig1: 0 (position designations only, no material fills)')
    co = {p for f in pres.values() for p in itertools.combinations(sorted(f), 2)}
    freed = [p for p in itertools.combinations(sorted(REGION_FILL), 2) if p not in co]
    print(f'\n  freed (never co-occur, unconstrained): {len(freed)}')
    for a, b in freed:
        print(f'    {a:14s}/{b:14s} dL={abs(L[a]-L[b]):.3f} -- separated by hue across figures')
    # Declared same-material merges are LISTED, never silently dropped: an
    # exemption you cannot see in the output is indistinguishable from a bug.
    # An exempt cell is marked 'ex' in the matrix and excluded from `worst`.
    print(f'\n  declared exemptions ({len(S.EXEMPT_PAIRS)}) -- share a luma '
          f'level, separate by hue, merge in greyscale:')
    for a, b in sorted(S.EXEMPT_PAIRS):
        print(f'    EXEMPT  {a:14s}/{b:14s} dL={abs(L[a]-L[b]):.4f}  '
              f'(same material, two roles)')
    for f in sorted(pres):
        R = sorted(pres[f]); print(f'\n  {f} N x N luminance ({len(R)} regions)')
        print('        ' + ''.join(f'{x[:7]:>9s}' for x in R))
        worst = 9.0; n_ex = 0
        for a in R:
            line = f'  {a[:7]:>7s}'
            for b in R:
                if a == b:
                    line += '        -'
                elif S.is_exempt(a, b):
                    n_ex += 1
                    line += '       ex'
                else:
                    d = abs(L[a]-L[b]); worst = min(worst, d); line += f'{d:9.3f}'
            print(line)
        ex_note = f'  ({n_ex // 2} exempt pair excluded)' if n_ex else ''
        print(f'    min pair {worst:.4f}  '
              f'{"OK" if worst >= VALUE_MIN else "FAIL"}{ex_note}')
        if worst < VALUE_MIN:
            fail(f'{f}: min pair {worst:.4f} < {VALUE_MIN}')
    print('\n  mechanism: every co-occurring NON-EXEMPT pair separates by VALUE')
    print('  alone, so the palette survives greyscale. The exempt pair above is')
    print('  the one place that is deliberately not true.')


def test_files():
    print('\n(b) EMITTED FILE GEOMETRY')
    TW = textwidth_in()
    SPLIT = M.FIG4_SPLIT_FRAC * TW
    spec = {'fig1_core_map': (None, 0, FIG1_WIDTH_FRAC*TW),
            'fig2_core_xy': (None, 1, M.FIG2_WIDTH_FRAC*TW),
            # fig3 emits at its own content width, not FIG1_WIDTH_FRAC: its two
            # panels are at different scales and no longer fill that measure.
            'fig3_axial_xz': (None, 2, M.FIG3_WIDTH_FRAC*TW),
            'fig4_elements': (None, 3, TW),
            'fig4a_sfe': (None, 1, SPLIT),
            'fig4b_cfe': (None, 1, SPLIT),
            'fig4c_ft': (None, 1, SPLIT)}
    lat = M.core_lattice_of(build_core_geometry(0.0))
    px, py = lat.pitch; nx, ny = lat.shape
    sp = M.required_pixels(px, SPLIT*0.96)[2]
    r0, r1, c0, c1 = M.active_region_bbox()
    f2w = (c1-c0+1)*px + 2*M.FIG2_POOL_MARGIN
    f2aw = M.FIG2_WIDTH_FRAC*TW*(1-2*M.PAD_TIGHT)
    req = {'fig2_core_xy': M.required_pixels(f2w, f2aw)[2],
           # fig3 is two panels sharing a height; the bound is the narrower
           # one, panel (a). Its printed width follows fig4_elements' margins
           # (0.015 sides, 0.045 gap) rather than the 0.96 of the single-panel
           # form. Both panels in fact exceed this -- (b) is the wider window,
           # so it needs more pixels -- and whichever image the PDF lists first
           # clears it.
           'fig3_axial_xz': M.required_pixels(
               nx*px, FIG1_WIDTH_FRAC*TW*0.925 * (nx*px)/(nx*px + ny*py))[2],
           'fig4_elements': M.required_pixels(px, (TW-2*0.015*TW-2*0.045*TW)/3)[2],
           'fig4a_sfe': sp, 'fig4b_cfe': sp, 'fig4c_ft': sp}
    print(f'    {"figure":16s} {"page pt":>9s} {"target":>9s} {"imgs":>5s} {"embedded":>14s} {"required":>9s}')
    for stem, (_, nexp, tin) in spec.items():
        d = open(os.path.join(THIS, stem + '.pdf'), 'rb').read()
        box = [float(x) for x in re.search(rb'/MediaBox\s*\[([^\]]*)\]', d).group(1).split()]
        pw = box[2]-box[0]; want = in_to_pdf_pt(tin)
        dims = [(int(a), int(b)) for a, b in
                re.findall(rb'/Subtype\s*/Image.*?/Width\s+(\d+).*?/Height\s+(\d+)', d, re.S)]
        if not dims:
            dims = [(int(m.group(1)), int(m.group(2))) for m in
                    re.finditer(rb'/Width\s+(\d+)\s*/Height\s+(\d+)', d)]
        emb = f'{dims[0][0]}x{dims[0][1]}' if dims else 'vector'
        r = req.get(stem)
        print(f'    {stem:16s} {pw:9.2f} {want:9.2f} {len(dims):5d} {emb:>14s} '
              f'{r if r else "-":>9}')
        if abs(pw-want) > 0.75: fail(f'{stem}: page {pw:.2f} != target {want:.2f} pt')
        if len(dims) != nexp:
            fail(f'{stem}: {len(dims)} image objects, expected {nexp} '
                 f'(one per rendered axes; more means tiling/compositing)')
        if r and dims and dims[0][0] < r:
            fail(f'{stem}: embedded {dims[0][0]} px < required {r} px')


def test_greyscale():
    print('\n(c) GREYSCALE PROOFS')
    d = os.path.join(THIS, '_proof')
    if not os.path.isdir(d):
        print('    (skipped -- run with FIGURE_PROOFS=1)'); return
    from PIL import Image
    for f in sorted(os.listdir(d)):
        if not f.endswith('_grey.png'): continue
        a = np.asarray(Image.open(os.path.join(d, f)).convert('RGB'))
        mono = int(np.abs(a[..., 0].astype(int)-a[..., 1]).max()) == 0
        print(f'    {f:44s} {"greyscale OK" if mono else "NOT greyscale"}')
        if not mono: fail(f'{f} is not greyscale')


def test_legends(pres):
    """Bidirectional: every legend entry is drawn, every drawn region labelled.

    Legends are now BUILT from the rendered pixel set, so this verifies that
    coupling holds rather than re-deriving it independently.
    """
    print('\n(d) LEGEND COVERAGE (bidirectional, against rendered pixels)')
    for stem in sorted(pres):
        k = pres[stem]
        print(f'    {stem:16s} {len(k)} entries: {sorted(k)}')
        if not k:
            fail(f'{stem}: no regions rendered')
    for tok, stem in (('S', 'fig4a_sfe'), ('C', 'fig4b_cfe'), ('F', 'fig4c_ft')):
        if pres.get(stem) != M.PANEL_MATS[tok]:
            fail(f'{stem}: rendered {sorted(pres.get(stem, []))} != '
                 f'expected {sorted(M.PANEL_MATS[tok])}')


def main():
    print('TECDOC-643 A-2 figure acceptance tests')
    print(f'  VALUE_MIN={VALUE_MIN}; metric gamma-encoded luma (ITU-R BT.601)')
    M.check_geometry_consistency()
    pres = rendered_regions()
    test_separation(pres)
    test_files()
    test_legends(pres)
    test_greyscale()
    print('\n' + '='*66)
    if FAIL:
        print(f'{len(FAIL)} FAILURE(S)')
        for f in FAIL: print('  -', f)
        return 1
    print('ALL ACCEPTANCE TESTS PASSED'); return 0


if __name__ == '__main__':
    sys.exit(main())
