"""
analyze_rod_sweep.py
--------------------
Analyze the control-rod withdrawal sweep and reproduce TECDOC-643 v1 Fig. 7.3
(reactivity vs % withdrawn) for the LEU BOL core.

Consumes the JSON written by run/run_rod_sweep.py and produces:
  - a printed table: fraction | %withdrawn | keff | sigma | rho(pcm) | rho($) |
                     integral worth vs fully-out (pcm and $)
  - the total blade worth (f=0 fully in  ->  f=1 fully out) in pcm and $
  - the interpolated critical position (%withdrawn where rho = 0), if it exists
  - a plot saved to plots/rod_worth_curve.png with:
        * the model's reactivity-vs-%withdrawn S-curve (in dollars)
        * the TECDOC LEU critical marker at 68% withdrawn
        * an ideal cosine-flux integral-worth curve for shape reference
        * annotations comparing total worth to TECDOC LEU Hf = 15.22 $

Two reference values, both from te_643v1 Section 7.2.5 / Table 7.7:
  - LEU BOL critical position       : ~68 % withdrawn
  - LEU Hf worth (ANL Monte Carlo)  : 15.22 $   (= 11.07 %Dk/k)

Dollar conversion uses the benchmark's own beta_eff = 727 pcm, backed out from
Table 7.7 (11.07 %/15.22 $ = 15.45/11.24 = 20.55/14.95 = 0.00727 for all three
LEU absorbers). Override with --beta to use the model's OpenMC-computed value.

Usage:
    python analyze_rod_sweep.py [results.json] [--beta 0.00727] [--out path.png]
"""

import json
import argparse
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- Benchmark references (te_643v1 Sec 7.2.5, Table 7.7) --------------------
BETA_BENCH = 0.00727            # 727 pcm, from Table 7.7 %/$ consistency
TECDOC_HF_WORTH_DOLLARS = 15.22 # LEU Hf, ANL Monte Carlo
TECDOC_HF_WORTH_PCT = 11.07     # LEU Hf, ANL Monte Carlo (%Dk/k)
TECDOC_CRIT_WITHDRAWN = 68.0    # percent withdrawn, LEU BOL critical


def load_sweep(path):
    """Load sweep JSON defensively; return (f_withdrawn, keff, sigma) arrays.

    Accepts either a top-level list of records or a dict with a 'results'/'points'
    key. Each record must carry a withdrawal fraction and a keff; sigma optional.
    """
    with open(path) as fh:
        data = json.load(fh)

    if isinstance(data, dict):
        for key in ("results", "points", "sweep", "data"):
            if key in data:
                data = data[key]
                break

    if not isinstance(data, list):
        raise ValueError(
            f"Could not find a list of sweep points in {path}. "
            f"Top-level type was {type(data).__name__}."
        )

    def pick(rec, names, default=None):
        for n in names:
            if n in rec:
                return rec[n]
        if default is not None:
            return default
        raise KeyError(f"None of {names} found in record: {list(rec.keys())}")

    f_list, k_list, s_list = [], [], []
    for rec in data:
        f_list.append(float(pick(rec, ("withdrawn_fraction", "fraction", "f", "frac"))))
        k_list.append(float(pick(rec, ("keff", "k", "k_combined", "combined_keff"))))
        s_list.append(float(pick(rec, ("sigma", "keff_sigma", "std", "unc"), default=0.0)))

    order = np.argsort(f_list)
    return (np.array(f_list)[order],
            np.array(k_list)[order],
            np.array(s_list)[order])


def reactivity_pcm(k):
    """rho = (k - 1) / k, in pcm."""
    return (k - 1.0) / k * 1e5


def sigma_rho_pcm(k, sig_k):
    """Propagate keff sigma to rho.  rho = 1 - 1/k  ->  drho/dk = 1/k^2."""
    return sig_k / (k * k) * 1e5


def cosine_integral_worth(x):
    """Ideal integral rod worth for a cosine axial flux, normalized 0..1.
    x = inserted fraction (0 = fully out, 1 = fully in).
    S(x) = x - sin(2 pi x) / (2 pi).
    """
    return x - np.sin(2.0 * np.pi * x) / (2.0 * np.pi)


def interp_zero_crossing(x, y):
    """Return x where y crosses 0 (linear interp on the first sign change).
    Returns None if y never changes sign.
    """
    for i in range(len(x) - 1):
        if y[i] == 0.0:
            return x[i]
        if y[i] * y[i + 1] < 0.0:
            t = -y[i] / (y[i + 1] - y[i])
            return x[i] + t * (x[i + 1] - x[i])
    return None


def analyze(path, beta, out_png):
    f, k, sig = load_sweep(path)
    pct = f * 100.0                      # % withdrawn
    rho = reactivity_pcm(k)              # pcm
    rho_sig = sigma_rho_pcm(k, sig)      # pcm
    rho_dollars = rho / (beta * 1e5)

    # Endpoints: f = 0 fully in (min k), f = 1 fully out (max k)
    i_in, i_out = int(np.argmin(f)), int(np.argmax(f))
    rho_in, rho_out = rho[i_in], rho[i_out]
    worth_pcm = rho_out - rho_in
    worth_sig = np.hypot(rho_sig[i_in], rho_sig[i_out])
    worth_dollars = worth_pcm / (beta * 1e5)

    # Integral worth vs fully-out reference: W(f) = rho_out - rho(f)
    worth_vs_out = rho_out - rho

    # --- Table ---------------------------------------------------------------
    print("=" * 78)
    print(f"Rod withdrawal sweep  ({os.path.basename(path)})")
    print(f"beta_eff = {beta*1e5:.0f} pcm   ($ = pcm / {beta*1e5:.0f})")
    print("=" * 78)
    print(f"{'frac':>5} {'%out':>6} {'keff':>9} {'sig':>7} "
          f"{'rho[pcm]':>10} {'rho[$]':>8} {'W_vs_out[pcm]':>14}")
    for j in range(len(f)):
        print(f"{f[j]:>5.2f} {pct[j]:>6.1f} {k[j]:>9.5f} {sig[j]:>7.5f} "
              f"{rho[j]:>10.0f} {rho_dollars[j]:>8.2f} {worth_vs_out[j]:>14.0f}")
    print("-" * 78)

    # --- Total worth ---------------------------------------------------------
    print(f"\nTOTAL BLADE WORTH  (f=0 fully in  ->  f=1 fully out)")
    print(f"  {worth_pcm:>8.0f} +/- {worth_sig:.0f} pcm")
    print(f"  {worth_dollars:>8.2f} $   (at beta = {beta*1e5:.0f} pcm)")
    print(f"\n  TECDOC LEU Hf (ANL MC, Table 7.7): {TECDOC_HF_WORTH_DOLLARS:.2f} $"
          f"  ({TECDOC_HF_WORTH_PCT:.2f} %)")
    d_dollars = worth_dollars - TECDOC_HF_WORTH_DOLLARS
    d_pcm = worth_pcm - TECDOC_HF_WORTH_PCT * 1e3
    print(f"  Model - benchmark: {d_dollars:+.2f} $   ({d_pcm:+.0f} pcm)")
    verdict = ("OVER-predicts" if d_dollars > 0 else "under-predicts")
    print(f"  -> model {verdict} Hf blade worth by {abs(d_dollars):.2f} $")

    # --- Critical position ---------------------------------------------------
    print(f"\nCRITICAL POSITION  (where rho = 0, i.e. keff = 1)")
    xcrit = interp_zero_crossing(pct, rho)
    if xcrit is None:
        if np.all(rho > 0):
            print("  Core is SUPERCRITICAL at every rod position in the sweep.")
            print("  The fresh clean core has more excess reactivity than the")
            print("  benchmark BOL core (which holds down burnup + experiment")
            print("  margin), so it does not reach keff = 1 even fully rodded-in.")
            print(f"  -> The {TECDOC_CRIT_WITHDRAWN:.0f}% critical checkpoint is NOT")
            print("     directly reproducible without matching the benchmark's")
            print("     excess-reactivity condition.  Use the WORTH SPAN as the")
            print("     clean blade comparison instead.")
        else:
            print("  Core is subcritical throughout the sweep.")
    else:
        print(f"  Model critical at {xcrit:.1f} % withdrawn")
        print(f"  TECDOC LEU BOL critical at {TECDOC_CRIT_WITHDRAWN:.0f} % withdrawn")
        print(f"  Difference: {xcrit - TECDOC_CRIT_WITHDRAWN:+.1f} % points")
    print("=" * 78)

    # --- Plot ----------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 6.0))

    # Model reactivity S-curve (dollars)
    ax.errorbar(pct, rho_dollars, yerr=rho_sig / (beta * 1e5),
                fmt="o-", color="#1f4e79", lw=2, ms=6, capsize=3,
                label="OpenMC model (reactivity)", zorder=5)

    # Ideal cosine integral-worth shape, anchored to model endpoints for shape
    # comparison only (NOT a fit): reactivity(f) = rho_out - W_tot * g(1 - f)
    fdense = np.linspace(0, 1, 200)
    g = cosine_integral_worth(1.0 - fdense)
    rho_ideal_dollars = (rho_out - worth_pcm * g) / (beta * 1e5)
    ax.plot(fdense * 100, rho_ideal_dollars, "--", color="#c05a2e", lw=1.5,
            alpha=0.8, label="ideal cosine-flux shape (endpoint-anchored)",
            zorder=3)

    # TECDOC critical position marker
    ax.axvline(TECDOC_CRIT_WITHDRAWN, color="#2e7d32", ls=":", lw=1.8,
               label=f"TECDOC LEU critical ({TECDOC_CRIT_WITHDRAWN:.0f}% out)")
    # rho = 0 line (critical)
    ax.axhline(0.0, color="gray", lw=0.8, alpha=0.6)

    # Worth-span annotation
    ax.annotate("", xy=(2, rho_dollars[i_out]), xytext=(2, rho_dollars[i_in]),
                arrowprops=dict(arrowstyle="<->", color="#555", lw=1.3))
    ax.text(4, (rho_dollars[i_in] + rho_dollars[i_out]) / 2,
            f"total worth\n{worth_dollars:.2f} $\n({worth_pcm:.0f} pcm)",
            va="center", fontsize=9, color="#333")
    ax.text(0.98, 0.05,
            f"TECDOC LEU Hf worth: {TECDOC_HF_WORTH_DOLLARS:.2f} $\n"
            f"model - bench: {d_dollars:+.2f} $",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
            bbox=dict(boxstyle="round", fc="#f5f5f5", ec="#ccc"))

    ax.set_xlabel("Control rods withdrawn (%)")
    ax.set_ylabel(r"Reactivity  $\rho$  (dollars)")
    ax.set_title("Reactivity vs rod position — TECDOC-643 Fig. 7.3 analog (LEU)")
    ax.set_xlim(0, 100)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.25)
    fig.tight_layout()

    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    fig.savefig(out_png, dpi=150)
    print(f"\nPlot written: {out_png}")
    return dict(f=f, k=k, rho_pcm=rho, worth_pcm=worth_pcm,
                worth_dollars=worth_dollars, xcrit=xcrit)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="?", default="rod_sweep_results.json",
                    help="sweep JSON from run_rod_sweep.py")
    ap.add_argument("--beta", type=float, default=BETA_BENCH,
                    help="beta_eff for dollar conversion (default 0.00727, "
                         "the TECDOC Table 7.7 value)")
    ap.add_argument("--out", default="plots/rod_worth_curve.png",
                    help="output PNG path")
    args = ap.parse_args()
    analyze(args.results, args.beta, args.out)