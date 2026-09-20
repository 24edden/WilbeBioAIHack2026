# Saved NVIDIA structure images

These Mol* renders visualize the actual recorded Boltz-2 CIF predictions. The UI automatically displays an image only when the selected run contains an artifact whose SHA-256 matches `source_sha256` in `catalog.json`. The PNG SHA-256 is verified before display. No inference or network call is made.

The exon-2-deleted render selects the `exon2_deleted` structure object in the original two-object Mol* scene. It is tied to the deleted CIF hash, not the primary wild-type object. Files retain labels describing prediction scope. Other studies do not inherit these images.

To add another saved render, append its exact source artifact hash, image hash and filename to the catalog. Never map images by a generic filename or by study title alone.
