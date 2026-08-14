# TESTAMENT III — Phase 1 Close-Out and Phase 2 Handoff

**Date:** 2026-08-04
**Supersedes:** `PROJECT_BIBLE.md` (2026-07-06) and `TESTAMENT_II` (2026-07-20), both
of which are stale in specific, listed ways. See §9.
**Status of Phase 1 geometry:** closed. Cross-validation itself has not started.

---

## 0. How to read this document

This is the third summarizing document in the project's history, and the second
one regressed against the first. That happened because it **restated** geometry
in prose instead of **citing** what it superseded — and an absence is invisible.
See §9.3, which is the most important process finding in the project.

So this document follows one rule, and any successor must too:

> **Cite claims to their source. Do not restate them.**
> A summary that writes "graphite block 7.6 x 8.0 [Bible §5]" cannot silently
> regress. One that re-derives geometry from scratch can.

Where a value is given below, its provenance tag comes with it. Where a claim
supersedes an earlier one, the superseded text and the commit that replaced it
are named.

---

## 1. What Phase 1 was, and what closed

**Task 1 (fresh-core cross-validation) is NOT complete.** Phase 1 geometry —
making the OpenMC model match the reference MCNP model dimension for dimension —
is what closed. The comparison against Kyle's reference k-eff values has not
been performed on a matched library and is Phase 2 work.

Success criterion for Phase 1 was the cross-validation spreadsheet reaching
MATCH, **not** k-eff agreement. That distinction was load-bearing throughout and
must survive into Phase 2: k-eff was a tripwire (does it build, does it run, is
the magnitude sane, do the blades move it the right way), never a target.

### The B-series — four geometry changes

| ID | Change | Provenance |
|---|---|---|
| B1 | Axial plate extension: 62 cm plates, 60 cm meat, 1 cm unfueled clad each end, end-box 15 -> 14 cm | `[MCNP]` |
| B2 | Flux trap and graphite reflector blocks 7.7x8.1 -> 7.6x8.0 (1 mm water gap to pitch) | `[MCNP]` |
| B3 | Absorber blade width 6.640 -> 6.630 | `[MCNP]` |
| B4 | Pool water boundary 38.5 cm on all four sides; lattice reduced to the 6x7 core positions | `[MCNP]` |

### The A-series — four spec items from Kyle

| ID | Item | Resolution |
|---|---|---|
| A1 | Flux trap water hole radius | 2.500 -> **2.820** (area-equivalent to the 50 mm square hole, 25 cm² -> r = 2.8209) |
| A2 | Graphite density | No mass density. **Atom density 8.724000E-02** direct from reference MCNP card `m00005` |
| A3 | Control element outer water | `CTRL_OUTER_OFFSET` 0.1075 -> **0.1305**, de-aliased from `STD_END_WATER`; `CTRL_BLADE_WATER` derives to 0.1275 |
| A4 | Blade top cladding | **1.0 cm of aluminium, top end only.** No side clad, no bottom clad |

### Everything else that landed

Provenance tagging and citation to TECDOC-643 A-2 Table 1; U-235 inventory
asserts; run provenance capture; the `core.py` output guard; terminology
correction; a full-repo audit and its corrections; SolidWorks export brought
current; spreadsheet verified against code constant by constant.

---

## 2. The axial stack — the single most consequential change

B1 is the change most likely to be misunderstood later, because "plates got
longer" is the wrong description.

```
-90 -> -45   45 cm   water
-45 -> -31   14 cm   homogenized end-box
-31 -> -30    1 cm   unfueled clad extension
-30 -> +30   60 cm   active meat
+30 -> +31    1 cm   unfueled clad extension
+31 -> +45   14 cm   homogenized end-box
+45 -> +90   45 cm   water
```

Sum: 2 x (45 + 14 + 1 + 30) = 180. Asserted.

**What actually changed physically:** the [30, 31] and [-31, -30] bands were
25 v/o Al / 75 v/o water homogenate and are now resolved cladding and open
coolant. The correct description is *"resolve end-box homogenate into clad and
coolant over ±30–31"*, not *"extend plates to 62 cm"*. Slightly less Al,
slightly more moderator, resolved rather than smeared.

**The coolant channels extend too.** Every channel, gap, and side plate goes to
±31 alongside the clad — only the meat stays at ±30. This is not optional: if
solids extended and channels did not, the [30, 31] band in every channel
footprint would be undefined space — 22 per standard element, 506 across the
core. It would pass an overlap check and leak particles. Channel height is
`[DERIVED]` off `PLATE_HEIGHT`; the spreadsheet has no channel-height row.

**Constant restructuring this forced.** `HALF_Z` was `ELEM_Z / 2.0`. Setting
`ELEM_Z = 62` would have silently moved the active meat to ±31, dragging blade
travel and depletion zoning with it. `HALF_Z` is now re-parented to
`MEAT_HEIGHT`, and `MEAT_HEIGHT` — previously derived backwards off the ±30
planes — became primary.

---

## 3. The pool boundary and the lattice

38.5 cm of water on all four lateral sides. The arithmetic that pins it:

- X: 6 positions x 7.7 + 2 x 38.5 = **123.200**
- Y: 7 positions x 8.1 + 2 x 38.5 = **133.700**
- Z: unchanged at **180.000**

**It cannot be lattice-tiled.** 38.5 = 5 x 7.7 exactly in x, but 38.5 / 8.1 =
4.75 in y. Implemented as an explicit water-filled bounding box around the
lattice universe, with vacuum on its faces. Using the complement of the core box
rather than four hand-written slabs is deliberate — it is watertight at the
corners, which is where a slab decomposition would leave undefined space.

Pool water is the **294 K bulk** material, not the 316.8 K core coolant.

Measured effect: leakage fraction is now **0.0005**. Effectively nothing escapes.
This is the clearest single confirmation that B4 landed correctly — more
informative than k-eff itself.

---

## 4. Terminology — three cases, all correct, all different

This was corrected twice and the final form is:

| Figure | Means | Cite when |
|---|---|---|
| **5 x 6** | Active core geometry: 30 fueled + irradiation positions. **Excludes the 12 graphite reflector positions.** | Citing TECDOC-643 A-2 Table 1's "Active Core Geometry" |
| **8 x 9** | Grid plate, including the surrounding water ring | Citing Table 1's "Grid Plate" row |
| **6 x 7** | The OpenMC lattice as built: 42 positions (23 standard + 5 control + 2 flux traps + 12 graphite) | Describing the model's lattice extent |

**"7 x 6" is retired** as a description of the core. It appeared in Kyle's
spreadsheet column and was carried forward wrongly.

**Do not "simplify" the lattice to 5 x 6.** `N_LAT_X = 6`, `N_LAT_Y = 7`,
`CORE_HALF_X = 23.100`, `CORE_HALF_Y = 28.350`, and the entire 38.5 cm pool
arithmetic depend on the 42-position lattice. The lattice must hold the graphite;
the core does not include it.

`CORE_HALF_X/Y` are **lattice** half-extents despite the name. Renaming would
touch three files for no physical gain; the inconsistency is recorded in-code
and in `SUPERSEDED_NOTES.md` §6 instead. `tallies.py`'s flux mesh spans them —
so it covers the graphite rows, not just fuel. Its docstring said "core
footprint" and was wrong; corrected.

---

## 5. Materials — final state

| Material | Density basis | T (K) | S(α,β) |
|---|---|---|---|
| Fuel U₃Si₂-Al | sum | 332.1 | none |
| Cladding Al-6061 | 2.70 g/cm³ | 330.7 | `c_Al27` |
| Structural Al | 2.70 g/cm³ | 330.7 | `c_Al27` |
| Blade top clad | *same object as structural Al* | 330.7 | `c_Al27` |
| Core water | sum | 316.8 | `c_H_in_H2O` |
| Pool water | sum | 294.0 | `c_H_in_H2O` |
| End-box homogenized (25 v/o Al + 75 v/o core water) | sum | 316.8 | `c_H_in_H2O` **and** `c_Al27` |
| Graphite | **atom density 8.724000E-02** | 294.0 | `c_Graphite` |
| B₄C | sum | 294.0 | none |

`USE_AL_SAB = True` by default, covering all three Al sites including the
end-box fraction.

### 5.1 Graphite — the value that moved three times

`1.70 -> 1.74 -> 2.26 -> 8.724000E-02 atom/b-cm`. The sequence matters because
it is the justification for the final `[MCNP]` tag:

1. **1.7000 `[TECDOC]`** — recorded in Testament II as a 7/20 meeting decision.
   TECDOC-643 specifies **no graphite density at all**. The tag was unsupported.
   The value was never implemented; only the comment carried it.
2. **1.7400** — what the code actually ran, tagged `[model-INFERRED]`.
3. **2.26** — Claude's reading of Kyle's "natural density" as the single-crystal
   value. **Committed (10f607f), then rejected by Kyle.** The commit is
   deliberately left in history; the log showing a value committed and corrected
   *is* the provenance record.
4. **8.724000E-02 atom/b-cm `[MCNP]`** — direct from card `m00005`, pasted
   verbatim by the model owner. Commit 6288fb4 supersedes 10f607f.

**It back-converts to 1.74000 g/cm³** using OpenMC's isotopic masses
(M_eff = 12.01112), a 0.0003% difference. So step 2 was this same number
round-tripped through a lossy mass-density conversion. The final change is a
**provenance and method fix, not a physics change** — phrase it that way in the
manuscript.

### 5.2 ZAID 6000 and the carbon problem

Kyle's card uses `6000` — **natural elemental carbon**, unsplit. OpenMC's
`add_element('C')` expands to C12/C13 using its own abundance table
(0.988922 / 0.011078, which differs from the IUPAC representative composition
0.9893 / 0.0107 — this is OpenMC's table by design, do not "correct" it).

The C-12 and C-13 spreadsheet rows are **N/A** on the MCNP side, not blank. It is
a method difference, not a missing value.

**This has already bitten once on the cluster.** See §8.2.

---

## 6. The verification discipline that caught things

Recorded because it worked, repeatedly, and Phase 2 should keep it.

**Plan-then-approve.** No production file touched before an explicit plan with
old -> new values and every cascaded constant. Caught the `HALF_Z` re-parenting
trap before it silently moved the active meat.

**Overlap checks at f = 0.0, 0.5, 0.99, 1.0, plus an explicit lost-particle
scan.** An overlap pass is *necessary, not sufficient* — cell deletions create
undefined space that passes overlap checks and leaks particles. Two such cases
were caught before they landed: the control-element slot water needing to extend
to −31, and B3's 0.005 cm blade side slivers. f = 0.99 was added specifically
because between f = 59/60 and f = 1.0 the blade cap is gone while the clad is
only partially clipped — a configuration nothing else exercised.

**Derive, never hardcode.** `CTRL_BLADE_WATER` is a residual.
`ABSORBER_SIDE_WATER` is derived. `BLADE_TOP_CLAD` derives from `CLAD_EXT`.
A consequence worth knowing: `ABSORBER_WIDTH + 2*ABSORBER_SIDE_WATER ==
ACTIVE_STACK_X` holds by **exact float equality**, because the noise in the
derived value cancels on the way back through the same subtraction.

**Negative-test the asserts.** Adding an assert proves nothing; injecting the
fault it is meant to catch does. `ABSORBER_THICK = 0.32` fires. The compensating
pair `BLADE_LENGTH 59.0` / `ROD_TRAVEL 61.0` — sum preserved, so the f=1 pin
alone passes — is now caught and previously built silently.

**Structural argument beats statistical.** The blade side sliver was verified by
3.6 M histories with zero losses, but the real proof is that `blade_x` and
`~blade_x` are exact complements inside a shared slot region. Watertight by
construction, not by sampling.

---

## 7. What the audit found, and what it means

A full-repo audit was run at `c45d4b8` and is committed as
`docs/PHASE1_AUDIT.md`.

**It found zero geometry defects.** Every dimension checked out, zero lost
particles at four blade positions, no physics wrong. What it found was one
structural weakness in the asserts, two distribution problems, and one process
finding. That is the normal, good outcome for an audit of well-done work.

### 7.1 The `[MCNP]` tag spans four evidence tiers

No fabricated tag was found — every one traces to a specific written decision.
But `\prvMCNP` renders in the manuscript as *from the reference MCNP model*, and
the tag currently covers:

| Strength | Constants |
|---|---|
| Verbatim card transcription | graphite `m00005` — **one** |
| Spreadsheet MCNP column | `POOL_WATER_THICK`, `ABSORBER_WIDTH`, `ENDBOX_HEIGHT`, `PLATE_HEIGHT` |
| Kyle verbal or relayed | `BLADE_TOP_CLAD`, `CTRL_OUTER_OFFSET` (which he said may not be in the model yet) |
| Structural alias | the four `FT_`/`REFL_BLOCK` constants |

**This needs a manuscript decision before Section 2.3 is written** — either a
footnote defining precisely what `\prvMCNP` asserts, or a split into
confirmed-from-source and confirmed-by-owner.

### 7.2 26 of 69 constants are untagged, and `\prvASM` is empty

These are the same finding. The untagged constants *are* the missing assumed
population. For a project whose central discipline is provenance tracking, 38%
untagged is the headline number.

### 7.3 D3 — the end-block budget closes by construction

`CTRL_BLADE_WATER` is the residual, so the layer-sum asserts **cannot fail**.
The only thing catching an upstream error in `ABSORBER_THICK` is the 0.1275 pin
added at A3. `ABSORBER_THICK` has since been pinned directly.

---

## 8. Cluster — proven working, with the specifics

Argonne RTR HPC (`rtrhpc1`), PBS/Torque, **128 OpenMP threads per node**.
OpenMC **0.15.3**, commit `27e38e89` — **identical to the local build**, so there
is no version skew to reconcile. The 0.15.0 in the old July statepoint is
history, not a live discrepancy.

### 8.1 Verified results, 2026-08-04

500,000 particles x 250 batches, 50 inactive, ENDF/B-VIII.0, ~4 minutes each:

| Case | k-eff | σ (pcm) |
|---|---|---|
| Rods in (f = 0.0) | **0.98027 ± 0.00011** | 11 |
| Rods out (f = 1.0) | **1.19620 ± 0.00010** | 10 |

**Blade worth = 18,458 ± 13 pcm.** Reference is 18,540 — a −82 pcm gap, 0.4%.

**This is not a validation result.** It is VIII.0 against a VII.0-based
reference target. An 82 pcm gap is well inside what a library change alone
produces. It is a very well-converged VIII.0 number that happens to land near
the target.

Corroboration: the rods-in value reproduces the local laptop run (0.98010 ±
0.00037) to 17 pcm. Leakage 0.00052 / 0.00049 across the pair. Three estimators
within 5 pcm.

### 8.2 Cluster gotchas, all encountered and solved

| Symptom | Cause | Fix |
|---|---|---|
| `/bin/bash^M: bad interpreter` | CRLF line endings from Windows | `dos2unix script.pbs` |
| `Could not find nuclide C12` | `endfb71_hdf5` has natural carbon only | Use `endfb80_hdf5`, or `add_nuclide('C0')` |
| Job "succeeds" with no transport | `python x.py \| tee log` discards stderr and returns tee's exit code | `python x.py 2>&1 \| tee log`, add `set -o pipefail` |
| `FileExistsError` on output dir | Staging copies previous results back in | `--output-dir "$LOCAL_TMP/results_$PBS_JOBID"` |
| Statepoint vanishes | Script stages in, never out | `cp -r "$LOCAL_TMP"/results_* "$PBS_O_WORKDIR"/` |
| `git unknown` in provenance | Job runs from `/tmp`, outside the work tree | Capture SHA in `$PBS_O_WORKDIR` before staging |

Available libraries: `endfb71_hdf5`, `endfb80_hdf5` at `/data/EP/openmc/data/`.
**VII.0 presence unconfirmed — this is a Phase 2 blocker.**

### 8.3 Source convergence

Both cases converge by roughly **batch 8** (rods-in climbs 0.9516 -> 0.9804 over
seven batches then oscillates with no trend; rods-out similar). **50 inactive is
generous, not marginal.**

Caveat: this is a k-trend argument, not an entropy measurement. **No run in this
project's history has had a Shannon entropy mesh** — `settings.py` has never
defined one, including for the July production baseline. OpenMC does not report
convergence automatically; it computes entropy per batch only if given a mesh,
and you inspect the trend yourself.

---

## 9. Superseded — what NOT to trust in the older documents

Recorded per claim, with what replaced it. `docs/SUPERSEDED_NOTES.md` carries the
full version with verbatim quotes.

### 9.1 `TESTAMENT_II` (2026-07-20)

| Claim | Now |
|---|---|
| Axial stack "45 / 15 / 60 / 15 / 45" | B1: 45 / 14 / 1 / 60 / 1 / 14 / 45 |
| `FT_HOLE_RADIUS` 2.5 `[ASSUMED]` | A1: 2.820 `[MCNP]` |
| Graphite 1.7000 `[TECDOC]` | A2: 8.724000E-02 atom/b-cm `[MCNP]`, card m00005 |
| Flux trap a full-pitch block | B2: 7.6 x 8.0 |
| Graphite a continuous in-plane wall | B2: discrete 7.6 x 8.0 blocks with 1 mm gaps |
| Cap 15 cm rigidly attached | B1 + A4: 14 cm, riding on the blade top clad |
| Control offset 0.1075 | A3: 0.1305 |
| k-eff 18,853 pcm and the −385 / −556 bias figures | **Retired.** Measured pre-`7660f56`, before the end-box slivers were replaced with full-pitch homogenate — a *correctness fix*. Neither endpoint of "18,853 -> 18,373" was ever measured at a single pinned configuration |
| §T2.2 voids all `[DECK]`-transcribed provenance | Reasoning survives and governs (audit C3 applies exactly that test), but the blanket form would wrongly void card `m00005`, the strongest provenance in the codebase |

### 9.2 `PROJECT_BIBLE.md` (2026-07-06)

8 x 9 lattice; vacuum at z = −65 / +95; graphite 1.70; "verify against the deck's
CYL surface". Also: **Task 1 is not complete**, contrary to its own header.

**Note:** "deck" is forbidden terminology project-wide. Always "MCNP model" or
"reference MCNP model".

### 9.3 The regression — the most important process finding

**Bible §5 described the graphite blocks as 7.6 x 8.0 with thin water gaps to the
pitch boundary. That is correct, and it is what B2 implements.**

Testament II §T2.5 replaced it with "continuous in-plane wall ... inter-block
channels pending the MCNP dimension." The code then carried a TODO in
`make_graphite_element` — *"Dimension is pending — it must come FROM THE MCNP
MODEL; do not invent a channel width"* — actively instructing readers not to
supply a value the project had already written down three weeks earlier.

**The regression did not just lose a fact. It inverted the epistemic status:** a
known quantity became an open question, and the open question was enforced. It
survived eleven days undetected, and B2 was handled all phase as a new
confirmation from Kyle.

**Why it happened:** T2.1 **cites** — a two-column table where every row names
what it overrides; all eleven rows survived. T2.5 **restates** — re-derives
geometry in prose with no reference to what it supersedes. The same document
contains both the safe pattern and the failing one.

**The correct fact was never contradicted. It was not carried forward, and an
absence is invisible.** A citing row can only fail by misstating something you
are looking at; a restating paragraph is a fresh assertion wearing a summary's
authority, and nothing in the process distinguishes the two.

**Two consequences:**

1. The four `FT_BLOCK_X/Y` and `REFL_BLOCK_X/Y` tags flagged in audit C3 as
   structural aliases are **better supported than the audit credited** —
   independently corroborated by a document written before Kyle's confirmation.
2. **Newer summaries are not more reliable than older ones.** When a summary and
   an older source disagree, check the code before assuming the summary is right.
   Supersession must be claim-by-claim, never wholesale.

This is the same mechanism behind the graphite 1.74 insertion and the 18,853
baseline measured on superseded geometry. **Three unrelated errors, one cause.**
The provenance discipline in the code is what caught all three — which is the
argument for the tagging being worth its overhead even when it feels like
bookkeeping.

---

## 10. Open items entering Phase 2

### 10.1 Blocking the matched-library comparison

| Item | Detail |
|---|---|
| **VII.0 availability** | `endfb71` and `endfb80` confirmed on the cluster. VII.0 **unconfirmed**. Kyle's reference values are VII.0. Either it exists, or the comparison moves to a library both sides have |
| **`run_vii_mat.py` rewrite** | Redefines **every** material independently — a full copy of an older `materials.py`, graphite still at 1.70. Two sources of truth, and the stale one is what a matched run would execute. Fix: import from `materials.py`, override only the `USE_NATURAL_CARBON` switch |
| **`C0` vs `C12`/`C13` on VII.0** | VII.0 and VII.1 both carry natural carbon only. `add_element('C')` will fail. `run_vii_mat.py:20` already implements the switch, keyed on `endfb70` |
| **`c_Al27` on VII.0** | Present in VIII.0 (confirmed on the cluster). Unverified on VII.0. If absent, `USE_AL_SAB = False` is **required**, not optional — and that is a method difference worth telling Kyle about |
| **Shannon entropy mesh** | Does not exist and never has. Needed before the numbers that get published |

### 10.2 With Kyle

- Graphite MT card — `m00005` shows the atom density but MT cards are separate in MCNP, so its absence proves nothing. `c_Graphite` on a reflector is a large effect
- Al MT card — he will add Al S(α,β) in his own time; the OpenMC side already has it. **Until both have it, a comparison is a known method difference, not a matched configuration**
- Whether the reference k-eff targets were themselves checked for source convergence
- Outer-pool water H-1 / O-16: 6.669090E-02 vs 6.673560E-02, 0.067% against a 0.010% tolerance, no decision on record. **This matters more since B4** — that material now fills the entire 38.5 cm pool rather than a thin ring
- ~~Depletion zoning — the seven `[MCNP-VISUAL]` claims (5 axial zones x 12 cm, 140 regions), read visually off a zx slice~~
  **ANSWERED 2026-08-12.** Kyle confirmed the reference subdivides **each fuel plate 2 x 10**, and that
  materials should be matched **per plate**. Implemented at `01edb31`: 12,280 meat cells and 12,280
  depletable materials, 1:1, zones 3.15 x 6.0 cm. All seven `[MCNP-VISUAL]` claims are resolved or
  superseded; their records are kept dated in `materials.py`. See the C5 amendment in `PHASE1_AUDIT.md`.
  *Residual:* zone uniformity was the natural reading of "2 x 10", not a separately confirmed statement.
- **NEW, from the same exchange:** ADDER uses CE/CM (`cecm`), CRAM48, 4 substeps — recorded as dormant
  `CoreConfig` fields. Still blocked: no depletion chain file exists on this machine, and OpenMC
  `substeps` needs 0.16.0 for `CECMIntegrator` (we run 0.15.3). Whether ADDER's "substep" means the
  same operation as OpenMC's is `[ASSUMED-EQUIVALENT — needs Kyle]`.
- Whether `0.1305` is in the surface cards or only in the report figure (tag is currently `[MCNP]`, upgraded on his say-so)

### 10.3 MCNP-side rows still marked "will be updated"

Not our action. They stay DIFF until Kyle updates: unfueled plate thickness
(0.150 -> 0.127) and homogenized region X/Y (7.600/8.000 -> 7.700/8.100).

### 10.4 Distribution

The deliverable repo `mascovale/CSM-Open-source-Reactor-Model-Library` is still
serving a **27 July model** — 2.5 cm flux trap, 60 cm plates, no pool. This is
the only finding with outside visibility. `scripts/sync_deliverable.sh` exists,
dry-run by default, refuses a dirty tree, warns on an unpushed branch. Excludes
`docs/`, `run_vii_mat.py`, `plots/`, `run_results/`, XML, HDF5.

### 10.5 Known-stale artifacts

`figures/*.pdf` and `fig1_core_map.png` predate the A-series — regenerate via
`python figures/make_figures.py` before the next manuscript draft. The eleven
`depletion_zones_*.png` from 27 July are untracked and **must not be regenerated**.

**AMENDED 2026-08-12.** The reason has changed but the instruction has not. They no longer
depict an *unconfirmed* scheme — they depict a **superseded** one, and by two generations:
5 axial zones with element-shared materials, against the confirmed 2 x 10 per-plate scheme
now implemented. Regenerating them would not make an assumption look authoritative; it
would silently produce figures of a model that no longer exists. Note also that plates are
not distinguishable in these views by design, so they could not evidence the per-plate
split even if regenerated — that verification lives in the 1:1 structural check in
`tests/check_depletion_zoning.py`.

`model/run_results/core_run/` is internally inconsistent — a Jul-21 statepoint
beside a Jul-31 `summary.h5` and `model.xml` that were accidentally overwritten
during the audit. A README in the directory records this. Do not interpret the
statepoint using the geometry files beside it.

---

## 11. Phase 2 — what it actually is

From the project scope:

**Task 1 (remainder)** — fresh-core cross-validation on a matched library, then
depletion models in ADDER-MCNP and OpenMC with additional metrics validated.

**Task 2** — runtime comparison, MCNP vs OpenMC, fresh and depleted, on both
CPU and GPU builds of OpenMC. *A baseline now exists:* 128 threads, ~500,000
active particles/sec, 125 M histories in ~4 minutes.

**Task 3** — MCNP -> OpenMC conversion tool assessment. **The tool has still
never been named.** Confirm with Kyle. Assessment covers model complexity, ease
of modification, and ease of use in an external tool such as ADDER.

**Overarching:** preparation for ADDER-OpenMC coupling, toward Proliferation
Resistance Optimization.

### Suggested order

1. Resolve the library question with Kyle — everything downstream depends on it
2. Rewrite `run_vii_mat.py` to import from `materials.py`
3. Add the entropy mesh; determine inactive batches from the trend rather than
   inheriting 50
4. Matched-library runs, both blade positions, on whatever library both sides have
5. *Then* compare to reference values — the first genuine cross-validation number
6. Push the deliverable repo
7. Manuscript Section 2.3 (unblocked — the axial stack decision is made)

---

## 12. Standing rules — carry these into Phase 2

1. **The reference MCNP model governs** where sources disagree. TECDOC-643 is
   supplementary. The PRO-X figure is not a governing source.
2. **Never tune geometry to chase k-eff.** Discrepancies are attributed, not
   absorbed.
3. **`[MCNP]` means Kyle confirmed it** — not "it came from the model generally."
4. **Cite, do not restate.** §9.3.
5. **No magic numbers.** Named constants in `geometry.py`, derived values
   computed from parents, single source of truth.
6. **Overlap checks at f = 0.0, 0.5, 0.99, 1.0 plus a lost-particle scan** after
   any geometry change. Necessary, not sufficient.
7. **Negative-test asserts.** Inject the fault; confirm it fires.
8. **Plan-then-approve** before production file edits.
9. **Never "deck."** Always "MCNP model" or "reference MCNP model."
10. **Phase 1 geometry is closed. Task 1 is not.** Do not describe the
    cross-validation as complete or validated.

---

*Successor documents: cite claims to their source. Do not restate them.*
