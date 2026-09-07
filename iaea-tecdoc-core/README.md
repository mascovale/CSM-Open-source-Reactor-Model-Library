# IAEA TECDOC-643 Core Model

OpenMC model of the IAEA TECDOC-643 Appendix A-2 generic 10 MW LEU research reactor
core. The model is currently organized as a flat collection of Python modules and
scripts; it is not packaged for installation with `pip`.

## Requirements

- Python 3.10 or newer
- OpenMC 0.15.3 or a compatible version
- An OpenMC continuous-energy cross-section library
- Matplotlib and NumPy for the figure and verification scripts

`requirements.txt` is intentionally empty because OpenMC and nuclear-data installations
are environment-specific. Set `OPENMC_CROSS_SECTIONS` to the absolute path of the
cross-section XML file before running the model. The driver has a machine-specific fallback
path, but relying on the environment variable is more portable.

## Structure

```text
iaea-tecdoc-core/
├── model/
│   ├── core.py             # central driver and command-line interface
│   ├── geometry.py         # reactor geometry and blade positions
│   ├── materials.py        # fuel, water, structural, absorber materials
│   ├── settings.py         # OpenMC settings and run provenance
│   └── tallies.py          # flux and reaction-rate tallies
├── figures/
│   ├── make_figures.py     # manuscript and geometry figures
│   ├── check_figures.py    # figure acceptance checks
│   └── figstyle.py         # shared figure style and palette
├── tests/
│   ├── plot_core.py        # geometry plots and zoning visualizations
│   ├── check_depletion_zoning.py
│   └── make_phase1_xs_plots.py
├── docs/                   # audits, decisions, and engineering records
└── scripts/                # delivery and repository tooling
```

Imports are resolved from `model/` by the scripts themselves. Run commands from this
directory so relative paths and generated output have predictable locations.

## Run an eigenvalue calculation

```bash
cd iaea-tecdoc-core
export OPENMC_CROSS_SECTIONS=/path/to/cross_sections.xml
python model/core.py --help
python model/core.py --particles 1000 --batches 20 --inactive 5 \
	--output-dir run_results/smoke
```

The default blade convention for the CLI is intuitive: `--insertion 0` means fully
withdrawn and `--insertion 100` means fully inserted. Output is written to the selected
directory. Existing run output is protected by default; choose a new directory or pass
`--overwrite-output` only when replacing a run deliberately.

Depletion zoning can be enabled for structural model checks:

```bash
python model/core.py --depletion-zoning --particles 1000 --batches 20 --inactive 5 \
	--output-dir run_results/zoning_smoke
```

This creates per-plate, 2-by-10 zoned fuel materials, but depletion integration itself is
not implemented. `build_depletion_operator()` and `run_depletion()` currently raise
`NotImplementedError`.

## Verification and figures

Run the geometry assertions directly:

```bash
python model/geometry.py
```

Check the depletion-zoning scaffold and its negative tests:

```bash
python tests/check_depletion_zoning.py
```

Generate figures and run the figure acceptance checks:

```bash
python figures/make_figures.py
python figures/check_figures.py
```

Generated XML, HDF5, output, and figure artifacts are normally ignored by Git. The
engineering records in `docs/` describe model assumptions, provenance, and known open
questions; they are not a substitute for the executable checks above.
