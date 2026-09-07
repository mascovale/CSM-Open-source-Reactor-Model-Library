# Superseded Notes — what HEAD contradicts in the project documents

**Purpose.** `PROJECT_BIBLE.md` (2026-07-06) and `TESTAMENT_II_2026-07-20.md`
(2026-07-20) are the onboarding documents for this project. Both live in
`/mnt/c/Users/23tho/Downloads/`, **outside version control**, so nothing in the
repository signals that they are stale. A reader — human or a future session —
picking up either document will find claims that the code contradicts.

This file records those contradictions. **Neither document has been edited.**
Where they disagree with the code, the code governs; where they disagree with
each other, Testament II governs the Bible (it says so itself in T2.1).

**Written at** `d74f158`, branch `phase1/geometry-finalization`, 2026-07-31.
**Phase 1 is not closed.** Nothing here says otherwise.

---

## 1. `TESTAMENT_II_2026-07-20.md`

Testament II is itself a supersession document — its T2.1 table supersedes the
Bible. Everything below supersedes *Testament II*.

### 1.1 Axial model — T2.1 and T2.5

> **T2.1:** "z = [−90, +90], symmetric about z = 0 (45 water / **15 end-box** /
> **60 fuel** / **15 end-box** / 45 water)"
> **T2.5:** "Axial: CORE_BOTTOM/TOP = ∓90 (vacuum), symmetric: 45 water / 15
> end-box / 60 active fuel / 15 end-box / 45 water"

**Contradicted by `880d0ad` (B1).** The stack is now

```
45 water / 14 end-box / 1 unfueled clad / 60 meat / 1 unfueled clad / 14 end-box / 45 water
```

The reference MCNP model carries 1 cm of unfueled cladding above and below the
meat. Plates are 62 cm (`PLATE_HEIGHT`), meat stays 60 cm (`MEAT_HEIGHT`), and
the homogenized end-box drops 15 → 14 cm (`ENDBOX_HEIGHT`). The ±90 and ±45
planes do not move — the centimetre the plates gain is the one the end-box
loses. Still symmetric, still 180 cm total, now tripwired by
`_AXIAL_STACK_SUM`.

**What survives:** z = [−90, +90], symmetry about z = 0, the 45 cm water bands,
and "withdrawn (f=1) blade top coincides with CORE_TOP; no cap above".

### 1.2 Flux trap — T2.5

> "**Flux trap:** full-pitch Al block, central ZCylinder water hole,
> `FT_HOLE_RADIUS = 2.5` **[ASSUMED]** — still pending."

**Two separate contradictions.**

- **Block geometry — `94eb953` (B2).** The block is no longer full pitch. It is
  `FT_BLOCK_X × FT_BLOCK_Y` = 7.6 × 8.0 inside the 7.7 × 8.1 pitch, with four
  water-gap cells around it — the same 1 mm gap as the fuel elements.
- **Hole radius — `9dd93cd` (A1).** `FT_HOLE_RADIUS = 2.820`, `[MCNP]`, Kyle
  confirmed 2026-07-31. Area-equivalent to the 50 mm square hole
  (25 cm² → r = 5/√π = 2.8209). The 2.500 was the *inscribed* radius. **No
  longer `[ASSUMED]` and no longer pending.**

**What survives:** central ZCylinder, hole water is core coolant at 316.8 K.

### 1.3 Graphite reflector — T2.1, T2.5, and the Bible's material table

> **T2.1:** "graphite **1.7000 g/cm³ [TECDOC]**, per 7/20 meeting. The 1.740
> deck-implied claim is void (T2.2)."
> **T2.5:** "**Graphite reflector:** continuous in-plane wall (full pitch) in
> the active z-range. **Inter-block water channels pending the MCNP dimension.**"

**Three contradictions.**

- **Density — `6288fb4` (A2 final).** Graphite is specified in atom/b-cm
  directly from reference MCNP card `m00005`: **8.724000E-02 atoms/b-cm total
  carbon**, `[MCNP]`. Not 1.7000, and not `[TECDOC]` — **TECDOC-643 specifies no
  graphite density at all.** The 1.7000 g/cm³ figure was recorded as decided at
  the 7/20 meeting but **was never implemented**; the code ran 1.7400
  throughout. An intermediate 2.26 g/cm³ "natural density" reading was committed
  at `10f607f` and rejected by Kyle; `10f607f` is deliberately left in history
  as the provenance record.
- **In-plane geometry — `94eb953` (B2).** No longer a continuous wall. Discrete
  7.6 × 8.0 blocks with water gaps between them.
- **The "pending MCNP dimension" is resolved and was a non-question.** The
  inter-block channel *is* the pitch gap — 0.1 cm in x, 0.1 cm in y. There is no
  separate channel dimension to obtain.

### 1.4 Control end block — T2.1 and T2.5

> "Guides 0.127 [TECDOC], feeder 0.219 (standard channel), **offset 0.1075 =
> STD_END_WATER [DERIVED]**, **g = 0.139** (residual)."

**Contradicted by `1350263` (A3).** `CTRL_OUTER_OFFSET` is now **0.1305**,
`[MCNP]`, and is **de-aliased from `STD_END_WATER`** — the standard element's
exterior channel (0.1075) and the control element's outer offset are different
physical things and no longer share a constant. The residual follows:
**`CTRL_BLADE_WATER` = 0.1275**, not 0.139.

Budget still closes exactly: 0.219 + 0.127 + 0.1275 + 0.310 + 0.1275 + 0.127 +
0.1305 = 1.1685 = `CTRL_END_BLOCK`.

**What survives:** guides 0.127, feeder 0.219 as a standard channel, and the
blade water being a residual rather than a specified value.

### 1.5 Moving blade cap — T2.5 and T2.4 item 3

> "a **15 cm** end-box-homog cap is **rigidly attached to the blade top** …
> spanning [z_top, min(z_top + 15, +90)], water above it to CORE_TOP."
> **T2.4:** "Withdrawn: the water/Al mixture rides directly above the blade at
> the same 15 cm thickness."

**Contradicted by `880d0ad` (B1) and `26d8704` (commit 17).** Two changes:

- The cap is **14 cm** (`ENDBOX_HEIGHT`), derived from the end-box constant.
- The cap **no longer rides on the blade top**. Since commit 17 a
  `BLADE_TOP_CLAD` = 1 cm **aluminium clad** rides on the B4C and the cap rides
  on the *clad*. At f = 0 the stack is B4C [−30,+30] / clad [+30,+31] / cap
  [+31,+45]. Side and bottom cladding are absent **by confirmation, not
  omission**.

An intermediate resolution (A4 "Option B", `880d0ad`) put *core coolant water*
in the [+30,+31] band and anchored the cap floor at `max(z_top, HALF_PLATE_Z)`.
That is also superseded: the clad now fills that band, and the `max()` guard was
dropped at commit 17 because `cap_bot = z_top + BLADE_TOP_CLAD = 31 + 60f` makes
it provably redundant.

**What survives:** the cap concept, that it translates with the blade, that at
f = 1 it is clipped out of the model entirely, and coplanarity with the
surrounding end-boxes at full insertion.

### 1.6 Interim matched-library baseline — T2.3

> "Rods in (f = 0.0) 0.98051 ± 0.00003 / 0.979959 / **+56 pcm**"
> "Rods out (f = 1.0) 1.19690 ± 0.00003 / 1.19753 / **−53 pcm**"
> "**This baseline is STALE as of 7/20.**"

**Correctly self-labelled stale, and now stale for additional reasons.** It
predates B1–B4 and the entire A-series. Also note the **18,853 pcm** blade-worth
figure that circulated separately: it derives from
`model/run_results/core_run/statepoint.200.h5`, written 2026-07-21 14:21 — **two
hours before commit `7660f56`** deleted the end-box gap sliver cells. It
therefore describes a geometry that has not existed on any branch since 07-21.
That statepoint also carries `openmc_version = [0, 15, 0]`, while all Phase 1
verification ran on 0.15.3.

**Do not compare any current number to +56 / −53 / 18,853 / 18,418.**

### 1.7 ENDF/B-VII.0 on Triforce — T2.1

> "**VII.0 exists:** `/opt/openmc-data/mcnp_endfb70/cross_sections.xml`"

**Not contradicted, but not verifiable from here.** That path **does not exist on
this machine**; only ENDF/B-VIII.0 and Lib80x are present under
`~/nuclear-data/`. The claim is about Triforce and may well be correct there.
Recorded because two Phase 1 open items depend on it and neither can be closed
locally: whether VII.0 carries `c_Al27`, and whether it resolves `C0` (VII.0 has
natural carbon only — the C-12/C-13 split arrived in VII.1).

### 1.8 **T2.2 Provenance Reset — superseded, and this one matters**

> "**No exact numerical values from Kyle's reference MCNP deck are known.** …
> Every prior claim of deck-transcribed exact values — atom densities 'taken
> directly from the deck,' the 1.740 graphite density, the 5-sig-fig m-card
> matches — is **void as [DECK] provenance**. … Until that spreadsheet arrives,
> treat every numeric spec as [TECDOC], [DERIVED], or [ASSUMED] — never [DECK]."

**Superseded by `6288fb4` (A2 final).** The rule was written on 2026-07-20 when
no verified transcription existed and prior claims of one had proven unreliable.
That epistemic situation has changed: on 2026-07-31 **the model owner pasted card
`m00005` verbatim**:

```
m00005     $     294.0    Graphite reflector
       6000    8.724000E-02
```

This is the **strongest provenance in the codebase** — a direct transcription
from the reference model, supplied by its owner, reproduced in the code comment
in full and asserted float-exact (`Σ C == 8.724000E-02`, Python `==` True).

**The T2.2 blanket rule must not be applied to it.** Read literally, T2.2 would
void the one value in the repository that has unimpeachable provenance. The
rule's *reasoning* — do not claim transcription you cannot support — is sound
and still governs everywhere else; its *blanket form* is now wrong.

Also note the terminology: T2.2 is written throughout in terms of `[DECK]` and
"the deck". Current project rules forbid "deck" entirely — it is "the reference
MCNP model" — and the provenance tag is `[MCNP]`, not `[DECK]`. The tag T2.2
prohibits no longer exists.

**What survives, and should be kept:** the epistemic discipline. Where a value's
origin is a spreadsheet column or a relayed statement rather than a card, the
tag should say so. The Phase 1 audit's Section C3 applies exactly this test and
found four `[MCNP]` tags that are structural aliases rather than confirmations.

---

## 2. `PROJECT_BIBLE.md`

Older (2026-07-06) and already largely superseded by Testament II's T2.1 table.
Only contradictions **not** already covered there are listed.

### 2.1 Lattice — Bible §5

> "**Lattice:** **8×9** rectangular lattice, pitch 7.7 × 8.1. Active 5×6 core …
> **water ring outside**. `lattice.outer = water_univ` guards boundary roundoff.
> **Vacuum boundaries at lattice edge and z = −65 / +95.**"

**Contradicted three ways.**

- **`b44c608` (B4).** The lattice is **6 (x) × 7 (y) core positions**, 42 total,
  with **no water ring** — `CORE_MAP` contains no `'W'` token. The surrounding
  water is an explicit pool box, `POOL_WATER_THICK` = 38.5 cm on all four sides.
  Model extent is 123.2 × 133.7 × 180.0 cm.
- **Vacuum is no longer at the lattice edge.** The core envelope planes are
  transmissive; vacuum sits on the pool faces at ±61.6 / ±66.85.
- **z = −65 / +95 was already superseded** by Testament II T2.1 to ∓90, which is
  still correct.

Note on terminology: see §6 — 8×9 is Table 1's *grid plate* row, 5×6 is its
*active core* row, and 6×7 is the lattice this model builds. All three are
correct for different things.

**What survives:** pitch 7.7 × 8.1, and `lattice.outer = water_univ` — kept as
roundoff insurance.

### 2.2 Graphite blocks — Bible §5

> "graphite reflector rows top/bottom (each block **7.6 × 8.0 with thin water
> gaps** to the pitch boundary, aligned to the fuel lattice)"

**The Bible was right and Testament II was wrong.** B2 (`94eb953`) implements
exactly this. See §4 — this is a process finding, not just a value one.

### 2.3 Flux trap — Bible §5

> "`FT_HOLE_RADIUS = 2.5` (**ASSUMED** — inscribed radius of the 50 mm square;
> verify against the deck's CYL surface). … A-2 Table 1 vs. Chapter
> 7/Appendix G treat flux traps differently — **confirm with Kyle which
> configuration is the benchmark reference.**"

**Radius contradicted by `9dd93cd`** (see 1.2). The *second* question — which
flux-trap configuration is the benchmark — **is not recorded as answered
anywhere.** The model places the two traps at D4 (centre) and A6 (edge), pinned
by assert, on the strength of A-2 §1's "one at core centre, one at core edge".
Flagging it as a possibly-still-open item that predates Testament II and was
never carried forward into it.

### 2.4 Material table — Bible §6

> "| Graphite | **1.70 g/cm³** | `c_Graphite` S(α,β) |"

Superseded — see 1.3. `c_Graphite` survives, **but whether the reference MCNP
model carries the corresponding MT card is an open question with Kyle.** Its
absence from the `m00005` snippet proves nothing, since MCNP specifies MT
separately. For a reflector this is a large effect.

### 2.5 Terminology — throughout both documents

Both use "deck" pervasively ("Kyle's deck", "the deck's CYL surface",
"deck-authoritative", "[DECK]"). Current project rules forbid the term: it is
"the MCNP model" or "the reference MCNP model". The code was cleaned of it at
`bb84f33`. The documents have not been.

---

## 3. Items with no home in either document

Recorded here because a reader of both documents would not otherwise learn them.

| Item | Status |
|---|---|
| Blade top cladding, 1 cm aluminium, top end only | `26d8704`. Neither document mentions blade cladding at all. Side and bottom absent by confirmation. |
| Absorber blade width 6.630, de-aliased from the 6.640 coolant channel width | `9c12dad` (B3). The two were one constant before. |
| `model_cross_validation.xlsx` | **Twelve copies** across Downloads and OneDrive, none in version control. Newest `.xlsx` (07-31 11:49) predates newest `.pdf` (07-31 16:09), so the canonical copy is unclear. Every `[MCNP]` and `[TECDOC]` tag traces to it. |
| OpenMC version | All Phase 1 verification ran on **0.15.3**; the production statepoint records **0.15.0**. Unpinned, unrecorded per run. |
| Deliverable repo | `mascovale/CSM-Open-source-Reactor-Model-Library` serves a 2026-07-27 model — `FT_HOLE_RADIUS = 2.5`, 60 cm plates, no pool. 19+ commits behind. |
| `run_vii_mat.py` | Independent copy of an older `materials.py`; runs clean, builds a *different* model (graphite 1.70, end-box 1.41975, no `c_Al27`). VII.0 blocker. |

---

## 4. A regression, not a supersession — the graphite block dimensions

**This is the most useful thing that came out of writing this file, and it is a
process finding rather than a value finding.**

The sequence:

| When | Document / commit | Claim |
|---|---|---|
| 2026-07-06 | `PROJECT_BIBLE.md` §5 | graphite blocks are "**7.6 × 8.0 with thin water gaps** to the pitch boundary, aligned to the fuel lattice" — **correct** |
| 2026-07-20 | `TESTAMENT_II` T2.5 | "**continuous in-plane wall** (full pitch) … **inter-block water channels pending the MCNP dimension**" — **wrong, and it overwrote the correct statement** |
| 2026-07-31 | `94eb953` (B2) | 7.6 × 8.0 blocks with pitch-gap water, implemented as a *new* confirmation from Kyle |

**A correct fact was replaced by a worse one, and the error survived eleven days
undetected.** Worse, it inverted the epistemic status: the Bible *knew* the
dimension; Testament II recorded it as an open question pending Kyle. The whole
of B2 was then handled as though the answer were new, and the code carried a
`TODO` in `make_graphite_element` — *"Dimension is pending — it must come FROM
THE MCNP MODEL; do not invent a channel width"* — instructing future readers not
to supply a value the project had already written down three weeks earlier.

Two consequences, both recorded deliberately:

**4.1 — The `FT_BLOCK_X/Y` and `REFL_BLOCK_X/Y` tags are better supported than
the audit credited.** Audit §C3 flagged these four `[MCNP]` tags as structural
aliases of `[TECDOC]` parents — accurate as far as it went, but it assessed them
only against Kyle's B2 statement. The 7.6 × 8.0 sizing is **independently
corroborated by a project document written three weeks before that
confirmation.** Two independent sources agreeing is materially stronger than one
confirmation restated. **The tags are unchanged** and the C3 precision point
stands — the code should say what the `[MCNP]` claim attaches to — but this is
not a weakly-supported value. An amendment recording this has been appended to
C3 in `PHASE1_AUDIT.md`.

**4.2 — Newer summaries are not more reliable than older ones.** Each
summarize-forward step is lossy, and **nothing in this project's process detected
the loss.** Testament II is explicitly a supersession document; its T2.1 table
asserts authority over the Bible wholesale. That framing makes a regression
invisible, because the newer document is assumed to dominate by construction.
The only reason this one surfaced is that someone read both documents against the
code at the same time, which had not happened in eleven days.

The practical rule: **when a summary and an older source disagree, check the
code before assuming the summary is right.**

### 4.3 — The generalization: T2.5 RESTATED where T2.1 CITED

**The same document contains both the safe pattern and the failing one.** That
is what makes this worth stating as a rule rather than an anecdote.

**T2.1 CITES.** Its supersession table is two columns — the original claim, and
what replaces it. Every row names what it is overriding:

> | §5: axial model z = [−65, +95] | **z = [−90, +90]**, symmetric about z = 0 … |
> | §6: graphite 1.70 g/cm³ | **1.7000 g/cm³ [TECDOC]**, per 7/20 meeting … |

A row like that **cannot silently regress.** To get it wrong you have to
misstate a claim you are looking directly at, and a reader can check the pairing
without leaving the page. All eleven rows survived.

**T2.5 RESTATES.** It re-derives the geometry from scratch, in prose, with no
reference to what it supersedes:

> "**Graphite reflector:** continuous in-plane wall (full pitch) in the active
> z-range … **Inter-block water channels pending the MCNP dimension.**"

Nothing in that sentence points at Bible §5. The reader has no signal that an
earlier, better statement exists, and the writer had no forcing function to
check one. The correct fact was not contradicted — **it was simply not carried
forward**, and its absence is invisible.

**Operational rule for any future summary document:**

> **Cite claims to their source; do not restate them.**
>
> `graphite block 7.6 × 8.0 [Bible §5]` is checkable and cannot regress
> silently. `graphite is a continuous wall, channel dimension pending` is a
> fresh assertion wearing a summary's authority, and nothing in the process
> distinguishes the two.

This applies directly to the document you are reading. Every entry above names
the commit that superseded the claim, and quotes the superseded text verbatim,
for exactly this reason — so a future reader can verify the pairing rather than
trust it, and so a wrong entry here fails visibly instead of quietly replacing
something correct.

---

## 5. Deliverable-repo sync exclusions

`~/CSM-Open-source-Reactor-Model-Library` (`github.com/mascovale/…`,
subdirectory `IAEA-Tecdoc-Core/`) is the project's **public deliverable**. It is a
different owner from the dev repo and is currently serving a 2026-07-27 model —
`FT_HOLE_RADIUS = 2.5`, 60 cm plates, 15 cm end-box, 8×9 lattice, no pool. Audit
BLOCKER 1.

**The deliverable is the model, not the engineering record.** When it is synced,
the following must NOT go with it:

| Exclude | Why |
|---|---|
| `docs/PHASE1_AUDIT.md` | Internal audit. Enumerates open questions, provenance weaknesses and process failures. Engineering record. |
| `docs/SUPERSEDED_NOTES.md` | This file. Same reason — it exists to orient someone reading stale internal documents. |
| `model/run_vii_mat.py` | Runs clean and builds a **different** model (graphite 1.70, end-box 1.41975, no `c_Al27`). Publishing a second, wrong source of truth is worse than publishing nothing. Rewrite it before it ships, or omit it. |
| `plots/` | Generated output. Nothing in it is tracked as of `4a76220`; the generators (`tests/plot_core.py`, `tests/make_phase1_xs_plots.py`) are what should ship. |
| `PROJECT_BIBLE.md` | Already excluded and confirmed absent — the existing rule. Keep it that way. |
| `figures/` generated output | `*.pdf`, `_proof/`, `solidworks_*.txt` — already `.gitignore`d; source only. |

`.gitignore` handles `plots/` and the `figures/` artifacts automatically. **`docs/`
and `run_vii_mat.py` are not covered by any ignore rule and must be excluded by
whoever runs the sync.**

Testament II T2.7 replaced the old `cp model/*.py` runbook with a whole-tree
rsync after the 7/20 stray-file incident. A whole-tree rsync will copy `docs/`
unless told otherwise — that is precisely the failure mode this list exists to
prevent.

---

## 6. Core / lattice / grid plate — three counts, all correct

**Do not reconcile these by "correcting" one.** They describe three different
things, and two of them are direct quotes from TECDOC-643 A-2 Table 1.

| Count | What it is | Source |
|---|---|---|
| **5 × 6 = 30** | **THE CORE.** 23 standard + 5 control + 2 flux traps. **Excludes the 12 graphite reflector positions, which are not core.** | `[TECDOC A-2 Table 1, "Active Core Geometry: 5 x 6 Positions"]` |
| **6 (x) × 7 (y) = 42** | **THE LATTICE AS BUILT.** The 30 core positions **plus** the 12 graphite reflector positions, which must live in the same `RectLattice`. A modelling extent, not a core description. | this model — `N_LAT_X`, `N_LAT_Y` |
| **8 × 9 = 72** | **THE GRID PLATE.** Counts the surrounding water ring. | `[TECDOC A-2 Table 1, "Grid Plate: 8 x 9 Positions"]` |

Arithmetic, verified against `CORE_MAP` at HEAD: the two all-graphite rows are
12 positions; the remaining 5 rows × 6 columns are 30, and 23 + 5 + 2 = 30
exactly. 30 + 12 = 42 = 6 × 7.

**Rules.**

- **The core is 5 × 6.** Describe it that way in prose, comments, docstrings and
  commit messages.
- **Never call the core 7 × 6.** That phrasing was used throughout this project
  until 2026-07-31 and is wrong: it transposes the lattice and calls a
  core-plus-reflector extent "the core". Every prose occurrence has been
  corrected; `grep -rniE '7x6|7 x 6'` should return nothing.
- **The lattice is 6 × 7, and say "lattice" when you mean it.** `N_LAT_X = 6`,
  `N_LAT_Y = 7`, `CORE_HALF_X = 23.100`, `CORE_HALF_Y = 28.350` are **unchanged
  and must stay so** — the 38.5 cm pool arithmetic (123.200 × 133.700) and
  `tallies.py`'s flux mesh both key off them. This is a naming correction only.
- **Cite 8 × 9 for the grid-plate row only.**

**One name kept despite being wrong.** `CORE_HALF_X` / `CORE_HALF_Y` are
**lattice** half-extents, not core half-extents — the core is smaller in y by one
reflector row at each end. The names predate this terminology and are retained
because renaming them would touch `tallies.py`, `check_depletion_zoning.py` and
the pool derivation for no physical gain. An in-code comment at the definition
says to read them as "lattice envelope". Flagged here so the inconsistency is
recorded rather than discovered.

**Open, for Kyle — do not guess.** The cross-validation spreadsheet's "Grid
plate positions" row reads **OpenMC 8 × 9 vs MCNP 7 × 6**. Under this
terminology *neither entry is obviously right*: 8 × 9 is the TECDOC grid-plate
figure rather than anything either model builds, and 7 × 6 is the transposed
lattice under the very naming this section retires. The row needs Kyle, not an
edit.

---

*Nothing in this file authorizes treating Phase 1 as complete or validated. The
matched-library work has not started.*
