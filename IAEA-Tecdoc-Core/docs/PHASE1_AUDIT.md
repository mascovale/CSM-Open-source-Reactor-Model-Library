# Phase 1 Geometry — Close-Out Audit

**Repository:** `~/iaea-tecdoc643-openmc` (dev), remote `github.com/Thomas-McCoy/iaea-tecdoc643-openmc`
**Audited at:** `c45d4b8` — 19 commits ahead of `main`, branch `phase1/geometry-finalization`, **unpushed**
**Date:** 2026-07-31
**Model:** IAEA TECDOC-643 Appendix A-2 Generic 10 MW LEU MTR, OpenMC 0.15.3, ENDF/B-VIII.0
**Audit type:** read-only. No file in the repository was modified, other than the creation of this document.

Phase 1 is **not** closed. This audit does not assert that the model is complete or
validated; it records what is in the tree and what is not yet settled. Closure is
Thomas's decision, and the matched-library (ENDF/B-VII.0) work has not started.

---

> ## STATUS — READ FIRST
>
> **This audit was performed at `c45d4b8` on 2026-07-31 and is a snapshot.**
> It has since been reviewed by a second reviewer and acted on. Several findings
> are closed. **The body below is the audit as written and has not been
> rewritten** — only this header and three explicitly-marked amendments (C3, F,
> H4) were added afterwards. Do not read a finding below without checking it
> here first.
>
> | # | Finding | Status now |
> |---|---|---|
> | 1 | Deliverable repo serves the pre-Phase-1 model | **OPEN — Thomas's action.** Unchanged. |
> | 2 | 12 tracked stale plots | **CLOSED** — `d74f158` untracked them and removed the `!plots/*.png` exception; `4a76220` untracked the remaining four. `plots/` now tracks nothing. |
> | 3 | `run_vii_mat.py` builds a different model | **OPEN — VII.0 blocker.** Rewrite (import from `materials.py`, override only the library switch) agreed, not started. |
> | 4 | Spreadsheet not on this machine | **SEVERITY REDUCED, NOT CLOSED.** Located at `/mnt/c/…` — a WSL mount outside the search path. **Twelve copies**, none in version control, canonical copy unclear. `2c50e9c` adds the first validation that does NOT route through it — three asserts against TECDOC-643 A-2 Table 1 covering fissile inventory, uranium density and enrichment — so the model is no longer *wholly* dependent on an unversioned document. **But the spreadsheet remains the sole authority for every other constant**, and Section G stays un-auditable until a CSV export is committed. |
> | 5 | Four `[MCNP]` tags are structural aliases | **AMENDED — see the note appended to C3.** Better supported than credited. Tags unchanged. |
> | 6 | `ABSORBER_THICK` untagged and unasserted | **CLOSED** — `e7f85be` tagged it `[MCNP]`, `0574cff` pinned it. |
> | 7 | `check_u235_mass.py` duplicates `MEAT_HEIGHT` | **CLOSED** — `c803e08`. |
> | 8 | `settings.py` duplications and stale comment | **CLOSED** — `c803e08`. |
> | 9 | Manuscript figure PDFs stale | **OPEN.** Not regenerated. |
> | 10 | `statepoint.200.h5` predates the end-box change | **OPEN, and WORSE than the audit found.** Nothing reads it, but on 2026-08-03 it was discovered that `model.xml` and `summary.h5` in that directory were **overwritten on 2026-07-31** by a `core.build_model()` smoke test writing to `core.py`'s relative default `output_dir`. The directory is now internally inconsistent: Jul-21 results beside Jul-31 geometry. See the amendment in E4. |
> | 11 | Non-canonical provenance tags | **CLOSED 2026-08-12.** `[MCNP-PROVISIONAL]` retired at `e0918c3`. The seven `[MCNP-VISUAL]` are now all resolved or superseded by Kyle's 2026-08-12 answers (zone counts and material granularity) — see the amendment appended to C5. Every surviving `[MCNP-VISUAL]` string in the source sits inside a dated SUPERSEDED/RETIRED record; none is a live claim. |
> | 12 | `CTRL_SIDE_PLATE_X` read only by a figure table | **OPEN.** Not acted on. |
> | 13 | Open external questions | **NOW 14** — flux-trap configuration added, see the amendment in F. |
>
> **D4 gaps closed by `0574cff`:** `ABSORBER_THICK` pinned; the 0.5650 guide span
> asserted directly as `CTRL_GUIDE_SPAN`; `BLADE_LENGTH` and `ROD_TRAVEL` pinned
> independently so a compensating pair can no longer satisfy the f=1 assert.
> `70eb9a8` documents that pin as an alignment of independently sourced values,
> not a derivation.
>
> **Still true and unchanged:** C3's negative result (no fabricated `[MCNP]`
> tag), D1/D2 clean, A2/A3 clean, C4 clean, C5's handling correct, H1/H2 pass
> with zero lost particles.

---

## Severity key

| Tag | Meaning |
|---|---|
| **BLOCKER** | Wrong physics or wrong geometry, or a published artifact that misrepresents the model |
| **RISK** | Correct at HEAD, fragile under future edits |
| **HYGIENE** | Cosmetic or organizational |
| **OPEN** | Correct as far as anyone knows; waiting on an external answer |

## Summary of findings

| # | Severity | Finding |
|---|---|---|
| 1 | **BLOCKER** | Deliverable repo publishes the pre-Phase-1 model (19 commits behind, `FT_HOLE_RADIUS = 2.5`, no B1–B4) |
| 2 | **BLOCKER** | 12 tracked plots in `plots/` predate B1–B4 and show geometry that no longer exists |
| 3 | **BLOCKER** | `run_vii_mat.py` runs successfully and silently builds a *different* model (graphite 1.70, no `c_Al27`, end-box 1.41975) |
| 4 | **BLOCKER** | `model_cross_validation.xlsx` is not present on this machine — Section G could not be performed |
| 5 | **RISK** | Four `[MCNP]` tags are structural aliases rather than Kyle-confirmed values; two more are milder cases (Section C3) |
| 6 | **RISK** | `ABSORBER_THICK = 0.31` carries no provenance tag and no assert, and is a spreadsheet row |
| 7 | **RISK** | `check_u235_mass.py:10` duplicates `MEAT_HEIGHT` as a literal — a fifth magic number, not previously caught |
| 8 | **RISK** | `settings.py` duplicates `PITCH_X`/`PITCH_Y` and `±HALF_Z`; its comment is stale (says "5-wide", core is 6×7) |
| 9 | **RISK** | Manuscript figure PDFs predate A1/A2-final/A3/commit 17 |
| 10 | **RISK** | `statepoint.200.h5` predates the commit that changed the end-box material |
| 11 | **HYGIENE** | 10 non-canonical provenance tags with no manuscript macro |
| 12 | **HYGIENE** | `CTRL_SIDE_PLATE_X` is defined in `geometry.py`, read only by a figure table |
| 13 | **OPEN** | 11 unresolved external questions (Section F) |

---

# A. Constants inventory

All module-level constants in `model/geometry.py` at HEAD. "Consumers" lists files
that read the name; `geometry.py` itself is omitted where it is the only reader.

| Constant | Line | Value | Tag | Derived from | Consumers beyond geometry.py |
|---|---|---|---|---|---|
| `PITCH_X` | 84 | 7.7 | `[TECDOC]` | primary | settings*, tallies, make_figures, check_figures, plot_core, check_depletion_zoning, make_phase1_xs_plots |
| `PITCH_Y` | 85 | 8.1 | `[TECDOC]` | primary | same as above |
| `ELEM_X` | 87 | 7.6 | `[TECDOC]` | primary | make_figures |
| `ELEM_Y` | 88 | 8.0 | `[TECDOC]` | primary | make_figures, plot_core |
| `MEAT_HEIGHT` | 96 | 60.0 | `[TECDOC]` | primary | make_figures, check_depletion_zoning |
| `PLATE_HEIGHT` | 98 | 62.0 | `[MCNP]` | primary | make_figures |
| `CLAD_EXT` | 99 | 1.0 | `[DERIVED]` | `(PLATE_HEIGHT − MEAT_HEIGHT)/2` | make_figures |
| `ELEM_Z` | 105 | 62.0 | `[MCNP]` | `= PLATE_HEIGHT` | make_figures |
| `GAP_X` | 112 | 0.05 | **none** | `(PITCH_X − ELEM_X)/2` | make_figures |
| `GAP_Y` | 113 | 0.05 | **none** | `(PITCH_Y − ELEM_Y)/2` | make_figures |
| `FT_BLOCK_X` | 123 | 7.6 | `[MCNP]` | `= ELEM_X` | — |
| `FT_BLOCK_Y` | 124 | 8.0 | `[MCNP]` | `= ELEM_Y` | — |
| `REFL_BLOCK_X` | 125 | 7.6 | `[MCNP]` | `= ELEM_X` | — |
| `REFL_BLOCK_Y` | 126 | 8.0 | `[MCNP]` | `= ELEM_Y` | — |
| `SIDE_PLATE_THICK` | 137 | 0.48 | `[TECDOC]` | primary | make_figures |
| `ACTIVE_STACK_X` | 141 | 6.64 | `[DERIVED]` | `ELEM_X − 2·SIDE_PLATE_THICK` | make_figures, plot_core |
| `PLATE_THICK_INNER` | 147 | 0.127 | `[TECDOC]` | primary | make_figures, check_u235_mass |
| `CLAD_THICK_INNER` | 149 | 0.038 | `[TECDOC]` | primary | make_figures, check_u235_mass |
| `CLAD_THICK_OUTER` | 150 | 0.0495 | `[TECDOC]` | primary | make_figures, check_u235_mass |
| `MEAT_THICK` | 152 | 0.051 | `[TECDOC]` | primary | make_figures, plot_core, check_depletion_zoning |
| `MEAT_WIDTH` | 153 | 6.3 | `[TECDOC]` | primary | make_figures, check_u235_mass, check_depletion_zoning |
| `PLATE_THICK_OUTER` | 158 | 0.15 | `[DERIVED]` | `MEAT_THICK + 2·CLAD_THICK_OUTER` | make_figures, check_u235_mass |
| `N_PLATES_STD` | 161 | 23 | `[TECDOC]` | primary | make_figures, check_u235_mass, check_depletion_zoning |
| `N_PLATES_CTRL` | 162 | 17 | `[TECDOC]` | primary | check_u235_mass |
| `WATER_CHAN_THICK` | 165 | 0.219 | `[TECDOC]` | primary | make_figures |
| `STD_STACK_HEIGHT` | 169 | 7.785 | `[DERIVED]` | plate/channel sum | make_figures |
| `STD_END_WATER` | 174 | 0.1075 | `[DERIVED]` | `(ELEM_Y − STD_STACK_HEIGHT)/2` | make_figures |
| `FT_HOLE_RADIUS` | 181 | 2.820 | `[MCNP]` | primary | make_figures, plot_core |
| `HALF_Z` | 195 | 30.0 | `[DERIVED]` | `MEAT_HEIGHT/2` | tallies, make_figures, plot_core, run_rod_sweep, make_phase1_xs_plots |
| `HALF_PLATE_Z` | 196 | 31.0 | `[DERIVED]` | `PLATE_HEIGHT/2` | make_figures |
| `BLADE_LENGTH` | 205 | 60.0 | **none** | primary | make_figures, plot_core, run_rod_sweep |
| `ROD_TRAVEL` | 206 | 60.0 | **none** | primary | make_figures, plot_core, run_rod_sweep |
| `BLADE_TOP_CLAD` | 216 | 1.0 | `[MCNP]` | `= CLAD_EXT` | — |
| `CORE_TOP` | 217 | +90.0 | **none** | primary | make_figures, check_figures, plot_core, run_rod_sweep, make_phase1_xs_plots |
| `CORE_BOTTOM` | 219 | −90.0 | **none** | primary | same as above |
| `ENDBOX_HEIGHT` | 223 | 14.0 | `[MCNP]` | primary | make_figures |
| `ENDBOX_ABOVE_TOP` | 225 | +45.0 | `[DERIVED]` | `HALF_PLATE_Z + ENDBOX_HEIGHT` | make_figures, plot_core, make_phase1_xs_plots |
| `ENDBOX_BELOW_BOT` | 226 | −45.0 | `[DERIVED]` | `−ENDBOX_ABOVE_TOP` | make_figures, plot_core |
| `POOL_WATER_AXIAL` | 227 | 45.0 | `[DERIVED]` | `CORE_TOP − ENDBOX_ABOVE_TOP` | — |
| `MEAT_BOT_Z` / `MEAT_TOP_Z` | 291–292 | ∓30.0 | **none** | `.z0` off shared planes | plot_core, check_depletion_zoning |
| `MEAT_ZONE_HEIGHT` | 302 | 12.0 | **none** | `MEAT_HEIGHT / N_AXIAL_ZONES` | plot_core, check_depletion_zoning |
| `MEAT_ZONE_VOLUME_PER_PLATE` | 303 | 3.8556 | **none** | `MEAT_THICK·MEAT_WIDTH·MEAT_ZONE_HEIGHT` | check_depletion_zoning |
| `ABSORBER_THICK` | 632 | 0.31 | **none** | primary | make_figures, plot_core, make_phase1_xs_plots |
| `ABSORBER_WIDTH` | 640 | 6.63 | `[MCNP]` | primary | — |
| `ABSORBER_SIDE_WATER` | 644 | 0.005 | `[DERIVED]` | `(ACTIVE_STACK_X − ABSORBER_WIDTH)/2` | — |
| `CTRL_FUEL_WIDTH_X` | 654 | 6.64 | **none** | `= ACTIVE_STACK_X` | make_figures |
| `CTRL_SIDE_PLATE_X` | 655 | 0.48 | **none** | `= SIDE_PLATE_THICK` | make_figures only |
| `CTRL_AL_PLATE_THICK` | 658 | 0.127 | `[TECDOC]` | primary | make_figures, plot_core, make_phase1_xs_plots |
| `N_CTRL_FUEL_PLATES` | 665 | 17 | **none** | primary | make_figures, check_depletion_zoning |
| `CTRL_PLATE_PITCH` | 666 | 0.346 | **none** | `PLATE_THICK_INNER + WATER_CHAN_THICK` | make_figures |
| `CTRL_FUEL_STACK_HALF` | 676 | 2.8315 | **none** | 17-plate stack /2 | make_figures, make_phase1_xs_plots |
| `CTRL_FEEDER_CHANNEL` | 682 | 0.219 | `[DERIVED — standard channel]` | `= WATER_CHAN_THICK` | make_figures, make_phase1_xs_plots |
| `CTRL_OUTER_OFFSET` | 694 | 0.1305 | `[MCNP]` | primary | make_figures, plot_core |
| `CTRL_END_BLOCK` | 697 | 1.1685 | **none** | `ELEM_Y/2 − CTRL_FUEL_STACK_HALF` | make_figures |
| `CTRL_BLADE_WATER` | 702 | 0.1275 | **none** | residual of end-block budget | make_figures, plot_core, make_phase1_xs_plots |
| `N_LAT_X` | 1358 | 6 | `[MCNP]` | primary | tallies |
| `N_LAT_Y` | 1359 | 7 | `[MCNP]` | primary | tallies |
| `CORE_HALF_X` | 1361 | 23.1 | `[DERIVED]` | `N_LAT_X/2 · PITCH_X` | tallies, check_depletion_zoning |
| `CORE_HALF_Y` | 1362 | 28.35 | `[DERIVED]` | `N_LAT_Y/2 · PITCH_Y` | tallies, check_depletion_zoning |
| `POOL_WATER_THICK` | 1365 | 38.5 | `[MCNP]` | primary | — |
| `POOL_HALF_X` | 1367 | 61.6 | `[DERIVED]` | `CORE_HALF_X + POOL_WATER_THICK` | make_phase1_xs_plots |
| `POOL_HALF_Y` | 1368 | 66.85 | `[DERIVED]` | `CORE_HALF_Y + POOL_WATER_THICK` | make_phase1_xs_plots |
| `CORE_MAP_COLS` | 1412 | 'ABCDEF' | `[TECDOC]`¹ | primary | make_figures |
| `CORE_MAP` | 1413 | 6×7 lattice tokens | **none** | primary | make_figures, plot_core, check_depletion_zoning |
| `STD_ELEMENT_IDS` / `CTRL_ELEMENT_IDS` | 1449–1450 | 23 / 5 labels | **none** | from `CORE_MAP` | check_depletion_zoning |

¹ The `[TECDOC]` near `CORE_MAP_COLS` is picked up from the surrounding block comment, which
explicitly states the letter/number convention is *this project's own* and carries no
`[TECDOC]` claim. The tag proximity is misleading; see C4.

### A1 — constants with no provenance tag

**26 of 69.** The physically meaningful ones, in order of concern:

| Constant | Line | Severity | Note |
|---|---|---|---|
| `ABSORBER_THICK` | 632 | **RISK** | 0.31 is a **spreadsheet row** (blade thickness 0.310) and a primary — no tag, no assert, no derivation. The single most exposed untagged constant. |
| `BLADE_LENGTH`, `ROD_TRAVEL` | 205–206 | **RISK** | Both 60.0, both primaries feeding blade travel and the `f=1 → CORE_TOP` pin. Both are spreadsheet rows (absorber blade height 60.000 MATCH). |
| `CORE_TOP`, `CORE_BOTTOM` | 217, 219 | **RISK** | ±90 primaries; model dimension Z = 180.000 is a MATCH row. |
| `CTRL_END_BLOCK`, `CTRL_BLADE_WATER`, `CTRL_FUEL_STACK_HALF` | 697, 702, 676 | HYGIENE | Derived and correct; would read `[DERIVED]`. |
| `N_CTRL_FUEL_PLATES`, `CTRL_PLATE_PITCH`, `CTRL_FUEL_WIDTH_X`, `CTRL_SIDE_PLATE_X` | 654–666 | HYGIENE | Aliases/derivations of tagged parents. |
| `GAP_X`, `GAP_Y` | 112–113 | HYGIENE | Derived; documented as tripwire-only. |
| `MEAT_BOT_Z`…`MEAT_ZONE_VOLUME_PER_PLATE` | 291–303 | HYGIENE | Depletion-zoning derivations; the block above them carries `[MCNP-VISUAL]`. |
| `CORE_MAP`, `STD_ELEMENT_IDS`, `CTRL_ELEMENT_IDS` | 1413–1450 | HYGIENE | Layout, not dimensions. |

### A2 — stated parent does not match computation

**None found.** Every constant whose comment names a parent is computed from that parent.
Two comments deserve a note but are not errors:

- `BLADE_TOP_CLAD` (216) is tagged `[MCNP]` for its *value* (1.0, Kyle-confirmed) while being
  *computed* as `= CLAD_EXT`. The comment states this explicitly. Correct but see C3.
- `ELEM_Z` (105) is tagged `[MCNP]` and computed `= PLATE_HEIGHT`. Same pattern.

### A3 — constants defined and never read

**None.** Every module-level name in `geometry.py` is read somewhere in the repository.

`CTRL_SIDE_PLATE_X` (655) is the weakest case — **HYGIENE**: it is never read inside
`geometry.py` and its only consumer is a SolidWorks-export table in `make_figures.py:672`.
It is a pure alias of `SIDE_PLATE_THICK`.

### A4 — materials inventory

Values read live from the built objects, not from source comments.

| Material | Density basis | Resolved | T (K) | S(α,β) | Provenance |
|---|---|---|---|---|---|
| `LEU_U3Si2_Al_fuel` | `sum` of atom densities | 6.25983 g/cm³, Σ = 5.13728E-02 | 332.1 | **none** | atom densities from reference MCNP model; no MT card on either side |
| `Al_6061_cladding` | mass, 2.70 g/cm³ | Σ = 6.026261E-02 | 330.7 | `c_Al27` | pure Al stands in for 6061-T6 |
| `light_water_294K` | `sum` | 0.99727 g/cm³, Σ = 1.000363E-01 | 294.0 | `c_H_in_H2O` | **H-1 disputed, see F** |
| `light_water_core_316K` | `sum` | 0.99074 g/cm³, Σ = 9.938134E-02 | 316.8 | `c_H_in_H2O` | — |
| `B4C control absorber` | `sum` | 2.00000 g/cm³, Σ = 1.093098E-01 | 294.0 | **none** | no MT card in reference model |
| `graphite_reflector` | **atom/b-cm, 8.724000E-02** | 1.74000 g/cm³ back-computed | 294.0 | `c_Graphite` | `[MCNP]` card m00005 |
| `aluminum_structure` | mass, 2.70 g/cm³ | Σ = 6.026261E-02 | 330.7 | `c_Al27` | — |
| `end_box_homogenized` | `sum` | 1.41806 g/cm³, Σ = 8.960167E-02 | 316.8 | `c_H_in_H2O` **+** `c_Al27` | 0.25 Al / 0.75 H₂O by volume |

Notes:

- `graphite_reflector` is the **only** material specified in atom/b-cm. That is deliberate
  (it is how card m00005 states it) and removes back-conversion round-off.
- `Al_6061_cladding` and `aluminum_structure` are **numerically identical** — same density,
  same composition, same temperature, same S(α,β). They differ only in name and figure
  colour. This is intentional but means any tally keyed on one of them silently excludes
  the other. Since commit 17, `aluminum_structure` also includes the blade top clad.
- `end_box_homogenized` correctly carries **two** S(α,β) tables. Verified in the exported XML.

---

# B. Magic-number hunt

Grepped every `.py` in the repo (excluding `geometry.py`) for the 30 known constant values,
code only, comments excluded from the hit test. Most hits were coincidental (matplotlib
figure sizes, font points, RGB tuples, legend row heights). **Genuine duplications:**

| # | File:line | Literal | Duplicates | Severity |
|---|---|---|---|---|
| 1 | `model/settings.py:79-80` | `PITCH_X = 7.7`, `PITCH_Y = 8.1` | `geometry.PITCH_X/Y` | **RISK** |
| 2 | `model/settings.py:83-84` | `-30.0`, `30.0` | `geometry.HALF_Z` | **RISK** |
| 3 | `model/check_u235_mass.py:10` | `ACTIVE_H = 60.0` | `geometry.MEAT_HEIGHT` | **RISK — new** |

### B1 — `settings.py`, confirmed still present and still correct

Deliberately left unfixed by instruction. Confirmed at HEAD:

- The literals are still there (lines 79–80) and the source box is still
  `±3·PITCH_X × ±3·PITCH_Y × ±30`.
- **It is still correct after B4.** ±23.1 × ±24.3 covers every fuelled position (fuel spans
  ±23.1 in x, ±20.25 in y), sits inside the 6×7 core envelope, and the
  `constraints={'fissionable': True}` rejection discards anything landing in graphite,
  flux traps or gaps. It survives by margin, not by construction.
- **The comment is stale.** Line 70 reads *"covers the 5-wide fuel columns"*. The core is
  **6 wide × 7 tall** in core positions; the fuelled sub-block is 6 wide × 5 tall. The
  "5-wide" figure describes neither. Line 78 also calls the bounds "approximate".

### B2 — `check_u235_mass.py`, a fifth duplication not previously caught

```python
model/check_u235_mass.py:10
ACTIVE_H = 60.0   # meat z-extent, cm (meat_zbot=-30 .. meat_ztop=+30)
```

The file imports `geometry as g` on line 7 and uses `g.PLATE_THICK_OUTER`,
`g.N_PLATES_STD`, `g.MEAT_WIDTH` etc. throughout — then hardcodes the one dimension B1
was about. It is numerically correct today (`MEAT_HEIGHT` is still 60.0) and it is a
standalone diagnostic that nothing imports, so the exposure is contained. But it is
exactly the pattern that made `make_figures.py`'s `ENDBOX_HEIGHT` wrong: a derived value
restated as a literal, in a file that already imports the module holding the real one.
**If `MEAT_HEIGHT` ever moves, this file reports wrong U-235 masses and nothing fails.**

Four duplications were found and fixed earlier this phase (`tallies.py` mesh,
`check_depletion_zoning.py` lower_left, `make_figures.py` `ENDBOX_HEIGHT`,
`CTRL_OUTER_OFFSET` aliasing). This is the fifth.

### B3 — documentation-only restatements (HYGIENE, not counted above)

`run/run_rod_sweep.py:6-8` and `tests/plot_core.py:8` restate the blade arithmetic
(`z_bot = -30 + f*60`) in docstrings. `model/Analyze_rod_sweep.py:18-23` hardcodes TECDOC
Table 7.7 reference worths. These are prose, but they will silently go stale.

---

# C. Provenance audit

### C1 — every distinct tag string in use

| Tag | Count | Locations |
|---|---|---|
| `[DERIVED]` | 20 | geometry.py throughout |
| `[MCNP]` | 18 | geometry.py ×17, materials.py ×1 |
| `[TECDOC]` | 17 | geometry.py throughout |
| `[MCNP-VISUAL — UNCONFIRMED, pending Kyle]` | 3 | materials.py:230, 249; geometry.py:276 |
| `[MCNP-VISUAL]` | 2 | materials.py:234, 237 |
| `[MCNP-VISUAL, inferred]` | 1 | materials.py:236 |
| `[DERIVED, MCNP-VISUAL]` | 1 | materials.py:235 |
| `[DERIVED — standard channel]` | 1 | geometry.py:682 |
| `[ASSUMED]` | 1 | geometry.py:180 (historical note inside the `FT_HOLE_RADIUS` comment) |
| `[INFERRED]` | **0** | — |

> **AMENDED 2026-08-12.** The `[MCNP-VISUAL]` counts and line numbers above are a
> snapshot of the audit date and no longer locate anything live. All seven claims were
> resolved or superseded on 2026-08-12; the strings that remain in `materials.py` are
> inside dated SUPERSEDED/RETIRED records, kept deliberately as history. The tag totals
> for `[MCNP]` also moved — `N_X_ZONES` and `N_AXIAL_ZONES` are now `[MCNP]`-backed.
> See the amendment appended to C5.

### C2 — macro mapping

| Tag | Maps to | Action |
|---|---|---|
| `[MCNP]` | `\prvMCNP` | clean |
| `[TECDOC]` | `\prvTEC` | clean |
| `[DERIVED]` | `\prvDER` | clean |
| `[ASSUMED]` | `\prvASM` | clean — but the single occurrence is describing a *superseded* value, not tagging a live one |
| `[DERIVED — standard channel]` | `\prvDER` + note | compound, renders if the trailing clause is dropped |
| **`[MCNP-VISUAL]` family (7)** | **none** | **RESOLVED 2026-08-12** — see C5 amendment. No live occurrence remains, so no fifth macro is needed. The historical records inside `materials.py` are comments only and never reach the manuscript. |
| `[INFERRED]` | **none** | named in the project rule, zero occurrences, no macro |

**HYGIENE:** `[MCNP-PROVISIONAL]` was fully retired at commit `e0918c3` — zero occurrences
remain. ~~The `[MCNP-VISUAL]` family has exactly the same exposure and has not been
addressed.~~ **AMENDED 2026-08-12: the `[MCNP-VISUAL]` family is now retired too.** No live
claim carries the tag; see the C5 amendment.

### C3 — every `[MCNP]` tag, checked individually

**This is the heart of the audit.** The rule is that `[MCNP]` means Kyle explicitly
confirmed the value. Eighteen occurrences, of which several are the same constant tagged in
both a comment block and inline.

| # | Constant | Line | Value | Was there a specific Kyle confirmation? |
|---|---|---|---|---|
| 1 | `PLATE_HEIGHT` | 98 | 62.0 | **YES** — B1 table, "Fuel plate height 60.000 → 62.000 `[MCNP]`", explicit row |
| 2 | `ELEM_Z` | 105 | 62.0 | **PARTIAL** — B1 row "Element dimension (Z) → 62.000 `[MCNP]`" exists, but the constant is written `= PLATE_HEIGHT`. The tag is on an alias. Defensible. |
| 3 | `FT_BLOCK_X` | 123 | `= ELEM_X` | **NO — structural alias.** See below. |
| 4 | `FT_BLOCK_Y` | 124 | `= ELEM_Y` | **NO — structural alias.** |
| 5 | `REFL_BLOCK_X` | 125 | `= ELEM_X` | **NO — structural alias.** |
| 6 | `REFL_BLOCK_Y` | 126 | `= ELEM_Y` | **NO — structural alias.** |
| 7 | `FT_HOLE_RADIUS` | 177, 181 | 2.820 | **YES** — A1 closed 2026-07-31, explicit, area-equivalent rationale given |
| 8 | `BLADE_TOP_CLAD` | 209, 216 | `= CLAD_EXT` | **YES for the value** (1.0 cm, top end only, 2026-07-31); the *linkage* to `CLAD_EXT` is this project's choice, stated in the comment |
| 9 | `ENDBOX_HEIGHT` | 223 | 14.0 | **YES** — B1 row "Homogenized region dimension (Z) 15.000 → 14.000 `[MCNP]`" |
| 10 | `ABSORBER_WIDTH` | 640 | 6.63 | **YES** — B3, "6.640 → 6.630 `[MCNP]`", explicit |
| 11 | `CTRL_OUTER_OFFSET` | 690, 694 | 0.1305 | **YES, with a caveat recorded in-code** — Kyle supplied it directly, but stated the reference model "either already carries it or will be updated to it", so the value may postdate the model |
| 12 | `N_LAT_X` | 1358 | 6 | **YES** — B4, "reduce it to the 6 (x) × 7 (y) core positions" |
| 13 | `N_LAT_Y` | 1359 | 7 | **YES** — B4, same |
| 14 | `POOL_WATER_THICK` | 1365 | 38.5 | **YES** — B4, "38.5 cm of pool water on all four lateral sides `[MCNP]`" |
| 15 | graphite (materials.py) | 142 | 8.724000E-02 | **YES — strongest in the set.** Kyle supplied card m00005 verbatim |

**FINDING 5 — RISK: four `[MCNP]` tags are structural aliases, not confirmations.**

```python
geometry.py:123-126
FT_BLOCK_X   = ELEM_X   # 7.600 cm   [MCNP]
FT_BLOCK_Y   = ELEM_Y   # 8.000 cm   [MCNP]
REFL_BLOCK_X = ELEM_X   # 7.600 cm   [MCNP]
REFL_BLOCK_Y = ELEM_Y   # 8.000 cm   [MCNP]
```

`ELEM_X` and `ELEM_Y` are themselves tagged `[TECDOC]`. These four constants are aliases of
`[TECDOC]` values wearing an `[MCNP]` tag. What Kyle actually confirmed (B2) was the
*statement* "flux trap and graphite reflector blocks are 7.6 × 8.0 inside the 7.7 × 8.1
pitch" — a claim about block sizing, which happens to coincide with the fuel element
envelope. That is a real confirmation, so the tag is not fabricated; but a reader who
takes `[MCNP]` to mean "this number was read off the reference model" is being told
something slightly stronger than what happened. **The honest tag is `[MCNP]` on the
*equality to `ELEM_X`/`ELEM_Y`*, i.e. `[DERIVED]` from `[TECDOC]` parents under an
`[MCNP]`-confirmed identity.** Not wrong; imprecise. Worth one comment line each.

`ELEM_Z` (#2) is the same pattern in milder form and `BLADE_TOP_CLAD` (#8) is explicitly
documented, so neither is a finding on its own.

**No `[MCNP]` tag was found that is fabricated or that rests on nothing.** Every one traces
to a specific written decision. That is the important negative result of this section.

> **AMENDMENT (added after review, 2026-07-31).** The four `FT_BLOCK_X/Y` /
> `REFL_BLOCK_X/Y` tags are **better supported than this section credited.**
>
> Writing `docs/SUPERSEDED_NOTES.md` surfaced that `PROJECT_BIBLE.md` §5 — dated
> **2026-07-06, three weeks before Kyle's B2 confirmation** — already described
> the graphite blocks as *"each block 7.6 × 8.0 with thin water gaps to the pitch
> boundary, aligned to the fuel lattice."* The 7.6 × 8.0 sizing is therefore
> **independently corroborated by a project document predating the
> confirmation**, not merely inferred from an `ELEM_X`/`ELEM_Y` alias.
>
> The tags are left unchanged. The finding stands as a *precision* point — the
> code should say what the `[MCNP]` claim attaches to — but it is not evidence
> of a weakly-supported value. See `SUPERSEDED_NOTES.md` §4 for how that
> corroboration was nearly lost.

### C4 — every `[TECDOC]` tag

Seventeen occurrences, all on the classical benchmark dimensions:
`PITCH_X/Y`, `ELEM_X/Y`, `MEAT_HEIGHT`, `SIDE_PLATE_THICK`, `PLATE_THICK_INNER`,
`CLAD_THICK_INNER/OUTER`, `MEAT_THICK`, `MEAT_WIDTH`, `N_PLATES_STD`, `N_PLATES_CTRL`,
`WATER_CHAN_THICK`, `CTRL_AL_PLATE_THICK`.

**Every one is traceable to TECDOC-643 A-2 Table 1** ("Generic 10 MW Reactor" element
specification: 77×81 mm pitch, 76×80 mm element, 23 plates, 1.27/1.5 mm plate, 0.38/0.495 mm
clad, 0.51×63×600 mm meat, 2.19 mm channel, 4.8 mm side plate, "17 + 4 Al plates" for the
control element). None of them depends on A-2 Fig. 2.

**HYGIENE — one caveat, not a violation:** none of the seventeen cites a table number
in-code. The tags say `[TECDOC]` but not *where*. A second reviewer cannot verify any of
them from the source file alone. Since the manuscript macro is `\prvTEC` and the citation
lives in prose, this may be acceptable — but it means the code is not self-documenting on
its single largest provenance class.

**No `[TECDOC]` tag was found that traces to A-2 Fig. 2**, and therefore none depends on the
three homogenized-diffusion panels that are not authoritative. `CORE_MAP_COLS` (1412) sits
near a `[TECDOC]` mention but the block comment explicitly disclaims it: *"The letter/number
convention is THIS PROJECT'S OWN — TECDOC-643 A-2 specifies no element labeling scheme."*
Correct as written.

### C5 — the seven `[MCNP-VISUAL]` claims

All in the depletion-zoning scaffolding. Source: a zx slice **plot** of the reference MCNP
model, read by eye. Not transcribed from the model source, not confirmed by Kyle.

| Claim | Location | Inferred from | What breaks if wrong |
|---|---|---|---|
| 5 axial depletion zones over the active height | materials.py:234, 249 | counting bands in a zx slice image | `N_AXIAL_ZONES` is the sole source of the zone count; every zone boundary, material and volume derives from it. A wrong count means the depletion mesh does not match the reference model at all — burnup distributions become non-comparable. |
| uniform zone height (60/5 = 12.0 cm) | materials.py:235 | bands *appeared* equal in the image | If the reference model uses non-uniform zones (e.g. finer near the ends), per-zone burnup is compared against differently-sized volumes. `MEAT_ZONE_HEIGHT` and `MEAT_ZONE_VOLUME_PER_PLATE` both silently mis-size. |
| all plates in an element share one zone material | materials.py:236 (`inferred`) | colours repeated across plates in the slice | If the reference model resolves per-plate, our 5 materials/element vs their 23×5 is a coarser model. Burnup gradients across the plate stack vanish. |
| one unique material per element per zone | materials.py:237 | distinct colours per element | If materials are shared between elements, our 140 materials over-resolve — harmless for accuracy, but the material maps will not correspond one-to-one. |

~~**Severity: OPEN, becoming BLOCKER the moment depletion results are compared.**~~ Today
zoning is off by default (`depletion_zoning=False`) and the Phase 1 fresh-core model does
not touch any of it, so nothing in the current geometry depends on these being right. The
in-code documentation of the uncertainty is unusually good — the block states plainly that
it is unconfirmed and lists each claim separately. That is the correct handling; it just
has not been resolved.

---

#### AMENDMENT 2026-08-12 — C5 IS CLOSED. All four claims resolved or superseded.

Kyle answered on 2026-08-12. Every claim in the table above is now settled, and the
scheme was reimplemented to match at commit `01edb31`. **The records are kept in
`materials.py`, dated and marked SUPERSEDED/RETIRED — history was not deleted.**

| C5 claim | Disposition | Resolved by |
|---|---|---|
| 5 axial depletion zones | **SUPERSEDED, twice.** 5 → an `[ASSUMED]` 8 × 20 (our own placeholder resolution, never a claim about the reference) → **10 axial, `[MCNP]`** | Kyle 2026-08-12: the reference subdivides each plate **2 × 10** |
| uniform zone height (12.0 cm) | **SUPERSEDED.** Now 6.0 cm, `[DERIVED]` from `MEAT_HEIGHT / N_AXIAL_ZONES` | same. See the residual note below |
| all plates in an element share one zone material | **RETIRED.** Materials are now **per plate**; cells and materials are 1:1, 12,280 of each | Kyle 2026-08-12: match the reference at per-plate materials |
| one unique material per element per zone | **SUPERSEDED** by the same change — the unit is now (element, plate, x, z), not (element, zone) | same |

The audit's own prediction on the third row was right: *"If the reference model resolves
per-plate, our 5 materials/element vs their 23×5 is a coarser model. Burnup gradients
across the plate stack vanish."* That is exactly what it was, and exactly why it changed.

**Two things this amendment does NOT claim:**

1. **The 560-material scheme was never a defect.** OpenMC does not require a 1:1
   cell-to-material mapping. Element-shared materials were valid OpenMC and a legitimate
   modeling choice; they averaged flux across an element's plates, so intra-element burnup
   gradients could not develop. The change was made to match the reference model, not to
   fix a bug, and `materials.py` records that distinction.
2. **Zone UNIFORMITY was not separately confirmed.** Kyle stated "2 × 10 on each fuel
   plate", and a uniform division is the natural reading, which is what is implemented.
   But non-uniform spacing was never explicitly raised or excluded in the exchange. This
   is a small residual, not a live blocker — flagged rather than closed silently.

**A new claim also arrives with this change, and it is not `[MCNP-VISUAL]`:** the
subdivision and the granularity are both now `[MCNP — Kyle confirmed 2026-08-12]`, i.e.
relayed statements rather than transcribed cards. That is the same provenance class as
several existing `[MCNP]` tags (see C3) and carries the same exposure — it rests on a
person, not a document.

### C6 — `[INFERRED]`

Zero occurrences repo-wide, and no manuscript macro. Two candidates that arguably *should*
carry it rather than what they have now:

- The seven `[MCNP-VISUAL]` claims are, strictly, inferences from an image. `[INFERRED]`
  with a note would map onto an existing concept — except `[INFERRED]` has no macro either,
  so this only helps if a fifth macro is added regardless.
- `Al_6061_cladding` (materials.py:53-58) uses **pure aluminium** for 6061-T6, with a
  comment that the ~2.7 w/o alloying elements have "negligible reactivity effect here". That
  is an inference and carries no tag at all.

---

# D. Assert inventory

**115 asserts** across the repository: 76 in `geometry.py`, 23 in `figures/make_figures.py`,
5 in `tests/plot_core.py`, 2 in `model/tallies.py`, and one each in `materials.py`,
`figstyle.py`, `run_rod_sweep.py`. All module-level asserts in `geometry.py` and
`materials.py` are reachable at import. The `__main__`-block asserts (geometry.py 1929–1931)
run only under `python geometry.py`. Point-containment asserts (1667–1863) run only when
`_run_point_checks` / `_run_blade_slot_checks` are called, which happens only from
`__main__`.

**RISK — reachability:** the point-containment and slot-check suites — the strongest
verification in the repository, covering the clad band, both end-boxes, the pool, the
blade stack, the side film and the full end-block walk — execute **only** when someone runs
`python geometry.py` by hand. Nothing in `tests/` calls them. There is no CI, no
`pytest`, no runner. A change that breaks them is caught only if a human remembers.

### D1 — float `==` / `!=` without tolerance

Of the 35 `==`/`!=` asserts, **34 are legitimate** — integer counts, string/label equality,
list equality, material-name comparison. One is a genuine float comparison:

```python
geometry.py:646
assert ABSORBER_WIDTH != ACTIVE_STACK_X, (...)
```

**HYGIENE, deliberate.** This is the B3 de-aliasing tripwire and was specified as `!=`
rather than `is not`. It compares 6.63 against 6.64 — well outside float epsilon — and its
purpose is to catch literal re-aliasing (someone writing `ABSORBER_WIDTH = ACTIVE_STACK_X`),
for which `!=` is exactly right. A tolerance version would be *stricter* (it would also
catch two independently-written values that converge), but the current form is not a defect.

**No other float equality asserts exist.** The codebase convention `abs(a - b) < 1e-12` is
applied consistently, including on the B4 chain through `3.5 × 8.1` that motivated it
(1373–1381 use `1e-9`, correctly loosened for that chain).

### D2 — `is` / `is not` for value comparison

**None.** All eight `is`/`is not` occurrences are `is not None` identity checks
(geometry.py 1667, 1690, 1744, 1801, 1833, 1857) — correct usage — or the word "is" inside
an f-string message (figstyle.py:175, plot_core.py:773), which the grep caught as a false
positive.

### D3 — budgets that could pass while wrong

**FINDING — RISK. The control end-block budget can absorb an error silently.**

`CTRL_BLADE_WATER` (702) is defined as the residual of the end-block budget:

```
CTRL_BLADE_WATER = (CTRL_END_BLOCK − CTRL_FEEDER_CHANNEL − 2·CTRL_AL_PLATE_THICK
                    − ABSORBER_THICK − CTRL_OUTER_OFFSET) / 2
```

The budget asserts at `geometry.py:828`, `838` and `1929-1931` then check that the layers
sum to `CTRL_END_BLOCK` and that the element closes on `ELEM_Y`. **Those sums close by
construction** — the residual is *defined* to make them close. If `ABSORBER_THICK` (0.31,
untagged, unasserted) or `CTRL_AL_PLATE_THICK` were wrong, the budget would still close
perfectly and the error would surface entirely as a wrong blade-water gap.

This is mitigated, and only recently: `geometry.py:722` now asserts
`abs(CTRL_BLADE_WATER − 0.1275) < 1e-9`, which pins the residual to Kyle's independently
supplied value and thereby *does* catch an upstream error. That assert is the only thing
standing between an error in `ABSORBER_THICK` and a silently-closing budget. It arrived at
commit `1350263` (A3) and was not present for most of the phase.

The same structure applies to `STD_END_WATER` (174), the standard element's residual — but
there it is asserted only `> 0` (175) and cross-checked against the built stack at
`412` with `1e-9`. There is no independent pin on its value.

### D4 — invariants that should be asserted and are not

Checked against the specific list requested:

| Invariant | Asserted? | Where |
|---|---|---|
| Axial stack closes to 180 | **YES** | geometry.py:246, cross-checked against `CORE_TOP − CORE_BOTTOM` at 250 |
| Control end-block closes to `ELEM_Y` | **YES** | geometry.py:1931 (`__main__`), plus per-element wall closure at 828/838 |
| Gap between block and pitch positive | **YES** | geometry.py:114-115 (`GAP_X/Y > 0`) and 128–134 (block-specific) |
| Blade fits in its slot | **YES** | geometry.py:649 (`0 < ABSORBER_WIDTH < ACTIVE_STACK_X`), 651 (side film positive) |
| Every dimension feeding a spreadsheet row | **NO — see below** |

**Gaps found:**

1. **`ABSORBER_THICK = 0.31` has no assert of any kind** — no bound, no relationship, no
   pin. It is a spreadsheet row and a primary. **RISK.**
2. **The 0.5650 guide-channel span is not directly asserted.** `ABSORBER_THICK + 2 ×
   CTRL_BLADE_WATER = 0.565` is the value Kyle filled into "Control guide coolant channel
   thickness". It is pinned only *transitively* (via the `CTRL_BLADE_WATER` pin at 722 plus
   `ABSORBER_THICK` being a literal). Documented as such in the comment at 704–712.
   **HYGIENE** — no silent path to a wrong value exists today, but the spreadsheet row has
   no assert naming it.
3. **`MEAT_WIDTH` vs `ACTIVE_STACK_X` lateral clad margin** is asserted in
   `make_figures.py:195` (`LATERAL_CLAD_MARGIN > 0`) but **not in `geometry.py`**. A
   geometry-only consumer never sees that check.
4. **`BLADE_LENGTH` / `ROD_TRAVEL` are never asserted equal to each other** — the
   f = 1 → `CORE_TOP` pin at 255 constrains their *sum* relative to `HALF_Z`, so a
   compensating error in both would pass.
5. **`N_PLATES_STD = 23` is not directly asserted.** It is checked indirectly through
   `STD_STACK_HEIGHT` at 412. `N_PLATES_CTRL` *is* directly asserted (672).

---

# E. Dead and unused inventory

### E1 — files not imported by anything

Determined by grepping every `.py` for `import <basename>` / `from <basename> import`,
then checking for an `if __name__ == '__main__'` block.

| File | Importers | Entry point? | Status |
|---|---|---|---|
| `model/geometry.py` | 10 | yes | core module |
| `model/materials.py` | 8 | yes | core module |
| `model/settings.py` | 4 | yes | core module |
| `model/core.py` | 2 | yes | driver |
| `figures/figstyle.py` | 2 | no | library for figures |
| `model/tallies.py` | 1 | yes | — |
| `figures/make_figures.py` | 1 | yes | imported by `check_figures.py` |
| `tests/plot_core.py` | 0 | yes | standalone |
| `tests/check_depletion_zoning.py` | 0 | yes | standalone |
| `tests/make_phase1_xs_plots.py` | 0 | yes | standalone |
| `figures/check_figures.py` | 0 | yes | standalone |
| `model/Analyze_rod_sweep.py` | 0 | yes | standalone |
| **`model/run_vii_mat.py`** | **0** | yes | **see BLOCKER below** |
| `model/check_u235_mass.py` | 0 | **no** | script with no guard; runs on import |
| `run/run_rod_sweep.py` | 0 | **no** | script with no guard |
| `archive/run_allin.py` | 0 | **no** | archived; imports `water_univ`, `graphite_univ`, `make_flux_trap` from geometry |
| `model/__init__.py` | 0 | n/a | empty |

**FINDING 3 — BLOCKER: `model/run_vii_mat.py` is a live, runnable second source of truth.**

- It is a **complete independent copy** of an older `materials.py` — its docstring still
  reads *"materials.py"* (line 2) and it imports nothing from the real module.
- **It runs successfully at HEAD** (`exit=0`), printing a materials summary. This is what
  makes it dangerous: nothing about invoking it signals that it is stale.
- Its graphite is **1.70 g/cm³** (line 127) — a value that was *never implemented* in the
  production model and has now been superseded twice (1.74, then 8.724000E-02 atom/b-cm from
  card m00005). Confirmed by running it: `[6] graphite_reflector — 1.7 g/cm3`.
- Its end-box is **1.41975 g/cm³** (line 166) against production's **1.41806** — a
  different homogenization.
- It carries **no `c_Al27`** on any material, and no `USE_AL_SAB` switch. The Al S(α,β)
  decision never reached it.
- Its one genuinely useful feature is line 20: `USE_NATURAL_CARBON = 'endfb70' in
  os.environ.get('OPENMC_CROSS_SECTIONS', '')` — the env-keyed switch the VII.0 run needs.

The planned fix (import from `materials.py`, override only the library-dependent switch) is
already agreed. Until then, **any VII.0 matched-library run driven by this file would use
the wrong graphite, the wrong end-box, and no aluminium thermal scattering.**

`archive/run_allin.py` (**HYGIENE**) still imports `make_flux_trap`, `water_univ`,
`graphite_univ` from geometry and would run against the current geometry with pre-B4
assumptions. It is in `archive/` and has no `__main__` guard.

### E2 — functions, classes and constants never called

- **Constants:** none unused (see A3). `CTRL_SIDE_PLATE_X` is the weakest — read only by a
  SolidWorks-export table.
- **Functions:** `core.py:build_depletion_operator` (195) and `core.py:run_depletion` (208)
  both `raise NotImplementedError` immediately and are called by nothing. They are
  documented scaffolding for the ADDER coupling, with the commented-out implementation
  below each. **HYGIENE** — intentional, clearly marked.
- `geometry.py:fuel_zone_planes` / `zone_z_bounds` are called only when
  `depletion_zoning=True`, which no production path currently sets.

### E3 — stale generated artifacts

**FINDING 2 — BLOCKER: 12 tracked plots in `plots/` predate B1–B4 entirely.**

`.gitignore` ignores `*.png` but re-includes `!plots/*.png`, so everything in `plots/` is
**tracked and will be published**.

| File | Modified | Generated by | Status |
|---|---|---|---|
| `plots/depletion_zones_*.png` (11 files) | 2026-07-27 15:41 | `tests/plot_core.py` | **STALE — predates B1, B2, B3, B4, A1, A2, A3, commit 17** |
| `plots/core_geometry_plots.png` | 2026-07-27 15:54 | `tests/plot_core.py` | **STALE — same** |
| `plots/phase1_xs*.png` (4 files) | 2026-07-31 16:52 | `tests/make_phase1_xs_plots.py` | current |

The 12 stale files depict a model with **60 cm plates, a 15 cm end-box, an 8×9 lattice with
a one-cell water ring, a vacuum boundary at ±30.8/±36.45 rather than a 38.5 cm pool, a
2.5 cm flux trap hole, a 6.640 cm blade, and no blade top clad.** Every one of those
features is now wrong. They are the *only* visual record of the depletion zoning in the
repository, and a reader who opens them will form a materially incorrect picture of the
model. `tests/plot_core.py` has not been modified since `cdb68b3` (2026-07-27).

**FINDING 9 — RISK: manuscript figure PDFs are stale.**

| File | Modified | Predates |
|---|---|---|
| `figures/fig1_core_map.pdf` … `fig4c_ft.pdf` (7 files) | 2026-07-31 13:24 | A1 `9dd93cd` (16:47), A2-final `6288fb4` (16:12), A3 `1350263` (14:31), commit 17 `26d8704` (16:52) |
| `figures/fig1_core_map.png` | 2026-07-30 09:54 | all of the above plus B-series |
| `figures/_proof/*.png` (24 files) | 2026-07-30 17:27–17:28 | all of the above |

These are `.gitignore`d and so not published, but they are the artifacts that would go into
the manuscript. `make_figures.py` runs clean at HEAD, so regenerating is a single command —
it simply has not been done since the A-series landed.

Generated XML (`model/geometry.xml`, `model/plots.xml`, `plots/model.xml`) is current and
ignored.

### E4 — `model/run_results/core_run/statepoint.200.h5`

**RISK.**

| Property | Value |
|---|---|
| Written | 2026-07-21 14:21:45 |
| k-eff | 0.97440 ± 0.00034 |
| Settings | 50 000 particles × 200 batches, 50 inactive, seed 1 |
| Shannon entropy | **absent** — no `entropy` dataset in the file |
| Companion files | `model.xml` (07-21 14:13), `summary.h5` (07-21 14:13), `tallies.out` (07-21 14:21) |

It was produced **two hours before commit `7660f56`** ("the updates to geometry are like an
ouroboros", 07-21 16:25), which deleted `_endbox_gap_cells` — the four water sliver cells
between element envelope and pitch in both end-box z-ranges — replacing them with solid
full-pitch homogenate. That is a material substitution over ~30 cm of height at every
element, not a refactor. It therefore describes a geometry that has not existed on any
branch since 07-21, and it predates the entire B-series and A-series besides.

**Nothing in the repository reads from it.** No `.py` file references `run_results`,
`statepoint`, or `core_run`. It is inert, tracked only in the sense that
`run_results/` is `.gitignore`d (confirmed: `git ls-files` returns nothing under it).

> **AMENDMENT (2026-08-03) — this directory has since been DAMAGED, and the
> damage was self-inflicted during audit follow-up.**
>
> On 2026-07-31 a `core.build_model()` smoke test was run to verify the new
> run-provenance printing. `core.py`'s `CoreConfig` carried a **relative**
> default `output_dir = 'run_results/core_run'`, so the build wrote its
> `model.xml` and `summary.h5` directly over the production run's copies:
>
> | File | Audit recorded | Now | Status |
> |---|---|---|---|
> | `statepoint.200.h5` | 5 690 800 B, Jul 21 14:21 | unchanged | INTACT |
> | `tallies.out` | 3 221 099 B, Jul 21 14:21 | unchanged | INTACT |
> | `model.xml` | 520 245 B, Jul 21 14:13 | **487 773 B, Jul 31 17:12** | **OVERWRITTEN** |
> | `summary.h5` | 15 900 536 B, Jul 21 14:13 | **15 911 216 B, Jul 31 17:13** | **OVERWRITTEN** |
>
> **The directory is now internally inconsistent: a Jul-21 statepoint beside a
> Jul-31 geometry description.** That is worse than either a clean directory or
> an untouched stale one, because it fails SILENTLY — anyone opening
> `summary.h5` to interpret `statepoint.200.h5` gets the wrong geometry with no
> error and no warning.
>
> The overwritten files are **not recoverable from this repository**:
> `run_results/` is `.gitignore`d and was never committed. Reconstructing the
> true geometry description would require checking out the tree as of
> 2026-07-21 ~14:13 and rebuilding.
>
> A `README.md` recording this has been placed **in the directory itself**, so
> the warning is found by anyone who opens it rather than only by readers of
> this audit. That README is untracked, like everything else there.
>
> `core.py` has since been fixed: `output_dir` resolves absolutely from the
> repository root rather than the cwd, and writing into a non-empty directory
> now raises unless an explicit overwrite flag is passed. Nothing in the
> directory was deleted.

Its practical significance is that it is the **only production-statistics run in the tree**,
and the 18 853 pcm blade-worth figure in circulation derives from it. That figure therefore
describes pre-`7660f56` geometry.

### E5 — untracked and mis-tracked files

- **Untracked, non-ignored: none.** `git status --porcelain --untracked-files=all` is empty.
  The tree is clean.
- **Tracked generated output: 16 files, all in `plots/`** (see E3). Twelve are stale. This
  is a deliberate `.gitignore` exception (`!plots/*.png`) for "curated verification plots" —
  the mechanism is fine, the curation has lapsed.
- **`.gitignore` coverage:** `*.xml`, `*.h5`, `*.out`, `run_results/`, `*.png` (with the
  `plots/` exception), `__pycache__/`, `*.py[cod]`, and since commit `38440be` also `*.pdf`,
  `figures/_proof/`, `figures/solidworks_*.txt`.
- **What it misses:** nothing observed. No editor artifacts, no `.DS_Store`, no `.ipynb`
  checkpoints, no stray venvs.

### E6 — deliverable repo

**FINDING 1 — BLOCKER: the published repo carries the pre-Phase-1 model.**

`~/CSM-Open-source-Reactor-Model-Library` → `github.com/mascovale/CSM-Open-source-Reactor-Model-Library`.
This is a **different owner** from the dev repo (`Thomas-McCoy`). Subdirectory
`IAEA-Tecdoc-Core/` mirrors the dev tree.

| File | Deliverable | Dev | Status |
|---|---|---|---|
| `model/geometry.py` | 2026-07-27 15:02 | HEAD | **DIFFERENT — 19 commits behind** |
| `model/materials.py` | 2026-07-27 15:37 | HEAD | **DIFFERENT** |
| `model/tallies.py` | 2026-07-06 21:44 | HEAD | **DIFFERENT — pre-B4 mesh bounds** |
| `model/settings.py` | — | — | same |
| `model/core.py` | — | — | same |

Confirmed directly in the published `geometry.py`:

```
line 121:  FT_HOLE_RADIUS = 2.5         # cm
line 120:  # with a different radius, update FT_HOLE_RADIUS here.
```

No `PLATE_HEIGHT`, no `POOL_WATER_THICK`, no `ENDBOX_HEIGHT`, no `BLADE_TOP_CLAD` — **none
of B1–B4 or the A-series is present.** The published model has 60 cm plates, a 15 cm
end-box, an 8×9 lattice with no pool, a 2.5 cm flux trap hole, graphite at the superseded
density, and the pre-B4 tally mesh. Its `plots/` directory (07-27) matches the stale set in
E3.

Its `run_results/` (07-01) is older still.

**`PROJECT_BIBLE.md` is confirmed ABSENT** from the deliverable repo — searched the whole
tree, no match. That rule is being honoured.

Its working tree is clean; last commit `fc180b9` (2026-07-27 15:46) by Thomas-McCoy.

---

# F. Open values — what is still unknown

| # | Item | Current value | Basis | Blocking on | Impact if wrong |
|---|---|---|---|---|---|
| 1 | Graphite S(α,β) MT card | `c_Graphite` applied, 294 K | Our choice; card m00005 snippet has no MT line | **Kyle** | **Large.** Thermal scattering on a reflector materially changes the thermal spectrum. Kyle's snippet proves nothing (MCNP specifies MT separately), so this is genuinely unknown, not merely unconfirmed. |
| 2 | Aluminium S(α,β) MT card | `c_Al27` on clad, structural Al, blade clad (330.7 K) and end-box Al (316.8 K) | 2026-07-20 meeting decision; Kyle confirmed Al gets S(α,β) | **Kyle** — both-sides change | Moderate. Reference model is also adding it; needs the same MT confirmation as graphite. |
| 3 | Depletion zone count | ~~`N_AXIAL_ZONES = 5`~~ → **`N_X_ZONES = 2`, `N_AXIAL_ZONES = 10`** | ~~`[MCNP-VISUAL]`~~ → **`[MCNP — Kyle confirmed 2026-08-12]`** | ~~Kyle~~ **RESOLVED 2026-08-12** | Closed. Reference subdivides each plate 2 × 10; implemented at `01edb31`. See the C5 amendment. |
| 4 | Uniform zone height | ~~12.0 cm~~ → **6.0 cm** | ~~`[DERIVED, MCNP-VISUAL]`~~ → **`[DERIVED]`** from `MEAT_HEIGHT / N_AXIAL_ZONES` | ~~Kyle~~ **RESOLVED 2026-08-12** | Closed by the 2 × 10 answer. Residual: uniformity was the natural reading of "2 × 10", not a separately confirmed statement — see the C5 amendment. |
| 5 | Plates share zone material | ~~assumed yes~~ → **NO — materials are per plate** | ~~`[MCNP-VISUAL, inferred]`~~ → **`[MCNP — Kyle confirmed 2026-08-12]`** | ~~Kyle~~ **RESOLVED 2026-08-12** | Closed. Cells and materials now 1:1 (12,280 each). The old scheme was valid OpenMC and a modeling choice, not a bug. |
| 6 | One material per element per zone | ~~assumed yes~~ → **superseded: one material per (element, plate, x, z)** | ~~`[MCNP-VISUAL]`~~ → **`[MCNP — Kyle confirmed 2026-08-12]`** | ~~Kyle~~ **RESOLVED 2026-08-12** | Closed by the same change as row 5. |
| 7 | Outer-pool water H-1 / O-16 | H-1 6.669090E-02 | OpenMC vs MCNP 6.673560E-02 — **0.067 %, outside the 0.010 % tolerance** | **Kyle / decision** | **Raised by B4.** This material now fills the entire 38.5 cm pool on all four sides instead of a one-cell ring, so its weight in the model is far greater than when the discrepancy was logged. No decision on record. |
| 8 | `c_Al27` on ENDF/B-VII.0 | assumed present, switch exists | VIII.0 grid is [20, 80, 294, 400, 600, 800] K; VII.0 unknown | **VII.0 library access** | **Load-bearing.** If VII.0 lacks `c_Al27`, `USE_AL_SAB` must be off for the matched run — the switch becomes mandatory, not optional. Cannot be checked here: `/opt/openmc-data/mcnp_endfb70/cross_sections.xml` **does not exist on this machine** (only VIII.0 and Lib80x under `~/nuclear-data`). |
| 9 | `C0` vs `C12`/`C13` on VII.0 | `add_element('C')` → C12/C13 | VII.0 carries natural carbon only; the split arrived in VII.1 | **VII.0 library access** | Model will fail to build, or silently resolve differently. `run_vii_mat.py:20` already has the env-keyed switch; `materials.py` has the `USE_NATURAL_CARBON` branch. |
| 10 | `run_vii_mat.py` rewrite | not started | Independent material definitions, stale on three counts | **Scheduling** | **VII.0 blocker.** See E1. |
| 11 | MCNP-side rows "will be updated" | unfueled plate 0.150 → 0.127; homogenized region X/Y 7.600/8.000 → 7.700/8.100 | Kyle stated the reference model is the incorrect side | **Kyle's edit** | Our side is already correct and must **not** be changed to match. Until Kyle's edit lands, those rows will read as mismatches. |
| 12 | MCNP-to-OpenMC conversion tool | unknown | Task 3, never named | **Kyle / project** | Out of Phase 1 scope; recorded because it was never confirmed. |
| 13 | ADDER depletion integrator | ~~unknown~~ → **CE/CM predictor-corrector (`cecm`), CRAM48 solver, 4 substeps** | **`[MCNP/ADDER — Kyle 2026-08-12]`**, recorded as dormant `CoreConfig` fields | ~~Task 4~~ **PARTIALLY RESOLVED 2026-08-12** | Settings known; **still blocked on two things** — no depletion chain file exists on this machine, and OpenMC `substeps` needs 0.16.0 for `CECMIntegrator` (this machine runs 0.15.3). Whether ADDER's "substep" is the same operation as OpenMC's is `[ASSUMED-EQUIVALENT — needs Kyle]`. |
| 14 | `CTRL_OUTER_OFFSET` 0.1305 vs the model as it stands today | 0.1305 `[MCNP]` | Kyle supplied directly; said the model "either already carries it or will be updated to it" | **Kyle's confirmation** | Low. Recorded in-code that the value may postdate the reference model, so a future surface-card diff could disagree without either side being wrong. |
| 15 | **Which flux-trap configuration is the benchmark** | D4 (centre) + A6 (edge), pinned by assert at `geometry.py:1483` | A-2 §1, "one water-filled flux trap near the centre of the core, another near an edge". `PROJECT_BIBLE.md` §5 asked Kyle to confirm A-2 Table 1 vs the Chapter 7 / Appendix G treatment, which differ. **No answer was ever recorded**, and the question was not carried forward into Testament II. | **Kyle** | **Low for the model, real for the manuscript.** The core layout is MATCH against the reference MCNP model on every count — 23 standard, 5 control, 2 flux traps, 12 graphite — so the geometry is correct whichever TECDOC section is authoritative. But the manuscript will cite TECDOC for that layout, and citing the section that describes a *different* configuration is a reviewer catch. |

### TODO / FIXME / VERIFY / PENDING comments

Complete list, whole repository:

| Location | Text | Waiting on |
|---|---|---|
| `model/core.py:77` | `TODO: ADDER-OpenMC coupling — confirm chain file, power basis, steps.` | Task 4 |
| `model/core.py:199` | `TODO: ADDER-OpenMC coupling — decide operator type (CoupledOperator vs ADDER-driven flux/microXS handoff), normalization mode, diff_burnable_mats` | Task 4 |
| `model/core.py:205` | `raise NotImplementedError("… TODO: ADDER-OpenMC coupling.")` | Task 4 |
| `model/core.py:213` | `TODO: ADDER-OpenMC coupling — fill in chain_file, power_w, timesteps, integrator` | Task 4 |
| `model/core.py:221` | `raise NotImplementedError("… TODO: ADDER-OpenMC coupling.")` | Task 4 |
| `model/core.py:131` | `# … Verify that rather than assume it: a base-fuel …` | internal note, not a blocker |
| ~~`model/materials.py:230`~~ | ~~`[MCNP-VISUAL — UNCONFIRMED, pending Kyle]`~~ | **RETIRED 2026-08-12** |
| ~~`model/materials.py:249`~~ | ~~`N_AXIAL_ZONES = 5  # [MCNP-VISUAL — UNCONFIRMED, pending Kyle]`~~ | **RETIRED 2026-08-12** |
| ~~`model/geometry.py:276`~~ | ~~`[MCNP-VISUAL — UNCONFIRMED, pending Kyle]`~~ | **RETIRED 2026-08-12** |

> **AMENDED 2026-08-12.** The `core.py` line numbers in the rows above have drifted by
> ~100 lines since the audit and no longer locate the text quoted; the TODOs themselves
> are still present and still waiting on Task 4, except the integrator/solver/substeps
> settings, which Kyle supplied (see row 13 of the table above). The three
> `[MCNP-VISUAL]` rows are retired outright — no live claim carries the tag.

No `FIXME`, `XXX`, or `HACK` anywhere. The `VERIFY` note that used to sit on
`FT_HOLE_RADIUS` was removed when A1 closed.

---

# G. Code vs spreadsheet

## **G is BLOCKED — the spreadsheet is not on this machine.**

**FINDING 4 — BLOCKER (for the audit, not the model).**

`model_cross_validation.xlsx` was searched for across the entire home directory to depth 6,
by name and by extension. The only spreadsheet found anywhere is
`~/projects/openmc-adder/adder/tests/analytic/reference_solutions.xlsx`, which belongs to an
unrelated third-party package.

It is not in the dev repo, not in the deliverable repo, and not in any parent directory.
There is no CSV or ODS export either.

**Consequences:**

- **G1** (row → constant mapping), **G2** (constants with no row), **G3** (stale OpenMC
  column), and **G4** (which side must move) **cannot be performed.** Any statement I made
  about them would be fabricated.
- More seriously for the project: **the artifact that defines Phase 1 success is not under
  version control and does not travel with the code.** Every provenance claim in this
  codebase — every `[MCNP]` tag, every "MATCH" annotation, the entire B5 verification — is
  checked against a document that a second reviewer cannot open from this repository. The
  audit trail terminates at a file nobody else can see.

What *can* be stated from the code side, as a partial substitute for G2 — constants that
carry a value a spreadsheet row would need, with what this phase recorded about them:

| Constant | Value | Recorded spreadsheet disposition |
|---|---|---|
| `PLATE_HEIGHT` / `ELEM_Z` | 62.000 | B1, OpenMC updated |
| `MEAT_HEIGHT` | 60.000 | MATCH |
| `ENDBOX_HEIGHT` | 14.000 | B1, OpenMC updated |
| `FT_BLOCK_X/Y`, `REFL_BLOCK_X/Y` | 7.600 / 8.000 | B2, OpenMC updated |
| `ABSORBER_WIDTH` | 6.630 | B3, OpenMC updated |
| `ACTIVE_STACK_X` | 6.640 | MATCH (coolant channel width) |
| `POOL_WATER_THICK` | 38.5 | B4, "team okay with any value near MCNP" |
| `FT_HOLE_RADIUS` | 2.820 | A1, → MATCH |
| graphite Σ C | 8.724000E-02 | A2, → MATCH; C-12/C-13 rows **N/A** on MCNP side |
| `CTRL_OUTER_OFFSET` | 0.1305 | A3, fills "Exterior coolant channel thickness" |
| `ABSORBER_THICK + 2·CTRL_BLADE_WATER` | 0.5650 | A3, fills "Control guide coolant channel thickness" |
| `BLADE_TOP_CLAD` | 1.000 | commit 17, **new row on both sides** |
| `CTRL_AL_PLATE_THICK` | 0.127 | B5 — **ours is correct**, MCNP side to move |
| `ABSORBER_THICK` | 0.310 | row exists; **constant is untagged and unasserted** (A1/D4) |

**Recommendation:** commit the spreadsheet, or a plain-text/CSV export of the Geometry and
Materials sheets, into `docs/`. Until then G cannot be audited by anyone.

---

# H. Does it still work

All runs at `c45d4b8`, ENDF/B-VIII.0, OpenMC 0.15.3.

### H1 — `python geometry.py`

**PASS.** Exit 0. All module-level asserts, the layer-sum tripwires, the blade z-range
asserts and the axial-stack sum assert pass at import.

### H2 — full model build, overlaps and lost particles

**PASS at all four blade positions.**

| f | Overlap check | Point checks | Slot checks | Lost particles |
|---|---|---|---|---|
| 0.0 | pass | pass | pass, blade z=[−30, +30] | **0** |
| 0.5 | pass | pass | pass, blade z=[0, +60] | **0** |
| 0.99 | pass (partially-clipped clad, cap fully clipped) | pass | pass, blade z=[+29.4, +89.4] | **0** |
| 1.0 | pass (blade top coincident with `CORE_TOP`) | pass | pass, blade z=[+30, +90] | **0** |

Only two warnings in the whole run, both benign: `Cell overlap checking is ON` (by design)
and `Could not compute uncertainties -- only one active batch simulated` (the debug run uses
2 batches).

### H3 — short tripwire, both blade positions

10 000 particles × 40 batches, 15 inactive, seed 1.

| f | k-eff |
|---|---|
| 0.0 (blades inserted) | **0.98090 ± 0.00180** |
| 1.0 (blades withdrawn) | **1.19690 ± 0.00190** |

Reported without interpretation, as instructed. Not compared to any historical value.
k-eff is not a Phase 1 success criterion. Note for the record that no run in this project
has ever carried a Shannon entropy mesh, so source convergence has never been monitored —
that belongs to whoever produces the VII.0 cross-validation numbers.

### H4 — every script at HEAD

| Script | Result |
|---|---|
| `model/geometry.py` | **PASS** — full protocol, above |
| `model/materials.py` | **PASS** — imports and builds all 8 materials |
| `model/settings.py` | **PASS** — writes `settings.xml`, prints summary |
| `model/tallies.py` | **PASS** — writes `tallies.xml`, mesh derives from geometry constants |
| `model/check_u235_mass.py` | **PASS** — prints per-element U-235 masses |
| `model/run_vii_mat.py` | **PASS (and this is the problem)** — exit 0, prints `graphite_reflector — 1.7 g/cm3`. See E1. |
| `tests/check_depletion_zoning.py` | **PASS** — `ALL CHECKS PASSED` |
| `tests/make_phase1_xs_plots.py` | **PASS** — writes 4 plots |
| `figures/make_figures.py` | **PASS** — all figures, consistency tripwires pass |
| `figures/check_figures.py` | **PASS with warnings** — reports luminance-pair violations (`fig3_axial_xz: min pair 0.0157 < 0.15`, `fig4_elements` and `fig4b_cfe: 0.1220 < 0.15`). Greyscale-legibility warnings, not errors. |
| `model/core.py` | **not run to completion** — exceeded the audit time budget; syntax and import verified, depletion entry points raise `NotImplementedError` by design |
| `tests/plot_core.py` | **not run** — exceeded the audit time budget; syntax verified. Note it generated the 12 stale plots in E3. |
| `model/Analyze_rod_sweep.py` | **not run** — requires rod-sweep statepoints that do not exist; syntax verified |
| `run/run_rod_sweep.py` | **not run** — full production sweep, far beyond the audit's transport budget; syntax verified |
| `archive/run_allin.py` | **not run** — archived; syntax verified |

Nothing was fixed. `figures/check_figures.py`'s luminance warnings are pre-existing and
were reported the same way before this phase.

> **AMENDMENT (added after review, 2026-07-31).**
>
> **`tests/plot_core.py` has since been run at HEAD and PASSES** — exit 0, no
> traceback, regenerating `core_geometry_plots.png` correctly against current
> geometry. Its depletion-zone views sit behind a `--depletion-zones` flag and
> were not invoked, so nothing unconfirmed was rendered. The regenerated file was
> restored with `git checkout` before `d74f158` so the untracking covered the
> stale content rather than a fresh render.
>
> **The remaining four are recorded as KNOWINGLY UNVERIFIED, not pending.** They
> will not be run, for stated reasons:
>
> | Script | Why it is not run |
> |---|---|
> | `model/core.py` | Its depletion entry points `raise NotImplementedError` by design. Import and syntax verified; there is nothing further to execute. |
> | `model/Analyze_rod_sweep.py` | Post-processes rod-sweep statepoints that do not exist in the tree. |
> | `run/run_rod_sweep.py` | Drives a full production sweep — far beyond any audit transport budget, and Phase 1 authorises no production runs. |
> | `archive/run_allin.py` | Archived. Imports `make_flux_trap`, `water_univ`, `graphite_univ` and would run against current geometry with pre-B4 assumptions. |
>
> This is a deliberate limit on the audit's coverage, not an outstanding task.
> Anyone relying on these four should verify them first.

---

# I. What a reviewer would ask

If this model landed at Argonne with no one to explain it, these are the four things that
would come back first.

**1. "Your published repository does not contain this model."**

The single most damaging finding. `github.com/mascovale/CSM-Open-source-Reactor-Model-Library`
serves a `geometry.py` with `FT_HOLE_RADIUS = 2.5`, 60 cm plates, a 15 cm end-box and an
8×9 lattice with no pool. Everything described in this audit lives on an **unpushed local
branch**. A reviewer who clones the public repo and reads the code will be reviewing a model
that no one has worked on since 27 July, and will reach conclusions that have nothing to do
with the current state. This is not a code defect; it is a distribution defect, and it makes
every other finding here moot for anyone outside this machine.

**2. "What is the reference model, exactly, and can I see it?"**

This is the weakest claim in the project. Nineteen constants are justified by `[MCNP]` or
`[TECDOC]` tags whose backing document — `model_cross_validation.xlsx` — is **not in the
repository and not on this machine**. The strongest provenance in the entire codebase is
the graphite density, precisely because Kyle pasted the actual card (`m00005`) and it went
into the comment verbatim. Nothing else has that. `CTRL_OUTER_OFFSET = 0.1305` is `[MCNP]`
on the strength of a value Kyle supplied verbally, which the code itself records "may
postdate the current state of the reference model" — a tag that means "Kyle confirmed it"
attached to a number that may not be in the reference model yet. That is defensible and
honestly documented, but a reviewer will notice, and the honest answer is that the model is
being validated against a spreadsheet rather than against the MCNP source.

**3. "Why is the blade top clad 1 cm?"**

Because the fuel plates' unfueled extension is 1 cm, and `BLADE_TOP_CLAD = CLAD_EXT`. The
value is Kyle-confirmed, but the *link* is this project's choice, and it produces a
suspiciously tidy result: the cap lands exactly coplanar with the surrounding end-boxes at
full insertion, which is the property the A4 Option B guard used to enforce explicitly and
which the arithmetic now delivers for free. A reviewer will ask whether the reference model
actually has 1 cm of aluminium there, or whether 1 cm was adopted because it made the
geometry close. The commit record answers this correctly — Kyle gave the thickness, the
`CLAD_EXT` linkage is documented as a convenience with a one-line decoupling path, and an
assert catches the decoupling — but the question will be asked, and the surrounding evidence
is a spreadsheet row rather than a surface card.

**4. "Which of these numbers has anyone actually checked against a neutronics result?"**

None of them, and that is by design this phase. The honest position is that Phase 1 matched
*geometry* to a spreadsheet, and that the k-eff numbers produced along the way are on
ENDF/B-VIII.0 against VII.0 reference targets, with three material questions open (graphite
MT card, Al MT card, pool water H-1) and no source-convergence diagnostic ever run. A
reviewer expecting a validated model will not find one; a reviewer expecting a documented,
tripwired geometry with its uncertainties enumerated will. The project should be careful to
present it as the latter.

**Runner-up, worth stating:** the strongest verification in this repository — the point
containment suites covering the clad band, the end-boxes, the pool, the full blade stack and
the end-block layer walk — runs **only** when a human types `python geometry.py`. There is
no CI and no test runner. The quality of those checks is genuinely high; their reachability
is not.

---

# FILES FOR SECOND REVIEW

Sorted by how much a reviewer gains per line read. A reviewer cannot read 6 367 lines.

### Top three — read these

| # | File | Lines | Why |
|---|---|---|---|
| 1 | **`model/geometry.py`** | 1 992 | Everything Phase 1 changed. All 69 constants, all provenance tags, 76 of the 115 asserts, and the entire point-containment suite. Unavoidable. If only one file is read, this is it. Concentrate on lines 84–310 (constants and axial tripwires) and 940–1010 (the blade clad/cap stack, the newest and least-reviewed code). |
| 2 | **`model/materials.py`** | 315 | Short, and holds the two claims most likely to be wrong: the graphite card transcription (137–171) and the seven `[MCNP-VISUAL]` depletion assumptions (227–252). High information per line. |
| 3 | **`model/run_vii_mat.py`** | 193 | Read it *because* it is wrong. It runs cleanly and produces a different model; understanding why is the fastest way to see how the repo can mislead someone. |

### Everything else

| File | Lines | Reviewer value |
|---|---|---|
| `model/tallies.py` | 68 | High per line — worked example of the derive-don't-restate rule after being caught violating it |
| `model/settings.py` | 130 | Read lines 63–92 only: the surviving magic numbers and the stale comment |
| `model/check_u235_mass.py` | 55 | One line matters (line 10, the new duplication) |
| `tests/check_depletion_zoning.py` | 410 | Skim — validates the zoning scaffolding, passes at HEAD |
| `tests/make_phase1_xs_plots.py` | 115 | Skim — the verification plot generator; short and derives everything |
| `model/core.py` | 277 | Skim — driver plus ADDER stubs that raise |
| `figures/make_figures.py` | 803 | Low unless reviewing figures — but lines 178–216 are a genuinely useful independent check of the geometry constants |
| `figures/figstyle.py` | 460 | Skip unless reviewing typography |
| `tests/plot_core.py` | 801 | Skip the code; note only that it produced the 12 stale plots |
| `figures/check_figures.py` | 222 | Skip unless reviewing figures |
| `model/Analyze_rod_sweep.py` | 238 | Skip — post-processing for runs that do not exist |
| `run/run_rod_sweep.py` | 227 | Skip |
| `archive/run_allin.py` | 61 | Skip — archived |
| `model/__init__.py` | 0 | Empty |

**Suggested reading order for a two-hour review:** `geometry.py` lines 84–310 → `materials.py`
137–252 → this audit's Sections C3 and F → `run_vii_mat.py` in full → `settings.py` 63–92.
That is roughly 700 lines and covers every BLOCKER and RISK in this report.

---

*End of audit. No repository file was modified in the course of it. This document was
written to `docs/PHASE1_AUDIT.md` and has not been committed.*
