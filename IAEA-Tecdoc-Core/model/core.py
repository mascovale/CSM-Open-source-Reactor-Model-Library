"""
core.py
-------
Central driver for the IAEA TECDOC-643 Appendix A-2 Generic 10 MW LEU
Research Reactor OpenMC model.

Single control surface: edit CoreConfig (or use the CLI) — everything else
(materials, geometry, settings, tallies) is assembled by build_model() so
every run goes through one code path with tallies attached.

CLI examples (from the repo root, conda env `openmc-env`):
    python model/core.py                               # defaults (all-in)
    python model/core.py --insertion 0 --particles 50000 --batches 150
    python model/core.py --insertion 68.5 --output-dir run_results/crit_search

BLADE DIRECTION CONVENTION (read this before touching insertion logic):
    CoreConfig.blade_insertion_percent is the INTUITIVE control-room sense:
        0   = blades fully WITHDRAWN  (core most reactive)
        100 = blades fully INSERTED   (absorber spans the active fuel)
    geometry.build_core_geometry() takes a WITHDRAWAL fraction f:
        f = 0.0 fully INSERTED, f = 1.0 fully WITHDRAWN
    build_model() converts: f_withdrawal = 1.0 - blade_insertion_percent/100.
"""

import argparse
import os
import pathlib
import sys
from dataclasses import dataclass, field, asdict

# Flat imports (materials.py, geometry.py, ... live in this directory)
_MODEL_DIR = pathlib.Path(__file__).resolve().parent
if str(_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_MODEL_DIR))

import openmc

# Local fallback only — the OPENMC_CROSS_SECTIONS env var takes precedence
# (set it in the Slurm submission script on the cluster).
_LOCAL_CROSS_SECTIONS = '/home/tmccoy/nuclear-data/endfb-viii.0-hdf5/cross_sections.xml'


# =============================================================================
# CONFIG
# =============================================================================

@dataclass
class CoreConfig:
    """All run knobs in one place. CLI overrides via main()."""
    # Blade position — intuitive sense: 0 = fully withdrawn, 100 = fully
    # inserted. See module docstring for the conversion to withdrawal fraction.
    blade_insertion_percent: float = 0.0

    # Eigenvalue run statistics
    particles: int = 50000
    batches:   int = 200
    inactive:  int = 50
    seed:      int | None = None          # None → OpenMC default (1)

    # Paths
    output_dir: str = 'run_results/core_run'
    cross_sections: str | None = None     # None → env var, then local fallback

    # Temperature treatment (materials without an explicit temperature
    # evaluate at 'default'; flux-trap water sets its own 316.8 K).
    temperature: dict = field(
        default_factory=lambda: {'method': 'interpolation', 'default': 294.0})

    # ── Depletion scaffold (NOT executed in this pass) ───────────────────────
    # TODO: ADDER-OpenMC coupling — confirm chain file, power basis, steps.
    chain_file: str | None = None          # e.g. chain_endfb80_pwr.xml
    power_w: float = 10.0e6                # 10 MW nominal core power
    depletion_timesteps: list = field(default_factory=list)   # e.g. [(30, 'd'), ...]
    depletion_integrator: str = 'predictor'                    # or 'cecm', ...


def resolve_cross_sections(cfg: CoreConfig) -> str:
    """Prefer OPENMC_CROSS_SECTIONS, then cfg override, then local fallback."""
    env = os.environ.get('OPENMC_CROSS_SECTIONS')
    if env:
        source, path = 'OPENMC_CROSS_SECTIONS env var', env
    elif cfg.cross_sections:
        source, path = 'CoreConfig.cross_sections', cfg.cross_sections
    else:
        source, path = 'local fallback path', _LOCAL_CROSS_SECTIONS
    print(f"[core] cross_sections from {source}: {path}")
    openmc.config['cross_sections'] = path
    return path


# =============================================================================
# MODEL ASSEMBLY
# =============================================================================

def build_model(cfg: CoreConfig) -> openmc.Model:
    """Assemble materials + geometry + settings + tallies into one Model."""
    resolve_cross_sections(cfg)

    # CRITICAL direction conversion — geometry uses WITHDRAWAL fraction
    # (f=0 fully inserted, f=1 fully withdrawn); cfg uses INSERTION percent
    # (0 withdrawn, 100 inserted). These are opposite senses:
    if not 0.0 <= cfg.blade_insertion_percent <= 100.0:
        raise ValueError(
            f"blade_insertion_percent must be in [0, 100], "
            f"got {cfg.blade_insertion_percent}")
    f_withdrawal = 1.0 - cfg.blade_insertion_percent / 100.0

    from materials import materials
    from geometry import build_core_geometry
    from settings import settings
    from tallies import build_tallies

    geometry = build_core_geometry(withdrawn_fraction=f_withdrawal)

    settings.particles   = cfg.particles
    settings.batches     = cfg.batches
    settings.inactive    = cfg.inactive
    settings.temperature = cfg.temperature
    if cfg.seed is not None:
        settings.seed = cfg.seed

    return openmc.Model(
        geometry=geometry,
        materials=materials,
        settings=settings,
        tallies=build_tallies(),
    )


# =============================================================================
# EIGENVALUE RUN
# =============================================================================

def run_eigenvalue(cfg: CoreConfig):
    """Build and run one eigenvalue calculation; return keff (ufloat)."""
    model = build_model(cfg)

    out = pathlib.Path(cfg.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[core] insertion={cfg.blade_insertion_percent:.1f}% "
          f"(withdrawal f={1.0 - cfg.blade_insertion_percent / 100.0:.3f})  "
          f"{cfg.particles} p/batch, {cfg.batches} batches "
          f"({cfg.inactive} inactive)  ->  {out}")

    sp_path = model.run(cwd=str(out))
    with openmc.StatePoint(sp_path) as sp:
        keff = sp.keff
    print(f"[core] keff = {keff.nominal_value:.5f} +/- {keff.std_dev:.5f}")
    return keff


# =============================================================================
# DEPLETION SCAFFOLD — framework only, nothing here runs in this pass
# =============================================================================

def build_depletion_operator(model: openmc.Model, chain_file: str, **kwargs):
    """Construct an openmc.deplete CoupledOperator for this model.

    TODO: ADDER-OpenMC coupling — decide operator type (CoupledOperator vs
    ADDER-driven flux/microXS handoff), normalization mode, and diff_burnable_mats
    for per-element depletion.
    """
    raise NotImplementedError(
        "Depletion scaffold only — not wired up in this pass. "
        "TODO: ADDER-OpenMC coupling.")
    # import openmc.deplete
    # return openmc.deplete.CoupledOperator(model, chain_file=chain_file, **kwargs)


def run_depletion(cfg: CoreConfig):
    """Run a depletion sequence from the CoreConfig placeholders.

    TODO: ADDER-OpenMC coupling — fill in:
      * cfg.chain_file           (depletion chain XML for ENDF/B-VIII.0)
      * cfg.power_w / power density basis (10 MW nominal)
      * cfg.depletion_timesteps  (burn steps + units)
      * cfg.depletion_integrator ('predictor', 'cecm', ...)
    """
    raise NotImplementedError(
        "Depletion scaffold only — not wired up in this pass. "
        "TODO: ADDER-OpenMC coupling.")
    # model = build_model(cfg)
    # op = build_depletion_operator(model, cfg.chain_file)
    # integrator = {
    #     'predictor': openmc.deplete.PredictorIntegrator,
    #     'cecm':      openmc.deplete.CECMIntegrator,
    # }[cfg.depletion_integrator](op, cfg.depletion_timesteps, power=cfg.power_w)
    # integrator.integrate()


# =============================================================================
# CLI
# =============================================================================

def main(argv=None):
    p = argparse.ArgumentParser(
        description='TECDOC-643 10 MW LEU core — central OpenMC driver')
    p.add_argument('--insertion', type=float, default=None, metavar='PCT',
                   help='blade insertion %% (0 = fully withdrawn, '
                        '100 = fully inserted)')
    p.add_argument('--particles', type=int, default=None)
    p.add_argument('--batches', type=int, default=None)
    p.add_argument('--inactive', type=int, default=None)
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--output-dir', type=str, default=None)
    args = p.parse_args(argv)

    cfg = CoreConfig()
    if args.insertion is not None:
        cfg.blade_insertion_percent = args.insertion
    if args.particles is not None:
        cfg.particles = args.particles
    if args.batches is not None:
        cfg.batches = args.batches
    if args.inactive is not None:
        cfg.inactive = args.inactive
    if args.seed is not None:
        cfg.seed = args.seed
    if args.output_dir is not None:
        cfg.output_dir = args.output_dir

    print(f"[core] config: { {k: v for k, v in asdict(cfg).items() if not k.startswith('depletion') and k != 'chain_file'} }")
    run_eigenvalue(cfg)


if __name__ == '__main__':
    main()
