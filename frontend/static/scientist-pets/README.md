# Right-facing scientist pets

All nine pets are permanently mirrored to face right toward speech bubbles.
Use these saved files directly. Do not mirror them again in CSS, JavaScript, or the build.

Each pet has an animated WebP, animated GIF, and still PNG at 288 × 288.
All seven frames, their exact visible pixels and alpha, timings (2.31-second loop),
and loop metadata were verified after mirroring. See mirror-verification.json.

The one-time transformation used the original scientist-pets pack as read-only input.
The original artwork in the creating-pets task was not overwritten.
manifest.json marks horizontalMirrorApplied=true. The normal build only copies these files.

The included scientist-pets.mjs helper resolves unknown roles to generic-scientist
and supports reducedMotion to choose the still PNG. Copy this entire folder
into any frontend public directory for reuse. No image generation, image processing,
API key, or backend is needed at runtime.
