# Agent skills

Two reusable Codex skills created from research into official OpenAI and NVIDIA documentation:

- `agent-harness-building`: agent loops, tool contracts, scoped permissions, durable state, recovery, tracing, and validation.
- `benchmark-creation`: task datasets, leakage control, graders, fair comparisons, uncertainty, reproducible execution, and a planning template.

Copy each skill directory into your personal Codex skills directory (`$CODEX_HOME/skills`, normally `~/.codex/skills`). Preserve the subdirectories. Check for an existing skill with the same name before copying. Once Codex discovers the skills, invoke `$agent-harness-building` or `$benchmark-creation`, or describe a matching task.

Examples:

- “Use $agent-harness-building to add resumable tool execution to this agent.”
- “Use $benchmark-creation to compare two research agents on citation accuracy, task completion, cost, and latency.”

The benchmark YAML is a planning template, not a runnable vendor configuration. Both skills contain official source links and version-sensitive notes. Validate installed API versions before implementation. These skills do not require API credentials to read; actual model/service runs may require credentials and incur cost.

The skill files and reference links have been structurally validated. This package does not contain a completed agent implementation or measured benchmark results. It contains only the two authored skills and their resources, not third-party installed plugins or project source files.

The [source inventory](../docs/SOURCE-INVENTORY.md) identifies the Markdown sources and their original SHA-256 hashes. The small YAML resources are included alongside the skills.
