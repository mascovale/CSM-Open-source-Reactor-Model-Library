# CSM Open-Source Reactor Model Library

An open-source collection of nuclear reactor models built with [OpenMC](https://openmc.org/).
Each top-level directory is an independent model project. Projects can be developed and
run separately; there is no shared Python package or repository-wide launcher.

## Repository layout

| Directory | Purpose | Status |
| --- | --- | --- |
| [`iaea-tecdoc-core/`](iaea-tecdoc-core/README.md) | IAEA TECDOC-643 Appendix A-2 generic 10 MW LEU research reactor OpenMC model | Implemented |
| [`hp-mr/`](hp-mr/README.md) | High-power microreactor model | Reserved project directory |
| [`lunar-fsp-microreactor/`](lunar-fsp-microreactor/README.md) | Lunar FSP microreactor model | Reserved project directory |
| [`marvel/`](marvel/README.md) | MARVEL reactor model | Reserved project directory |
| [`msre/`](msre/README.md) | Molten Salt Reactor Experiment model | Reserved project directory |
| [`pebble-bed-htgr/`](pebble-bed-htgr/README.md) | Pebble-bed high-temperature gas reactor model | Reserved project directory |
| [`radiant-kaleidos/`](radiant-kaleidos/README.md) | Radiant Kaleidos microreactor model | Reserved project directory |

At present, `iaea-tecdoc-core` is the repository's implemented model. The other
directories contain documentation placeholders for future model projects.

## Working with a model

Read the README inside the model directory before running it. Model-specific dependencies,
cross-section libraries, input assumptions, run commands, and validation checks belong in
that README rather than in this root document.

The implemented IAEA model is run from its project directory. Its central driver builds
the geometry, materials, settings, and tallies, then launches an OpenMC eigenvalue run:

```text
cd iaea-tecdoc-core
python model/core.py --help
```

The driver accepts controls for blade insertion, particle and batch counts, output location,
and optional depletion zoning. See [`iaea-tecdoc-core/README.md`](iaea-tecdoc-core/README.md)
for the complete workflow and verification commands.
