"""
export_sw.py
------------
Regenerate the SolidWorks external files WITHOUT rebuilding the manuscript
figures.

    python figures/export_sw.py

Both writers live in make_figures.py, whose __main__ renders every figure — a
minutes-long job that rewrites seven PDFs. That coupling is why the on-disk
export went eight commits stale: nobody re-ran the figure build just to refresh
two text files, so solidworks_equations.txt still carried FT_HOLE_RADIUS = 2.5
after A1 had moved it to 2.820.

This entry point calls the two writers and exits. Importing make_figures pulls
in matplotlib and the palette checks but renders nothing.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_figures import (SW_COUNTS, SW_DERIVED, SW_LENGTHS,
                          write_solidworks_appearances,
                          write_solidworks_equations)

if __name__ == '__main__':
    eq = write_solidworks_equations()
    ap = write_solidworks_appearances()
    n = len(SW_LENGTHS) + len(SW_COUNTS) + len(SW_DERIVED)
    print(f"\n  equations   {eq}  ({n} equations: {len(SW_LENGTHS)} lengths, "
          f"{len(SW_COUNTS)} counts, {len(SW_DERIVED)} derived)")
    print(f"  appearances {ap}")
