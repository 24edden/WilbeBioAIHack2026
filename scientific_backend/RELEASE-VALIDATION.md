# Public packaging validation — 20 September 2026

The original scientific suite passed **776 tests** in the isolated release
checkout with a fresh runtime and the existing authorized plugin installation
used only for read-only hash validation. Provider transports were mocked; no
scientific run, paid probe, sequence search, NVIDIA prediction or production write
was submitted. The existing scientific service and its saved histories were not
modified.

All 31 `app/*.py` files and every existing scientific instruction file retain
their imported bytes; `SOURCE-IMPORT.json` records the imported SHA-256 values.
The public profile source lock separately pins the seven runtime/instruction
inputs from which those nine-agent profiles were generated.

Packaging adds only setup, source hydration, a public archive allowlist,
documentation, and checks. Six external scientific input/reference files are
excluded from Git/archive even when privately hydrated. The proprietary source
client is never part of the public source tree.

The final network-blocking safe runner passed **797 tests and 25 subtests**,
including the unchanged 776-test scientific suite, eight packaging/integrity
checks and all public-profile source-lock/regeneration checks. The case builder
verified all three derived packs against their original source pins. The public
source archive was generated after private input hydration and still excluded
every external input. One installed-library deprecation warning concerns the
Starlette/AnyIO blocking-portal alias; it did not affect results.

The explicitly limited public-only runner also passed **738 tests and 25
subtests**, with one registry-installation test deselected and the three
synthesis-checkpoint suites omitted as documented in SETUP.md. The complete
797-test release gate above used the authorized installed plugin. All 58 installed
dependencies matched `requirements.lock.txt` exactly.

The BCMA compact variant input was independently reproduced with a standard-
library column projection of the original pinned public GEO MAF file. Read-only
validation on the original private source host confirmed 585 rows, 61,749 bytes
and the original output SHA-256
`72007e8b5bfa71bff7e75edf36ab3c4c866ca1274058b3b16eb15e66a70881d7`.
The release installer contains the recipe and public URL/source pin. This check
made no external data download and left the original source untouched. The public
download route was not exercised in this environment; fresh downloads must still
match every original byte/hash before installation.

Mocked transport validation does not establish vendor entitlement or scientific
validity. Live read-only integration checks belong in the overall release handoff.
