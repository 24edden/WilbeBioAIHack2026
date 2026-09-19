# Setup and readiness

Checked September 17, 2026. No cloud GPU was launched and no credits were spent by this setup.

**Latest update:** Scott confirms “I got Rosalind.” Life-sciences database/literature skills, NGS tools and scientific viewers are now exposed in this session. Treat Rosalind acquisition as user-confirmed. The historical browser check below predates that confirmation. Research mode, exact model/API entitlement and live scientific execution have not been independently tested.

## Completed locally

| Item | Evidence |
|---|---|
| Codex | This task runs in the existing Codex app; bundled CLI is present |
| Brev CLI | v0.6.335, official macOS arm64 archive, SHA-256 checked against release checksums |
| Python | 3.13.1, isolated environment in `assayguard/.venv` |
| Science libraries | RDKit 2026.3.6, scikit-learn 1.9.1, matplotlib 3.11.2; exact lock saved |
| Public dataset | BACE CSV downloaded from the URL in DeepChem's loader; hash saved |
| Demo | Ten completed runs: five seeds × two split policies; offline report and figures |
| Tests | Four tests cover split integrity, data quality, similarity and agent tool restrictions |

The Brev binary is **project-local**, not a global install. From the event-prep folder:

```sh
./bin/brev --version
./bin/brev login
```

`brev login` opens the NVIDIA/Brev sign-in flow. The browser security policy check was unavailable in this task, so account existence and sign-in were not verified. Complete authentication yourself in a normal browser. Do not paste tokens into this document or a repository. The CLI version check emitted a blocked telemetry-network warning in the sandbox; the version itself was confirmed.

## Before arrival

1. [Brev console](https://brev.nvidia.com): sign in or create an account. The organizer says GPU credits begin at the hackathon. Confirm the event organization before starting a paid instance.
2. **Rosalind obtained, user-confirmed.** Run one small public-data example and record the available mode, actual model and tools. Workbench access and API entitlement should be checked separately if a custom application is chosen.
3. **Discord confirmed:** the signed-in Chrome session is already in NVIDIA Developer, and [#london-ai-bio-hack](https://discord.com/channels/1019361803752456192/1547305592203378919) was opened successfully. No post has been sent.
4. Keep the offline report, pitch and registration email available on the laptop.

## Earlier Rosalind setup attempt and remaining checks

The “Try in ChatGPT” button displayed an “Open ChatGPT?” launch prompt. The attempt to activate that prompt returned an element error; it subsequently disappeared. Opening the app through the computer-use tool was explicitly refused because this desktop app cannot be controlled for safety reasons. Therefore the launch outcome, installation and account entitlement are not confirmed. A supported plugin-catalog search for “Rosalind” returned no result in this session.

In the desktop app, finish any **Set up Rosalind Workbench** onboarding shown. If nothing opened, return to the setup page and choose **Try in ChatGPT**, then **Open ChatGPT**. The landing page also says Workbench can be installed from the app's plugin marketplace.

Check which mode is available: **Explore** uses the ChatGPT models available to the account; **Research** supports advanced workflows and has a separate access process. OpenAI's current documentation says verified organization members can request Research access on behalf of their organization, with individual access coming soon. Do not submit an employer access request without the appropriate authority; ask the event's OpenAI team how attendee access is provisioned. Workbench installation alone does not establish GPT-Rosalind or API access. [Official setup and access explanation](https://developers.openai.com/blog/rosalind-workbench).

Once installed, a useful first check is: “List the scientific tools and modes available in this Workbench. Then help me compare the weekend project ideas in PROJECT-PORTFOLIO.md using only public data.” A public molecular structure viewer example from the onboarding can test the viewer without requiring a large analysis.

## Friday GPU checklist

Use the organizer's assigned image/instance if one is provided. Ask a mentor to confirm organization, credit allocation, GPU model, driver and shutdown policy. If the instance was created in the console:

```sh
./bin/brev refresh
./bin/brev ls
./bin/brev shell YOUR_ASSIGNED_INSTANCE
```

On the remote instance:

```sh
nvidia-smi
python -c 'import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())'
```

For nvMolKit, use NVIDIA's [installation guide](https://github.com/NVIDIA-BioNeMo/nvMolKit). It requires an NVIDIA GPU with compute capability 7.0 or newer, compatible CUDA drivers and CUDA-enabled PyTorch. The Mac baseline cannot supply this hardware. Use a separate GPU environment because nvMolKit pins compatible RDKit builds.

Choose a PyTorch CUDA backend supported by the instance's driver **before** installing nvMolKit. NVIDIA documents a CUDA 12.8 example; this is conditional, not a command to run blindly on every image:

```sh
# Only if the assigned image/driver supports this backend:
python -m pip install torch --index-url https://download.pytorch.org/whl/cu128
python -m pip install nvmolkit scikit-learn matplotlib
```

Run the vendor's three-molecule smoke test before the project workload, then `python gpu_check.py`. Record versions and the device. Stop if numerical parity fails; do not silently fall back and report GPU success.

## BioNeMo Agent Toolkit

The event's named toolkit is [NVIDIA BioNeMo Agent Toolkit](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit), a catalog of scientific skills. Its `nvmolkit-usage` capability fits AssayGuard. Browse its catalog with the vendor-documented command:

```sh
npx skills add NVIDIA-BioNeMo/bionemo-agent-toolkit --list
```

Then install the selected skill into the team project using the interactive install flow. The toolkit was researched and its README downloaded; it was **not** installed globally. Do not confuse BioNeMo Agent Toolkit with the separate NeMo Agent Toolkit orchestration/observability framework.

## OpenAI live path

`assayguard/agent.py` uses the documented Responses API function-calling pattern and only three bounded scientific tools (the GPU tool is opt-in). Configure the exact event-granted model ID using `OPENAI_MODEL` and a project API key using `OPENAI_API_KEY`. No API key was searched for or copied from your machine, and no live API request was sent during preparation.

If GPT-Rosalind is enabled only in Codex or Workbench, use the provided scientific review prompt in RESEARCH.md with saved metrics, then accurately describe that interaction. Do not invent a model ID or treat Workbench as a generic API endpoint.

## After a GPU session

Save results and source to persistent workspace/repository before stopping the instance. Brev documents `/home/ubuntu/workspace` as persistent across stops, but deletion removes the instance storage. Use the stop control for idle compute after confirming team ownership. No automatic create/stop/delete actions are configured here.

Sources: [Brev CLI setup](https://docs.nvidia.com/brev/cli/getting-started), [Brev quickstart](https://docs.nvidia.com/brev/getting-started/quickstart), [nvMolKit](https://github.com/NVIDIA-BioNeMo/nvMolKit), [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).
