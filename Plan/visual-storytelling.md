# Visual storytelling for TRACE

19 September 2026. Brainstorming and implementation proposal only. No application,
dependency or deployment changes are made by this document. Time estimates are
rough engineer-hours for a bounded implementation, not measured commitments.

**Recommendation:** let a finding open a scientific scene that the researcher can
inspect. Start with a treatment/lab timeline, a contextual image or structure, and
two competing mechanisms. A click should expose evidence, change the view, or
record a decision. Keep one main scene on screen at a time.

This follows [the existing feature direction](feature-direction.md): make the
question, assumptions and missing evidence visible. It also preserves the current
progression through evidence, question/agents, investigation and results. A
persistent question panel is being developed separately; scenes should respond
to the selected run and finding beneath it, not add another full-page dashboard.

## What the current data can support

The bundled case contains a VCF with KRAS p.Gly12Asp and DPYD
c.1905+1G>A, dated laboratory values, and treatment notes. For example, its CEA
rows are 4.1, 18.6 and 47.3 ng/mL on 12 January, 2 March and 20 April 2025. The
notes record treatment starting 20 January and a restaging assessment on 5 March.
These are observations in the bundled demo files, not validated clinical truth.
There is **no infection finding or organism identification in this case**.

Backend `Finding` already has `finding_id`, provenance and a free-form `detail`
object. The current frontend's normalized `Finding` drops the ID and detail.
Clinical tool events mostly expose counts or trend directions, not all plotted
measurements. A faithful interactive timeline therefore needs a small normalized
data artifact; it cannot be reverse-engineered from prose or event timestamps.
The event timestamp is when an agent acted, not when a biological event happened.

## Ranked concepts

Impact/value use a relative 1–5 design score. They are prioritization judgments,
not predictions of judging marks. Estimates include a basic usable interaction
but exclude domain review and obtaining new datasets.

| Rank | Concept and researcher action | Visual impact | Scientific value | Time | Data readiness and boundary |
|---|---|---:|---:|---|---|
| 1 | **Evidence timeline.** Treatment markers sit above separate analyte plots. Select a point to open its exact CSV row and relevant note; brush a period to focus the investigation. | 4 | 5 | 3–5 h | Current sample has dates, units and reference ranges. Needs full-series artifact and source mapping. Use points and gaps, never an invented smooth disease trajectory. |
| 2 | **The biological subject comes into focus.** A selected finding opens a large contextual organism image, molecular diagram or tissue schematic beside its evidence. Controls: inspect source, pin, replace focus, hide. | 5 | 4 | 2–4 h for curated images | A small reviewed asset registry is feasible. Infection imagery needs a new synthetic fixture or actual supported organism data. The displayed picture is reference material unless it was uploaded as a specimen image. |
| 3 | **Compare possible mechanisms.** Two short pathways share observed inputs but diverge at uncertain links. Select a link to see support, conflicts and assumptions; mark it unresolved and preserve the revision. | 5 | 5 | 5–8 h; 2–3 h read-only subset | Requires authored structured mechanism records and evidence typing. Existing findings can be references. A source-removal action changes evidential support, not a biological variable. |
| 4 | **Follow the disagreement.** Selecting a finding lights up the specialist, source and critic exchange that produced it. Two agents reusing the same source converge on one source node. | 4 | 5 | 2–4 h | Messages and provenance exist. Stable finding IDs and canonical source IDs must reach the UI. Show a sent message only when that event exists; decorative pulses must not imply work happened. |
| 5 | **From sequence to structure.** Select the KRAS variant, then locate its mapped residue in a rotatable reference structure. Switch cartoon/surface, reset camera, open structure metadata. | 5 | 4 | 4–7 h for one reviewed structure | A relevant PDB entry exists. Sequence/chain/residue mapping needs verification. Use a static preview until the viewer is ready. Structure proximity alone does not establish the reason for treatment failure. |
| 6 | **Compare investigations.** A compact case-by-model matrix reveals a trace when selected: grounded output, abstention, timeout and measured latency. Scientist chooses comparable runs. | 4 | 4 | 2–4 h after evaluation artifacts exist | Coordinate with the evaluation workstream. Requires frozen inputs and recorded settings. Show missing usage/metrics as unavailable; no synthetic performance leaderboard. |
| 7 | **What would distinguish these explanations?** A two-column prediction card shows the same proposed measurement under mechanisms A and B. Researcher chooses a measurement and sees what would challenge each. | 4 | 5 | 3–5 h | Needs authored predictions with contexts/controls. Can start as a qualitative proposed-test card. No probability animation or predicted assay curve without an actual model and parameters. |

The highest-value small release is **1 + 2**, with **3** as the differentiating
feature if its state and evidence mapping can work. Concept 5 is a strong visual
upgrade to concept 2, not a reason to postpone the basic reference-card version.

## The bacteria idea, made concrete

Use an alternate synthetic infection scenario if the team wants this visual in
the demo. The scene needs explicit source status:

| Investigation state | Scene and copy |
|---|---|
| Prompt asks about an infection, but evidence has not been inspected | A restrained abstract specimen icon: “Infection is the research question. Organism not established.” No species photo is selected from the question alone. |
| Source describes possible bacterial infection, organism unspecified | A clearly labelled generic bacterial illustration: “Illustration. Organism not identified in the supplied evidence.” A blank specimen frame also works. |
| Uploaded record explicitly identifies *E. coli* | A reviewed *E. coli* reference micrograph: “Reference micrograph, not this sample.” Alongside it show the source's exact wording, date and specimen context. |
| Sources disagree or identification is ambiguous | Keep both source statements visible and label identification unresolved. Do not switch to a confident species hero image. |
| Researcher uploads microscopy | Display the actual uploaded image with file provenance. Do not replace it with a stock/generated image or infer organism identity from an unimplemented vision model. |

A concrete candidate is **CDC PHIL 10042**, a digitally colorized electron
micrograph of a dividing *E. coli*, credited to CDC/Evangeline Sowers and Janice
Haney Carr, with photo credit Janice Haney Carr. Its record marks it public domain.
The species image is educational context, not evidence from the investigation.
[Image record](https://wwwn.cdc.gov/phil/Details.aspx?pid=10042).

Keep the image in a fixed scene frame, with a short caption and source button.
Reveal it when the supporting finding arrives, but preserve a scientist's pinned
view until they choose another. A gentle fade is enough. Avoid animated bacterial
multiplication, a spreading red body map, or a realistic generated microscope
image: those would suggest measurements or progression the system does not have.

## Three recommended scenes for the five-minute presentation

Use the existing sample for the main narrative. If infection is selected as the
team's final domain, replace the whole case with a coherent infection fixture;
do not abruptly change patients halfway through the presentation.

### Scene 1: “Show me the turning point” (0:35–1:35)

After a brief problem statement, upload/select the bundled case, type the research
question and start. Clinical evidence reveals the timeline. Select the 2 March CEA
point to expose value, units, source row and nearby treatment notes. Switch analyte
to neutrophils without moving the time axis. This makes the available evidence
legible in a few seconds and demonstrates real control.

Plot analytes on separate labelled scales. Only use reference ranges provided
with the records, and label them as those supplied ranges. Missing dates stay in
an “Undated evidence” list. Do not infer the exact date of every cycle from the
notes' summary, connect incompatible units, or equate sequence with causation.

### Scene 2: “Zoom into the finding” (1:35–2:35)

Select the KRAS p.Gly12Asp finding. The frame changes from timeline to a reference
structure with the VCF line attached. Begin with a cached image; if the optional
viewer is working, select “Locate mapped residue” and rotate once.

**PDB 5US4** is a concrete candidate: a human KRAS G12D structure bound to GDP,
determined by X-ray diffraction at 1.83 Å. Label it “Experimental reference
structure; not a structure measured from this patient.” Pin the entry version,
assembly and verified residue mapping before adding a highlighted site.
[PDB entry](https://www.rcsb.org/structure/5US4).

A useful entity-resolution trap: this entry lists *Homo sapiens* as the organism
and *E. coli* as the expression system. A keyword-based image selector would
incorrectly show bacteria for this patient's protein finding. Select assets from
typed entities and their role, not arbitrary text matches. The UI must not infer
an infection from the expression host.

### Scene 3: “Challenge the explanation” (2:35–4:20)

Open two **proposed** explanations, such as a target-pathway explanation and
treatment-exposure limitation. Present them as hypotheses under review, with
sources and unresolved links, not established patient mechanisms. Select the
weakest link to open its evidence. Mark it unresolved and show a saved revision.
The missing-evidence panel then exposes a qualitative discriminating measurement.

If source exclusion is implemented, label the interaction “Review without this
source” and show which links lose support. Do not animate the patient improving
or the molecule reverting: removing evidence is not an intervention. This
distinction follows the difference between observation and intervention in
[Pearl's causal-calculus paper](https://proceedings.mlr.press/r0/pearl95a.html).

Finish the remaining 40 seconds with one abstention case, actual evaluation
results if available, and the downloadable run record. Keep a labelled recorded
fallback for every scene. A recorded visual remains responsive to inspection;
do not call its saved model outputs live inference.

## How this serves the judging rubric

The event gives equal weight to scientific impact, NVIDIA/OpenAI use, execution,
originality and presentation/reproducibility. A scene earns scientific value by
making evidence and alternatives inspectable. An editable uncertain link is more
distinctive than a generic spinning molecule. A versioned, repeatable scene earns
execution/reproducibility value; it should load even if the network is lost.

Visual polish does not establish central vendor use. If a live Rosalind or
BioNeMo result is available, the scene should expose the real input/output and
provider identifier associated with that finding. A WebGL structure viewer is
not a BioNeMo prediction. Hosting on Brev CPU is not GPU scientific inference.
Use the labels “uploaded measurement”, “external reference”, “model output”,
“illustration” and “proposed mechanism” consistently.

## A modular scene boundary

Do not let an LLM emit executable HTML, image URLs, arbitrary chart code or a new
page layout. Add a small versioned `VisualArtifact` vocabulary. A dataset/backend
adapter produces normalized artifacts; a renderer registry selects a trusted
view by `kind`. Changing the dataset should require a new adapter and manifest,
not edits across all the page components.

Suggested seams, as future files rather than current implementation:

| Layer | Responsibility |
|---|---|
| Dataset adapter | Normalize measurements, named entities and source references. Preserve identity, units, dates and evidence status. |
| Artifact builder | Construct `lab_series`, `reference_image`, `structure`, `mechanism_comparison` or `run_comparison` objects. Validate links to this run. |
| Asset registry | Map reviewed entity IDs to local assets with source URL, creator, licence, version and checksum. Unknown mappings yield a neutral placeholder. |
| Renderer registry | Render the supported `kind`. Unknown schema/kind gives a readable fallback with its source information. No backend-specific parsing in views. |
| Scene state | Store `run_id`, selected finding/artifact, pinned state and view mode. Edits to mechanisms create revisions rather than mutate a completed report. |

Minimal example, **proposed schema, not an existing API**:

```json
{
  "schema_version": 1,
  "artifact_id": "ref-kras-g12d-v1",
  "run_id": "example-run",
  "kind": "structure",
  "title": "KRAS G12D reference structure",
  "finding_ids": ["finding-genomics-1"],
  "origin": "external_reference",
  "data": {
    "asset_id": "pdb-5us4-v1.3",
    "entity": {"type": "protein", "id": "UniProt:P01116", "variant": "p.Gly12Asp"},
    "residue_mapping_status": "unverified"
  },
  "source_refs": [
    {"source_id": "patient-0-vcf", "locator": "line 7"},
    {"source_id": "pdb-5us4-v1.3", "url": "https://www.rcsb.org/structure/5US4"}
  ],
  "caption": "Experimental reference structure. Not measured from this patient."
}
```

In a real artifact, source IDs must resolve through that run's source manifest.
The sample above deliberately leaves residue mapping unverified, so the renderer
must not highlight a residue yet. A `lab_series` object's rows additionally need
`date`, `value`, `unit`, optional `ref_low`/`ref_high`, and a source/row reference.
A mechanism object needs typed edges with supporting/conflicting finding IDs,
evidence category and user revision metadata, as described in the feature plan.

For a first release, expose artifacts through an **additive, versioned report
field or separate run-artifact endpoint**, coordinated with the backend owner.
Preserve current events. A later optional event could be:

```json
{
  "type": "artifact_ready",
  "run_id": "example-run",
  "ts": 1789820000000,
  "payload": {"artifact_id": "ref-kras-g12d-v1", "schema_version": 1}
}
```

This event is a proposal and requires coordinated backend/frontend support.
An old UI should still show existing findings. Reject cross-run/stale artifact
references. Deduplicate ready events by artifact ID/version. Display the newest
available evidence indicator without stealing focus from a pinned scene.

## Rendering, assets and precomputation

Streamlit already supports Plotly point/box selections through `on_select` and
returns selection data on rerun. That is a practical route from a timeline point
to a source panel. Selection, not hover, should drive substantive actions.
Plotly is not currently declared in `frontend/requirements.txt`; implementing it
would be a separate dependency change. [Streamlit documentation](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart).

Mol* supports structure representations, component selections and structure
loading. A dedicated embedded component can be investigated for the optional
structure scene; compatibility with this Streamlit deployment has not been
tested. Ship the sourced static preview first, with an open-reference action and
text fallback. [Mol* display documentation](https://molstar.org/viewer-docs/managing-the-display/).

| Asset | Proposed use and rights record |
|---|---|
| Uploaded CSV/notes/VCF | Render measurements and provenance directly. Bundle only the redistributable demo data. |
| CDC PHIL reference image | Select a record individually, record its rights and contributor credit, preserve the reference/sample distinction. PHIL includes both public-domain and restricted assets; it is not a blanket licence. [CDC FAQ](https://wwwn.cdc.gov/PHIL/FAQ.aspx). |
| PDB coordinates and structure-summary image | PDB archive/API data and RCSB Structure Summary molecular images have the stated CC0 terms. Keep the structure and depositor citation. Molecule of the Month art instead uses CC BY 4.0. [RCSB policy](https://www.rcsb.org/pages/usage-policy). |
| Reactome reference pathway | Optional source for a future curated pathway. Reactome data are CC0; illustrations/icons are CC BY 4.0 with attribution and modification disclosure. Do not copy an entire viewer without checking its software dependencies. [Reactome licence](https://reactome.org/license). |
| Team-authored SVG illustration | Best generic fallback: scalable, consistent, easy to recolor and explicitly illustrative. No generated bitmap is needed for the first release. |
| Generated artwork | Optional decorative concept art only, pre-generated and labelled illustration. Never a fake micrograph, patient scan, assay output or mechanistic proof. No image-generation call is proposed for the live demo path. |

Before rehearsal, prepare the small asset registry, image thumbnails, chosen
structure file and any expensive verified model results. Save content hashes,
source version, provenance and generation settings as applicable. Local chart
rendering and scene selection stay interactive. Cached scientific computation
must retain its own “precomputed” label; switching the view is fresh UI work,
not fresh scientific inference.

Use deliberate typography, clean boundaries and a single selected accent in the
existing dark theme. Avoid decorative cursor trails, animated background biology,
random graphs, unlabeled percentage rings and sensational infection imagery.
Motion should stop after conveying the new event. Respect reduced-motion settings,
provide a static/data-table equivalent, and keep essential source information
available by keyboard and touch rather than hover alone.

## Small implementation plan and cut line

1. **One hour:** agree artifact/source IDs with the dataset teammate, make a
   sample-only reviewed manifest and preserve finding IDs in frontend state.
   Record the scene boundary in `INTEGRATION.md` when implementing it.
2. **Two to four hours:** add the scene frame and two renderers: timeline and
   reference image. Pin/hide/source actions work. Add the two sample artifacts;
   the same case, source hashes and asset versions work in replay and demo modes.
3. **One to two hours:** rehearse the complete click path on the hosted CPU
   deployment. Check missing assets, unknown entities, stale run IDs, missing
   dates, conflicting units, narrow screens and reduced motion. These are the
   acceptance checks, not just a screenshot review.
4. **Only if time remains:** add two editable proposed mechanism cards with
   persisted revision/source links. Add 3D after the static scene and basic
   interaction are reliable. Treat these as separate bounded workstreams.

**Cut line:** if entity/source mapping or viewer performance is uncertain, keep
the timeline and sourced static visual. The visible success condition is that a
judge can click a changing scene, inspect the underlying evidence, understand
what is assumed, and reproduce that same view from the saved run. A polished
picture without that connection should not displace the working investigation.
