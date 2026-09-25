"""
This module generates fixed-source fission-matrix (FM) OpenMC run inputs for
a MARVEL reactor model. Ported from the JSI TRIGA model generator.

Classes:
    FissionMatrixRuns: generates 'local' or 'global' FM run(s) for a reactor
"""

import logging
import os
from typing import ClassVar

import numpy as np
import openmc


logger = logging.getLogger(__name__)
MRD = 10  # decimal digits kept in source box coordinates


class FissionMatrixRuns:
    """ Generates fixed-source fission-matrix (FM) OpenMC run inputs for a
    reactor, one independent neutron source per fuel cell
    (`reactor.fuel_cells`: rod x radial ring x azimuthal sector x axial
    segment), switching the model from criticality to fixed source. See `generate` for the 'local'/'global' modes.

    Attributes:
        reactor (Reactor): owning reactor instance.
    """

    # Default per-source-region particle budget, split over 100 batches, so
    # that every fuel cell's source region accumulates ~1e6 particles
    # regardless of mode (see `generate`).
    _PARTICLES_PER_CELL_PER_BATCH = 10000
    _DEFAULT_BATCHES = 100

    _DEFAULT_SLURM_OPTIONS: ClassVar[dict] = {
        'job_name': 'marvel_fm',
        'partition': None,
        'account': None,
        'time': '1-00:00:00',
        'cpus_per_task': 4,
        'mem': '8G',
        'modules': [],
        'conda_env': None,
        'openmc_cmd': 'openmc',
        'min_mem_per_job_gb': 1,
    }

    def __init__(self, reactor):
        """ Initializes the FM run generator.

        Args:
            reactor (Reactor): reactor to generate FM runs for.
        """
        self.reactor = reactor

    def generate(
        self,
        mode: str = 'global',
        output_dir: str = 'fm_runs',
        *,
        particles: int | None = None,
        batches: int | None = None,
        energy: 'openmc.stats.Univariate | None' = None,
        slurm: bool = True,
        slurm_options: dict | None = None,
    ) -> str:
        """ Generates fixed-source fission-matrix (FM) OpenMC input files.
        Input files only are written - no OpenMC run is launched.

        In 'local' mode, a separate run is generated for every fuel cell,
        each with its own source confined (via a cell domain constraint,
        redundantly reinforced with a 'fissionable' constraint) to that one
        cell, in `<output_dir>/source_XXX/` (XXX from 001 to the number of
        fuel cells).

        In 'global' mode, a single run is generated with one source per
        fuel cell, all active at once with equal (unweighted) strength,
        directly in `<output_dir>/`. Every cell gets an equal share of the
        run's particle budget regardless of its own volume, matching
        'local' mode's convention - see `_generate_global_run`.

        `output_dir` holds either a 'local' or a 'global' run at a time -
        the two layouts are not namespaced separately, so generating one
        after the other into the same `output_dir` will mix their files.

        A SLURM submission script (`submit_fm_<mode>.sh`) is also written
        into the run directory unless `slurm` is False. It is always a
        single job: for 'local' mode, the job loops over every source_XXX
        subfolder itself, running them in parallel across the job's
        allocated CPUs via `xargs -P`, one `openmc` process per source at
        first - but since each process is assumed to need at least
        `min_mem_per_job_gb` GB, the script caps how many run concurrently
        to what the job's allocated memory can support, handing any CPUs
        freed up by that cap to the remaining processes as OpenMP threads
        (`OMP_NUM_THREADS`) instead of leaving them idle; for 'global'
        mode, it runs the one `openmc` process directly, using all
        allocated CPUs as OpenMP threads. Either way, the script prints
        its total wall-clock execution time at the end of the SLURM log
        once the run(s) finish.

        Args:
            mode (str): 'global' or 'local' (see above).
            output_dir (str): directory in which the 'local'/'global' run
                tree is generated; default 'fm_runs'.
            particles (int, optional): source particles per batch for the
                generated fixed-source run(s). Defaults to giving every fuel
                cell's source region ~1e6 particles total over `batches`
                batches: 10000 in 'local' mode (each per-cell run has its
                own dedicated source), or `10000 * len(reactor.fuel_cells)`
                in 'global' mode, since there every cell's source only gets
                an equal share of the one run's particle budget (see
                `_generate_global_run`) rather than a dedicated one.
            batches (int, optional): number of batches for the generated
                fixed-source run(s) (default: 100).
            energy (openmc.stats.Univariate, optional): energy distribution
                shared by every generated source; defaults to a Watt fission
                spectrum.
            slurm (bool, optional): whether to also write a SLURM submission
                script (default: True).
            slurm_options (dict, optional): overrides for the SLURM script;
                see `_DEFAULT_SLURM_OPTIONS` for the recognized keys
                ('job_name', 'partition', 'account', 'time',
                'cpus_per_task', 'mem', 'modules', 'conda_env',
                'openmc_cmd', 'min_mem_per_job_gb'). 'min_mem_per_job_gb'
                (default: 1) is the assumed memory footprint of a single
                'local'-mode `openmc` process, used to cap how many run
                concurrently under the job's allocated memory.

        Returns:
            str: path to the generated run directory (`output_dir`).

        Raises:
            ValueError: if `mode` is not 'global'/'local', if the reactor
                has no fuel cells, or if 'local' mode is requested with more
                than 999 fuel cells (exceeds the 'source_XXX' naming scheme).
        """
        if mode not in ('global', 'local'):
            raise ValueError(f"mode must be 'global' or 'local' (got {mode!r})")

        reactor = self.reactor
        fuel_cells = reactor.fuel_cells
        n_cells = len(fuel_cells)
        if n_cells == 0:
            raise ValueError("Reactor has no fissionable fuel cells.")
        if mode == 'local' and n_cells > 999:
            raise ValueError(
                "'local' mode supports at most 999 fuel cells for the "
                f"'source_XXX' naming scheme ({n_cells} found)."
            )

        tally_names = [t.name for t in reactor.model.tallies]
        if 'fm_raw' not in tally_names:
            logger.warning(
                "Reactor model has no 'fm_raw' tally; generated fixed-source "
                "runs will not produce fission-matrix results."
            )

        if batches is None:
            batches = self._DEFAULT_BATCHES
        if particles is None:
            particles = self._PARTICLES_PER_CELL_PER_BATCH
            if mode == 'global':
                particles *= n_cells

        energy = energy if energy is not None else openmc.stats.Watt()
        base_dir = output_dir
        os.makedirs(base_dir, exist_ok=True)

        original_settings = reactor.model.settings
        try:
            if mode == 'local':
                self._generate_local_runs(
                    base_dir, fuel_cells, particles, batches, energy)
            else:
                self._generate_global_run(
                    base_dir, fuel_cells, particles, batches, energy)
        finally:
            reactor.model.settings = original_settings

        if slurm:
            self._write_slurm_script(base_dir, mode, n_cells, slurm_options)

        return base_dir

    def _generate_local_runs(self, base_dir, fuel_cells, particles,
                             batches, energy):
        """ Generates one fixed-source run per fuel cell, each confined to
        that single cell, under `base_dir/source_XXX/`.

        Args:
            base_dir (str): 'local' mode run directory.
            fuel_cells (tuple of openmc.Cell): fuel cells to generate
                sources for (see `Reactor.fuel_cells`).
            particles (int): source particles per batch.
            batches (int): number of batches.
            energy (openmc.stats.Univariate): shared source energy
                distribution.
        """
        reactor = self.reactor
        for idx, cell in enumerate(fuel_cells, start=1):
            source = self._build_source(cell, energy)
            settings = self._fixed_source_settings(particles, batches, source)

            subdir = os.path.join(base_dir, f'source_{idx:03d}')
            os.makedirs(subdir, exist_ok=True)

            reactor.model.settings = settings
            reactor.model.export_to_xml(directory=subdir)

    def _generate_global_run(self, base_dir, fuel_cells, particles,
                             batches, energy):
        """ Generates a single fixed-source run with one source per fuel
        cell, all active at once with equal (unweighted) strength, under
        `base_dir`.

        Every cell gets an equal share of the run's particle budget
        regardless of its own volume - matching 'local' mode's convention,
        where every per-cell run also gets an equal (indeed, the same
        dedicated) particle budget. No source-strength weighting or
        extraction-side renormalization is needed for this run type as a
        result.

        Args:
            base_dir (str): 'global' mode run directory.
            fuel_cells (tuple of openmc.Cell): fuel cells to generate
                sources for (see `Reactor.fuel_cells`).
            particles (int): source particles per batch.
            batches (int): number of batches.
            energy (openmc.stats.Univariate): shared source energy
                distribution.
        """
        reactor = self.reactor
        sources = []
        for cell in fuel_cells:
            sources.append(self._build_source(cell, energy, strength=1.0))

        settings = self._fixed_source_settings(particles, batches, sources)
        reactor.model.settings = settings
        reactor.model.export_to_xml(directory=base_dir)

    def _fuel_cell_box(self, cell):
        """ Computes the axis-aligned box bounding a fuel cell in global
        coordinates: the full fuel cross section of its rod (radial rings and
        azimuthal sectors are rejected by the cell domain constraint) over
        the cell's axial segment, with a small radial pad and axial shrink
        (keeps the box off the boundary with neighboring axial segments).

        Args:
            cell (openmc.Cell): fuel cell.

        Returns:
            tuple: (lower_left, upper_right), each a 3-tuple of floats.
        """
        info = self.reactor.fuel_cell_info(cell)
        eps = 1.0e-6
        lower_left = np.round(
            (info.x - info.r_out - eps, info.y - info.r_out - eps, info.z_bot + eps), MRD)
        upper_right = np.round(
            (info.x + info.r_out + eps, info.y + info.r_out + eps, info.z_top - eps), MRD)
        return tuple(lower_left), tuple(upper_right)

    def _build_source(self, cell, energy, strength=1.0):
        """ Builds an independent neutron source confined to a single fuel
        cell.

        The source's spatial box bounds the cell (see `_fuel_cell_box`).
        Sampled sites are then constrained to fall within the cell itself,
        with a redundant 'fissionable' constraint since every fuel cell is,
        by construction, fissionable.

        Args:
            cell (openmc.Cell): fuel cell the source should be confined to.
            energy (openmc.stats.Univariate): source energy distribution.
            strength (float, optional): source strength (default: 1.0).

        Returns:
            openmc.IndependentSource: source confined to `cell`.
        """
        lower_left, upper_right = self._fuel_cell_box(cell)
        spatial = openmc.stats.Box(lower_left, upper_right)

        return openmc.IndependentSource(
            space=spatial,
            angle=openmc.stats.Isotropic(),
            energy=energy,
            particle='neutron',
            strength=strength,
            constraints={
                'domains': [cell],
                'fissionable': True,
                'rejection_strategy': 'resample',
            },
        )

    @staticmethod
    def _fixed_source_settings(particles, batches, source):
        """ Builds a fresh fixed-source openmc.Settings for a FM run.

        Args:
            particles (int): source particles per batch.
            batches (int): number of batches.
            source (openmc.IndependentSource or list of openmc.IndependentSource):
                source(s) for the run.

        Returns:
            openmc.Settings: fixed-source settings.
        """
        settings = openmc.Settings()
        settings.run_mode = 'fixed source'
        settings.particles = int(particles)
        settings.batches = int(batches)
        settings.source = source
        # First-generation response only, needed for a fission-matrix tally:
        # in fixed-source mode create_fission_neutrons=False stops OpenMC
        # from banking any new fission-neutron sites at all, so a source
        # particle's history ends at its own terminal fission rather than
        # spawning further generations. create_delayed_neutrons stays at
        # its default (True) - fission matrix coefficients should reflect
        # total (prompt + delayed) neutron yield per fission.
        settings.create_fission_neutrons = False
        settings.create_delayed_neutrons = True
        return settings

    def _write_slurm_script(self, base_dir, mode, n_cells, slurm_options):
        """ Writes a SLURM submission script for the FM run(s) generated in
        `base_dir`. Always a single job (no SLURM job array): in 'local'
        mode the job itself loops over every source_XXX subfolder, running
        them in parallel across the job's allocated CPUs, capped so that
        no more processes run concurrently than the job's allocated memory
        supports at `min_mem_per_job_gb` GB each - any CPUs freed up by
        that cap are handed to the remaining processes as OpenMP threads;
        in 'global' mode it runs the single `openmc` process directly.

        Args:
            base_dir (str): 'local'/'global' mode run directory.
            mode (str): 'global' or 'local'.
            n_cells (int): number of fuel cells (loop bound, 'local' mode
                only).
            slurm_options (dict or None): overrides for
                `_DEFAULT_SLURM_OPTIONS`.

        Returns:
            str: path to the written submission script.
        """
        opts = dict(self._DEFAULT_SLURM_OPTIONS)
        if slurm_options:
            opts.update(slurm_options)

        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        lines = ['#!/bin/bash']
        lines.append(f"#SBATCH --job-name={opts['job_name']}_{mode}")
        lines.append("#SBATCH --output=logs/slurm-%j.out")
        lines.append("#SBATCH --error=logs/slurm-%j.err")
        if opts.get('partition'):
            lines.append(f"#SBATCH --partition={opts['partition']}")
        if opts.get('account'):
            lines.append(f"#SBATCH --account={opts['account']}")
        lines.append(f"#SBATCH --time={opts['time']}")
        lines.append(f"#SBATCH --cpus-per-task={opts['cpus_per_task']}")
        if opts.get('mem'):
            lines.append(f"#SBATCH --mem={opts['mem']}")
        lines.append('')
        lines.append(
            '# Cluster-specific: pass partition/account/modules/conda_env '
            'via slurm_options={...} to generate_fm_runs().'
        )
        for module in opts.get('modules') or []:
            lines.append(f'module load {module}')
        if opts.get('conda_env'):
            # sbatch runs this script in a non-interactive, non-login shell,
            # where `conda activate` is not yet a shell function - sourcing
            # conda.sh (found via `conda info --base`, so this works on any
            # machine/conda install location) defines it first.
            lines.append('CONDA_BASE="$(conda info --base)"')
            lines.append('source "${CONDA_BASE}/etc/profile.d/conda.sh"')
            lines.append(f"conda activate {opts['conda_env']}")
        lines.append('')
        # sbatch copies the batch script into a spool directory before
        # executing it, so "$0" does not reliably point back at this run
        # directory under SLURM - $SLURM_SUBMIT_DIR (the directory `sbatch`
        # was invoked from) is the reliable one there. Falls back to the
        # script's own directory for manual/non-SLURM execution.
        lines.append(
            'cd "${SLURM_SUBMIT_DIR:-$(dirname "$(readlink -f "$0")")}"'
        )
        lines.append('')
        # Falls back to the logical CPU count (nproc) when not running under
        # SLURM (SLURM_CPUS_PER_TASK unset) - e.g. testing this script
        # directly on a login/dev node - rather than hardcoding serial (1).
        lines.append('TOTAL_CPUS=${SLURM_CPUS_PER_TASK:-$(nproc)}')
        lines.append('START_TIME=$(date +%s)')
        lines.append('')
        if mode == 'local':
            # Each concurrent openmc process is assumed to need at least
            # min_mem_per_job_gb GB, so cap how many run at once to what
            # the job's allocated memory supports, and hand any CPUs freed
            # up by that cap to the remaining processes as OpenMP threads
            # instead of leaving them idle (e.g. 64 CPUs/16 GB with a 1
            # GB/job floor -> 16 concurrent processes, 4 threads each).
            # Reads the job's actual memory allocation at run time, the
            # same way TOTAL_CPUS does above, rather than trusting the
            # --mem value baked into the #SBATCH header (sbatch/salloc
            # overrides on the command line take precedence over it).
            lines.append('if [ -n "${SLURM_MEM_PER_NODE:-}" ]; then')
            lines.append('    TOTAL_MEM_MB=$SLURM_MEM_PER_NODE')
            lines.append('elif [ -n "${SLURM_MEM_PER_CPU:-}" ]; then')
            lines.append(
                '    TOTAL_MEM_MB=$((SLURM_MEM_PER_CPU * TOTAL_CPUS))')
            lines.append('else')
            lines.append(
                "    TOTAL_MEM_MB=$(free -m | awk '/^Mem:/{print $2}')")
            lines.append('fi')
            lines.append(
                f'MIN_MEM_PER_JOB_MB=$(({opts["min_mem_per_job_gb"]} * 1024))'
            )
            lines.append(
                'MAX_PARALLEL_BY_MEM=$((TOTAL_MEM_MB / MIN_MEM_PER_JOB_MB))')
            lines.append(
                '[ "$MAX_PARALLEL_BY_MEM" -lt 1 ] && MAX_PARALLEL_BY_MEM=1')
            lines.append('N_PARALLEL=$TOTAL_CPUS')
            lines.append(
                '[ "$MAX_PARALLEL_BY_MEM" -lt "$N_PARALLEL" ] '
                '&& N_PARALLEL=$MAX_PARALLEL_BY_MEM')
            lines.append('CPUS_PER_JOB=$((TOTAL_CPUS / N_PARALLEL))')
            lines.append(
                'echo "Running ${N_PARALLEL} job(s) in parallel, '
                '${CPUS_PER_JOB} CPU(s) each '
                '(${TOTAL_CPUS} CPUs, ${TOTAL_MEM_MB} MB total)"'
            )
            lines.append('export OMP_NUM_THREADS=$CPUS_PER_JOB')
            lines.append(
                f'seq -f "source_%03g" 1 {n_cells} | xargs -I{{}} '
                '-P "$N_PARALLEL" '
                f'bash -c \'cd "{{}}" && {opts["openmc_cmd"]}\''
            )
        else:
            lines.append('export OMP_NUM_THREADS="$TOTAL_CPUS"')
            lines.append(opts['openmc_cmd'])
        lines.append('')
        lines.append('END_TIME=$(date +%s)')
        lines.append('ELAPSED=$((END_TIME - START_TIME))')
        lines.append(
            'printf "Execution time: %02d:%02d:%02d (%d s)\\n" '
            '$((ELAPSED/3600)) $((ELAPSED%3600/60)) $((ELAPSED%60)) '
            '"${ELAPSED}"'
        )

        script = '\n'.join(lines) + '\n'
        script_path = os.path.join(base_dir, f'submit_fm_{mode}.sh')
        with open(script_path, 'w') as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        return script_path
