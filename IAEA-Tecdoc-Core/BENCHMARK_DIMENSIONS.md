# IAEA TECDOC-643 Appendix A-2 — Benchmark Dimensions
## Source files
- **v2** = `te_643v2_prn.pdf` (Volume 2: Analysis, Appendices A–F)
- **v1** = `te_643v1_prn.pdf` (Volume 1: Summary, Chapters 1–7)

All page numbers are **printed** page numbers (as stamped in the PDF body).

---

## Standard fuel element — heterogeneous cross-section

| Dimension | Value (cm) | Source | Note |
|-----------|-----------|--------|------|
| Element envelope, x | **7.60** | v2 p.32 Fig.2 top-left | "Standard Element" label; 7.60 arrow |
| Element envelope, y | **8.00** | v2 p.32 Fig.2 top-left | 8.00 arrow on right edge |
| Lattice pitch, x | **7.70** | v2 p.32 Fig.2 both models | All "Model for…" diagrams show 7.70 |
| Lattice pitch, y | **8.10** | v2 p.32 Fig.2 both models | All "Model for…" diagrams show 8.10 |
| Side plate thickness (physical) | **0.48** | v2 p.32 Fig.2 top-left | Left margin annotation |
| Fuel-meat margin (each side in x) | **0.17** | v2 p.32 Fig.2 top-left | Right margin annotation; equals (6.64 − 6.30)/2 |
| Active stack width (between side plates) | **6.64** | derived | ELEM_X − 2×SIDE_PLATE = 7.60 − 0.96 |
| Fuel meat width | **6.30** | v2 p.32 Fig.2 top-left | "6.30" arrow |
| Fuel meat thickness (y, per plate) | **0.051** | v2 p.32 Fig.2 top-left | "0.051" label on meat slice |
| Inner clad thickness | **0.038** | v2 p.32 Fig.2 top-left | "0.038" label |
| Outer clad thickness | **0.0495** | v2 p.30 Table 1 | "0.495 mm outer plates" |
| Water channel thickness | **0.219** | v2 p.32 Fig.2 top-left; v2 p.30 Table 1 | "0.219" in Fig.2; "2.19 mm" in Table 1 |
| Plate thickness (all plates, fuel + Al) | **0.127** | v2 p.30 Table 1 | "Plate Thickness, mm: 1.27"; applies to fuel **and** the 4 Al control guide/slider plates |
| Plates per standard element | **23** | v2 p.30 Table 1 | |
| Active fuel height | **60.0** | v2 p.30 Table 1 | "76 × 80 × 600 mm" element dimensions |

**Homogenized "Model for Standard Element" (diffusion code, top-right Fig.2, v2 p.32):**
Fueled region 6.30 cm + side margin 0.70 × 2 = 7.70 cm total.
The 0.70 cm homogenized margin absorbs the 0.48 cm physical side plate plus the 0.05 cm inter-element gap; this grouping is a diffusion-code artifact, not a physical dimension.

---

## Control fuel element — guide region dimensions

| Dimension | Value (cm) | Source | Note |
|-----------|-----------|--------|------|
| Guide region depth (each end, y) | **1.075** | v2 p.32 Fig.2 bottom-right | "1.075" annotation on right margin |
| Absorber (Hf blade) thickness | **0.310** | v2 p.32 Fig.2 bottom-right | "0.31" label on absorber (black bar) |
| Absorber offset from element face | **0.395** | v2 p.32 Fig.2 bottom-right | "0.395" annotation = distance from element face to absorber near edge |
| Al guide plate thickness | **0.127** | v2 p.30 Table 1 | "Plate Thickness: 1.27 mm"; same row for all plates; confirmed by 4 Al plates × 0.127 = 0.508 cm < 1.075 ✓ |
| Inner water channel (guide → absorber) | **0.268** | derived | ABSORBER_GAP − Al_plate = 0.395 − 0.127 |
| Outer water channel (absorber → slider) | **0.243** | derived | GUIDE_REGION − ABSORBER_GAP − ABSORBER_THICK − Al_plate = 1.075 − 0.395 − 0.310 − 0.127 |
| Al slider plate thickness | **0.127** | v2 p.30 Table 1 | Same as guide plate |
| Number of Al plates total | **4** | v2 p.30 Table 1 | "17 + 4 Al Plates"; 2 per end (guide + slider) |
| Control fuel plates | **17** | v2 p.30 Table 1 | |
| Fuel region height (between guide ends) | **5.85** | derived | ELEM_Y − 2 × GUIDE_REGION = 8.00 − 2.15 |

**Guide-region internal layout (per end, reading from element face inward):**
```
[Al guide 0.127 | H₂O 0.268 | Hf/H₂O 0.310 | H₂O 0.243 | Al slider 0.127] = 1.075 cm ✓
```
The two water channels are **asymmetric** (0.268 vs 0.243) because the absorber is offset 0.395 cm from the element face rather than centered.

---

## Control element — fueled-region width and side-plate dimensions

| Diagram | Fuel width (cm) | Side margin (cm) | Total x (cm) | Source |
|---------|----------------|-----------------|-------------|--------|
| Model, without blades | 6.30 | 0.70 | 7.70 | v2 p.32 Fig.2 bottom-left |
| Model, with blades | 6.60 | 0.55 | 7.70 | v2 p.32 Fig.2 bottom-right |
| Physical element (Table 1) | — | — | 7.60 × 8.00 | v2 p.30 Table 1 ("76 × 80 mm") |

---

## Figure inconsistencies (Fig. 2, v2 p.32)

1. **Without-blades vs with-blades fuel width mismatch**: the without-blades model shows 6.30 cm fueled width and 0.70 cm side margin; the with-blades model shows 6.60 cm and 0.55 cm. These are both homogenized diffusion-code representations, not physical element dimensions. The physical element has 0.48 cm Al side plates and 6.64 cm interior (from Table 1 "76 mm" element).

2. **Control element fills full x-pitch (7.70 cm) in both models, while standard element heterogeneous cross-section shows a 7.60 cm envelope**: the control element models absorb the 0.05 cm inter-element water gap on each x-side into the homogenized side margin. This is a diffusion-code modeling choice, not a physical difference between standard and control elements.

3. **Standard element heterogeneous y-envelope = 8.00 cm, but all "Model for…" diagrams show 8.10 cm** (= y-pitch): the models again absorb the inter-element gap into the model region.

**OpenMC geometry call (Part B):** the physical element dimensions from Table 1 (76 × 80 mm envelope, 0.48 cm Al side plates, 6.64 cm interior) are used for the heterogeneous OpenMC model for **both** standard and control elements. The 6.60/0.55 and 6.30/0.70 values in Fig. 2 are diffusion-code homogenized representations only; they are not implemented in the Monte Carlo model. The control element x-envelope is 7.60 cm (leaving the same 0.05 cm water gap to the pitch boundary as the standard element).

---

## As-implemented control-element end block (current `geometry.py`)

The literal Fig.2 guide-region reading above (1.075 cm, asymmetric 0.268/0.243 cm
water channels from a 0.395 cm absorber offset) is **not** what the OpenMC model
implements. Starting with commit `65fb194` ("Rework control-element end blocks:
standard follower pitch, feeder channel, symmetric blade water, outer guide
offset") and finalized in the 2026-07-20 meeting, the end block instead uses a
symmetric layout built outward from the 17-plate follower stack, with the
blade-flanking water gap as the free residual:

```
[feeder channel 0.219 | Al guide 0.127 | blade water 0.139 | absorber 0.310 |
 blade water 0.139 | Al guide 0.127 | outer offset 0.1075] = 1.1685 cm
```

| Constant | Value (cm) | Provenance |
|----------|-----------|------------|
| `CTRL_AL_PLATE_THICK` | 0.127 | [TECDOC] Table 1 "1.27 mm"; reverted 2026-07-20 from a 0.15 cm Argonne TH-analysis convenience |
| `CTRL_FEEDER_CHANNEL` | 0.219 | Standard fuel-to-fuel water channel (`WATER_CHAN_THICK`) — same width as every plate-to-plate channel in the follower stack |
| `CTRL_OUTER_OFFSET` | 0.1075 | [DERIVED] = `STD_END_WATER`, the standard element's own last-plate-to-envelope water gap |
| `CTRL_BLADE_WATER` | 0.139 | Computed residual (symmetric both sides of the blade): `(1.1685 − 0.219 − 2×0.127 − 0.310 − 0.1075) / 2` |
| `CTRL_END_BLOCK` (total, each end) | 1.1685 | = `ELEM_Y/2 − CTRL_FUEL_STACK_HALF` = 4.0 − 2.8315 |

This total (1.1685 cm) differs from the Fig.2-derived guide-region depth
(1.075 cm) above — the discrepancy is an open reconciliation item between the
literal figure annotation and the as-built follower-stack-driven model; it has
not been resolved as of this writing.

Two related 2026-07-20 meeting decisions, in `materials.py` (not a dimension
table entry, noted here for provenance tracking):
- Graphite reflector density set to **1.7000 g/cm³** [TECDOC] (replaces the
  deck-implied ~1.740 g/cm³ atom-density spec).
- Al-27 thermal scattering (`c_Al27` S(a,b)) enabled (`USE_AL_SAB = True`) on
  clad, structural aluminum, and `end_box_homog`, gated on the active
  cross-section library providing `c_Al27` (ENDF/B-VIII.0 does; VII.0 does not).

Also per the 2026-07-20 meeting: the control blade's B4C absorber now carries a
15 cm homogenized (`end_box_homog`) end-box cap rigidly attached to its top
face, translating with the blade and clipped at `CORE_TOP`; not a dimension
change, but it changes what fills the slot above the blade at intermediate
withdrawal fractions (previously fixed end-box/water bands).
