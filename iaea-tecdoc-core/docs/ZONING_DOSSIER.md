# Depletion Zoning — Changes Dossier

**Status: working document, raw material for a written report. Not a polished
deliverable.** Completeness is preferred over prose. Where something is
uncertain it is flagged inline as **[UNCERTAIN]** rather than smoothed over.

Written 2026-08-12. Code state: commits `01edb31` (zoning code), `e000b30`
(audit docs), `d76faf0` (plot lattice-origin fix), `0b95056` (plot legibility
and size guards, hue-map axes), `5520fb3` (COST-block cell-search correction),
on branch `phase1/geometry-finalization`.

**Revision note.** Three claims in the first draft were flagged as uncertain and
have since been checked; all three were wrong or overstated and are corrected in
place, each marked at the point of correction. They were: the cell-search
mechanism (§8), the consequence of a missing material volume (§3.2), and the
value of the plot distinctness assertion (§10 item 7). The flagging was what
made them findable — that is the argument for flagging rather than smoothing.

Audience note: written for an engineer who is not a professional programmer.
Programming concepts are explained where they appear.

---

## 1. CHRONOLOGY

Four states, in order. Each superseded the last. All of the superseded records
are still in `model/materials.py`, dated — nothing was deleted.

### 1.0 Original — axial-only, 5 zones (2026-07-27)

**What it was.** Each fuel plate's active meat was cut into 5 stacked slabs of
12.0 cm. One depletable material per element per axial zone, shared by every
plate of that element: 28 elements × 5 = **140 materials** over
614 plates × 5 = **3,070 cells**.

**Why.** Preparation for an ADDER-OpenMC depletion coupling. A depletion solve
needs the fuel divided into regions that burn independently; a single lumped
fuel material would burn uniformly and could not show axial burnup shape.

**What triggered it.** Kyle Anderson asked for it as Phase 1.5 work.

**Provenance.** The scheme was read *visually* off a zx slice plot of the
reference MCNP model — counting colour bands in an image. Tagged
`[MCNP-VISUAL — UNCONFIRMED, pending Kyle]`. It was never transcribed from the
MCNP source and never confirmed.

### 1.1 The 2D generalization — 8 × 20 (2026-08-12)

**What changed.** The subdivision became two-dimensional: the meat is now cut in
the **width** direction (x) as well as the **axial** direction (z). Resolution
set to `N_X_ZONES = 8`, `N_AXIAL_ZONES = 20` → 160 zones per element, 98,240
cells, 4,480 materials (still element-shared).

**Why.** A purely axial division cannot represent burnup gradients across the
6.3 cm width of a plate. The outer edges of a plate see a different neutron
spectrum than the centre (they face the water channels and the side plates), so
they burn differently.

**What triggered it.** A direct request to generalize, with the explicit goal
that *any* `(N_X_ZONES, N_AXIAL_ZONES)` pair must work.

**What it superseded.** The 5-zone count. **Not** the plate-sharing inference —
that survived this change untouched, which turned out to matter (see 1.3).

**Provenance.** 8 × 20 was tagged `[ASSUMED]` — explicitly *our own choice of
resolution*, not a claim about the reference model. This distinction is the
whole reason the change was safe to make: it did not pretend to new knowledge.

### 1.2 The 2 × 10 retarget (2026-08-12)

**What changed.** Constants only: `N_X_ZONES = 2`, `N_AXIAL_ZONES = 10`.
20 zones per element, 12,280 cells, 560 materials (still element-shared).
Zone size 3.15 × 6.0 cm; 0.9639 cm³ of meat per plate per zone.

**Why / what triggered it.** Kyle confirmed on 2026-08-12 that the reference
MCNP model subdivides **each fuel plate 2 × 10**. This is real information about
the reference, so it displaced our placeholder.

**What it superseded.** The `[ASSUMED]` 8 × 20, and — one step further back —
the `[MCNP-VISUAL]` 5. Three values now on record.

**Provenance change.** The counts moved from `[ASSUMED]` to
`[MCNP — Kyle confirmed 2026-08-12]`. This matters: it means changing them is no
longer a free choice, it is a departure from the confirmed reference.

**Also landed in this step (unrelated to geometry):** the ADDER-side depletion
settings Kyle supplied the same day — `cecm` integrator, `cram48` solver,
4 substeps — recorded as dormant `CoreConfig` fields. See §9.

### 1.3 Per-plate materials (2026-08-12)

**What changed.** Material *granularity*, not geometry. Cells are unchanged at
12,280. Materials went from 560 (one per element per zone, shared across all
plates of that element) to **12,280** — one per plate per zone. **Cells and
materials are now 1:1.** Every material owns exactly one plate's zone,
0.9639 cm³. The standard/control volume distinction disappeared entirely: there
is no longer a 23-plate or 17-plate multiplier anywhere in the material path.

**Why / what triggered it.** Kyle confirmed that materials should be matched at
per-plate resolution too.

**What it superseded — and this is the important one.** The last surviving
`[MCNP-VISUAL]` inference: *"all plates in an element share a zone material."*
That claim had survived two zone-count supersessions. The in-code note had
warned, verbatim: *"plate-sharing is the ONE inference still implemented, and it
is still unconfirmed. Superseding the zone COUNT does not retire it."* A
separate answer retired it, exactly as the note anticipated.

**Critical framing, which must survive into the report:** the 560-material
scheme **was not a bug.** OpenMC does not require a one-to-one mapping between
cells and materials; many cells sharing one material is normal and is still used
throughout this model (cladding, water, graphite). Element-shared materials were
*valid* — they were a **modelling choice**. What that choice meant physically:
a depletion solve would have seen one flux and reaction-rate spectrum averaged
over all 23 plates of an element in a given zone, so burnup gradients *across
the plate stack* could not develop. Per-plate materials let them. We changed it
to **match the reference model, not to fix a defect.**

---

## 2. THE GEOMETRY MECHANISM

### 2.1 What a "cell" is, and what a "material" is

These are two different things and the distinction is the key to everything
below.

A **material** is a *recipe*: a list of nuclides and how much of each, plus a
density and a temperature. `LEU_U3Si2_Al_fuel` says "this much U-235, this much
U-238, this much Al-27, this much Si, at 332.1 K." A material has **no position
and no shape.** It does not know where it is. You could use the same material in
a thousand different places.

A **cell** is a *region of space* with something in it. A cell says "the volume
bounded by these surfaces is filled with material X." Cells have position and
shape; they do not have composition of their own — they point at a material.

The relationship is many-to-one by default: **many cells can point at the same
material.** That is normal and is what this model does for cladding — every one
of the 614 cladding cells points at the single `Al_6061_cladding` material.

Why the distinction matters for depletion: a depletion calculation burns
**materials**, not cells. It computes a reaction rate for each material,
solves how the nuclide inventory changes, and writes back a new composition.
If ten cells share one material, they burn as one lump with one averaged
spectrum — the ten cells cannot diverge from each other. That is exactly the
limitation the per-plate change removed.

### 2.2 How the meat region is defined by half-spaces

OpenMC builds solids by intersecting **half-spaces**. A plane divides all of
space into two halves; a half-space is one of them. `+surface` means the side
where the coordinate is greater than the plane; `-surface` means less than.

An X-plane at x = −3.15 splits space into "everything left of −3.15" (`-`) and
"everything right of −3.15" (`+`). Intersect `+` of that plane with `-` of an
X-plane at x = +3.15 and you have an infinite slab 6.3 cm thick in x, unbounded
in y and z. Add a pair of Y-planes and a pair of Z-planes and the slab becomes a
closed rectangular box.

The unzoned fuel meat is exactly that — six planes, three matched pairs:

```
meat_region = +meat_left & -meat_right     # x: −3.15 to +3.15   (6.3 cm wide)
            & +meat_bottom & -meat_top     # y: one plate's meat thickness (0.051 cm)
            & +_z_fuel_bot & -_z_fuel_top  # z: −30 to +30       (60 cm tall)
```

`&` is intersection — "and". The result is a rectangular box 6.3 × 0.051 × 60 cm
= 19.278 cm³, the active meat of one plate.

### 2.3 How the zone planes subdivide it, and why N−1 not N+1

To cut a 60 cm tall stack into 10 slabs you need **9** internal cuts. The
outermost bounds (−30 and +30) already exist — they are the meat's own
boundaries, which were built long before zoning existed.

So the code creates `N_AXIAL_ZONES - 1 = 9` interior Z-planes at
−24, −18, −12, −6, 0, +6, +12, +18, +24, and reuses the existing planes at ±30
for the two outer edges. Same in x: `N_X_ZONES - 1 = 1` interior X-plane at
x = 0, reusing the meat's own ±3.15 planes at the edges.

Creating N+1 planes instead would build **duplicate surfaces coincident with the
existing meat boundaries** — two different plane objects at exactly z = −30.
That is not merely wasteful. Coincident surfaces are a classic source of
particle-tracking trouble: a neutron sitting exactly on the boundary can be
ambiguous about which cell it is in, which produces "lost particles". The
`zone_z_bounds(k)` and `zone_x_bounds(j, ...)` functions exist precisely to hand
back the *existing* surface at the edges and a *new* interior plane elsewhere:

```
zone k = 0                 → lower bound is the existing _z_fuel_bot  (z = −30)
zone k = N_AXIAL_ZONES − 1 → upper bound is the existing _z_fuel_top  (z = +30)
otherwise                  → an interior plane from the shared list
```

### 2.4 Why x planes and z planes are handled differently

This asymmetry is real and is the least obvious part of the design.

The **z** meat boundaries (`_z_fuel_bot`, `_z_fuel_top`, at ±30) are created
**once, at module level**, when `geometry.py` is first loaded. Every element in
the core reuses those same two plane objects. So a function that needs the
z edges can just reach up and grab them from module scope.

The **x** meat boundaries are *not* like that. Each fuel element is built as its
own self-contained "universe" — a reusable sub-assembly that the core lattice
then places at 28 different positions. Each element builder creates its **own**
`meat_left` and `meat_right` X-planes at ±3.15 in its own local coordinates.
There are 28 separate pairs of them, one per element.

Consequence: `zone_x_bounds()` **cannot** reach up and grab the x edges from
module scope, because there is no single module-level pair to grab — there are
28. So the calling element passes its own pair in as arguments:

```
zone_x_bounds(j, meat_left, meat_right)     # edges passed IN by the caller
zone_z_bounds(k)                            # edges read from module scope
```

Why not just hoist the x planes to module level and make them symmetric?
Because doing so would create those surfaces earlier in the program's life, which
shifts the automatic ID number assigned to every surface created afterwards. That
would change the exported model file even with zoning switched *off*, breaking
the byte-identity guarantee (§6.4). The asymmetric API was chosen to protect that
guarantee.

The **interior** planes are different again: both the interior x planes and the
interior z planes are created **once and shared across all 28 elements**, because
they sit at the same coordinates in every element's local frame. Creating them
inside the per-element builder would put 27 redundant duplicate planes in the
model at each interior position.

### 2.5 Why y is never subdivided

y is the direction the plates are stacked in. A standard element has 23 plates
stacked in y, each 0.127 cm thick, of which only the middle 0.051 cm is fuel
meat — the rest is cladding, and between plates is a water coolant channel.

The meat is therefore **already** discretized in y by physical structure: each
plate is its own separate slab of fuel with cladding and water on either side.
Subdividing a 0.051 cm meat thickness further would produce sub-slabs
0.025 cm thick with no physical boundary between them, and no meaningful spectral
difference across such a distance. There is nothing to resolve.

With per-plate materials (§1.3) the y direction is now fully resolved anyway —
every plate has its own materials — so the plate itself is the y zone.

### 2.6 One zone cell, start to finish

A real cell from the current model, `std0_meat_0_x0_z0` — element A2, plate 0,
x zone 0, z zone 0. This is the bottom-left corner zone of the first plate of the
first standard element. Its region as OpenMC stores it:

```
(3480 -3487 3485 -3486 1 -3488)
```

Six half-spaces, in order:

| Token | Surface | Type | Position | Where it came from |
|---|---|---|---|---|
| `+3480` | `meat_left` | X-plane | x = −3.15 | **element-local** — A2's own meat edge |
| `-3487` | interior x zone plane | X-plane | x = 0.0 | **shared** across all 28 elements, created lazily |
| `+3485` | `meat_bottom` | Y-plane | y = −3.843 | **plate-local** — plate 0's meat underside |
| `-3486` | `meat_top` | Y-plane | y = −3.792 | **plate-local** — plate 0's meat topside |
| `+1` | `_z_fuel_bot` | Z-plane | z = −30.0 | **module-level shared** — note the ID, `1`, one of the very first surfaces built |
| `-3488` | interior z zone plane | Z-plane | z = −24.0 | **shared**, created lazily |

The surface ID numbers themselves tell the story of §2.4: ID `1` is the
module-level z boundary created at import; IDs in the 3480s are element-local
surfaces created while building A2; IDs 3487/3488 are the lazily-created shared
zone planes, which get high numbers because they are not created until the first
zoned element asks for them.

Resulting box: x from −3.15 to 0.0 (3.15 cm), y 0.051 cm, z from −30 to −24
(6 cm). Volume 3.15 × 0.051 × 6.0 = **0.9639 cm³**, which is exactly the volume
recorded on the material that fills it, `fuel_A2_p0_x0_z0`.

Note that the y bounds are the **unmodified** plate meat bounds. The zone cell
substitutes its own x and z bounds but inherits y untouched — which is why a
zone cell has six half-spaces, the same as the unzoned meat cell it replaced,
rather than eight (see §6.2).

---

## 3. THE MATERIAL MECHANISM

### 3.1 What `clone()` does and why each zone needs its own material object

In the program, the base fuel is a single object in memory. If you simply wrote
`material_for_zone_1 = fuel` and `material_for_zone_2 = fuel`, you would not have
two materials — you would have two *names for the same one*. Burn one and the
other changes too, because they are the same object.

`clone()` makes a genuine independent copy: same nuclides, same densities, same
temperature, but a **new object with a new ID**. Twelve thousand clones are
twelve thousand materials that start life identical and can then diverge.

This is the mechanism by which burnup gradients become representable. At time
zero every one of the 12,280 materials has exactly the same composition. After
the first depletion step they differ, because each saw a different neutron flux.

The code deliberately re-specifies **nothing** after cloning — composition,
density, temperature and any thermal-scattering data are all inherited. Only
three things are set: the name, `depletable = True`, and the volume.

### 3.2 Why volume must be set, and what breaks without it

A material's composition is stored as a *density* — atoms per unit volume. A
depletion solve needs absolute *quantities*: how many atoms of U-235 are in this
region, so it can compute how many fission and know how many are left.

Atoms = density × volume. Without a volume the solver cannot make that
conversion.

**The failure is LOUD, not silent — corrected 2026-08-12.** An earlier draft of
this dossier speculated that a missing volume would produce a silent
misnormalization. That was wrong, and the correction matters because it changes
how much weight the guards below deserve. OpenMC raises:

```
RuntimeError: Volume not specified for depletable material with ID=X
```

The OpenMC user's guide states that the volume is required in order to compute
the proper normalization of tally results against the source rate. So a
volume-less depletable material stops the run; it does not quietly produce a
wrong burnup.

**Consequent adjustment to how the base-fuel exclusion should be described.**
The base `fuel` material is a real trap: OpenMC **automatically** flags any
material containing actinides as depletable, so the base fuel has been
`depletable = True` since long before zoning existed — and it has no volume,
because it is a recipe, not a region. When zoning is on it fills nothing, so
`core.build_model()` drops it from the exported set entirely, after first
asserting that no cell still uses it.

That exclusion is **defense in depth, not the thing standing between us and a
wrong answer.** OpenMC would have caught the volume-less material on its own, at
the start of the depletion run, with a clear message naming the offending ID.
What the exclusion buys is failing *earlier* (at model build, in our own code,
with our own message) and keeping an unused material out of the exported file.
Both are worth having. Neither is load-bearing for correctness, and the guard
should not be presented as though it were.

### 3.3 How the volume is computed, and why analytic not stochastic

Computed directly from the geometry constants:

```
MEAT_ZONE_WIDTH            = MEAT_WIDTH  / N_X_ZONES        = 6.3 / 2  = 3.15 cm
MEAT_ZONE_HEIGHT           = MEAT_HEIGHT / N_AXIAL_ZONES    = 60 / 10  = 6.0 cm
MEAT_ZONE_VOLUME_PER_PLATE = MEAT_THICK × MEAT_ZONE_WIDTH × MEAT_ZONE_HEIGHT
                           = 0.051 × 3.15 × 6.0            = 0.9639 cm³
```

OpenMC also offers a **stochastic** volume calculation: fire random points into
a bounding box, count how many land in each cell, infer volumes statistically.
That was not used, for three reasons:

1. **These cells are exactly rectangular boxes** — pure intersections of six
   planes. The volume is known in closed form. A statistical estimate of a
   quantity you can compute exactly is strictly worse.
2. **A stochastic estimate carries an uncertainty**, which would propagate into
   the depletion normalization as a systematic error that varies per zone.
3. **Reproducibility.** The analytic value is bit-identical on every run; a
   stochastic one depends on the random seed and sample count.

The checks exploit this: because the cells are exact boxes, a cell's *bounding
box* volume **is** its volume, so the test can compare declared material volumes
against geometry-derived volumes deterministically.

### 3.4 The registry, memoization, and the key

The registry is a dictionary — a lookup table from a key to a material object:

```
_zoned_fuel_registry = {}                       # key -> Material
key = (element_id, plate_index, x_index, zone_index)
```

**Memoization** means: when asked for a material, first check whether one already
exists for that key; if so hand back the *same* object rather than making a new
one. Without it, building the geometry twice in one program run (which the tests
do routinely) would silently create a second set of 12,280 materials.

**What the key means.** It is the definition of granularity, expressed as data.
The key answers "what makes two zones the same zone?" Under the old scheme the
key was `(element_id, x_index, zone_index)` — plate was *absent*, so two
different plates of the same element produced the same key and therefore got the
same material. That absence **was** the plate-sharing model. Adding
`plate_index` to the key is the entire granularity change; everything else
follows from it.

### 3.5 The 1:1 invariant

With per-plate materials, **every meat cell has its own material and no material
is shared.** 12,280 cells, 12,280 materials, exactly one each.

Why it matters: it is the property that distinguishes the new scheme from the old
one, and it is not something you can see by looking at the pictures (§6.5). It is
also the property that a subtle bug would break. The most likely programming
error here is a **mis-keyed registry** — for example forgetting `plate_index` in
the key while still passing it to the name — which would make many cells share a
material while the *counts* still looked plausible. Hence the three-clause check
in §4.

---

## 4. EVERY VERIFICATION CHECK

86 checks in `tests/check_depletion_zoning.py`, all passing. Below: what each
asserts and **what specific failure it would catch**. Where a check has no
nameable failure mode, that is stated.

### §1 — Zone constants and tiling (13 checks)

| # | Check | Failure it catches |
|---|---|---|
| 1 | x zones tile the meat width exactly | The x zone width and the x zone count have gone out of step, so the zones do not fill the meat — leaving a gap or an overlap at the +x edge |
| 2 | z zones tile the meat height exactly | Same in z. Historically the real hazard: zone bounds derived from the *element* extent (62 cm) rather than the *meat* extent (60 cm), which would mis-size every depletion volume by 3% |
| 3 | interior x plane count == N_X_ZONES − 1 | An off-by-one that creates duplicate planes coincident with the meat edges (lost-particle risk), or too few, which crashes |
| 4 | interior z plane count == N_AXIAL_ZONES − 1 | Same in z |
| 5 | x zone planes memoized | The lazy cache is broken and each element builds its own duplicate set — 27 redundant coincident planes per interior position |
| 6 | z zone planes memoized | Same in z |
| 7 | 2D zone volume == thickness × width × height | **WEAK — near-tautological.** It recomputes the constant the same way `geometry.py` does, from the same inputs, so it can only fail if someone replaces the derivation with a hardcoded literal. That *is* a real failure mode in this repo's history (the tally mesh bounds were hardcoded and went stale), so it earns its place as an anti-hardcoding tripwire — but it is not a physics check and should not be described as one |
| 8 | plate count == 23×23 + 5×17 == 614 | Same class: a tripwire on the plate-count constants, not a zoning check |
| 9 | even N_X_ZONES puts one interior plane on x = 0 | Interior planes generated with a half-cell offset. **Narrow** — it only bites for even counts, and its real value is documentary: it records that no other surface in the model sits at x = 0, so the centreline plane collides with nothing |
| 10–13 | `[N_X=2, N_Z=10]` benchmark literals: 3.15 cm, 6.0 cm, 0.9639 cm³, and 20 × 0.9639 == 19.278 | Hand-checkable numbers against arithmetic drift. #13 is the strongest of the four — it is a **conservation identity** linking the zone volume back to the whole-plate meat volume through an independent route, so it catches accumulated floating-point error, not just typos |

**Note on the guard.** #10–13 only run when the counts are 2 × 10. If the counts
change and the guard is not retargeted, these **silently stop running** — the
suite still reports success while asserting none of them. That trap was hit once
during this work (the guard was left at 8 × 20 after retargeting to 2 × 10) and
there is now a warning about it in the file docstring.

### §2 — Core map (2 checks)

| # | Check | Failure it catches |
|---|---|---|
| 14 | 23 standard + 5 control labels, all unique | A core-map edit that duplicates or loses an element position |
| 15 | flux traps at D4 and A6 | A core-map edit that moves the flux traps. **Inherited, not zoning-specific** — it lives here because this script builds a full core anyway |

### §3 — Zoning OFF (4 checks)

| # | Check | Failure it catches |
|---|---|---|
| 16 | exactly 1 depletable material — the base fuel | The zoning-off path has started creating zoned materials, i.e. the switch leaks |
| 17 | that material has no volume | Documents the trap in §3.2 — if this ever became non-None someone set a volume on the shared recipe |
| 18 | 614 meat cells, one per plate | The zoning-off path has started splitting cells |
| 19 | every meat cell filled with the base fuel | Same, from the material side |

### §4 — Zoning ON, materials (16 checks)

| # | Check | Failure it catches |
|---|---|---|
| 20 | exactly 12,280 = 614 × N_X × N_Z depletable materials | The registry key has collapsed (too few — sharing where there should be none) or duplicated (too many) |
| 21 | every one has a non-None volume | A code path that creates a material without passing volume — the silent-misnormalization trap |
| 22 | no two share a name | The name format has lost an index, so two distinct zones produce the same name — would make the material map ambiguous downstream |
| 23 | the zoned materials are the only depletable ones | A stray actinide-bearing material has crept into the exported set |
| 24 | registry and geometry agree on the material set | The registry holds materials that no cell uses, or vice versa |
| 25 | every (element, plate, x, z) quadruple present exactly once | The strongest name-side check: catches a missing plate, a missing zone, or an off-by-one in any of the four indices |
| 26 | no cell filled with base fuel when zoned | The split missed a meat cell — that cell would burn as part of a volume-less lump |
| 27 | base fuel absent from the geometry's material set | Same, from the other direction |
| 28–30 | exported set has 12,280 depletable, none volume-less, base fuel excluded | Verifies what `core.build_model()` actually hands to a solver, not just what the geometry contains |
| 31 | **sum of all material volumes == analytic total meat volume** | **The load-bearing volume check.** Catches a mis-derived zone volume — e.g. a per-element multiplier left in place after the per-plate change, which would inflate the total 23-fold. Nothing else ties the 12,280 declared volumes back to the geometry |
| 32 | `[N_X=2,N_Z=10]` total == 11836.692 cm³ | Hand-checkable absolute value |
| 33 | **U-235 mass conserved across the decomposition** | The same conservation expressed as *mass*, through OpenMC's own `get_mass()` — the quantity a depletion solve actually normalizes on. Catches an error in the density/volume coupling that a pure volume check could miss |
| 34 | all zoned materials keep the base composition | Someone re-specified composition inside `make_zoned_fuel` instead of inheriting it |
| 35 | all keep the base temperature (332.1 K) | Same for temperature — a silent 294 K default would change the cross sections |

### §5 — Zoning ON, cells and the 1:1 invariant (16 checks)

| # | Check | Failure it catches |
|---|---|---|
| 36 | 614 × 20 = 12,280 meat cells | Cell-side count error |
| 37 | **meat volume identical zoning on vs off** | The single best geometric check: the zone cells must occupy *exactly* the volume the one unzoned cell did. Catches a gap, an overlap, or a mis-sized zone — any of which changes the total |
| 38 | geometry meat volume == analytic 614-plate volume | Ties the measured geometry to first-principles dimensions |
| 39 | geometry meat volume == sum of declared material volumes | Ties the *cells* to the *materials* by volume — the two are computed by completely different routes |
| 40 | every material carries the single-plate zone volume | Catches a surviving per-element multiplier; would fail loudly if the std/ctrl distinction were reintroduced |
| 41 | **1:1 (a)** material count == cell count | Gross granularity error |
| 42 | **1:1 (b)** every cell references a distinct material | Sharing where there should be none — the direct statement of the invariant |
| 43 | **1:1 (c)** cell-referenced materials == `get_zoned_fuels()` exactly, as sets | **The one that actually binds.** (a) and (b) together can still pass a registry that hands two cells the same material *while* creating a compensating orphan that no cell uses — counts match, distinctness within the used set might still hold. Set equality in both directions catches orphans and unregistered materials |
| 44–45 | sample plate has N_X × N_Z cells; every (x,z) pair once | Per-plate structural completeness |
| 46–47 | x and z zone cells contiguous — no gap, no overlap | Adjacent zones must share an edge exactly. Catches a plane at the wrong coordinate |
| 48–49 | zone cells span exactly the meat bounds | The union must reach the meat edges, not fall short or overhang |
| 50 | the x tiling is identical at every z | Catches skew — an x boundary that drifts with height, which would mean the x planes were somehow rebuilt per z |
| 51 | every zone cell region carries exactly 6 half-spaces | Catches the redundant-constraint regression: intersecting the zone x bounds *on top of* the meat x bounds instead of substituting them. Costs ~30% of the geometry file across all cells, and is invisible in any physics result |

### §6 — Coordinate probes (5 checks)

| # | Check | Failure it catches |
|---|---|---|
| 52–53 | probe coordinates are the expected zone centres | Arithmetic drift in the probe itself |
| 54–55 | zone ordering over the full (x,z) grid, standard and control element | **Tests the model from the outside.** Everything above inspects the data structures; this fires a coordinate into the built geometry and asks "what material is here?" Catches inverted ordering (z0 at the top instead of the bottom), transposed x and z, or a lattice-position error |
| 56 | zone ordering in a **second** plate of the same element | **New with per-plate materials.** Under element sharing, plate 1 resolved to identical materials to plate 0; now it must resolve to a disjoint set. This tests the per-plate split *from coordinates*, independently of names — the name-set check (#25) could pass on a registry that is internally consistent but wired to the wrong cells |

### §7 — XML export (3 checks)

| # | Check | Failure it catches |
|---|---|---|
| 57–58 | geometry.xml and materials.xml parse; material count correct | The in-memory model is fine but does not survive serialization |
| 59 | materials.xml re-reads through OpenMC | The file is well-formed XML but not valid OpenMC input |

### §8 — Overlap and lost particles (16 checks)

Four blade positions (f = 0.0, 0.5, 0.99, 1.0) × zoning on/off × two checks.

| Check | Failure it catches |
|---|---|
| no overlaps | Two cells claiming the same point in space. Runs OpenMC's own `--geometry-debug` scan. This is the check that would catch a zone plane in the wrong place producing a genuinely overlapping region |
| no lost particles | A point in space belonging to *no* cell — a gap. The complementary failure to an overlap. Both are fatal to transport and neither is visible in the Python data structures |

f = 0.99 is included specifically because it puts the control blade in a
near-but-not-exactly-withdrawn position, where an off-by-epsilon in the blade
travel logic would show up.

### §9 — Backward compatibility (9 checks)

| Check | Failure it catches |
|---|---|
| (1, 10) builds, 6,140 cells, volume preserved, 6 half-spaces | The degenerate single-x-zone case must reproduce the old axial-only behaviour exactly. Catches a code path that assumes N_X_ZONES > 1 |
| (1, 1) builds, 614 cells, one per plate, volume preserved | Full degeneracy must reproduce the *unzoned* meat region. Catches an assumption that zoning always splits something |

### §10 — Negative tests (2 checks) — see §5 below

### §11 — On-disk verification (not assertions)

Greps that print the current state of the source to the test output — the
constants, the name format, the provenance tags. Not checks; a record so that a
saved test log documents what code produced it.

---

## 5. THE NEGATIVE TESTS

Every check above answers "does the model look right?" Negative tests answer a
different and equally important question: **"would we notice if it were
wrong?"** A check that never fails might be a check that cannot fail.

Both run in a **forked subprocess** — a separate copy of the program — so that
deliberately corrupted state cannot leak back into the real test run.

### 5.1 Off-by-one in the x zone count

**Defect injected.** The zone *count* is bumped from 2 to 3 while the derived
zone *width* keeps its old 3.15 cm value.

**Why representative.** This is the canonical "changed one thing, forgot the
other" error, and it is the specific failure the tiling assert was written for.

**What fired:**
```
FIRED AssertionError: x zones do not tile the active meat width
FIRED ValueError from make_zoned_fuel: x_index 2 outside [0, 2)
```
Two independent guards caught it. The second was **unanticipated** — the range
check in `make_zoned_fuel` rejects the desynchronised index at material creation,
before it can reach the volume sum. That is a genuine defence-in-depth result and
was discovered by running the test, not by designing it.

### 5.2 Off-by-one in the interior plane count

**Defect injected.** The interior plane list is built one plane short.

**Why representative.** N−1 vs N is the exact arithmetic the design turns on
(§2.3), and an off-by-one there is the most likely way to get duplicate or
missing surfaces.

**What fired:**
```
FIRED plane-count: 0 interior x planes, expected 1
FIRED IndexError from zone_x_bounds: list index out of range
```

### 5.3 The scale-invariance limitation — important, and a real limit

**The tiling asserts cannot falsify a zone count.** If you simply edit
`N_AXIAL_ZONES` from 10 to 7, the zone height recomputes to 60/7 and the assert
passes — correctly, because that configuration *is* internally consistent. The
assert catches a **mismatch between a count and its derived quantities**, never a
"wrong" count.

The counts themselves are **not falsifiable from inside the code.** Nothing in
this repository can tell you the reference model uses 2 × 10 rather than 3 × 11.
Only the reference model can. That is why the provenance tagging (§7) does real
work here: it is the only mechanism that records *how well we know* the numbers,
and no amount of testing substitutes for it.

This limitation is stated in the test output itself so it cannot be forgotten:

```
NOTE: the tiling asserts are scale-invariant by construction — they
      cannot falsify a zone COUNT, only a count/derivation mismatch.
```

---

## 6. DESIGN DECISIONS AND ALTERNATIVES REJECTED

### 6.1 Uniform `_x0` naming vs name identity at N_X_ZONES = 1

- **Chosen:** every material and cell carries the full `_x{j}_z{k}` suffix at all
  zone counts, including `N_X_ZONES = 1`, where the pre-2D scheme emitted just
  `_z{k}`.
- **Rejected:** suppressing `_x0` when there is only one x zone, to keep names
  byte-identical to the old 1D scheme.
- **Why.** The alternative introduces a special case in the naming logic — the
  kind of "if there's only one, do it differently" branch that later produces
  surprises. Backward compatibility was redefined as **geometric, volumetric and
  region-expression identity**, which is what actually matters, and the naming
  change was documented in the test docstring so a future reader does not read
  `_x0` in a diff as a regression.

### 6.2 Six half-spaces vs eight

- **Chosen:** the zone cell **substitutes** its x bounds for the meat's x bounds:
  `+x_lo & -x_hi & meat_y & +z_lo & -z_hi`.
- **Rejected:** intersecting the zone bounds *on top of* the full meat region,
  `meat_xy & +x_lo & -x_hi & +z_lo & -z_hi`, which is the more obvious way to
  write it.
- **Why.** The rejected form carries two logically redundant constraints (a zone
  is already inside the meat in x). Geometrically identical, but every cell
  becomes eight half-spaces instead of six. Across 12,280 cells that is roughly
  30% of the geometry file, and it makes the tracking work harder for no benefit.
  A check asserts the count stays at six (#51) because the regression is
  completely invisible in any physics result.

### 6.3 Lazy plane construction

- **Chosen:** interior zone planes are created on **first use**, not when the
  module loads.
- **Rejected:** creating them at module level alongside the other surfaces,
  which is simpler and more obvious.
- **Why.** OpenMC assigns automatic ID numbers to surfaces in creation order.
  Creating zone planes at import would consume IDs *even when zoning is off*,
  shifting the ID of every surface created afterwards and changing the exported
  file for the unzoned model. That would break the byte-identity gate (§6.4).

### 6.4 The byte-identity gate

- **Chosen:** after every change, export the zoning-**off** model and compare its
  SHA-256 hash against a baseline captured before the work started. Verify by
  hash diff; **do not** merely assert it in code.
- **Rejected:** trusting that "zoning is off by default so nothing changed."
- **Why.** The Phase 1 fresh-core cross-validation baseline must not move. An
  assert inside the code can only test what its author thought to test; a hash
  over the entire exported file tests *everything*, including surface ID ordering
  and numeric formatting. The rule was: if the hash moves, stop and report — do
  not adjust the baseline to match.
- **Result:** held across all three changes. `geometry.xml` `79a73a91…`
  (468,872 bytes), `materials.xml` `49cde120…` (2,066 bytes), 3,459 surfaces.

### 6.5 Colour keyed on (element, x, z) rather than per plate

- **Chosen:** in the diagnostic plots, colour encodes element hue, x zone, and
  z zone — 560 distinct colours over 12,280 materials, so all plates of an
  element share a colour within a zone.
- **Rejected:** encoding the plate index too.
- **Why.** 23 plates × 2 × 10 = 460 shades inside a single element hue is not
  distinguishable at any figure size, and adding it would destroy the gradient
  reading the plots exist for.
- **The cost of this choice, stated plainly:** the figures **cannot verify the
  per-plate split.** That verification lives entirely in the 1:1 structural check
  (§4, #41–43). This is an accepted reduction in what the pictures prove, and it
  is why the 1:1 check is non-negotiable.

### 6.6 Not building a per-plate colour mode

- **Chosen:** leave it unbuilt; document the limitation instead.
- **Rejected:** a `--color-mode plate`.
- **Why.** It would be speculative work to visualize something the structural
  check already proves, in a set of figures that were under a do-not-regenerate
  instruction at the time.

### 6.7 Not building a per-plate materials switch before Kyle answered

- **Chosen:** implement element-shared materials only, and wait.
- **Rejected:** a configurable flag with both granularities available.
- **Why.** A switch means one live branch and one untested branch, doubling the
  test matrix, to hedge a question that might not resolve binary — the reference
  could have differentiated some elements and not others. The judgement was that
  the change would be about a dozen lines whenever the answer came, so carrying
  an untested branch in the meantime was the worse trade.
- **Outcome:** the answer came the same day and the change was ~20 lines. The
  registry key already had the right shape to extend. **This decision was
  vindicated, but note the timing was lucky** — had the answer taken a month, the
  cost of waiting would have been the same, so the reasoning stands independently
  of the outcome.

### 6.8 Analytic volumes over stochastic — see §3.3

### 6.9 Asymmetric `zone_x_bounds` API — see §2.4

---

## 7. PROVENANCE HISTORY

This project tags every physical constant with where it came from. The tags in
play:

| Tag | Meaning |
|---|---|
| `[TECDOC]` | transcribed from IAEA-TECDOC-643 |
| `[MCNP]` | from the reference MCNP model |
| `[MCNP-VISUAL]` | **read off a picture** of the reference model, by eye |
| `[DERIVED]` | computed from other tagged constants |
| `[ASSUMED]` | our own choice, no external authority |

`[MCNP-VISUAL]` was a project-specific tag invented for exactly this scaffolding
and it was always understood to be the weakest class on the list.

### 7.1 The zone-count arc — four numbers, three of them ours

| Value | Tag | Basis | Status |
|---|---|---|---|
| **5 axial** | `[MCNP-VISUAL]` | counting colour bands in a zx slice image | SUPERSEDED 2026-08-12 |
| **8 × 20** | `[ASSUMED]` | our own resolution choice; never a claim about the reference | SUPERSEDED 2026-08-12 (same day) |
| **2 × 10** | `[MCNP — Kyle confirmed 2026-08-12]` | Kyle's statement that the reference subdivides each plate 2 × 10 | **LIVE** |
| **8 per half = 16 full-height** | `[TECDOC-643 App. A-2, Sec. 3.1 "Burnup Results", p. 31]` | REBUS-3 fuel-cycle model, half-core symmetry, 5-group ENDF/B-IV | a **different model**, not a target |

**The TECDOC number is the one most likely to be misread**, and there are two
separate traps in it:

1. It is **eight above the midplane under half-core symmetry** — i.e. sixteen
   over the full active height if mirrored, *not* eight over the full height.
   Comparing "8" against our "10" compares the wrong two numbers.
2. It describes **REBUS-3**, a diffusion-based fuel-cycle code on five-group
   ENDF/B-IV data with a half-core model. Different method, different library,
   different geometry from this continuous-energy full-core Monte Carlo model.
   That it disagrees with the confirmed 10 is unsurprising and is *not* a
   discrepancy to reconcile.

There is also a **coincidence hazard now retired**: while the resolution was
8 × 20, `N_X_ZONES` was 8 and collided numerically with TECDOC's eight-per-half.
A warning was written into `materials.py` at the time and deliberately kept
(reworded as historical) after the retarget, because the underlying hazard —
TECDOC's 8 being a different kind of number from any of ours — has not gone away.

### 7.2 The plate-sharing inference and how it was retired

Distinct from the count, and it outlived two count supersessions.

The original visual reading produced four claims, of which the third was:
*"all plates in an element share a zone material."* It was tagged
`[MCNP-VISUAL, inferred]` — inferred because it rested on colours *repeating*
across plates in the slice image, which is weaker evidence than a colour being
present.

When the 2D generalization landed, an explicit note was added:

> *"Note the third: plate-sharing is the ONE inference still implemented, and it
> is still unconfirmed. Superseding the zone COUNT does not retire it."*

When the 2 × 10 retarget landed, that note was extended: Kyle's answer had
superseded the count *twice over* and **still** had not retired the sharing
claim. The distinction was made explicit as a two-line table:

```
SUBDIVISION  per plate, 2 x 10   ->  12,280 cells  [MCNP — confirmed]
MATERIALS    shared per element  ->     560 mats   [MCNP-VISUAL, STILL LIVE]
```

A separate answer from Kyle — that materials should be per plate — retired it,
exactly as the note had anticipated. The verbatim sentence is preserved in
`materials.py` with a dated RETIRED marker beneath it, so the record shows both
what was believed and what ended it.

**Current state: no `[MCNP-VISUAL]` claim remains live anywhere in the zoning
scheme.** Every surviving occurrence of the string sits inside a dated
SUPERSEDED/RETIRED record or is a negative statement about what the 8 × 20
resolution did *not* carry. This was checked by enumeration, not assumed.

`docs/PHASE1_AUDIT.md` §C5 and `docs/TESTAMENT_III` were amended accordingly in
commit `e000b30`, with records struck through rather than deleted.

---

## 8. COSTS

All measured 2026-08-12 on this machine. **No eigenvalue or depletion run has
ever been performed on this model** — every number below is model construction
or the geometry-debug scan.

| Config | cells | materials | build | geometry.xml | materials.xml | peak RSS | scan f=0.5 |
|---|---|---|---|---|---|---|---|
| unzoned | 614 | 1 | 0.14 s | 0.47 MB | 0.002 MB | 155 MB | 3.4 s |
| **2 × 10 per-plate (live)** | **12,280** | **12,280** | **0.68 s** | **1.86 MB** | **4.92 MB** | **183 MB** | **8.4 s** |
| 2 × 10 element-shared | 12,280 | 560 | 0.21 s | 1.85 MB | 0.22 MB | 168 MB | 6.4 s |
| 8 × 20 element-shared | 98,240 | 4,480 | 1.55 s | 12.16 MB | 1.79 MB | 263 MB | 47.7 s |

### What drives each

- **geometry.xml** tracks the **cell** count. Going element-shared → per-plate at
  the same resolution moved it 1.85 → 1.86 MB: the cells did not change, only the
  material ID each one references.
- **materials.xml** tracks the **material** count, and grew **22×** (0.22 →
  4.92 MB) for exactly that change. Each material is a full nuclide list.
- **build time** is dominated by object construction — 12,280 `clone()` calls.
- **the scan** tracks cells, not materials: 6.4 → 8.4 s for a 22× material
  increase is mostly noise.

### How OpenMC actually finds cells — corrected 2026-08-12

An earlier draft of this dossier said OpenMC searches cells within a universe
*linearly*, and inferred from that a per-boundary-crossing cost proportional to
the per-universe cell count. **That was wrong as stated**, and the correction
changes what the scan timings below mean. Verified against OpenMC's Theory and
Methodology documentation:

- **Finding a cell given a point** (Theory & Methodology §2.3) **is** a linear
  loop over the cells of a universe, recursing into any universe that fills a
  cell. That part of the original claim was right.
- **Handling surface crossings** (§2.6) is the common case during transport, and
  it does **not** do that. When a particle crosses a surface, OpenMC searches
  only that surface's **neighbor list** — the small set of cells known to lie on
  the other side. The full linear search is the **fallback** used only when the
  neighbor-list search misses.
- **Building neighbor lists** (§2.7): as of OpenMC 0.11 these are **cell-based**
  and are built *dynamically during transport*. OpenMC moved to cell-based lists
  from surface-based ones precisely because surface-based lists degrade badly
  when one surface bounds many cells — which is exactly the situation zoning
  creates, since each shared interior zone plane bounds two cells in every one
  of the 614 plates.
- Reference: Harper, Romano, Forget, Smith, *Nuclear Science and Engineering*,
  doi [10.1080/00295639.2020.1719765](https://doi.org/10.1080/00295639.2020.1719765).

**So the per-universe cell count is not paid in full on every boundary
crossing.** It is paid on the fallback path, and neighbor lists exist to keep the
model off that path.

### What the geometry_debug scan does and does not measure

**Does:** run OpenMC's particle tracker over the built geometry, checking for
overlapping cells and for points belonging to no cell.

**Critically — it exercises the UNMITIGATED `find_cell` path.** Overlap checking
works by locating a point from scratch and confirming exactly one cell claims it,
which is the linear §2.3 search — precisely the path that neighbor lists bypass
during real transport. That makes the scan a **worst case** and an **upper bound
on the geometry-search term**, not a transport predictor. The 8.4 s at 2 × 10
should be read as "the geometry search costs no more than this", not as "transport
will cost this much more."

**We do not have a transport penalty number, and none is estimated here.**
Producing one requires an actual eigenvalue run, which has not been done.

**Does NOT measure:**

1. **The depletion solve.** A depletion calculation runs a Bateman/CRAM matrix
   solve **per depletable material, per timestep**. Per-plate materials
   multiplied that work by **22×** while leaving the cell count — and therefore
   the scan — untouched. A flat scan time does not mean the change was free; it
   means the change was free *for transport*.
2. **Eigenvalue runtime.** The scan uses 200 particles over 2 batches. A
   production run is 50,000 × 200.
3. **Convergence or accuracy.** Nothing here is a physics result.

### Do not extrapolate the scan linearly

There is a large fixed cost — roughly 3.2 s of startup at any size — so the cheap
end looks flatter than it is. Twenty times the cells from unzoned to 2 × 10 cost
only 1.9× the time. Fit a straight line through those two points and it predicts
~28 s at 8 × 20; the measured value is **47.7 s**, 1.7× worse. Cost accelerates
once cells dominate the fixed overhead.

### The formula that now matters most

Cells and materials share **one** formula:

```
614 plates × N_X_ZONES × N_AXIAL_ZONES
```

Raising the resolution therefore costs on **both** axes simultaneously — more
cells for transport *and* more materials for the depletion solve. Under the old
element-shared scheme, materials were `28 × N_X × N_Z` and grew 22× more slowly.
Anyone proposing a resolution study needs to see this before proposing it.

**Resolved 2026-08-12** — the flagged uncertainty about the cell-search
mechanism has been checked against OpenMC's Theory and Methodology docs and the
corrected picture is above. The measured timings are unchanged; what changed is
what they mean. Two things follow that a resolution study needs to respect:

- The scan is an **upper bound on the geometry-search term**, because it runs
  the unmitigated `find_cell` path. Real transport benefits from neighbor lists.
- **No transport penalty has been measured, and none should be quoted.** The
  temptation is to convert the scan ratio into "transport will be N× slower".
  That inference does not hold and is not made here.

---

## 9. WHAT IS NOT BUILT

The zoning is **structural scaffolding only.** No depletion is configured or
executed. `build_depletion_operator()` and `run_depletion()` both raise
`NotImplementedError` on their first statement, by design.

Five blockers, plainly:

1. **No depletion chain file exists anywhere on this machine.** Not in the repo,
   not in `~/nuclear-data`, not in `~/projects/openmc-adder`; no
   `OPENMC_CHAIN_FILE` set. A chain file describes what decays into what and with
   what half-life — depletion is impossible without one. The intent is an
   ENDF/B-VIII.0 chain matched to the VIII.0 cross sections already in use.
   **This is the single largest gap.**

2. **No `openmc.deplete` code path exists.** Not one line is live; the
   implementation sits commented out beneath the two `NotImplementedError`
   raises.

3. **No timestep schedule.** `depletion_timesteps` is an empty list. No cycle
   length, step count or units have been decided.

4. **No power normalization basis.** `power_w = 10.0e6` is recorded but never
   read, and there is no decision on whether that is `power` or `power_density`,
   or how it divides across the zones.

5. **`substeps` cannot be applied on this build.** ADDER uses 4. OpenMC's
   `substeps` parameter does not exist in the installed **0.15.3** — verified:
   the string appears in no file in the installed package. Upstream it was added
   in **0.16.0 for `CECMIntegrator`**, the integrator we use. (It landed earlier,
   in 0.15.4, for `LEQIIntegrator`/`SILEQIIntegrator` — do not copy a bare
   version number onto the wrong class.) Matching ADDER requires an upgrade.

**Settled but unused** (Kyle, 2026-08-12): integrator `cecm` (CE/CM
predictor-corrector), solver `cram48` (48th-order IPF CRAM — which is *also*
OpenMC's default, so this is a match rather than an override, recorded
explicitly so the agreement is on record).

Also absent: any per-zone tally. `tallies.py` has only a global flux mesh, so
nothing independently cross-checks what a depletion operator would compute.
And nothing reads `depletion_results.h5`.

---

## 10. KNOWN LIMITATIONS AND RESIDUAL RISK

1. **Zone uniformity was inferred, not confirmed.** Kyle stated "2 × 10 on each
   fuel plate". A uniform division is the natural reading and is what is
   implemented, but non-uniform spacing was never explicitly raised or excluded
   in the exchange. If the reference uses finer zones near the ends — a common
   choice, since axial flux gradients are steepest there — our uniform zones
   would compare per-zone burnup against differently-sized volumes.

2. **The `[MCNP]` tags rest on a relayed statement, not transcribed cards.**
   Both 2 × 10 and per-plate materials come from what Kyle said, not from reading
   the MCNP input deck. That is the same provenance class as several existing
   `[MCNP]` tags in this project, and it carries the same exposure: **it rests on
   a person, not a document.** A surface-card diff could disagree later without
   either side having done anything wrong.

3. **ADDER substep equivalence is unconfirmed.** OpenMC's `substeps` subdivides
   the Bateman/CRAM solve interval into identical sub-intervals, reusing LU
   factorizations, with **no additional transport**. Whether ADDER's "substep"
   means the same operation or re-solves transport is unknown. Setting 4 on both
   sides could be a false match that looks like agreement while comparing
   different schemes. Tagged `[ASSUMED-EQUIVALENT — needs Kyle]`.

4. **No TECDOC extract exists in the repository.** The `[TECDOC-643 App. A-2,
   Sec. 3.1, p. 31]` citation was written on Thomas's explicit confirmation and
   **cannot be verified from the working tree.** In a project where every tag is
   supposed to trace to a document, this is the one citation that currently
   cannot. Committing an extract would close it.

5. **The plots cannot verify the per-plate split** (§6.5). Plate index is not
   encoded in the colour, by design. Per-plate verification lives solely in the
   1:1 structural check.

6. **The plot code was silently broken from B4 until 2026-08-12.** Its lattice
   origin still used the pre-B4 8×9 lattice extent, putting every slice one full
   pitch cell out of position. The identical fix had been applied to
   `check_depletion_zoning.py` when B4 landed but was missed here. It was found
   only because the figures were finally regenerated — and it was caught by the
   script's own slice probe, which refused to plot. **Worth noting as a process
   finding: a diagnostic that is never run is not a diagnostic.**

7. **The zone plots degrade at high axial counts — found by stress test,
   now guarded.** The z lightness ramp becomes imperceptible somewhere between
   20 and 40 axial zones. The `element`-mode assertion that used to sit here
   tested only whether colours were distinct at **8-bit precision**, which
   passed at 8 × 40 while the figure was unreadable: an assertion guarding
   mathematical distinctness but not perceptual distinguishability was not
   guarding what mattered.

   **Closed 2026-08-12** by `check_ramp_legibility()`, which checks the size of
   the step between adjacent zones instead. It fires at
   `N_AXIAL_ZONES >= 19`, and in mode `element` at `N_X_ZONES >= 15`. At the
   live 2 × 10 the z step is 0.0589, **1.96× the threshold**.

   **The threshold is a judgement, not a derivation.** `MIN_PERCEPTUAL_RAMP_STEP
   = 0.03` (~8 of 255) comes from inspecting the stress renders at
   N_AXIAL_ZONES = 5, 10, 20 and 40 — unmistakable at 5 and 10, borderline at
   20, gone at 40. It is **not** taken from CIEDE2000 or any colour-difference
   standard and must not be cited as one. It deliberately fires at 20, the case
   judged "borderline but usable", on the principle that borderline is what a
   guard should catch.

   Residual: the guard makes an illegible figure impossible to produce, but it
   does not make a legible one at high resolution. If `N_AXIAL_ZONES` ever needs
   to exceed ~18, the fix is a **cycling** lightness ramp rather than a wider
   one. That is recorded in the `plot_core.py` docstring and is not built.

8. **A figure-size guard now exists** (`MAX_FIGURE_WIDTH_IN = 25.0`) but nothing
   checks the *content* of a figure beyond the ramp step. A plot can still be
   correct in every measurable respect and useless to look at.

9. **The plot code carried a second stale-dimension bug, found only by looking
   at the output.** `plot_element_hue_map()` set axis limits and ticks for
   1-based cell centres while drawing tiles on 0-based ones, so every label sat
   one cell up and left of the tile it named, column A and row 7 fell outside
   the visible area, and the A6 flux trap floated outside the grid. Same origin
   as the lattice-origin bug: hardcoded values from before B4 re-indexed
   `core_map_label` to 0-based positions. Fixed 2026-08-12 by deriving from
   `CORE_MAP`.

   **Both plot bugs were found by inspection, not by any test**, and both had
   been present for weeks. The figures have no automated correctness check at
   all — the slice probe verifies that slices land in fuel, and the new guards
   verify legibility and size, but nothing verifies that what is drawn
   corresponds to the model. Treat any figure from this module as unverified
   until looked at.

10. **No physics has been validated.** Everything verified is structural: counts,
    volumes, mass conservation, geometry integrity. No eigenvalue, no depletion,
    no comparison against the reference. The zoning being *correctly built* says
    nothing about whether it is *the right zoning*.

---

## APPENDIX — key file map

| File | Role |
|---|---|
| `model/materials.py` | Owns `N_X_ZONES` / `N_AXIAL_ZONES`, `make_zoned_fuel()`, the registry, and the full provenance record. Holds **no** geometry dimensions |
| `model/geometry.py` | Zone plane construction, `zone_x_bounds` / `zone_z_bounds`, the two element builders, all derived dimensions |
| `model/core.py` | `CoreConfig.depletion_zoning` switch, model assembly, dormant ADDER settings, the two unimplemented depletion entry points |
| `tests/check_depletion_zoning.py` | All 86 checks, the negative tests, the degenerate-count builds |
| `tests/plot_core.py` | `--depletion-zones` diagnostic figures |
| `docs/PHASE1_AUDIT.md` | §C5 carries the amended provenance record |
