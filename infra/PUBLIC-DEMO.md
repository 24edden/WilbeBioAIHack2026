> **Historical prototype deployment.** These commands launch the earlier backend and `frontend/legacy_app.py`. For the current scientific release use [the root startup guide](../README.md) and [scientific backend setup](../scientific_backend/SETUP.md).

# Public Brev access and presentation QR

Checked on 20 September 2026 using the installed authenticated Brev CLI.
No public-access policy was changed during this check, and the integrated pet UI
has not yet replaced the existing Brev deployment.

The existing HTTPS destination is `https://trace-z484f0h2c.gobrev.dev` on
`agentic-takeoff-cpu`. Its HTTP mapping targets port 8501 and currently reports
`allow_public_unauthenticated: false`. Visitors therefore need NVIDIA sign-in
and authorization; a QR pointing there is not yet an anonymous audience demo.

`brev ports update --help` confirms that `--public` makes an HTTP mapping
accessible without authentication. After choosing the audience deployment and
authorizing public access, the exact existing UI mapping can be updated with:

```bash
brev ports update agentic-takeoff-cpu --id nport-3JYgrteCljH3QfKBYxoOidbJJCf --public --json
```

Re-read `brev ports ls agentic-takeoff-cpu --json` first to confirm the mapping
still belongs to TRACE. This command is a proposed action, not a deployment log.
Keep the backend API, SSH and notebooks private. The current prototype exposes
backend selection in Settings, so use a separate audience deployment with that
endpoint fixed server-side before opening access to arbitrary visitors.

For approximately 50 participants, serve bundled synthetic examples or recorded
investigations for the audience; reserve expensive provider runs for the presenter
or a bounded queue. No 50-user load test has been performed. Session memory,
uploaded files, provider concurrency and run retention still need explicit limits
for a durable public service.

Once published, test the HTTPS URL on a signed-out phone using mobile data, then
generate the presentation QR from that exact URL. Export both SVG and a high
resolution PNG, retain the quiet border, and print the URL under the code. Do not
encode a localhost address, SSH forward, credential or temporary preview URL.

Official connectivity reference: https://docs.nvidia.com/brev/cli/connectivity
