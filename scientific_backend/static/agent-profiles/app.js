"use strict";

// This page only reads the adjacent published metadata. It has no provider clients.
const byId = (id) => document.getElementById(id);
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined && text !== null) element.textContent = String(text);
  if (className) element.className = className;
  return element;
}
function list(values, className, itemTag = "span") {
  const result = node("ul", null, className);
  for (const value of values || []) {
    const item = node("li");
    item.append(node(itemTag, value));
    result.append(item);
  }
  return result;
}
function display(value) {
  if (Array.isArray(value)) return value.join(" → ");
  if (value && typeof value === "object") return Object.entries(value).map(([key, item]) => `${key}: ${display(item)}`).join(" · ");
  return value == null ? "" : String(value);
}
function label(value) {
  return String(value || "").replaceAll("_", " ");
}

async function start() {
  const response = await fetch("./agent-profiles.json", { cache: "no-cache", credentials: "omit" });
  if (!response.ok) throw new Error("The metadata file could not be loaded.");
  const data = await response.json();
  if (!Array.isArray(data.agents) || !Array.isArray(data.skills) || !Array.isArray(data.skill_categories)) {
    throw new Error("The metadata file has an unexpected format.");
  }
  const skills = new Map(data.skills.map((skill) => [skill.id, skill]));
  const categories = new Map(data.skill_categories.map((category) => [category.id, category]));
  const names = new Map(data.agents.map((agent) => [agent.id, agent.name]));
  const roleName = (id) => names.get(id) || label(id);
  byId("snapshot").textContent = `Snapshot ${data.snapshot_date} · Profile version ${data.profile_version} · ${data.agents.length} scientific agents`;
  byId("model-name").textContent = `${data.model_policy.provider} / ${data.model_policy.default_model}`;
  byId("model-note").textContent = data.model_policy.identity_note;
  byId("model-selection").textContent = `Model selection: ${display(data.model_policy.selection)}`;

  for (const category of data.skill_categories) {
    const card = node("article", null, "source-card");
    card.dataset.category = category.id;
    card.append(node("h4", category.label), node("p", category.description));
    const count = data.skills.filter((skill) => skill.category === category.id).length;
    card.append(node("p", `${count} registered ${count === 1 ? "skill" : "skills"}`, "source-count"));
    byId("categories").append(card);
    const option = node("option", category.label);
    option.value = category.id;
    byId("category-filter").append(option);
  }

  function skillGroups(ids) {
    const container = node("div", null, "group-list");
    const groups = new Map();
    for (const id of ids || []) {
      const skill = skills.get(id) || { id, name: id, category: "unclassified" };
      if (!groups.has(skill.category)) groups.set(skill.category, []);
      groups.get(skill.category).push(skill);
    }
    for (const [categoryId, entries] of groups) {
      const group = node("div", null, "skill-group");
      group.append(node("span", categories.get(categoryId)?.label || label(categoryId), "skill-category-label"));
      const tags = node("ul", null, "skill-tags");
      for (const skill of entries) {
        const item = node("li");
        const tag = node("span", skill.name, "skill-tag");
        tag.dataset.category = categoryId;
        tag.title = `${skill.id}${skill.version ? ` · ${skill.version}` : ""}${skill.origin ? `\n${skill.origin}` : ""}`;
        item.append(tag);
        tags.append(item);
      }
      group.append(tags);
      container.append(group);
    }
    if (!groups.size) container.append(node("p", "None assigned.", "secondary"));
    return container;
  }

  function detailBlock(title, content) {
    const block = node("div", null, "detail-block");
    block.append(node("h4", title));
    if (content instanceof Node) block.append(content);
    else block.append(node("p", content));
    return block;
  }

  const cards = [];
  data.agents.forEach((agent, index) => {
    const main = agent.main_investigation;
    const card = node("article", null, "agent-card");
    card.id = `agent-${agent.id}`;
    const header = node("div", null, "agent-card-header");
    header.append(node("span", `AGENT ${String(index + 1).padStart(2, "0")}`, "agent-number"));
    const title = node("h3", agent.name);
    title.id = `title-${agent.id}`;
    card.setAttribute("aria-labelledby", title.id);
    header.append(title, node("p", agent.purpose, "agent-purpose"));
    const product = node("div", null, "work-product");
    product.append(node("strong", "Work product"), node("p", agent.work_product));
    const skillsSection = node("div", null, "skills-section");
    const skillHeading = node("div", null, "skill-heading");
    skillHeading.append(node("h4", "Automatic skills"), node("span", "Main investigation"));
    skillsSection.append(skillHeading, skillGroups(main.automatic_skills));
    const optional = node("details", null, "optional-skills");
    optional.append(node("summary", `Optional skills · ${main.optional_skills.length} eligible`), skillGroups(main.optional_skills));
    skillsSection.append(optional);

    const access = node("div", null, "nvidia-access");
    access.append(node("p", "NVIDIA access", "eyebrow"));
    access.append(node("p", agent.nvidia.can_request_matched_comparison ? "May request a matched comparison" : "No direct comparison request tool", "nvidia-status"));
    access.append(node("p", agent.nvidia.can_propose_registered_followup ? "May propose a registered follow-up for execution." : "Cannot propose a registered NVIDIA follow-up."));

    const details = node("details", null, "agent-details");
    details.append(node("summary", "Inputs, tools & handoffs"));
    const detailContent = node("div", null, "detail-content");
    detailContent.append(detailBlock("Inputs", list(agent.inputs)));
    detailContent.append(detailBlock("Handoff recipients", agent.recipients.map(roleName).join(" · ") || "No direct handoff recipients listed."));
    detailContent.append(detailBlock("Acceptance", display(agent.acceptance)));
    detailContent.append(detailBlock("Main investigation tools", list(main.tools, "tool-list", "code")));
    for (const condition of main.conditional_tools || []) {
      detailContent.append(detailBlock(condition.when, list(condition.tools, "tool-list", "code")));
    }
    detailContent.append(detailBlock("NVIDIA submission ownership", `${agent.nvidia.submission_owner}. ${agent.nvidia.note}`));
    if ((agent.additional_workflows || []).length) {
      const workflows = detailBlock("Additional workflows", "These workflows have their own skill and tool assignments.");
      for (const workflow of agent.additional_workflows) {
        const entry = node("div", null, "workflow");
        entry.append(node("h4", workflow.name), node("p", workflow.note), skillGroups(workflow.automatic_skills));
        if (workflow.tools.length) entry.append(node("p", "Tools"), list(workflow.tools, "tool-list", "code"));
        workflows.append(entry);
      }
      detailContent.append(workflows);
    }
    details.append(detailContent);
    card.append(header, product, skillsSection, access, details);
    byId("agent-grid").append(card);
    const assigned = [...main.automatic_skills, ...main.optional_skills, ...(agent.additional_workflows || []).flatMap((workflow) => workflow.automatic_skills)];
    cards.push({ element: card, categories: new Set(assigned.map((id) => skills.get(id)?.category)), search: `${JSON.stringify(agent)} ${assigned.map((id) => skills.get(id)?.name || id).join(" ")}`.toLowerCase() });
  });

  for (const participant of data.participants || []) {
    const card = node("article", null, "participant");
    card.append(node("p", label(participant.kind), "eyebrow"), node("h3", participant.name), node("p", participant.role, "participant-role"), node("p", participant.note, "participant-note"));
    byId("participants").append(card);
  }
  for (const note of data.interpretation_notes || []) byId("notes").append(node("li", note));

  function filter() {
    const search = byId("search").value.trim().toLowerCase();
    const category = byId("category-filter").value;
    let visible = 0;
    for (const card of cards) {
      const matches = (!search || card.search.includes(search)) && (category === "all" || card.categories.has(category));
      card.element.hidden = !matches;
      if (matches) visible += 1;
    }
    byId("profile-count").textContent = `${visible} of ${cards.length} profiles`;
    byId("empty-state").hidden = visible !== 0;
  }
  byId("search").addEventListener("input", filter);
  byId("category-filter").addEventListener("change", filter);
  filter();
  byId("content").hidden = false;
}

start().catch(() => {
  byId("snapshot").textContent = "Profile metadata unavailable in this view.";
  const error = byId("load-error");
  error.hidden = false;
  error.textContent = "The profile metadata could not be loaded. Open this folder through an HTTP server, or use the guide and metadata download above. No model or scientific service has been contacted.";
});
