# Public access for the TRACE demo

Researched 19 September 2026. This is an implementation recommendation, not a
deployment record. The user prefers a **free branded URL first**. No domain was
purchased, public access policy changed, or hosting account created during this
review. The authoritative existing release record is
[infra/DEPLOYMENT.md](../infra/DEPLOYMENT.md).

## Recommendation

Use **Cloudflare Pages for the audience link**, with a small, interactive browser
explorer built from the public synthetic event recordings. Request a project name
such as `trace-bio` or `trace-wilbe` and keep the actual assigned `pages.dev` URL.
These names are suggestions; availability has not been checked or reserved.
Keep the current Streamlit application on Brev for the presenter's full workflow.

This gives about 50 participants a useful experience without creating 50 Python
sessions or starting 50 model investigations. Pages serves static assets from a
distributed network, and static requests that do not invoke Functions are free and
unlimited under the documented pricing. This makes a small static explorer a
strong fit for the audience size. It is an architectural estimate, not a measured
50-user capacity result. [Pages pricing](https://developers.cloudflare.com/pages/functions/pricing/)

The explorer should let a visitor replay a supplied case, select an agent, inspect
one source, switch between a supported and an unsupported question, and read weak
points. It must visibly say **Recorded demonstration with simulated model outputs**.
A static page cannot run the existing Python application unchanged or answer an
arbitrary new research question. This extra viewer is a proposed artifact; the
repo currently contains Streamlit fixtures, not a ready static export.

If shipping a second viewer would jeopardize the working demonstration, use a
public Streamlit Community Cloud deployment in an explicitly restricted demo
mode instead. It offers a configurable `streamlit.app` subdomain and supports
public viewing without an NVIDIA account. Its dynamic-session capacity must be
rehearsed. Do not promise 50 concurrent investigators merely because the URL is
public. [Streamlit app URL](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings),
[public sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)

## What the current deployment supports

| Current fact | Consequence |
|---|---|
| `trace-z484f0h2c.gobrev.dev` reaches NVIDIA authentication and authorizes only the deploying account | Useful presenter/team entry, unsuitable for an audience QR today. Do not print it as a no-login trial. |
| Existing Brev CPU runs one Streamlit container and one private FastAPI worker | Keep this working topology for the stage demo. No GPU is needed merely to serve the UI. |
| API files, runs and event history live in process memory | Restart loses them; adding workers/replicas breaks lookups without shared storage. |
| Background workers and real cancellation now exist | Better responsiveness does not create global admission control or durable jobs. |
| Variant scoring has a per-run bound of eight workers | This is not a global provider limit. Fifty simultaneous runs could request up to 400 concurrent variant operations before other agent calls. |
| UI allows backend selection; API lacks authentication and ownership checks | Public configuration must be restricted in server-side code, and real user data needs tenant isolation. Hiding a widget alone is insufficient. |
| Server histories, uploads and run stores lack retention enforcement | A long audience session can accumulate memory even when every individual run finishes. |

NVIDIA describes Brev tunnels as browser-authenticated entry points. A custom name
or a QR code does not remove that access requirement. Changing the existing access
policy is a separate deployment operation. [Brev connectivity](https://docs.nvidia.com/brev/cli/connectivity)

## A practical free publishing route

The deployable unit for Pages should be a directory of HTML, CSS, JavaScript and
approved public JSON, separate from the Python service. Proposed name:
`public-demo/`. It should contain an `index.html`, local assets, a versioned
synthetic event bundle, a short source/license notice, and links to the repository
and reproduction instructions. Do not copy the whole repository or local uploads.

1. Build and test the browser explorer locally, including a narrow phone viewport.
   Do not embed credentials, run IDs from private investigations, provider URLs,
   or links that require the presenter's login. Keep the core page usable without
   video. Keep each asset below the Pages 25 MiB limit.
2. Sign into a team-owned Cloudflare account. In Workers & Pages, create a Pages
   project using Direct Upload, enter the project name and upload only the built
   viewer directory. Direct Upload supports a folder or ZIP in the dashboard.
   A Direct Upload project cannot later switch to Git integration; use a new
   project if that becomes necessary.
3. Save the **actual production URL** returned by the service. A requested project
   name can receive a suffix if already in use. Use the stable production hostname
   in slides, not a per-deployment preview URL.
4. Verify HTTPS, the correct revision, and all explorer controls in a signed-out
   browser on a phone using mobile data. Confirm that no NVIDIA or hosting login
   is requested. Have a second person follow the same path.
5. Generate the presentation QR from that exact verified URL. Store the URL,
   deployed artifact hash, revision and check time alongside it. Keep the same
   production URL when updating content.

Cloudflare documents the Direct Upload flow and assigned URL behavior in its
[upload guide](https://developers.cloudflare.com/pages/get-started/direct-upload/).
The [Pages limits](https://developers.cloudflare.com/pages/platform/limits/) include
20,000 files on the Free plan and 25 MiB per asset. These limits are ample for a
small viewer but do not turn Pages into a Python application server.

No domain purchase is needed for this route. Later, add an owned domain through
the Pages custom-domain settings and complete the provider's DNS validation. The
apex requires a Cloudflare zone; an externally managed subdomain can use the
documented CNAME setup after associating it with the project. The domain's price
depends on the selected name and registrar and has not been quoted. Keep the
original audience URL available so the printed QR remains useful.
[Custom-domain setup](https://developers.cloudflare.com/pages/configuration/custom-domains/)

## If the audience must use the current Streamlit UI

Community Cloud is the smaller code migration, provided the public deployment is
restricted to local mock execution or supplied recordings. It needs a connected
GitHub repository, a deliberate published revision, a deployment entry point, and
the actual combined backend/frontend Python dependencies. This repo's frontend
imports local engine modules in Demo mode, so installing only the frontend's
requirements is insufficient. Keep all model secrets out of this deployment.

Before publishing, add a server-enforced public demo profile: fixed allowed source
modes, no arbitrary backend URL, no live-provider selection, bounded question
length and rate, synthetic cases only, bounded retained history and a global
active-run limit. Any remaining file control must enforce size/count limits before
reading bytes. The current one-run-per-session guard is useful but a visitor can
open more tabs. These controls are **work to implement**, not existing guarantees.

Deploy the tested public entry point, choose an available branded subdomain, make
the app public, warm it before the talk and repeat the signed-out phone check.
Community Cloud's documentation says resource limits can change and that apps
hibernate after 12 hours without traffic. Check the account's current limits;
avoid treating an old memory figure as a reserved capacity commitment.
[Deployment flow](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app),
[resources and hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)

Streamlit's server computes for every connected viewer and each browser tab has
its own WebSocket session. Replication needs session affinity. With 50 active
investigations polling every 0.3 seconds, the application can attempt roughly
167 polling/render cycles per second before other interactions. That arithmetic
is a planning bound, not observed throughput.
[Streamlit architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture)

## Capacity rehearsal and service growth

| Audience behavior | Initial approach | Evidence needed before a capacity claim |
|---|---|---|
| 50 people scan and inspect recorded cases | Static Pages explorer; all interaction after load is browser-local | Anonymous/mobile checks, bundle size, console errors and successful 50-client page-load rehearsal on a test deployment. |
| 50 people interact with mock Streamlit runs | Limited public demo; start conservatively with four globally active runs and a bounded queue or explicit busy state | Browser sessions, not just HTTP health requests, at 10, 25, then 50 users; p95 interaction latency, CPU, RAM and cleanup after disconnect. |
| 50 people submit live model jobs | Separate durable job queue, protected API and a small measured worker pool | Per-provider rate limits, actual token/cost and duration distributions, ownership tests, queue recovery and run deadline enforcement. |

The suggested four-run starting budget is deliberately provisional. A batch of
50 submissions with four slots and a 30-second median run takes roughly 13 waves,
or 6.5 minutes for the last wave before variability. Keep queue position and
expected waiting explicit; 50 visitors does not require 50 simultaneous model
jobs. Never describe this example as measured TRACE performance.

Suggested rehearsal acceptance targets: no crashes or cross-session leakage,
95th-percentile ordinary interactions below two seconds, steady memory after
finished/abandoned sessions expire, and the busy state appearing before resource
exhaustion. Pause a load rehearsal if it disrupts other teammates. No remote load
test was run for this document.

For live user data, add authenticated ownership on upload/start/events/report/log
and cancellation; allowlist models; enforce total input bytes, active jobs, queue
length, provider calls, output tokens and overall deadline; expire uploads and
histories; store jobs/reports outside the API process. Use object storage for
files, a durable database for ownership/status and a queue for workers. Keep the
API reachable only from trusted server components until these boundaries exist.
GPU inference can remain on Brev or verified hosted model endpoints independently
of the website. These changes belong at the existing adapters/stores boundaries.

A later managed CPU host such as Render can serve the existing application with
WebSockets and managed HTTPS. Render gives services a unique `onrender.com` URL
and supports custom domains. Its free web instances sleep after 15 minutes of
inactivity, so they are a less predictable primary stage dependency. Changing
hosts does not fix process-local stores. [Render web services](https://render.com/docs/web-services),
[free deployment behavior](https://render.com/docs/your-first-deploy)

## QR and fallback handoff

Use one audience QR on the final slide and a smaller repeat on the opening slide.
Place the human-readable hostname immediately below it. Prefer an SVG plus a
large PNG export, dark modules on a plain white square, with a clear four-module
quiet zone. Keep stars, gradients and logos outside the code itself. Test the
projected slide from the back of the room with two phones.

Do not generate a QR for a proposed hostname, localhost, a signed-in session,
or a temporary SSH forward. The current Brev URL is a private presenter link,
so no audience QR has been generated by this review. Once a public URL is verified,
store `Presentation/assets/audience-qr.svg`, `audience-qr.png` and
`audience-link.json` containing the URL, actual deployment/revision and check time.

The public page should retain a compact recording and reproduction links if live
execution is busy. The presenter should separately have a local recorded run and
short offline video. Switch explicitly to a recorded demonstration if the live
path stalls; preserve its original simulated/live/precomputed label. The
[access slide script](../Presentation/access-slide-script.md) has speaker copy
for both verified-public and not-yet-public states.
