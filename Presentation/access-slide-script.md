# Audience access and QR slide

Drafted 19 September 2026. Use alongside [demo-script.md](demo-script.md).
Deployment recommendation and exact prerequisites:
[public-demo-hosting.md](../Plan/public-demo-hosting.md).

## Current truth

The Brev application exists behind NVIDIA authentication. Its current access policy
does not admit the whole audience. No free branded audience site or public QR was
created by the hosting review. Do not paste an example hostname into the final
deck or describe the current Secure Link as anonymous access.

## Slide after the public viewer has been verified

**Title:** Explore TRACE

**Main visual:** Large QR for the verified stable production URL.

**Below:** The actual short hostname in readable text.

**Three actions:** Follow an agent. Inspect a source. Challenge a conclusion.

**Small mode label:** Recorded demonstration with simulated model outputs.

**Footer:** Repository and reproduction instructions are on the site.

Do not use the mode label above if the final site has different behavior. Name the
actual mode precisely, for example “Interactive mock workflow” for fresh execution
using simulated providers. A replay of real model output must carry its original
execution details and must not be described as fresh inference.

## Closing speaker script, about 20 seconds

“Scan this to explore the same synthetic example on your phone. Follow the agents,
open a source and inspect the weak points. The audience version uses recorded,
simulated outputs, so everyone can inspect it without waiting for compute. The
site also links to our code and reproduction steps.”

Use only after signed-out mobile verification. If the public page instead supports
fresh mock execution, replace the third sentence with: “The audience version runs
the workflow with simulated models, and it tells you when a run is waiting.”

## If the audience deployment is not ready

Remove the QR and replace it with the verified repository link and a screenshot.
Say: “We have the working hosted demonstration here. The repository contains the
synthetic case and reproduction instructions; we are preparing the public trial.”
Use “here” only while actually showing the working deployed application. Do not
show a QR that leads the room to a login gate or an unregistered hostname.

## Short hosting answer for judges

“The audience explorer serves public example data from a static host, so 50 people
inspecting it do not trigger 50 model jobs. Our full workflow runs separately on
Brev. Live public investigations need a bounded queue, per-user data ownership
and measured provider budgets; those are the next service boundaries.”

This is an architecture explanation, not a claim that a 50-user load test passed.
If the static explorer is still proposed, say “Our planned audience explorer”
instead. Hosting on Brev is infrastructure use; it does not by itself establish
meaningful in-product NVIDIA model use under the judging rubric.

## Production checklist for the slide owner

1. Take the exact production URL from a successful deployment, not a suggested name.
2. Open it signed out, then on mobile data; confirm useful content without NVIDIA login.
3. Generate QR SVG and PNG locally from that URL; store both under
   `Presentation/assets/` with an `audience-link.json` provenance record.
4. Put the readable hostname below the QR. Keep the QR black on white, with a clear
   quiet zone, and keep the astral artwork outside it.
5. Scan the projected final slide from the back of the room on two phones.
6. Keep a local recording and offline video ready. Keep the audience URL stable
   across updates and later domain changes.

No slide template or QR artifact is being presented as finished until those checks
are complete. This script is stored now so the access step does not become a
last-minute presentation dependency.
