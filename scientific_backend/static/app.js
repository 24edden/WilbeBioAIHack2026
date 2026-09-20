'use strict';

const $ = (id) => document.getElementById(id);
const state = {synthesisEligibility: new Map(), modelLimits: null, engineeringCheck: null, exampleSource: null, showAllEvents: false, showAllEvaluations: false, cases: [], history: [], datasets: [], datasetId: null, datasetEpoch: 0, lessons: [], lessonsAvailable: false, run: null, mode: 'live', capabilities: null, probing: null, version: null, source: 'User message', fileName: null, customHypothesis: false, busy: false, poll: null, epoch: 0, signatures: {}, pendingKeys: new Map(), toastTimer: null, pollingErrors: 0};
const activeStates = new Set(['queued', 'running', 'pending', 'resuming', 'reviewing', 'cancelling', 'cancel_requested', 'waiting']);
const architectureRoles = [
  {id: 'coordinator', label: 'Coordinator', aliases: ['investigator'], purpose: 'Preserve the question, route specialist work and synthesize the assessment.'},
  {id: 'clinical_scientist', label: 'Clinical scientist', purpose: 'Qualify the clinical timeline and phenotype when clinical inputs are available.'},
  {id: 'translational_scientist', label: 'Translational scientist', purpose: 'Connect the supported mechanism to a testable research and design objective.'},
  {id: 'bioinformatician', label: 'Bioinformatician', purpose: 'Check source identity, input versions, joins, exclusions and analysis readiness.'},
  {id: 'statistician', label: 'Statistician', purpose: 'Examine numerical support, comparisons, uncertainty and the independent sample unit.'},
  {id: 'clinical_pharmacologist', label: 'Clinical pharmacologist', purpose: 'Assess exposure and drug-specific explanations when the needed inputs exist.'},
  {id: 'molecular_scientist', label: 'Molecular / structural scientist', aliases: ['molecular_specialist', 'molecular_structural_scientist'], purpose: 'Qualify exact molecular inputs and the appropriate BioNeMo modeling branch.'},
  {id: 'assay_scientist', label: 'Assay / wet-lab scientist', aliases: ['assay_wet_lab_scientist'], purpose: 'Specify controls, endpoints and the experiment that distinguishes alternatives.'},
  {id: 'reviewer', label: 'Independent reviewer', aliases: ['independent_reviewer'], purpose: 'Challenge evidence support, contradictions and the proposed next experiment.'}
];
const roleKey = (value) => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const words = (value) => String(value ?? '').replace(/[_-]+/g, ' ');
const textValue = (value) => value == null ? 'Not supplied' : typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
const asArray = (value) => Array.isArray(value) ? value : value == null ? [] : [value];
const prettyDate = (value, options) => {const d = new Date(value); return Number.isNaN(d.getTime()) ? 'Not recorded' : new Intl.DateTimeFormat(undefined, options || {dateStyle: 'medium', timeStyle: 'short'}).format(d);};
const freshKey = () => window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
const isActive = (run) => activeStates.has(String(run?.status || '').toLowerCase());
const selectedDecision = () => (state.run?.decisions || []).find(d => String(d.version) === String(state.version)) || state.run?.decisions?.at(-1);
const safeUrl = (value) => {if (typeof value !== 'string' || !value.trim()) return null; try {const u = new URL(value, location.origin); return ['http:', 'https:'].includes(u.protocol) && (u.origin === location.origin || /^https?:\/\//i.test(value)) ? u.href : null;} catch {return null;}};
const modelName = (capability) => capability?.model === 'gpt-6-astra' ? 'GPT-6 Astra' : /rosalind/i.test(capability?.model || '') ? 'GPT-Rosalind' : capability?.label || capability?.model || 'Configured model';
const modelLabel = (capability) => capability?.model === 'gpt-6-astra' ? 'GPT-6 Astra · high reasoning (Rosalind placeholder)' : modelName(capability);
const capabilityMessage = (provider, capability) => {
  const detail = String(capability?.detail || 'Capability has not been verified.');
  if (provider === 'rosalind' && /invalid_api_key|incorrect api key|error code: 401/i.test(detail)) return 'OpenAI rejected the configured API key (401). Update the service’s OpenAI key and restart the service, then check connection again.';
  return detail.replace(/sk-[A-Za-z0-9*_-]+/g, '[redacted]');
};

async function api(path, options = {}) {
  const response = await fetch(path, {headers: {'Content-Type': 'application/json'}, ...options});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body.detail ?? body.error ?? `The service returned ${response.status}.`;
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(v => v.msg || textValue(v)).join('; ') : detail.message || textValue(detail);
    throw new Error(message);
  }
  return body;
}

function toast(message, error = false) {
  clearTimeout(state.toastTimer);
  $('toast').textContent = message;
  $('toast').className = `toast${error ? ' error' : ''}`;
  $('toast').hidden = false;
  state.toastTimer = setTimeout(() => {$('toast').hidden = true;}, error ? 11000 : 5500);
}

function badge(status, label) {
  const normalized = String(status || '').toLowerCase();
  const type = /ready|available|verified|completed|success|supported|qualified/.test(normalized) && !/not|unavailable|unverified/.test(normalized) ? 'success' : /failed|error|invalid/.test(normalized) ? 'danger' : /block|missing|pending|unavailable|unverified|not|configured|skip/.test(normalized) ? 'warning' : 'pale';
  return `<span class="pill ${type}">${esc(label ?? words(status || 'Unknown'))}</span>`;
}

function changed(key, value) {
  const signature = JSON.stringify(value);
  if (state.signatures[key] === signature) return false;
  state.signatures[key] = signature;
  return true;
}

async function refreshHealth() {
  try {
    const health = await api('/api/health');
    const healthy = !['error', 'failed', 'unhealthy', 'degraded'].includes(health.status) && health.worker_alive !== false;
    $('service-status').innerHTML = `<span class="status-dot ${healthy ? '' : 'error'}"></span> ${healthy ? 'Service connected' : health.worker_alive === false ? 'Worker offline' : esc(words(health.status))}`;
    const caps = health.capabilities || {};
    state.capabilities = caps;
    const limits = health.model_limits;
    state.modelLimits = limits; state.engineeringCheck = health.engineering_checks?.bionemo || null;
    $('execution-limits').textContent = limits ? `${Number(limits.agent_max_output_tokens).toLocaleString()} output tokens per specialist response; ${Number(limits.synthesis_max_output_tokens || limits.agent_max_output_tokens).toLocaleString()} for synthesis and independent review, including reasoning. ${limits.budget_mode === 'advisory' ? 'Aggregate request, token and tool thresholds issue alerts; they do not stop this run.' : 'Aggregate execution limits follow the server configuration.'}` : '';
    renderEngineeringCheck(health.engineering_checks?.bionemo);
    $('integration-status').textContent = caps.bionemo?.prediction_verified === true ? 'Matched molecular prediction receipt verified. Scientific performance remains unverified.' : 'CAR-T matched molecular comparison not yet verified.';
    if (changed('capabilities', caps)) {
      $('capability-list').innerHTML = ['rosalind', 'bionemo'].map(provider => {
        const c = caps[provider] || {status: 'unavailable', detail: 'Provider configuration not returned.'};
        return `<div class="capability-item"><div class="capability-top"><span class="provider-mark" aria-hidden="true">${provider === 'rosalind' ? '✳' : '◈'}</span><div><div class="provider-name">${provider === 'rosalind' ? esc(modelLabel(c)) : 'NVIDIA BioNeMo'}</div><div class="provider-model">${esc(c.model || (provider === 'rosalind' ? 'Scientific reasoning' : 'Molecular prediction'))}</div></div></div><div class="capability-state">${badge(c.status)}<button class="probe-button" data-probe="${provider}" title="Test this provider connection; may make a provider request">Verify ↗</button></div><p class="capability-detail">${esc(capabilityMessage(provider, c))}</p></div>`;
      }).join('');
    }
    updateStartButton();
    updateProbeButtons();
    $('architecture-model-label').textContent = `${modelName(caps.rosalind)} + source tools`;
    if (state.run) renderLiveOverview(state.run);
  } catch {
    $('service-status').innerHTML = '<span class="status-dot error"></span> Service disconnected';
    $('integration-status').textContent = 'Provider status unavailable — integration acceptance cannot be confirmed.';
    if (!state.signatures.capabilities) $('capability-list').innerHTML = '<p class="capability-placeholder">Unable to reach the service. Provider status is unknown.</p>';
  }
}

async function loadCases() {
  const response = await api('/api/cases');
  state.cases = Array.isArray(response) ? response : response.cases || [];
  if (!state.cases.length) throw new Error('No evidence collections are installed. Add a case package to the service.');
  $('case-select').innerHTML = state.cases.map(c => `<option value="${esc(c.id)}">${esc(c.title)}</option>`).join('');
  $('case-select').disabled = false;
  const preferredCase = state.cases.find(c => c.id === 'cart-discovery') || state.cases.find(c => /cd19/i.test(c.id));
  if (preferredCase) $('case-select').value = preferredCase.id;
  selectCase(false);
  $('load-cd19-example').disabled = !state.cases.some(c => c.id === 'cd19-car-t');
}

function formatBytes(value) {
  if (value == null || !Number.isFinite(Number(value))) return 'Size not indexed';
  const bytes = Number(value);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

async function refreshDatasets() {
  $('refresh-datasets').disabled = true;
  try {
    const response = await api('/api/datasets');
    state.datasets = Array.isArray(response) ? response : response.datasets || [];
    $('dataset-count').textContent = String(state.datasets.length);
    $('dataset-readiness').textContent = `${state.datasets.length} collections indexed by the service. This inventory does not establish that every file is readable, qualified or analyzed; the investigation records its actual tool choices and accepted evidence.`;
    $('dataset-select').innerHTML = '<option value="">Choose an indexed collection</option>' + state.datasets.map(dataset => `<option value="${esc(dataset.id)}">${esc(dataset.title || dataset.id)}${dataset.files_count != null ? ` · ${esc(dataset.files_count)} files` : ''}</option>`).join('');
    $('dataset-select').disabled = !state.datasets.length;
    if (state.datasetId && state.datasets.some(d => d.id === state.datasetId)) {
      $('dataset-select').value = state.datasetId;
      await selectDataset(state.datasetId);
    } else {
      state.datasetId = null;
      $('dataset-description').textContent = '';
      $('dataset-file-list').innerHTML = `<div class="state-placeholder">${state.datasets.length ? 'Select a collection to inspect its indexed files. File inspection does not start a model call.' : 'No data collections are registered in this service.'}</div>`;
    }
  } catch (error) {
    $('dataset-count').textContent = '—';
    $('dataset-select').disabled = true;
    $('dataset-select').innerHTML = '<option>Catalog unavailable</option>';
    $('dataset-readiness').textContent = 'The data catalog is unavailable from this service. Available files and readiness cannot be confirmed.';
    $('dataset-file-list').innerHTML = `<div class="state-placeholder">${esc(error.message)}</div>`;
  } finally {$('refresh-datasets').disabled = false;}
}

async function selectDataset(id) {
  state.datasetId = id || null;
  const epoch = ++state.datasetEpoch;
  if (!id) {$('dataset-file-list').innerHTML = '<div class="state-placeholder">Select a collection to inspect its indexed files.</div>'; $('dataset-description').textContent = ''; return;}
  const indexed = state.datasets.find(dataset => dataset.id === id);
  $('dataset-description').textContent = indexed?.description || '';
  $('dataset-file-list').innerHTML = '<div class="state-placeholder">Reading indexed file metadata…</div>';
  try {
    const response = await api(`/api/datasets/${encodeURIComponent(id)}`);
    if (epoch !== state.datasetEpoch) return;
    state.datasetFiles = Array.isArray(response.files) ? response.files : [];
    $('dataset-file-list').innerHTML = `<div class="dataset-file-heading"><span class="pill pale">Indexed files · not an analysis result</span><span class="small muted">${state.datasetFiles.length} files listed${indexed?.bytes != null ? ` · ${esc(formatBytes(indexed.bytes))}` : ''}</span></div><label class="sr-only" for="dataset-file-filter">Search indexed filenames</label><input id="dataset-file-filter" type="search" placeholder="Search indexed filenames or formats…"><div id="dataset-files-table"></div>`;
    $('dataset-file-filter').addEventListener('input', renderDatasetFiles);
    renderDatasetFiles();
  } catch (error) {
    if (epoch === state.datasetEpoch) $('dataset-file-list').innerHTML = `<div class="state-placeholder">Could not read this collection’s index: ${esc(error.message)}</div>`;
  }
}

function renderDatasetFiles() {
  const search = $('dataset-file-filter').value.trim().toLowerCase();
  const matched = (state.datasetFiles || []).filter(file => `${file.name} ${file.format} ${file.id}`.toLowerCase().includes(search));
  const visible = matched.slice(0, 250);
  $('dataset-files-table').innerHTML = visible.length ? `<div class="data-table-wrap"><table class="data-table"><thead><tr><th scope="col">Indexed file</th><th scope="col">Format</th><th scope="col">Size</th><th scope="col">Host availability</th><th scope="col">File ID</th></tr></thead><tbody>${visible.map(file => `<tr><td>${esc(file.name || 'Unnamed file')}</td><td>${esc(file.format || 'Not indexed')}</td><td>${esc(formatBytes(file.bytes))}</td><td>${file.available === true ? 'On this host · hash check before analysis' : file.available === false ? 'Unavailable on this host' : 'Not checked'}</td><td class="mono">${esc(file.id)}</td></tr>`).join('')}</tbody></table></div><p class="dataset-table-note">Showing ${visible.length} of ${matched.length} matching indexed files.${matched.length > visible.length ? ' Narrow the search to find additional files.' : ''} Analysis and review happen only through recorded investigation actions.</p>` : '<div class="state-placeholder">No indexed files match this search.</div>';
}

function loadCd19Example() {
  const example = state.cases.find(c => c.id === 'cd19-car-t');
  if (!example) return;
  $('case-select').value = example.id;
  selectCase(false);
  $('hypothesis').value = example.hypothesis || '';
  state.exampleSource = example.hypothesis_source?.name || 'CD19 case example';
  state.source = `User-selected CD19 example: ${state.exampleSource}`;
  state.fileName = null; state.customHypothesis = true;
  $('hypothesis-file').value = '';
  $('source-name').textContent = `Source: ${state.source}`;
  updateStartButton(); $('hypothesis').focus();
}

const roleLabel = value => architectureRoles.find(role => [role.id, ...(role.aliases || [])].includes(roleKey(value)))?.label || words(value);
const excerpt = (value, limit = 340) => {const text = String(value || ''); return text.length > limit ? text.slice(0, limit).trimEnd() + '…' : text;};

function operationEvents(run) {
  const events = asArray(run?.events);
  const action = asArray(run?.actions).find(item => run?.operation?.id && item.id?.startsWith(run.operation.id) && item.started_at);
  const start = action?.started_at || run?.operation?.input?.created_at;
  return start ? events.filter(event => !event.time || event.time >= start) : events;
}

function roleActivity(run, role) {
  const aliases = [role.id, ...(role.aliases || [])];
  const events = operationEvents(run).filter(event => aliases.includes(roleKey(event.agent)));
  const reusedIds = ['synthesis_continuation', 'research_brief', 'sequence_discovery'].includes(run?.operation?.kind) ? asArray(run.operation.input?.reused_handoff_ids) : [];
  const products = asArray(run?.handoffs).filter(product => aliases.includes(roleKey(product.sender || product.role)) && (!run?.operation?.id || !product.operation_id || product.operation_id === run.operation.id || reusedIds.includes(product.id)));
  const latest = products.at(-1), event = events.at(-1), lifecycle = events.filter(item => ['agent', 'handoff'].includes(item.type)).at(-1);
  const reused = !!latest && reusedIds.includes(latest.id) && latest.operation_id !== run?.operation?.id;
  const interpretation = run?.operation?.kind === 'research_brief' && ['coordinator', 'reviewer'].includes(role.id) && events.length > 0;
  const sequenceDiscovery = run?.operation?.kind === 'sequence_discovery' && ['molecular_scientist', 'reviewer'].includes(role.id) && events.length > 0;
  let status = 'Not started', statusKey = '';
  if (events.length || products.length) {
    if (run?.mode !== 'live') status = 'Offline record';
    else if ((lifecycle?.status === 'running' || aliases.includes(roleKey(run?.active_agent))) && isActive(run)) {status = sequenceDiscovery ? 'Finding sequences' : interpretation ? 'Explaining results' : 'Working now'; statusKey = 'running';}
    else if (sequenceDiscovery && ['failed', 'error'].includes(lifecycle?.status || event?.status)) {status = 'Sequence search stopped'; statusKey = 'failed';}
    else if (sequenceDiscovery && lifecycle?.status === 'completed') {status = 'Sequence search checked'; statusKey = 'completed';}
    else if (interpretation && ['failed', 'error'].includes(lifecycle?.status || event?.status)) {status = 'Explanation stopped'; statusKey = 'failed';}
    else if (interpretation && lifecycle?.status === 'completed') {status = 'Explanation checked'; statusKey = 'completed';}
    else if (reused) {status = latest.result_status === 'blocked' ? 'Reused · blocked finding' : latest.result_status === 'inconclusive' ? 'Reused · inconclusive' : 'Reused accepted work'; statusKey = latest.result_status === 'blocked' ? 'blocked' : 'completed';}
    else if (latest?.result_status === 'blocked' || lifecycle?.status === 'blocked') {status = 'Blocked · missing input'; statusKey = 'blocked';}
    else if (latest) {status = latest.result_status === 'inconclusive' ? 'Completed · inconclusive' : 'Work product complete'; statusKey = 'completed';}
    else if (lifecycle?.status === 'completed') {status = 'Completed'; statusKey = 'completed';}
    else if (['failed','error'].includes(lifecycle?.status || event?.status)) {status = 'Stopped with error'; statusKey = 'failed';}
    else if (!isActive(run) && lifecycle?.status === 'running') {status = 'Stopped before handoff'; statusKey = 'failed';}
    else status = 'Activity recorded';
  }
  return {role, events, products, latest, event, lifecycle, status, statusKey, reused, interpretation, sequenceDiscovery};
}

function activityHeadline(run) {
  const active = architectureRoles.map(role => roleActivity(run, role)).filter(item => item.statusKey === 'running').sort((a,b) => String(a.event?.time || '').localeCompare(String(b.event?.time || ''))).at(-1);
  if (active) return `${active.role.label} · ${active.event?.title || 'Recorded agent work in progress'}`;
  const latest = run.last_activity || asArray(run.events).at(-1);
  if (latest) return `${roleLabel(latest.agent || 'Harness')} · ${latest.title || words(latest.type)}`;
  return run.status === 'queued' ? 'Queued · waiting for a worker; no specialist work recorded yet' : words(run.stage || 'Preparing source qualification');
}

function renderLiveOverview(run) {
  $('live-overview').hidden = false;
  const roles = architectureRoles.map(role => roleActivity(run, role));
  const active = roles.filter(role => role.statusKey === 'running').at(-1);
  const latest = asArray(run.handoffs).at(-1);
  const events = asArray(run.events);
  const evaluations = asArray(run.stage_evaluations);
  const title = active ? `${active.role.label} is working.` : run.status === 'completed' ? 'The assessment is ready for review.' : isActive(run) ? 'Your investigation is progressing.' : 'The recorded work is preserved.';
  $('live-overview-title').textContent = title;
  $('live-overview-detail').textContent = activityHeadline(run);
  $('live-overview-status').className = `pill ${isActive(run) ? 'pale' : run.status === 'completed' ? 'success' : 'warning'}`;
  $('live-overview-status').textContent = words(run.status);
  $('live-metrics').innerHTML = [[roles.filter(role => role.events.length || role.products.length).length, 'of 9 roles recorded'], [asArray(run.handoffs).length, 'accepted handoffs'], [asArray(run.evidence).length, 'evidence records'], [evaluations.length, 'stage evaluations']].map(([count,label]) => `<div><strong>${count}</strong><span>${label}</span></div>`).join('');
  const alerts = asArray(run.budget_alerts).length ? run.budget_alerts : events.filter(event => event.type === 'budget');
  $('budget-alerts').hidden = !alerts.length;
  $('budget-alerts').innerHTML = alerts.length ? `<strong>Usage advisory · ${alerts.length} recorded ${alerts.length === 1 ? 'alert' : 'alerts'}</strong><p>${esc(alerts.slice(-3).map(alert => typeof alert === 'string' ? alert : alert.detail || alert.message || alert.reason || alert.title || (alert.threshold != null ? `${words(alert.category)}: observed ${alert.observed}; alert threshold ${alert.threshold}.` : textValue(alert))).join(' '))}</p><small>${(run.worker_budget_policy?.mode || state.modelLimits?.budget_mode) === 'advisory' && isActive(run) ? 'Aggregate thresholds are advisory. The run continues while service and scientific qualification checks remain enforced.' : 'This records actual server alerts. Execution status above remains authoritative.'}</small>` : '';
  $('activity-result').innerHTML = latest ? `<div class="digest-route">${esc(roleLabel(latest.sender || latest.role))} <span>→</span> ${esc(asArray(latest.recipient).map(roleLabel).join(', '))}</div><h3>${esc(excerpt(latest.question,160))}</h3><p>${esc(excerpt(latest.result || latest.summary,450))}</p><div class="digest-evidence">${[...new Set(asArray(latest.claims).flatMap(claim => asArray(claim.evidence_ids)))].slice(0,4).map(id => `<button class="evidence-link" data-show-evidence="${esc(id)}">${esc(id)} ↗</button>`).join('')}</div>${asArray(latest.limitations).length ? `<p class="digest-limitation"><strong>Limitation</strong> ${esc(excerpt(latest.limitations[0],200))}</p>` : ''}<button class="evidence-link" data-show-handoff="${esc(latest.id)}">Read rationale, evidence &amp; handoff checks ↗</button>` : '<h3>Waiting for the first accepted handoff.</h3><p>Actual agent actions appear beside this panel as they occur. Scientific results appear only when a work product has been accepted.</p>';
  renderMolecularOverview(run);
  $('activity-recent').innerHTML = events.length ? events.slice(-4).reverse().map(event => `<li><span class="activity-event-dot ${event.status === 'running' && isActive(run) ? 'active' : ''}"></span><div><strong>${esc(event.title || words(event.type))}</strong><small>${esc(roleLabel(event.agent || 'Harness'))} · ${esc(prettyDate(event.time,{hour:'2-digit',minute:'2-digit',second:'2-digit'}))}</small></div></li>`).join('') : '<li>No activity has been recorded yet.</li>';
}

function renderEngineeringCheck(check) {
  const verified = check?.monomer_service_verified === true;
  const linkList = Array.isArray(check?.links) ? check.links : check?.links && typeof check.links === 'object' ? Object.entries(check.links).map(([name,url])=>({name,url})) : [];
  if (check?.receipt_url) linkList.push({name:'Engineering receipt',url:check.receipt_url});
  for (const artifact of asArray(check?.artifacts)) if (artifact.url) linkList.push({name:artifact.name || 'Engineering structure',url:artifact.url});
  const markup = `<div class="engineering-heading"><span>NVIDIA service check</span>${badge(verified ? 'verified' : check?.status || '', verified ? 'Monomer verified' : words(check?.status || 'No receipt'))}</div><p>${verified ? 'A real Boltz-2 monomer prediction passed artifact validation.' : 'No validated engineering prediction is recorded for this service yet.'} This is an engineering check, not a CAR-T hypothesis test or matched binder comparison.</p>${check?.request_id || check?.check_id ? `<p class="engineering-id">Receipt / request <span class="mono">${esc(check.request_id || check.check_id)}</span></p>` : ''}${check?.confidence_score != null ? `<p>Reported structure confidence: <strong>${esc(check.confidence_score)}</strong> · not measured affinity</p>` : ''}${asArray(check?.artifacts).length ? `<details><summary>Validated artifact fingerprint</summary>${check.artifacts.map(artifact => `<p class="engineering-id">${esc(artifact.name)}<span class="mono">${esc(artifact.sha256 || 'Hash not supplied')}</span></p>`).join('')}</details>` : ''}${linkList.length ? `<div class="engineering-links">${linkList.map(link => {const url=safeUrl(link.url || link.href);return url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(link.name || link.label || 'Engineering artifact')} ↗</a>` : '';}).join('')}</div>` : ''}`;
  $('engineering-check').innerHTML = markup;
  $('live-engineering-details').innerHTML = markup;
  updateStructureOptions();
}

function structureScope(scope) {
  const labels = {
    exploratory_public_isoform_structure: 'Exploratory public CD19 ectodomain predictions: wild-type and exon-2-deleted monomers. These structures do not test CAR binding, trafficking or efficacy.',
    engineering_monomer_only: 'Engineering monomer service check only; not a CAR-T hypothesis test or matched binder comparison.',
    qualified_molecular_prediction: 'Qualified molecular prediction from the recorded inputs; not experimental evidence of CAR-T efficacy.'
  };
  return labels[scope] || words(scope || 'Use the scope recorded in the provider receipt.');
}

function structureLabel(artifact) {
  const key = artifact.label || String(artifact.name || '').replace(/_prediction\.cif$/, '');
  if (artifact.scope === 'exploratory_public_isoform_structure') {
    if (key === 'wild_type') return 'Wild-type CD19 ectodomain';
    if (key === 'exon2_deleted') return 'Exon-2-deleted CD19 ectodomain';
  }
  return words(artifact.label || String(artifact.name || 'Validated structure').replace(/\.(cif|pdb)$/i, ''));
}

function renderMolecularOverview(run) {
  const latestDecision = asArray(run.decisions).at(-1);
  const modeling = run.agent_modeling || latestDecision?.rd_handoff?.modeling;
  const specialist = asArray(run.handoffs).filter(item => ['molecular_scientist','molecular_specialist'].includes(item.sender || item.role)).at(-1);
  const status = modeling?.status || specialist?.result_status || 'not recorded';
  const service = state.engineeringCheck?.monomer_service_verified === true ? 'Monomer service check verified' : 'Monomer service check unverified';
  const operation = asArray(run.followup_operations).filter(item => item.kind === 'bionemo_public_structure').at(-1);
  const artifacts = asArray(operation?.artifacts).filter(artifact => artifact.scope === 'exploratory_public_isoform_structure' && /^[a-f0-9]{64}$/i.test(artifact.sha256 || '') && safeUrl(artifact.url) && asArray(operation.provider_receipts).some(receipt => receipt.status === 'completed' && receipt.label === artifact.label && receipt.model === artifact.model && receipt.request_id === artifact.request_id));
  const phase = ({reviewing:'scientific review in progress',completed:'follow-up completed',queued:'queued',running:'running',blocked:'follow-up blocked',failed:'follow-up failed',unknown:'external outcome unresolved',cancelled:'follow-up cancelled'})[operation?.status] || words(operation?.status || 'not recorded');
  const publicSummary = operation ? `Public CD19: ${artifacts.length} validated ${artifacts.length === 1 ? 'structure' : 'structures'} · ${phase}` : '';
  $('live-nvidia-summary').textContent = `NVIDIA · ${[publicSummary, `Matched binder comparison: ${words(status)}`, service].filter(Boolean).join('  |  ')} · inspect receipts & outputs ↗`;
  const publicMarkup = operation ? `<div class="public-structure-status"><h5>Public CD19 isoform predictions</h5>${badge(operation.result_status || operation.status, `${artifacts.length} validated ${artifacts.length === 1 ? 'structure' : 'structures'}`)}<p>${esc(phase)}${operation.new_decision_version != null ? ` · decision v${esc(operation.new_decision_version)}` : ''}. Provider result: ${esc(words(operation.result_status || 'not yet returned'))}.</p><p>${esc(structureScope('exploratory_public_isoform_structure'))}</p>${artifacts.length ? `<div class="engineering-links">${artifacts.map(artifact => `<button type="button" class="evidence-link" data-view-structure="${esc(artifact.preview_url || '')}">View ${esc(structureLabel(artifact))} ↗</button>`).join('')}</div>` : ''}</div>` : '';
  $('case-molecular-status').innerHTML = `${publicMarkup}<h5>Matched reference/candidate binder comparison</h5>${badge(status)}<p>${esc(excerpt(modeling?.reason || specialist?.result || 'No qualified matched reference/candidate prediction has been recorded for this investigation.',430))}</p>${specialist ? `<button class="evidence-link" data-show-handoff="${esc(specialist.id)}">Read molecular specialist’s qualification ↗</button>` : ''}${asArray(modeling?.artifacts).length ? `<div class="engineering-links">${modeling.artifacts.map(artifact => {const url=safeUrl(artifact.url);return url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(structureLabel(artifact))} ↗</a>` : '';}).join('')}</div>` : ''}<p class="engineering-scope-note">Service checks, public isoform predictions and matched binder comparisons have separate scope and receipts. Structure confidence does not establish CAR-T efficacy.</p>`;
}

function selectCase(setHypothesis = false) {
  const c = state.cases.find(c => c.id === $('case-select').value);
  if (!c) return;
  $('case-description').textContent = c.description || c.subtitle || '';
  if (setHypothesis) {
    $('hypothesis').value = c.hypothesis || '';
    state.source = c.hypothesis_source?.name ? `Selected ${c.title}: ${c.hypothesis_source.name}` : `Selected case hypothesis: ${c.title}`;
    state.fileName = null;
    $('hypothesis-file').value = '';
    $('source-name').textContent = `Source: ${c.hypothesis_source?.name || c.title}`;
  }
  const readiness = Array.isArray(c.readiness) ? c.readiness : typeof c.readiness === 'object' ? [c.readiness] : [];
  const ready = readiness.filter(r => ['ready', 'verified', 'available'].includes(r.status)).length;
  const readinessSummary = readiness.length ? `${ready}/${readiness.length} readiness checks met` : words(c.readiness || 'Evidence qualification required');
  const limitations = asArray(c.limitations);
  $('case-readiness').innerHTML = `<span class="status-dot"></span><div><span>${esc(c.evidence_count != null ? `${c.evidence_count} pinned evidence records` : 'Pinned evidence collection')} · ${esc(readinessSummary)}</span>${readiness.length || limitations.length ? `<details class="readiness-details"><summary>Inspect readiness &amp; limitations</summary>${readiness.map(r => `<div class="readiness-item">${badge(r.status)}<span><strong>${esc(r.label || words(r.status))}</strong>${esc(r.detail || '')}</span></div>`).join('')}${limitations.length ? `<ul>${limitations.map(l => `<li>${esc(textValue(l))}</li>`).join('')}</ul>` : ''}</details>` : ''}</div>`;
  updateStartButton();
}

function updateStartButton() {
  const capability = state.capabilities?.rosalind;
  $('start-run').disabled = state.busy || state.probing === 'rosalind' || !state.cases.length || $('hypothesis').value.trim().length < 10 || (state.mode === 'live' && !capability);
  if (!state.busy) $('start-run').innerHTML = state.probing === 'rosalind' ? 'Checking model connection…' : state.mode === 'demo' ? 'Start offline walkthrough <span aria-hidden="true">↗</span>' : capability?.status === 'verified' ? 'Start live investigation <span aria-hidden="true">↗</span>' : capability ? 'Check model connection <span aria-hidden="true">↗</span>' : 'Checking connection…';
  $('mode-explainer').textContent = state.mode === 'demo' ? 'Offline walkthrough using pinned evidence; interpretation is scripted. This mode makes no model calls.' : state.probing === 'rosalind' ? `Checking ${modelLabel(capability)} with a real model/tool round trip. No investigation has started yet.` : capability?.status === 'verified' ? `${modelLabel(capability)} · live reasoning and visible tool calls. New investigations test hypotheses and continue with qualified, reviewer-selected follow-ups until a stated stopping point. BioNeMo requires appropriate inputs.` : capability ? `${modelLabel(capability)}. ${capabilityMessage('rosalind', capability)} Check connection before starting; the check makes a real model/tool round trip when a credential is configured.` : 'Live investigation uses the configured model with visible tool calls. Reading the provider connection status…';
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll('[data-mode]').forEach(b => {const selected = b.dataset.mode === mode; b.classList.toggle('selected', selected); b.setAttribute('aria-pressed', String(selected));});
  updateStartButton();
}

async function refreshHistory() {
  try {
    const response = await api('/api/runs');
    state.history = Array.isArray(response) ? response : response.runs || [];
    $('run-count').textContent = String(state.history.length);
    if (!changed('history', [state.history, state.run?.id])) return;
    $('mobile-run-select').innerHTML = '<option value="">Choose a previous run</option>' + state.history.map(run => `<option value="${esc(run.id)}" ${run.id === state.run?.id ? 'selected' : ''}>${esc(state.cases.find(c => c.id === run.case_id)?.title || words(run.case_id))} · ${esc(words(run.status))} · ${esc(prettyDate(run.created_at))}</option>`).join('');
    $('run-history').innerHTML = state.history.length ? state.history.map(run => {
      const c = state.cases.find(c => c.id === run.case_id);
      return `<button class="history-item ${run.id === state.run?.id ? 'selected' : ''}" data-run="${esc(run.id)}"><strong>${esc(c?.title || run.title || words(run.case_id) || 'Investigation')}</strong><small><span>${esc(words(run.status))}</span><span>·</span><span>${esc(run.mode === 'live' ? 'Live' : 'Offline')}</span></small></button>`;
    }).join('') : '<p class="sidebar-empty">Your investigations will appear here.</p>';
  } catch { /* A later poll retries; run progress errors are surfaced separately. */ }
}

async function refreshLessons() {
  try {
    const response = await api('/api/lessons');
    state.lessons = Array.isArray(response) ? response : response.lessons || [];
    state.lessonsAvailable = true;
    $('lesson-count').textContent = String(state.lessons.length);
    if (changed('lessons', state.lessons)) {
      $('lesson-list').innerHTML = state.lessons.length ? state.lessons.map(lesson => `<article class="card lesson-card"><div class="lesson-heading"><span class="step-label">${esc(lesson.id)}</span>${badge('', words(lesson.status || 'provisional'))}</div><h4>${esc(lesson.procedure)}</h4><p class="lesson-conditions"><strong>Conditions</strong> ${esc(lesson.conditions)}</p><dl class="lesson-meta"><dt>Origin</dt><dd>${esc(words(lesson.origin_case_id))} · decision v${esc(lesson.decision_version)} · ${esc(lesson.mode === 'live' ? 'Live' : 'Offline')}</dd><dt>In scope</dt><dd>${esc(asArray(lesson.scope_case_ids).map(words).join(', '))}</dd><dt>Excluded</dt><dd>${esc(asArray(lesson.excluded_case_ids).map(words).join(', '))}</dd><dt>Proposed by</dt><dd>${esc(lesson.author)}</dd><dt>Review</dt><dd>${lesson.review ? esc(`${lesson.review.approved ? 'Approved' : 'Not approved'} by ${lesson.review.reviewer || 'recorded reviewer'}`) : 'Scientist review pending'}</dd><dt>Evaluation</dt><dd>${lesson.evaluation ? esc(lesson.evaluation.quality_passed ? 'Passing quality judgment recorded; see pinned evaluation in export/API' : 'Quality judgment did not pass') : 'Disjoint evaluation pending'}</dd>${lesson.release_id ? `<dt>Release record</dt><dd class="mono">${esc(lesson.release_id)}</dd>` : ''}</dl><p class="lesson-footnote">${lesson.status === 'released' ? 'A release is recorded. Reuse remains subject to mode, case scope and server suspension checks.' : 'This lesson is not released for reuse.'}</p></article>`).join('') : '<div class="state-placeholder">No lessons have been proposed. Case corrections remain attached to their original decisions.</div>';
    }
  } catch (error) {
    state.lessonsAvailable = false;
    $('lesson-count').textContent = '—';
    $('lesson-list').innerHTML = '<div class="state-placeholder">Learning records are unavailable from this service. No review or release status can be confirmed.</div>';
    delete state.signatures.lessons;
  }
  if (state.run) setFormsEnabled(!isActive(state.run));
}

async function refreshSkills() {
  $('refresh-skills').disabled = true;
  try {
    const response = await api('/api/skills');
    const skills = Array.isArray(response) ? response : response.skills || [];
    state.skillCatalog = skills;
    renderSkillReceipts(state.run);
    $('skills-count').textContent = String(skills.length);
    $('skill-registry').innerHTML = skills.length ? `<div class="skill-registry-grid">${skills.map(skill => `<article class="card skill-registry-card"><div class="lesson-heading"><h4>${esc(skill.name || skill.id)}</h4>${badge('', `v${skill.version ?? 'not recorded'}`)}</div><p>${esc(skill.description || 'No description supplied.')}</p>${skill.external_plugin ? `<p class="skill-runtime-status">${badge(skill.available === true ? 'verified' : 'pending', skill.available === true ? 'Installation verified' : skill.available === false ? 'Runtime unavailable' : 'Installation status not reported')}<span>This registered external skill requires the private plugin runtime; its bytes are checked before use.</span></p>` : ''}<dl class="lesson-meta"><dt>Skill ID</dt><dd class="mono">${esc(skill.id)}</dd><dt>Roles</dt><dd>${esc(asArray(skill.roles).map(words).join(', ') || 'Not recorded')}</dd><dt>Origin</dt><dd>${esc(textValue(skill.origin))}</dd><dt>SHA-256</dt><dd class="mono">${esc(skill.sha256 || 'Not recorded')}</dd></dl></article>`).join('')}</div>` : '<div class="state-placeholder">No scientific skills are registered in this service.</div>';
  } catch (error) {
    $('skills-count').textContent = '—';
    $('skill-registry').innerHTML = '<div class="state-placeholder">The scientific skill registry is unavailable from this service. Skill availability cannot be confirmed.</div>';
  } finally {$('refresh-skills').disabled = false;}
}

function allAppliedSkillReceipts(run) {
  const entries = [
    ...asArray(run?.skill_receipts),
    ...asArray(run?.research_briefs).flatMap(item => asArray(item.skill_receipts).map(receipt => ({...receipt, operation_id: receipt.operation_id || item.operation_id || item.id}))),
    ...asArray(run?.sequence_discoveries).flatMap(item => asArray(item.skill_receipts).map(receipt => ({...receipt, operation_id: receipt.operation_id || item.operation_id || item.id})))
  ];
  const seen = new Set();
  return entries.filter(receipt => {
    const key = [receipt.operation_id, receipt.skill_id, receipt.role, receipt.version, receipt.sha256].join(':');
    if (seen.has(key)) return false;
    seen.add(key); return true;
  }).map(receipt => {
    const pinned = asArray(state.skillCatalog).find(skill => skill.id === receipt.skill_id && skill.version === receipt.version && skill.sha256 === receipt.sha256);
    return {...receipt, origin: receipt.origin || pinned?.origin || 'Source not recorded for this exact instruction version', source_url: receipt.source_url || pinned?.source_url || pinned?.provenance?.source_url, source_path: receipt.source_path || pinned?.path};
  });
}

function appliedSkillGroups(receipts) {
  const groups = new Map();
  for (const receipt of receipts) {
    const key = [receipt.skill_id, receipt.version, receipt.sha256].join(':');
    if (!groups.has(key)) groups.set(key, {...receipt, roles: [], operations: new Set(), count: 0});
    const item = groups.get(key); item.count++;
    if (!item.roles.includes(receipt.role)) item.roles.push(receipt.role);
    if (receipt.operation_id) item.operations.add(receipt.operation_id);
  }
  return [...groups.values()].sort((a,b) => Number(/^Team TBD(?::|-authored)/.test(a.origin)) - Number(/^Team TBD(?::|-authored)/.test(b.origin)) || String(a.name || a.skill_id).localeCompare(String(b.name || b.skill_id)));
}

function appliedSkillCard(skill) {
  const local = /^Team TBD(?::|-authored)/.test(skill.origin), sourceUrl = safeUrl(skill.source_url);
  return `<article class="applied-skill-card"><div><span class="step-label">${local ? 'TEAM TBD WORKFLOW' : /^(Installed |OpenAI-authored installed )/.test(skill.origin) ? 'INSTALLED ATTRIBUTED SKILL' : 'RECORDED INSTRUCTION SOURCE'}</span>${badge('', (/^\d/.test(String(skill.version)) ? `v${skill.version}` : skill.version || 'Version not recorded'))}</div><h4>${esc(skill.name || skill.skill_id)}</h4><p class="skill-source">${esc(skill.origin)}</p><p><strong>Loaded for</strong> ${esc(skill.roles.map(roleLabel).join(', '))}</p><p class="small muted">${skill.count} ${skill.count === 1 ? 'load receipt' : 'load receipts'} · ${skill.operations.size} ${skill.operations.size === 1 ? 'operation' : 'operations'}</p>${sourceUrl ? `<a href="${esc(sourceUrl)}" target="_blank" rel="noopener" class="evidence-link">Source reference ↗</a>` : ''}<details><summary>Exact instruction fingerprint</summary><code>${esc(skill.sha256 || 'Not recorded')}</code>${skill.source_path ? `<p>Instruction path: ${esc(skill.source_path)}</p>` : ''}</details></article>`;
}

function renderSkillReceipts(run = null) {
  const receipts = allAppliedSkillReceipts(run);
  $('skill-receipt-count').textContent = String(receipts.length);
  if (!changed('skillReceipts', [run?.id, receipts, run?.mode, state.capabilities?.rosalind?.model])) return;
  const groups = appliedSkillGroups(receipts), local = groups.filter(skill => /^Team TBD(?::|-authored)/.test(skill.origin)), attributed = groups.filter(skill => !/^Team TBD(?::|-authored)/.test(skill.origin));
  const returned = [...new Set([...asArray(run?.decisions).flatMap(item => asArray(item.metadata?.returned_models)), ...asArray(run?.actions).flatMap(item => asArray(item.provider_metadata?.returned_models))])];
  const model = returned.length ? `Returned model: ${returned.join(', ')}.` : `Configured model: ${modelName(state.capabilities?.rosalind)}; returned identity is recorded separately.`;
  $('applied-skills-context').textContent = `${model} ${receipts.length ? `${groups.length} exact instruction versions loaded across ${receipts.length} receipts.` : 'No applied instruction receipts have been recorded yet.'} Team TBD authors its workflow guidance; installed skills retain their own attribution. Loading a skill does not establish GPT-Rosalind model access, a successful model call or a BioNeMo prediction.`;
  $('applied-skills-cards').innerHTML = receipts.length ? `${attributed.length ? `<div class="applied-skill-grid">${attributed.map(appliedSkillCard).join('')}</div>` : '<p class="small muted">No separately attributed installed skill has a recorded load in this investigation yet.</p>'}${local.length ? `<details class="local-skill-group"><summary>${local.length} Team TBD scientific workflow versions · inspect names and roles</summary><div class="applied-skill-grid">${local.map(appliedSkillCard).join('')}</div></details>` : ''}` : '<div class="state-placeholder">The registry lists instruction definitions. Only actual load receipts appear here.</div>';
  $('skill-receipts').innerHTML = receipts.length ? `<div class="data-table-wrap"><table class="data-table skill-receipt-table"><thead><tr><th scope="col">Applied instruction</th><th scope="col">Source</th><th scope="col">Role</th><th scope="col">Operation / receipt</th><th scope="col">Loaded at</th><th scope="col">Pinned SHA-256</th></tr></thead><tbody>${receipts.map(receipt => `<tr><td><strong>${esc(receipt.name || receipt.skill_id)}</strong><small>v${esc(receipt.version)} · ${esc(receipt.skill_id)}</small></td><td>${esc(receipt.origin)}</td><td>${esc(roleLabel(receipt.role))}</td><td class="mono">${esc(receipt.operation_id || 'Not recorded')}<small>${esc(receipt.id || receipt.purpose || '')}</small></td><td>${esc(prettyDate(receipt.loaded_at))}</td><td class="mono">${esc(receipt.sha256)}</td></tr>`).join('')}</tbody></table></div>` : `<div class="state-placeholder">${run ? 'No skill-load receipts have been recorded in this investigation.' : 'No investigation selected. Only persisted skill-load receipts will appear here.'}</div>`;
}

async function openRun(id, scroll = false) {
  clearTimeout(state.poll);
  const epoch = ++state.epoch;
  try {
    const run = await api(`/api/runs/${encodeURIComponent(id)}`);
    if (epoch !== state.epoch) return;
    state.version = null;
    state.signatures = Object.fromEntries(Object.entries(state.signatures).filter(([key]) => key === 'capabilities'));
    state.run = run.run || run;
    resetForms();
    renderRun();
    switchTab(state.run.decisions?.length ? 'decision' : 'workproducts');
    $('architecture').open = true;
    refreshHistory();
    try {localStorage.setItem('rosalind-last-run', id);} catch {}
    try {const url = new URL(location.href); url.searchParams.set('run', id); history.replaceState(null, '', url);} catch {}
    if (scroll) $('live-overview').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'});
    schedulePoll();
  } catch (error) {toast(error.message, true);}
}

function schedulePoll() {
  clearTimeout(state.poll);
  if (!state.run) return;
  state.poll = setTimeout(pollRun, isActive(state.run) ? 1000 : 5000);
}

async function pollRun() {
  if (!state.run) return;
  const id = state.run.id, epoch = state.epoch;
  try {
    const result = await api(`/api/runs/${encodeURIComponent(id)}`);
    if (epoch !== state.epoch) return;
    const run = result.run || result;
    const oldStatus = state.run.status;
    state.run = run;
    state.pollingErrors = 0;
    renderRun();
    if (oldStatus !== run.status) {refreshHistory(); refreshHealth();}
  } catch (error) {
    if (epoch !== state.epoch) return;
    state.pollingErrors++;
    $('run-status-detail').textContent = 'Connection interrupted. Reconnecting; the last confirmed state is shown.';
    $('service-status').innerHTML = '<span class="status-dot error"></span> Reconnecting';
    $('run-signal').className = 'run-signal';
    if (state.pollingErrors === 1) toast(`Progress connection interrupted: ${error.message}`, true);
  }
  if (epoch === state.epoch) schedulePoll();
}

async function refreshSynthesisEligibility(run) {
  const button = $('continue-synthesis');
  button.hidden = true;
  if (run.mode !== 'live' || !['failed', 'budget_exhausted'].includes(run.status) || asArray(run.decisions).length) return;
  const key = `${run.id}:${run.operation?.id}:${run.status}`;
  if (!state.synthesisEligibility.has(key)) {
    state.synthesisEligibility.set(key, null);
    try {
      const result = await api(`/api/runs/${encodeURIComponent(run.id)}/synthesis-checkpoint`);
      state.synthesisEligibility.set(key, result);
    } catch { state.synthesisEligibility.set(key, {eligible: false}); }
  }
  if (!state.run || `${state.run.id}:${state.run.operation?.id}:${state.run.status}` !== key) return;
  const eligibility = state.synthesisEligibility.get(key);
  button.hidden = eligibility?.eligible !== true;
  button.disabled = state.busy;
  button.title = eligibility?.eligible ? 'Start a new synthesis and review operation using the seven verified specialist handoffs. The failed request stays recorded.' : '';
}

function renderRun() {
  const run = state.run;
  if (!run) return;
  $('empty-state').hidden = true;
  $('main').classList.add('has-run');
  renderLiveOverview(run);
  $('run-workspace').hidden = false;
  $('run-progress').hidden = false;
  $('run-mode-badge').textContent = run.mode === 'live' ? 'Live investigation' : 'Offline walkthrough · no model calls';
  $('run-status-title').textContent = ({completed: 'Investigation complete', running: 'Investigation in progress', queued: 'Investigation queued', blocked: 'Investigation needs an input', failed: 'Investigation stopped with an error', cancelled: 'Investigation cancelled', canceled: 'Investigation cancelled'})[run.status] || `Investigation ${words(run.status)}`;
  $('run-status-detail').textContent = activityHeadline(run);
  $('run-signal').className = `run-signal ${isActive(run) ? 'running' : esc(run.status)}`;
  $('run-id').textContent = run.id;
  $('run-id').title = run.id;
  $('cancel-run').hidden = !isActive(run);
  $('resume-run').hidden = !['failed', 'blocked', 'cancelled', 'canceled', 'paused', 'interrupted', 'budget_exhausted'].includes(run.status) || asArray(run.actions).some(a => ['unknown', 'submitting'].includes(a.state) || (a.state === 'failed' && a.id.startsWith(run.operation?.id || '')));
  refreshSynthesisEligibility(run);
  const runPath = `/api/runs/${encodeURIComponent(run.id)}`;
  $('export-json').href = `${runPath}/export.json`;
  $('export-report').href = `${runPath}/report.md`;
  $('export-json').download = `${run.id}.json`;
  $('run-error').hidden = !run.error;
  $('run-error').textContent = run.error ? textValue(run.error) : '';
  $('pinned-hypothesis').textContent = run.hypothesis?.text || '';
  $('pinned-source').textContent = run.hypothesis?.source_name || 'Source not recorded';
  const hash = run.hypothesis?.sha256 || '';
  $('pinned-hash').textContent = hash ? `sha256:${hash.slice(0, 18)}…` : 'Not yet recorded';
  $('pinned-hash').title = hash;
  $('pinned-time').textContent = prettyDate(run.created_at);
  renderTimeline(run.events || []);
  renderArchitecture(run);
  renderWorkProducts(run.handoffs || []);
  renderStageEvaluations(run.stage_evaluations || []);
  renderSkillReceipts(run);
  renderUsage(run);
  renderEvidence(run.evidence || []);
  const decisions = run.decisions || [];
  const previousLatest = state.signatures.latestVersion;
  const latest = decisions.at(-1)?.version;
  if (state.version == null || String(state.version) === String(previousLatest)) state.version = latest ?? null;
  state.signatures.latestVersion = latest;
  $('decision-count').textContent = String(decisions.length);
  if (changed('versions', [decisions.map(d => d.version), state.version])) {
    $('decision-version').innerHTML = decisions.length ? decisions.map(d => `<option value="${esc(d.version)}" ${String(d.version) === String(state.version) ? 'selected' : ''}>Version ${esc(d.version)}${d === decisions.at(-1) ? ' · latest' : ''}</option>`).join('') : '<option>No decision yet</option>';
    $('decision-version').disabled = !decisions.length;
  }
  renderDecision(selectedDecision());
  setFormsEnabled(!isActive(run));
}

function renderUsage(run) {
  const usage = run.usage || {};
  const tokens = Number(usage.input_tokens || 0) + Number(usage.output_tokens || 0);
  const returnedModels = [...new Set([...(run.decisions || []).flatMap(d => d.metadata?.returned_models || []), ...(run.actions || []).flatMap(a => a.provider_metadata?.returned_models || [])])];
  const activeLive = run.mode === 'live' && isActive(run);
  const dispatched = new Set(asArray(run.events).filter(e => e.type === 'model' && /^Model request \d+ dispatched$/.test(e.title || '')).map((e, index) => e.id || `event-${index}`)).size;
  const responses = new Set(asArray(run.events).filter(e => e.type === 'model' && /^Model response \d+ received$/.test(e.title || '')).map((e, index) => e.id || `event-${index}`)).size;
  const callSummary = activeLive && (responses || dispatched) ? `<span><strong>${responses}</strong> model responses recorded</span><span><strong>${dispatched}</strong> model dispatches recorded in trail</span><span><strong>${esc(usage.model_calls ?? 0)}</strong> model calls in settled receipts</span>` : `<span><strong>${esc(usage.model_calls ?? 0)}</strong> model calls</span>`;
  $('usage').innerHTML = `${callSummary}<span><strong>${esc(usage.tool_calls ?? 0)}</strong> tool calls</span><span><strong>${esc(tokens)}</strong> tokens in settled receipts</span>${activeLive ? '<span class="usage-pending">Current operation tokens pending final receipt; a dispatch does not prove successful completion.</span>' : ''}${returnedModels.length ? `<span>Returned model: <strong>${esc(returnedModels.join(', '))}</strong></span>` : run.mode === 'live' ? '<span>No returned model identity in settled receipts yet</span>' : ''}`;
}

function renderTimeline(events) {
  if (!changed('events', [events, state.showAllEvents])) return;
  const nearBottom = $('timeline').scrollHeight - $('timeline').scrollTop - $('timeline').clientHeight < 70;
  const visibleEvents = state.showAllEvents ? events : events.slice(-12);
  $('event-count').textContent = `${events.length} events${!state.showAllEvents && events.length > 12 ? ' · latest 12' : ''}`;
  $('toggle-trail').hidden = events.length <= 12;
  $('toggle-trail').textContent = state.showAllEvents ? 'Show recent activity only' : `Show full trail (${events.length} events)`;
  $('timeline').innerHTML = events.length ? visibleEvents.map(e => `<li class="timeline-event ${esc(e.status || '')}"><div class="event-heading"><span class="event-title">${esc(e.title || words(e.type))}</span><time class="event-time" datetime="${esc(e.time)}">${esc(prettyDate(e.time, {hour: '2-digit', minute: '2-digit', second: '2-digit'}))}</time></div><p class="event-detail">${esc(typeof e.detail === 'object' ? textValue(e.detail) : e.detail || '')}</p>${e.agent ? `<span class="agent-label">${esc(words(e.agent))}</span>` : ''}</li>`).join('') : '<li class="event-detail">Waiting for the first persisted event…</li>';
  if (nearBottom) $('timeline').scrollTop = $('timeline').scrollHeight;
}

function renderArchitecture(run = null) {
  const summaryBrief = !isActive(run) ? selectedResearchBrief(asArray(run?.decisions).at(-1)) : null;
  if (!changed('architecture', [run?.id, run?.status, run?.mode, run?.operation?.id, run?.events, run?.handoffs, summaryBrief?.id])) return;
  const order = ['bioinformatician','statistician','clinical_scientist','clinical_pharmacologist','molecular_scientist','translational_scientist','assay_scientist','coordinator','reviewer'];
  const roles = order.map(id => roleActivity(run, architectureRoles.find(role => role.id === id)));
  const recorded = roles.filter(item => item.events.length || item.products.length).length;
  $('architecture-roles').innerHTML = roles.map((item,index) => {
    const {role,latest,event,status,statusKey,events,products,reused,interpretation,sequenceDiscovery} = item;
    const recipients = latest?.recipient || run?.process_contract?.roles?.find(r => r.id === role.id)?.recipients || run?.process_contract?.additional_routes?.[role.id] || [];
    const plainSummary = latest && asArray(summaryBrief?.content?.role_summaries).find(summary => roleKey(summary.role) === role.id);
    const result = plainSummary?.what_found || latest?.result || event?.detail || role.purpose;
    return `<article class="architecture-role role-${statusKey || 'waiting'}"><div class="role-heading"><span class="role-symbol" aria-hidden="true">${statusKey === 'running' ? '<span class="agent-spinner"></span>' : statusKey === 'completed' ? '✓' : statusKey === 'blocked' ? '◇' : String(index+1).padStart(2,'0')}</span>${badge(statusKey,status)}</div><h3>${esc(role.label)}</h3><p class="role-current-work">${esc(excerpt(result,230))}</p>${plainSummary ? `<p class="role-summary-source">Plain-language interpretation · original handoff below</p>` : ''}${asArray(recipients).length ? `<div class="role-route"><span>${latest ? 'Handed off →' : 'Planned route →'}</span>${esc(asArray(recipients).map(roleLabel).join(', '))}</div>` : ''}<div class="role-observation">${events.length || products.length ? `<strong>${events.length} events · ${products.length} work products</strong>${reused ? `<span class="no-call-note">${sequenceDiscovery ? 'Original scientific handoff + sequence-discovery activity' : interpretation ? 'Original scientific handoff + interpretation activity' : 'Prior accepted handoff · no new model call'}</span>` : latest?.model_called === false ? '<span class="no-call-note">Prerequisite check only · no model call</span>' : ''}${latest ? `<button class="evidence-link" data-show-handoff="${esc(latest.id)}">Rationale, evidence &amp; limitations ↗</button>` : `<span>${esc(event?.title || 'Recorded work in progress')}</span>`}` : '<span>Waiting for recorded work; no activity is implied.</span>'}</div></article>`;
  }).join('');
  $('architecture-status').textContent = run ? `${recorded}/9 roles recorded · ${asArray(run.handoffs).length} handoffs` : '9 intended roles · no run selected';
  $('architecture-note').textContent = run?.operation?.kind === 'sequence_discovery' ? 'The molecular specialist and reviewer are finding and qualifying sequence inputs. Earlier scientific handoffs stay preserved; this operation does not rerun all specialists or submit a NVIDIA prediction.' : run?.operation?.kind === 'research_brief' ? 'The accepted scientific handoffs are preserved as source work. Coordinator and reviewer activity here writes and checks a separate explanation; it does not rerun all specialists or issue a new scientific decision.' : run?.operation?.kind === 'synthesis_continuation' ? 'The seven specialist handoffs retain their original provenance. This new operation runs synthesis and independent review; reused work is labeled and does not count as a new specialist call.' : run?.mode === 'live' ? 'Live status comes from actual agent events. Read each accepted work product’s scientific rationale, evidence and limitations. Blocked branches remain visible and do not stop unrelated qualified work.' : run ? 'Explicit offline walkthrough. Recorded stages do not represent model calls.' : 'Submit your own hypothesis to start the team. Roles remain inactive until work is recorded.';
}

function renderStageEvaluations(evaluations) {
  $('stage-evaluation-count').textContent = `${evaluations.length} recorded ${evaluations.length === 1 ? 'evaluation' : 'evaluations'}`;
  if (!changed('stageEvaluations', [evaluations,state.showAllEvaluations])) return;
  $('toggle-evaluations').hidden = evaluations.length <= 5;
  $('toggle-evaluations').textContent = state.showAllEvaluations ? 'Show latest evaluations only' : `Show all ${evaluations.length} stage evaluations`;
  const accepted = evaluations.filter(e => e.verdict === 'accepted').length;
  const rejected = evaluations.filter(e => e.verdict === 'rejected').length;
  const blocked = evaluations.filter(e => e.result_status === 'blocked').length;
  const repair = evaluations.filter(e => e.repair_allowed === true).length;
  $('stage-evaluation-summary').innerHTML = evaluations.length ? `<div class="stage-summary"><span>${accepted} contracts accepted</span><span>${rejected} rejected attempts</span><span>${blocked} blocked results</span><span>${repair} attempts permitted a repair</span></div>` : '';
  const openIds = new Set([...document.querySelectorAll('[data-stage-evaluation][open]')].map(el => el.dataset.stageEvaluation));
  $('stage-evaluation-list').innerHTML = evaluations.length ? (state.showAllEvaluations ? [...evaluations].reverse() : evaluations.slice(-5).reverse()).map((evaluation, index) => {
    const id = evaluation.id || `evaluation-${index}`;
    const roleId = String(evaluation.stage || '').startsWith('handoff:') ? evaluation.stage.slice(8) : null;
    const role = architectureRoles.find(r => r.id === roleId);
    const label = roleId ? `${role?.label || words(roleId)} handoff` : words(evaluation.stage || 'Recorded boundary');
    const checks = asArray(evaluation.checks);
    const passed = checks.filter(check => check.passed === true).length;
    const verdict = evaluation.verdict === 'accepted' ? badge('', 'Contract accepted') : evaluation.verdict === 'rejected' ? badge('failed', 'Contract rejected') : badge('', words(evaluation.verdict));
    return `<details class="stage-evaluation-card" data-stage-evaluation="${esc(id)}" ${openIds.has(String(id)) ? 'open' : ''}><summary><div><strong>${esc(label)}</strong><small>${evaluation.attempt != null ? `Attempt ${esc(evaluation.attempt)} · ` : ''}${passed}/${checks.length} checks passed · ${esc(prettyDate(evaluation.created_at))}</small></div><div class="stage-verdicts">${verdict}${evaluation.result_status ? badge(/blocked|failed|error/.test(evaluation.result_status) ? evaluation.result_status : '', `Result: ${words(evaluation.result_status)}`) : ''}${evaluation.repair_allowed === true ? badge('pending', 'Repair permitted') : ''}</div><span class="evidence-chevron" aria-hidden="true">›</span></summary><div class="stage-evaluation-body"><p>${esc(evaluation.reason || 'No reason recorded.')}</p><ul class="stage-check-list">${checks.map(check => `<li><span class="stage-check-state ${check.passed === true ? 'passed' : check.passed === false ? 'failed' : ''}">${check.passed === true ? 'Pass' : check.passed === false ? 'Fail' : 'Unrecorded'}</span><div><strong>${esc(words(check.id || 'Check'))}</strong><p>${esc(check.detail || '')}</p></div></li>`).join('')}</ul><dl class="lesson-meta"><dt>Operation</dt><dd class="mono">${esc(evaluation.operation_id || 'Not recorded')}</dd><dt>Receipt</dt><dd class="mono">${esc(id)}</dd><dt>Contract hash</dt><dd class="mono">${esc(evaluation.process_contract_sha256 || 'Not recorded')}</dd><dt>Subject hash</dt><dd class="mono">${esc(evaluation.subject_sha256 || 'Not recorded')}</dd><dt>Receipt hash</dt><dd class="mono">${esc(evaluation.sha256 || 'Not recorded')}</dd></dl><p class="stage-scientific-note">Scientific validity is not established by these software checks.${evaluation.repair_allowed === true ? ' Repair was permitted for this attempt; subsequent receipts show whether it happened.' : ''}</p></div></details>`;
  }).join('') : '<div class="state-placeholder">No stage evaluations have been recorded in this run. No stage acceptance is inferred from a planned role or a running event.</div>';
}

function renderWorkProducts(handoffs) {
  $('work-products-count').textContent = String(handoffs.length);
  if (!changed('workproducts', handoffs)) return;
  const openIds = new Set([...document.querySelectorAll('[data-work-product][open]')].map(el => el.dataset.workProduct));
  $('work-products-list').innerHTML = handoffs.length ? handoffs.map((handoff, index) => {
    const id = handoff.id || `handoff-${index + 1}`;
    const role = architectureRoles.find(r => [r.id, ...(r.aliases || [])].includes(roleKey(handoff.role || handoff.sender)));
    const sender = role?.label || words(handoff.role || handoff.sender || 'Unspecified sender');
    const recipient = asArray(handoff.recipient).map(value => architectureRoles.find(r => [r.id, ...(r.aliases || [])].includes(roleKey(value)))?.label || words(value)).join(', ') || 'Unspecified recipient';
    const claims = asArray(handoff.claims), limitations = asArray(handoff.limitations);
    return `<details class="work-product-card card" data-work-product="${esc(id)}" ${openIds.has(String(id)) || index === handoffs.length - 1 ? 'open' : ''}><summary><span class="work-product-index">${String(index + 1).padStart(2, '0')}</span><div><strong>${esc(sender)} <span aria-hidden="true">→</span> ${esc(recipient)}</strong><small>${esc(id)}${handoff.case_id ? ` · ${esc(handoff.case_id)}` : ''}</small></div>${badge(handoff.result_status || 'recorded')}<span class="evidence-chevron" aria-hidden="true">›</span></summary><div class="work-product-body">${handoff.acceptance_evaluation_id ? `<button class="evidence-link" data-show-evaluation="${esc(handoff.acceptance_evaluation_id)}">Inspect this handoff’s stage evaluation ↗</button>` : ''}${handoff.model_called === false ? '<div class="notice">This work product did not call a model. Its recorded status and limitations explain the gate.</div>' : ''}<div class="work-product-question"><span class="step-label">ASSIGNED QUESTION</span><p>${esc(textValue(handoff.question))}</p></div><div class="work-product-grid"><section><h4>Method</h4><p class="long-text">${esc(textValue(handoff.method))}</p></section><section><h4>Decision it could change</h4><p class="long-text">${esc(textValue(handoff.decision_it_could_change))}</p></section></div>${handoff.result || handoff.summary ? `<section class="work-product-result"><h4>Recorded result</h4><p class="long-text">${esc(textValue(handoff.result || handoff.summary))}</p></section>` : ''}<section class="work-product-inputs"><h4>Pinned input versions</h4>${handoff.input_versions ? valueTable(handoff.input_versions) : '<p class="small muted">No input versions were included in this work product.</p>'}</section>${asArray(handoff.skill_receipt_ids).length ? `<section class="work-product-inputs"><h4>Recorded scientific skill provenance</h4>${valueTable(handoff.skill_versions)}<p class="small mono long-text">${esc(handoff.skill_receipt_ids.join(' · '))}</p><button class="evidence-link" data-show-skills>Inspect loaded skill receipts ↗</button></section>` : ''}${claims.length ? `<section class="work-product-claims"><h4>Claims in this handoff</h4><ul class="claim-list">${claims.map(claim => `<li><span class="claim-kind">${esc(words(claim.kind || 'Unspecified'))}</span>${esc(claim.text || textValue(claim))}<div class="claim-links">${asArray(claim.evidence_ids).map(evidenceId => `<button class="evidence-link" data-show-evidence="${esc(evidenceId)}">${esc(evidenceId)} ↗</button>`).join('')}</div></li>`).join('')}</ul></section>` : ''}${limitations.length ? `<div class="limitation-box"><h4>Handoff limitations</h4><ul>${limitations.map(l => `<li>${esc(textValue(l))}</li>`).join('')}</ul></div>` : ''}</div></details>`;
  }).join('') : '<div class="state-placeholder">No structured handoffs have been recorded in this run. Planned roles alone do not count as completed agent work.</div>';
}

function valueTable(values) {
  if (values == null || (Array.isArray(values) && !values.length) || (typeof values === 'object' && !Object.keys(values).length)) return '';
  if (Array.isArray(values) && values.every(v => v && typeof v === 'object' && !Array.isArray(v))) {
    const keys = [...new Set(values.flatMap(v => Object.keys(v)))];
    return `<div class="data-table-wrap"><table class="data-table"><thead><tr>${keys.map(k => `<th scope="col">${esc(words(k))}</th>`).join('')}</tr></thead><tbody>${values.map(v => `<tr>${keys.map(k => `<td>${esc(textValue(v[k]))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  const pairs = typeof values === 'object' ? Object.entries(values) : [['Value', values]];
  return `<div class="data-table-wrap"><table class="data-table"><tbody>${pairs.map(([key, value]) => `<tr><th scope="row">${esc(words(key))}</th><td class="long-text">${esc(textValue(value))}</td></tr>`).join('')}</tbody></table></div>`;
}

function renderEvidence(evidence) {
  $('evidence-count').textContent = String(evidence.length);
  $('evidence-summary').textContent = evidence.length ? `${evidence.length} pinned ${evidence.length === 1 ? 'record' : 'records'}` : '';
  if (!changed('evidence', [evidence, state.run?.required_analysis_operations])) return;
  const openIds = new Set([...document.querySelectorAll('.evidence-row[open]')].map(el => el.dataset.evidence));
  $('evidence-list').innerHTML = evidence.length ? evidence.map((e, i) => {
    const source = e.source || {}, url = safeUrl(source.url), sourceName = source.name || 'Source not recorded';
    const analysisArtifacts = asArray(state.run?.required_analysis_operations).filter(op => op.evidence_id === e.id).flatMap(op => asArray(op.artifacts));
    const downloads = analysisArtifacts.map(a => {const link = safeUrl(a.url); return link ? `<a href="${esc(link)}" download>${esc(a.name)} ↗</a>` : '';}).join('');
    return `<details class="evidence-row" data-evidence="${esc(e.id)}" ${openIds.has(String(e.id)) ? 'open' : ''}><summary><span class="evidence-index">${String(i + 1).padStart(2, '0')}</span><div class="evidence-summary"><strong>${esc(e.title || e.id)}</strong><small>${esc(e.id)} · ${esc(sourceName)}</small></div>${badge('', words(e.kind || 'Evidence'))}<span class="evidence-chevron" aria-hidden="true">›</span></summary><div class="evidence-body"><p class="long-text">${esc(e.summary || '')}</p>${downloads ? `<div class="artifact-links">${downloads}</div>` : ''}${valueTable(e.values)}<div class="evidence-locator"><strong>SOURCE LOCATOR</strong>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(sourceName)} ↗</a>` : esc(sourceName)}<div class="long-text">${esc(textValue(source.locator || 'No locator supplied'))}</div><span class="hash mono">${source.sha256 ? `sha256:${esc(source.sha256)}` : 'Source fingerprint not provided'}</span></div></div></details>`;
  }).join('') : '<div class="state-placeholder">Accepted evidence will appear here as sources are qualified.</div>';
}

function renderHypothesisGovernance(decision) {
  const governance = decision.governance;
  if (!governance) return decision.prior_governance ? '<div class="notice">New modeling evidence is available. The earlier hypothesis assessment has not been reassessed against it.</div>' : '';
  const hypotheses = asArray(governance.hypotheses);
  const live = state.run?.governance_state?.decision_version === decision.version ? state.run.governance_state : null;
  const labels = {possible: 'Possible', probable: 'Probable', clearly_ruled_out: 'Clearly ruled out'};
  const reason = live?.reason || governance.continuation_reason || '';
  const next = live?.next_analysis_id || governance.next_action_id;
  const actionLabel = live?.status === 'queued' ? 'Next test queued' : live?.status === 'running' ? 'Testing the next hypothesis' : live?.status === 'stopped' ? 'Investigation stopped' : governance.stop_reason === 'continue' ? 'Next test selected' : 'Current stopping point';
  const links = (ids) => asArray(ids).map(id => `<button class="evidence-link" data-show-evidence="${esc(id)}">${esc(id)} ↗</button>`).join(' ');
  return `<section class="hypothesis-governance" aria-label="Hypothesis testing and next actions"><div class="card governance-summary"><span class="step-label">HYPOTHESIS TESTING</span><h3>${esc(actionLabel)}${next ? ` · ${esc(next)}` : ''}</h3><p>${esc(reason)}</p><p class="small muted">${esc(words(live?.stop_reason || governance.stop_reason))} · States are scoped scientific assessments, not numerical probabilities. Unresolved hypotheses remain visible.</p></div><div class="hypothesis-ledger">${hypotheses.map(h => `<article class="card hypothesis-card-record"><div class="hypothesis-record-heading"><span class="mono">${esc(h.hypothesis_id)}</span>${badge(h.status === 'probable' ? 'success' : h.status === 'clearly_ruled_out' ? 'failed' : 'pending', labels[h.status] || words(h.status))}</div><h4>${esc(h.statement)}</h4><p class="small muted">${h.origin === 'user' ? 'User hypothesis' : 'Agent-generated alternative'} · ${esc(h.scope_type || 'biological')} · ${esc(h.scope)}</p><p>${esc(h.rationale)}</p><div class="hypothesis-evidence"><strong>Support</strong>${links(h.supporting_evidence_ids) || '<span class="small muted">No qualifying support cited</span>'}<strong>Counterevidence</strong>${links(h.contradicting_evidence_ids) || '<span class="small muted">No qualifying contradiction cited</span>'}</div>${h.falsification_test ? `<details><summary>Discriminating test and result</summary><p>${esc(h.falsification_test)}</p><p>${esc(h.falsification_result)}</p>${links(h.test_evidence_ids)}</details>` : ''}${asArray(h.next_analysis_ids).length ? `<p class="hypothesis-next"><strong>Next tests:</strong> ${esc(h.next_analysis_ids.join(', '))}</p>` : ''}${h.blocker ? `<p class="hypothesis-blocker"><strong>Unresolved requirement:</strong> ${esc(h.blocker)}</p>` : ''}</article>`).join('')}</div></section>`;
}

function renderDecision(decision) {
  renderFindingsOverview(decision); renderResearchBrief(decision); renderSequenceDiscovery(decision); renderFollowups(decision); refreshFollowups(decision); updateStructureOptions();
  if (!changed('decision', [decision, state.run?.mode, state.run?.governance_state])) return;
  $('feedback-form').hidden = !decision;
  $('lesson-form').hidden = !decision;
  $('outcome-form').hidden = !decision?.rd_handoff;
  $('molecular-preparation').hidden = !decision;
  $('manual-modeling').hidden = !decision?.rd_handoff;
  if (!decision) {
    $('decision-content').innerHTML = '<div class="state-placeholder">The investigation has not issued a decision yet.</div>';
    $('handoff-content').innerHTML = '<div class="state-placeholder">The R&amp;D handoff will be assembled from accepted evidence.</div>';
    return;
  }
  const limitations = asArray(decision.limitations);
  const claims = asArray(decision.claims);
  const alternatives = asArray(decision.alternatives);
  const experiment = decision.next_experiment;
  const changes = asArray(decision.changes);
  $('decision-content').innerHTML = `${state.run.mode !== 'live' ? '<div class="notice">Offline walkthrough: this interpretation is scripted from the pinned case evidence. No model inference was performed.</div>' : ''}<div class="decision-hero">${badge('', `DECISION V${decision.version}`)}<h3>${esc(decision.summary || 'Evidence assessment')}</h3><p>${esc(textValue(decision.assessment))}</p></div>${renderHypothesisGovernance(decision)}${changes.length ? `<div class="change-list"><h4>What changed in this version</h4><ul>${changes.map(c => `<li>${esc(typeof c === 'object' ? c.description || c.summary || textValue(c) : c)}</li>`).join('')}</ul></div>` : ''}<div class="decision-grid"><section class="card decision-block"><h4>Evidence-linked claims</h4>${claims.length ? `<ul class="claim-list">${claims.map(c => `<li><span class="claim-kind">${esc(words(c.kind || 'Inference'))}</span>${esc(c.text || textValue(c))}<div class="claim-links">${asArray(c.evidence_ids).map(id => `<button class="evidence-link" data-show-evidence="${esc(id)}">${esc(id)} ↗</button>`).join('')}</div></li>`).join('')}</ul>` : '<p class="small muted">No accepted claims supplied.</p>'}</section><section class="card decision-block"><h4>Competing explanations</h4>${alternatives.length ? `<ul class="detail-list">${alternatives.map(a => `<li><strong>${esc(a.title || 'Alternative explanation')}</strong>${esc(a.reason || textValue(a))}</li>`).join('')}</ul>` : '<p class="small muted">No alternatives recorded in this version.</p>'}</section></div>${limitations.length ? `<div class="limitation-box"><h4>What this evidence cannot establish</h4><ul>${limitations.map(l => `<li>${esc(textValue(l))}</li>`).join('')}</ul></div>` : ''}${experiment ? `<section class="card next-experiment"><span class="step-label">THE NEXT DISCRIMINATING OBSERVATION</span><h3>${esc(experiment.title || 'Next experiment')}</h3><p class="experiment-design">${esc(textValue(experiment.design))}</p><div class="experiment-outcomes">${[['positive', 'Supports the hypothesis'], ['negative', 'Challenges the hypothesis'], ['inconclusive', 'Remains inconclusive']].map(([key, title]) => `<div><strong>${title}</strong><p>${esc(textValue(experiment[key]))}</p></div>`).join('')}</div></section>` : ''}`;
  $('feedback-version-note').textContent = String(decision.version) === String(state.run.decisions.at(-1)?.version) ? `Reviewing decision v${decision.version}. Earlier versions remain intact.` : `Historical decision v${decision.version}. Select the latest version to submit a correction.`;
  prepareLessonForm(decision);
  renderHandoff(decision);
}

function renderHandoff(decision) {
  const handoff = decision.rd_handoff;
  if (!handoff) {$('handoff-content').innerHTML = '<div class="state-placeholder">No R&amp;D handoff was issued for this decision.</div>'; return;}
  const modeling = handoff.modeling || {}, candidates = asArray(handoff.candidates), artifacts = asArray(modeling.artifacts);
  $('handoff-content').innerHTML = `<div class="handoff-hero"><span class="handoff-icon" aria-hidden="true">⌁</span><div><span class="step-label">EVIDENCE → DESIGN</span><h3>${esc(handoff.objective || 'Research design objective')}</h3>${badge(handoff.status)}<p style="margin-top:10px">Experiment <span class="mono">${esc(handoff.experiment_id || 'Not assigned')}</span> · decision v${esc(decision.version)}</p></div></div><div class="handoff-grid"><section class="card"><h4>Reference design</h4><p class="long-text">${esc(textValue(handoff.reference))}</p></section><section class="card"><h4>BioNeMo modeling readiness</h4><div class="model-status">${badge(modeling.status)}</div><p class="long-text">${esc(modeling.reason || 'No modeling readiness assessment supplied.')}</p>${artifacts.length ? `<div class="artifact-links">${artifacts.map(a => {const url = safeUrl(typeof a === 'string' ? a : a.url || a.path); const label = typeof a === 'string' ? a : a.name || a.title || a.id || 'Model artifact'; return url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>` : `<span>${esc(textValue(a))}</span>`;}).join('')}</div>` : ''}</section></div><section class="card candidate-section"><h3>Candidate / design comparison</h3>${candidates.length ? valueTable(candidates) : '<p class="muted small">No qualified candidates are available. Missing inputs remain a visible readiness requirement.</p>'}</section>${asArray(handoff.return_requirements).length ? `<section class="card requirements"><h4>Required with returned results</h4><ul>${asArray(handoff.return_requirements).map(r => `<li>${esc(textValue(r))}</li>`).join('')}</ul></section>` : ''}`;
  if (modeling.result) $('handoff-content').insertAdjacentHTML('beforeend', `<section class="card candidate-section" style="margin-top:16px"><h3>Returned BioNeMo output</h3><p class="small muted">Provider-reported predictions and metrics. These are not experimental measurements.</p>${valueTable(modeling.result)}</section>`);
  $('outcome-experiment').value = handoff.experiment_id || '';
  $('candidate-options').innerHTML = candidates.map(c => `<option value="${esc(c.id || c.candidate_id || '')}">${esc(c.name || c.title || '')}</option>`).join('');
  const candidateIds = candidates.map(c => c.id || c.candidate_id || '');
  if (!candidateIds.includes($('outcome-candidate').value)) $('outcome-candidate').value = candidateIds.length === 1 ? candidateIds[0] : '';
  $('outcome-mode-note').textContent = !candidates.length ? 'No candidate or experimental arm has been issued yet. A qualified handoff with a registered design ID is required before results can be returned.' : state.run.mode === 'live' ? 'Results stay attached to the exact experiment and candidate. Include assay provenance, controls and quality checks.' : 'Offline return path: submitted values are test inputs, not newly validated scientific findings. Describe their origin in the notes.';
  $('modeling-mode-note').textContent = state.run.mode === 'live' ? 'Runs a real BioNeMo comparison and may incur provider charges. Exact sequences, provenance and target retention are required; the server validates scientific readiness.' : 'Live mode is required for molecular prediction. Start a live investigation and provide qualified sequences to run BioNeMo.';
}

function setFormsEnabled(enabled) {
  const decision = selectedDecision();
  const isLatest = String(decision?.version) === String(state.run?.decisions?.at(-1)?.version);
  for (const name of ['feedback-form', 'outcome-form', 'modeling-form']) {
    $(name).querySelectorAll('button[type="submit"]').forEach(b => {b.disabled = !enabled || !isLatest || state.busy || (name === 'modeling-form' && state.run?.mode !== 'live') || (name === 'outcome-form' && !decision?.rd_handoff?.candidates?.length);});
  }
  $('lesson-form').querySelector('button[type="submit"]').disabled = !enabled || state.busy || !decision || !state.lessonsAvailable;
  renderResearchBrief(decision);
  renderSequenceDiscovery(decision);
  renderFollowups(decision);
}

function resetForms() {
  ['feedback-form', 'outcome-form', 'modeling-form', 'lesson-form'].forEach(id => $(id).reset());
  state.preparedMolecularFor = null;
  state.preparedDiscoveryFor = null;
  $('sequence-fill-status').textContent = '';
  $('manual-modeling').open = false;
}

function prepareLessonForm(decision) {
  const origin = state.cases.find(c => c.id === state.run.case_id);
  $('lesson-origin-note').textContent = `Origin: ${origin?.title || words(state.run.case_id)}, immutable decision v${decision.version}. This creates a proposal for separately evaluated reuse.`;
  const previousScope = new Set([...$('lesson-scope').selectedOptions].map(o => o.value));
  const previousExcluded = new Set([...$('lesson-excluded').selectedOptions].map(o => o.value));
  previousExcluded.add(state.run.case_id);
  $('lesson-scope').innerHTML = state.cases.filter(c => c.id !== state.run.case_id).map(c => `<option value="${esc(c.id)}" ${previousScope.has(c.id) ? 'selected' : ''}>${esc(c.title)}</option>`).join('');
  $('lesson-excluded').innerHTML = state.cases.map(c => `<option value="${esc(c.id)}" ${previousExcluded.has(c.id) ? 'selected' : ''}>${esc(c.title)}${c.id === state.run.case_id ? ' · origin' : ''}</option>`).join('');
  syncLessonScope('scope');
}

function syncLessonScope(changedField) {
  const primary = changedField === 'scope' ? $('lesson-scope') : $('lesson-excluded');
  const other = changedField === 'scope' ? $('lesson-excluded') : $('lesson-scope');
  const chosen = new Set([...primary.selectedOptions].map(o => o.value));
  [...other.options].forEach(option => {if (chosen.has(option.value)) option.selected = false;});
}

async function submitLesson() {
  const decision = selectedDecision();
  if (!state.run || !decision || state.busy) return;
  const body = {origin_run_id: state.run.id, decision_version: decision.version, procedure: $('lesson-procedure').value.trim(), conditions: $('lesson-conditions').value.trim(), scope_case_ids: [...$('lesson-scope').selectedOptions].map(o => o.value), excluded_case_ids: [...$('lesson-excluded').selectedOptions].map(o => o.value), author: $('lesson-author').value.trim()};
  if (body.scope_case_ids.includes(state.run.case_id) || body.scope_case_ids.some(id => body.excluded_case_ids.includes(id))) {toast('Use a scope different from the origin and keep included and excluded cases separate.', true); return;}
  state.busy = true; updateStartButton(); setFormsEnabled(false);
  try {
    await api('/api/lessons', {method: 'POST', body: JSON.stringify(body)});
    $('lesson-form').reset(); prepareLessonForm(decision);
    toast('Provisional lesson saved. Scientist review and disjoint evaluation are still required before release.');
    await refreshLessons();
  } catch (error) {toast(error.message, true);}
  finally {state.busy = false; updateStartButton(); setFormsEnabled(!isActive(state.run));}
}

function switchTab(name, focus = false) {
  document.querySelectorAll('[data-tab]').forEach(button => {
    const selected = button.dataset.tab === name;
    button.setAttribute('aria-selected', String(selected));
    button.tabIndex = selected ? 0 : -1;
    $(`panel-${button.dataset.tab}`).hidden = !selected;
    if (selected && focus) button.focus();
  });
}

function idempotentPayload(action, body) {
  const signature = `${action}:${JSON.stringify(body)}`;
  if (!state.pendingKeys.has(signature)) state.pendingKeys.set(signature, freshKey());
  return {signature, payload: {...body, idempotency_key: state.pendingKeys.get(signature)}};
}

async function submitRun() {
  if (state.busy || !$('hypothesis').value.trim()) return;
  if (state.mode === 'live' && state.capabilities?.rosalind?.status !== 'verified') {await verifyProvider('rosalind'); return;}
  state.busy = true; updateStartButton();
  const original = $('start-run').innerHTML;
  $('start-run').textContent = 'Starting…';
  const {signature, payload} = idempotentPayload('start', {case_id: $('case-select').value, hypothesis: $('hypothesis').value, source_name: state.source, mode: state.mode});
  try {
    const result = await api('/api/runs', {method: 'POST', body: JSON.stringify(payload)});
    const run = result.run || result;
    if (!(run.id || run.run_id)) throw new Error('The service accepted the request but did not return a run ID. Retry with the same hypothesis to reconcile.');
    state.pendingKeys.delete(signature);
    await openRun(run.id || run.run_id, true);
    switchTab('workproducts');
    toast(state.mode === 'demo' ? 'Offline walkthrough started. No model calls will be made.' : 'Live investigation started. Actual model and tool activity will appear in the trail.');
  } catch (error) {toast(error.message, true);}
  finally {state.busy = false; $('start-run').innerHTML = original; updateStartButton(); if (state.run) setFormsEnabled(!isActive(state.run));}
}

async function mutateRun(action, body, onSuccess) {
  if (!state.run || state.busy) return;
  const id = state.run.id;
  const {signature, payload} = idempotentPayload(`${id}:${action}`, body);
  state.busy = true; updateStartButton(); setFormsEnabled(false);
  try {
    await api(`/api/runs/${encodeURIComponent(id)}/${action}`, {method: 'POST', body: JSON.stringify(payload)});
    state.pendingKeys.delete(signature);
    if (onSuccess) onSuccess();
    const result = await api(`/api/runs/${encodeURIComponent(id)}`);
    if (state.run?.id === id) {state.version = null; state.run = result.run || result; renderRun(); schedulePoll();}
    refreshHistory();
  } catch (error) {toast(error.message, true);}
  finally {state.busy = false; updateStartButton(); if (state.run) setFormsEnabled(!isActive(state.run));}
}

function installModelingForm() {
  $('outcome-form').insertAdjacentHTML('beforebegin', `<section id="sequence-discovery" class="card sequence-discovery" hidden><div class="brief-heading"><div><span class="step-label">AI · FIND THE MISSING MOLECULAR INPUTS</span><h3>Find target and binding-domain sequences</h3></div><button type="button" class="button primary small-button" id="discover-sequences">Find missing sequences with AI ↗</button></div><p class="small muted">The agent searches source records, checks sequence identity and scientific fit, then proposes verified inputs for this investigation. This step makes model and retrieval calls; it does not run NVIDIA inference.</p><p id="sequence-discovery-status" class="brief-status" role="status" aria-live="polite"></p><div id="sequence-discovery-content"></div><p id="sequence-fill-status" class="brief-status" role="status"></p></section><section id="molecular-preparation" class="card molecular-preparation" hidden><div class="brief-heading"><div><span class="step-label">MOLECULAR CONTEXT FROM THIS INVESTIGATION</span><h3>Understand the NVIDIA comparison</h3></div><button type="button" id="prepare-modeling" class="button secondary small-button">Prepare from this investigation ↗</button></div><p class="small muted">Use the recorded outputs, exact sequences and a model-written scientific rationale. Viewing or preparing these results makes no new NVIDIA call.</p><div id="molecular-preparation-content"></div><p id="molecular-preparation-status" class="brief-status" role="status"></p></section><details id="manual-modeling" class="manual-modeling" hidden><summary>New binding-domain comparison · provide or edit qualified inputs</summary><form id="modeling-form" class="card outcome-card"><div class="card-heading"><div><span class="step-label">QUALIFIED MOLECULAR COMPARISON</span><h3>Compare a binding-domain design</h3><p class="small muted">For a new target–binder comparison with qualified binder inputs.</p></div><span class="icon-square" aria-hidden="true">◈</span></div><p class="muted small" id="modeling-mode-note"></p><div class="form-grid"><label class="outcome-notes-label">Target amino-acid sequence<textarea id="modeling-target" rows="3" required placeholder="Exact target sequence; no placeholder sequences" spellcheck="false" autocapitalize="characters"></textarea></label><label>Reference binding-domain sequence<textarea id="modeling-reference" rows="3" required placeholder="Qualified reference sequence" spellcheck="false" autocapitalize="characters"></textarea></label><label>Candidate binding-domain sequence<textarea id="modeling-candidate" rows="3" required placeholder="Candidate sequence to compare" spellcheck="false" autocapitalize="characters"></textarea></label><label class="outcome-notes-label">Sequence source &amp; scientific qualification<textarea id="modeling-source" rows="2" required placeholder="Accession/version, design provenance and evidence qualifying this comparison"></textarea></label></div><label class="checkbox-label"><input type="checkbox" id="modeling-retained" required> I have evidence that the target is retained in this comparison.</label><div class="form-footer"><span class="small muted">Predicted binding does not establish whole-cell efficacy.</span><button class="button primary" type="submit">Run live BioNeMo <span aria-hidden="true">↗</span></button></div></form></details>`);
}

function updateProbeButtons() {
  document.querySelectorAll('[data-probe]').forEach(button => {
    button.disabled = Boolean(state.probing);
    button.textContent = state.probing === button.dataset.probe ? 'Checking…' : 'Check connection ↗';
  });
}

async function verifyProvider(provider) {
  if (state.probing) return;
  state.probing = provider;
  updateStartButton(); updateProbeButtons();
  try {
    const result = await api('/api/capabilities/probe', {method: 'POST', body: JSON.stringify({provider})});
    toast(provider === 'rosalind' && result.status === 'verified' ? `${modelName(result)} model/tool round trip passed. Select Start live investigation to investigate your hypothesis.` : result.detail ? capabilityMessage(provider, result) : result.message || 'Connection check finished. Inspect the provider status.', ['failed', 'missing'].includes(result.status));
    state.signatures.capabilities = null;
    await refreshHealth();
  } catch (error) {toast(error.message, true);}
  finally {state.probing = null; updateStartButton(); updateProbeButtons();}
}

function installEvents() {
  $('explain-results').addEventListener('click', () => requestResearchBrief());
  $('discover-sequences').addEventListener('click', requestSequenceDiscovery);
  $('prepare-modeling').addEventListener('click', () => {const brief = selectedResearchBrief(); if (brief) prepareModelingFromBrief(brief); else requestResearchBrief(true);});
  $('case-select').addEventListener('change', () => selectCase(false));
  $('load-cd19-example').addEventListener('click', loadCd19Example);
  $('live-nvidia-summary').addEventListener('click', () => {$('live-engineering-panel').open = true;});
  $('toggle-evaluations').addEventListener('click', () => {state.showAllEvaluations = !state.showAllEvaluations; renderStageEvaluations(state.run?.stage_evaluations || []);});
  $('toggle-trail').addEventListener('click', () => {state.showAllEvents = !state.showAllEvents; delete state.signatures.events; renderTimeline(state.run?.events || []);});
  $('hypothesis').addEventListener('input', () => {
    state.customHypothesis = true;
    state.source = state.fileName || state.exampleSource ? `${state.fileName || state.exampleSource} (edited in composer)` : 'User message';
    $('source-name').textContent = `Source: ${state.source}`;
    updateStartButton();
  });
  $('hypothesis-file').addEventListener('change', async (event) => {
    const file = event.target.files[0]; if (!file) return;
    if (file.size > 512000) {toast('Please choose a text or Markdown brief smaller than 500 KB.', true); event.target.value = ''; return;}
    try {
      const content = await file.text();
      if (content.length > 24000) throw new Error('This brief exceeds 24,000 characters. Import the relevant hypothesis section.');
      if (!content.trim()) throw new Error('This file is empty. Choose a brief containing your hypothesis.');
      if (content.includes('\u0000')) throw new Error('This does not appear to be a text brief. Use .md, .txt or .json.');
      $('hypothesis').value = content; state.source = file.name; state.fileName = file.name; state.exampleSource = null; state.customHypothesis = true;
      $('source-name').textContent = `Source: ${file.name}`; updateStartButton();
      toast('Brief imported. Its wording and filename will be pinned to the run.');
    } catch (error) {toast(error.message, true);}
  });
  document.querySelectorAll('[data-mode]').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));
  $('start-run').addEventListener('click', submitRun);
  $('new-investigation').addEventListener('click', () => {$('hypothesis').focus(); $('hypothesis-title').scrollIntoView({behavior: 'smooth', block: 'center'});});
  $('run-history').addEventListener('click', e => {const button = e.target.closest('[data-run]'); if (button) openRun(button.dataset.run, true);});
  $('mobile-run-select').addEventListener('change', () => {if ($('mobile-run-select').value) openRun($('mobile-run-select').value, true);});
  $('capability-list').addEventListener('click', e => {
    const b = e.target.closest('[data-probe]'); if (!b) return;
    verifyProvider(b.dataset.probe);
  });
  $('cancel-run').addEventListener('click', () => mutateRun('cancel', {}, () => toast('Cancellation requested. New work will stop; submitted provider jobs may still finish.')));
  $('resume-run').addEventListener('click', () => mutateRun('resume', {}, () => toast('Resume requested. The service will reconcile persisted work.')));
  $('continue-synthesis').addEventListener('click', () => {
    if (state.run) mutateRun('continue-synthesis', {source_operation_id: state.run.operation.id}, () => toast('New synthesis operation queued. Accepted specialist work is reused with its original provenance.'));
  });
  document.querySelectorAll('[data-tab]').forEach(b => {
    b.addEventListener('click', () => switchTab(b.dataset.tab));
    b.addEventListener('keydown', e => {
      const tabs = ['data', 'skills', 'evidence', 'workproducts', 'decision', 'handoff', 'learning'], index = tabs.indexOf(b.dataset.tab);
      let next;
      if (e.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (e.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      if (next !== undefined) {e.preventDefault(); switchTab(tabs[next], true);}
    });
  });
  $('decision-version').addEventListener('change', () => {state.version = $('decision-version').value; resetForms(); renderDecision(selectedDecision()); setFormsEnabled(!isActive(state.run));});
  $('main').addEventListener('click', e => {
    const fillSequence = e.target.closest('[data-fill-sequences]');
    if (fillSequence) {fillDiscoveredSequences(); return;}
    const useSequence = e.target.closest('[data-use-sequence-role]');
    if (useSequence) {fillDiscoveredSequences(useSequence.dataset.useSequenceRole); return;}
    const followup = e.target.closest('[data-run-followup]');
    if (followup) {runFollowup(followup.dataset.runFollowup, followup.dataset.followupVersion); return;}
    const structureLink = e.target.closest('[data-view-structure]');
    if (structureLink) {const url=structureLink.dataset.viewStructure; if (previewOptions().some(option => option.url === url)) {state.structureUserSelected=true; $('architecture').open=true; $('structure-select').value=url; loadStructurePreview(url); $('structure-preview-panel').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});} return;}
    if (e.target.closest('[data-open-findings]') || e.target.closest('[data-open-followups]')) {e.preventDefault(); switchTab('decision'); const target=e.target.closest('[data-open-followups]') ? $('recommended-followups') : $('panel-decision'); target.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'}); return;}
    const handoffLink = e.target.closest('[data-show-handoff]');
    if (handoffLink) {
      switchTab('workproducts');
      const record = [...document.querySelectorAll('[data-work-product]')].find(el => el.dataset.workProduct === handoffLink.dataset.showHandoff);
      if (record) {record.open = true; record.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'}); record.querySelector('summary').focus();} return;
    }
    const evaluationLink = e.target.closest('[data-show-evaluation]');
    if (evaluationLink) {
      state.showAllEvaluations = true; renderStageEvaluations(state.run?.stage_evaluations || []);
      const receipt = [...document.querySelectorAll('[data-stage-evaluation]')].find(el => el.dataset.stageEvaluation === evaluationLink.dataset.showEvaluation);
      if (!receipt) {toast('This evaluation receipt is not present in the selected run.', true); return;}
      switchTab('workproducts'); receipt.open = true; receipt.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center'}); receipt.querySelector('summary').focus(); return;
    }
    if (e.target.closest('[data-show-skills]')) {switchTab('skills', true); return;}
    const b = e.target.closest('[data-show-evidence]'); if (!b) return;
    const row = [...document.querySelectorAll('[data-evidence]')].find(el => el.dataset.evidence === b.dataset.showEvidence);
    if (!row) {toast('This claim references evidence that is not present in the displayed run.', true); return;}
    switchTab('evidence'); row.open = true; row.scrollIntoView({behavior: 'smooth', block: 'center'}); row.querySelector('summary').focus();
  });
  $('feedback-form').addEventListener('submit', e => {
    e.preventDefault(); const decision = selectedDecision(); if (!decision) return;
    const text = $('feedback-text').value.trim(); if (!text) return;
    mutateRun('feedback', {decision_version: decision.version, text}, () => {$('feedback-text').value = ''; toast('Correction saved against the selected version. A revised assessment will follow.');});
  });
  $('outcome-form').addEventListener('submit', e => {
    e.preventDefault(); const decision = selectedDecision(); if (!decision) return;
    const body = {decision_version: decision.version, experiment_id: $('outcome-experiment').value.trim(), candidate_id: $('outcome-candidate').value.trim(), endpoint: $('outcome-endpoint').value.trim(), value: Number($('outcome-value').value), unit: $('outcome-unit').value.trim(), notes: $('outcome-notes').value.trim()};
    if (!Number.isFinite(body.value)) {toast('Enter a finite measured value.', true); return;}
    mutateRun('outcomes', body, () => {$('outcome-form').reset(); toast('Returned result saved. The investigation will qualify it and create a new decision version.');});
  });
  $('modeling-form').addEventListener('submit', e => {
    e.preventDefault(); const decision = selectedDecision(); if (!decision || state.run.mode !== 'live') return;
    mutateRun('modeling', {decision_version: decision.version, target_sequence: $('modeling-target').value.trim(), reference_binder: $('modeling-reference').value.trim(), candidate_binder: $('modeling-candidate').value.trim(), source_note: $('modeling-source').value.trim(), target_retained: $('modeling-retained').checked}, () => {toast('BioNeMo comparison requested. Scientific gates and actual provider results appear in the trail.');});
  });
  $('lesson-scope').addEventListener('change', () => syncLessonScope('scope'));
  $('lesson-excluded').addEventListener('change', () => syncLessonScope('excluded'));
  $('lesson-form').addEventListener('submit', e => {e.preventDefault(); submitLesson();});
  $('refresh-datasets').addEventListener('click', refreshDatasets);
  $('dataset-select').addEventListener('change', () => selectDataset($('dataset-select').value));
  $('refresh-skills').addEventListener('click', refreshSkills);
  document.addEventListener('visibilitychange', () => {if (!document.hidden) {refreshHealth(); refreshHistory(); refreshLessons(); if (state.run) {clearTimeout(state.poll); pollRun();}}});
}

async function init() {
  installModelingForm(); installEvents(); installStructureControls();
  renderArchitecture();
  renderEvidence([]); renderWorkProducts([]); renderStageEvaluations([]); renderDecision(null);
  const outcomes = await Promise.allSettled([loadCases(), refreshHealth(), refreshLessons(), refreshDatasets(), refreshSkills()]);
  if (outcomes[0].status === 'rejected') {
    $('case-select').innerHTML = '<option>Evidence collections unavailable</option>';
    $('case-description').textContent = outcomes[0].reason.message;
    $('case-readiness').innerHTML = '<span class="status-dot error"></span><span>Case data could not be loaded.</span>';
    toast(outcomes[0].reason.message, true);
  }
  await refreshHistory();
  let last = new URL(location.href).searchParams.get('run');
  if (!last) {try {last = localStorage.getItem('rosalind-last-run');} catch {}}
  if (last && state.history.some(r => r.id === last)) await openRun(last);
  setInterval(() => {if (!document.hidden) {refreshHealth(); refreshHistory(); refreshLessons();}}, 15000);
}

Object.assign(state, {followupQuery:null, followupData:null, followupLoading:false, followupError:'', structureUrl:null, structureUserSelected:false, structureEpoch:0, structureData:null, structureCache:new Map(), structureRotation:{x:-.25,y:.45,zoom:1}});

function evidenceLinks(ids) {
  return asArray(ids).map(id => `<button class="evidence-link" data-show-evidence="${esc(id)}">${esc(id)} ↗</button>`).join('');
}

const discoverySequenceRoles = [
  {role:'target', label:'Target', field:'modeling-target'},
  {role:'reference_binder', label:'Reference binding domain', field:'modeling-reference'},
  {role:'candidate_binder', label:'Candidate binding domain', field:'modeling-candidate'}
];

function selectedSequenceDiscovery(decision = selectedDecision()) {
  return asArray(state.run?.sequence_discoveries).filter(item =>
    String(item.decision_version) === String(decision?.version) && ['completed', 'needs_inputs'].includes(item.status)).at(-1);
}

function verifiedDiscoveredSequences(discovery) {
  return asArray(discovery?.sequences).filter(item => item.verified === true && discoverySequenceRoles.some(role => role.role === item.role) &&
    typeof item.sequence === 'string' && /^[ACDEFGHIKLMNPQRSTVWY]+$/.test(item.sequence) && Number(item.length) === item.sequence.length &&
    /^[a-f0-9]{64}$/i.test(item.sequence_sha256 || '') && !['rejected','failed','unqualified','unsupported'].includes(item.qualification?.status));
}

function discoverySequenceSource(sequence) {
  const url = safeUrl(sequence.source_url);
  return `${sequence.label || sequence.id}; sequence ${sequence.id}; SHA-256 ${sequence.sequence_sha256}; source ${url || 'source recorded in discovery'}${sequence.source_locator ? '; locator ' + textValue(sequence.source_locator) : ''}`;
}

function renderSequenceDiscovery(decision) {
  const run = state.run, latest = asArray(run?.decisions).at(-1), discovery = selectedSequenceDiscovery(decision);
  const operation = asArray(run?.sequence_discovery_operations).filter(item => String(item.decision_version ?? item.input?.decision_version) === String(decision?.version)).at(-1);
  const running = Boolean(isActive(run) && run?.operation?.kind === 'sequence_discovery') || ['queued','running','reviewing'].includes(operation?.status);
  const eligible = Boolean(decision) && run?.mode === 'live' && String(decision.version) === String(latest?.version) && !state.busy && !isActive(run);
  $('sequence-discovery').hidden = !decision;
  $('discover-sequences').disabled = !eligible || running;
  $('discover-sequences').textContent = running ? 'Searching and qualifying…' : discovery ? 'Search for more sequences ↗' : 'Find missing sequences with AI ↗';
  $('sequence-discovery-status').textContent = running ? 'AI sequence discovery is in progress. Source retrieval, scientific qualification and reviewer checks are recorded in the execution trail.' : discovery ? `Discovery ${discovery.status === 'completed' ? 'complete' : 'returned partial inputs'} · decision v${discovery.decision_version}. ${discovery.summary || ''}` : operation && ['failed','unknown','blocked','cancelled'].includes(operation.status) ? `Sequence discovery ${words(operation.status)}. ${operation.error || operation.reason || 'Inspect the execution trail before starting another search.'}` : !decision ? '' : run?.mode !== 'live' ? 'Live mode is required for AI sequence discovery.' : String(decision.version) !== String(latest?.version) ? 'Select the latest decision to search against the current scientific context.' : 'Find missing inputs from the investigation context and public sources. Candidate identity and source checks determine what can be filled.';
  if (!changed('sequenceDiscovery', [run?.id, decision?.version, discovery])) return;
  if (!discovery) {
    $('sequence-discovery-content').innerHTML = '<p class="small muted">No sequence-discovery result has been saved for this decision yet.</p>';
    return;
  }
  const inventory = verifiedDiscoveredSequences(discovery);
  const priorSelections = new Map(discoverySequenceRoles.map(item => [item.role, $(`discovered-${item.role}`)?.value]));
  $('sequence-discovery-content').innerHTML = `${discovery.scientific_rationale ? `<p class="discovery-rationale">${esc(discovery.scientific_rationale)}</p>` : ''}${discovery.qualification_note ? `<p class="small muted">${esc(discovery.qualification_note)}</p>` : ''}<div class="discovery-role-grid">${discoverySequenceRoles.map(slot => {
    const options = inventory.filter(sequence => sequence.role === slot.role);
    const selected = options.find(item => item.id === priorSelections.get(slot.role)) || options[0];
    return `<article class="discovery-role"><h4>${esc(slot.label)}</h4>${options.length ? `<label for="discovered-${slot.role}" class="sr-only">Verified ${esc(slot.label.toLowerCase())} sequence</label><select id="discovered-${slot.role}">${options.map(item => `<option value="${esc(item.id)}"${item.id === selected?.id ? ' selected' : ''}>${esc(item.label || item.id)} · ${esc(item.length)} aa</option>`).join('')}</select><button type="button" class="evidence-link" data-use-sequence-role="${slot.role}">Use selected ${esc(slot.label.toLowerCase())} · replaces this field ↗</button>${options.map(item => {const url = safeUrl(item.source_url); return `<details class="discovery-source"><summary>${esc(item.label || item.id)} · inspect verified sequence and source</summary><pre class="exact-sequence" tabindex="0">${esc(item.sequence)}</pre><p>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">Source record ↗</a>` : 'Source URL not recorded'}${item.source_locator ? ` · ${esc(textValue(item.source_locator))}` : ''}</p>${item.qualification ? `<p>${esc(textValue(item.qualification))}</p>` : ''}<code>${esc(item.sequence_sha256)}</code></details>`;}).join('')}` : '<p class="small muted">No qualified sequence found for this role. This field stays unchanged.</p>'}</article>`;
  }).join('')}</div>${inventory.length ? '<div class="discovery-fill-actions"><button type="button" class="button primary small-button" data-fill-sequences>Fill empty fields with these selections ↗</button><p class="small muted">Existing sequence edits stay intact. Source citations are added to your notes. Target retention must be checked separately before a new NVIDIA comparison.</p></div>' : ''}${asArray(discovery.missing_inputs).length ? `<div class="binder-input-note"><h4>Still needed</h4>${briefTextList(discovery.missing_inputs)}</div>` : ''}<p class="brief-provenance">Sequence discovery ${esc(discovery.id || '')} · human review ${esc(words(discovery.human_review_status || 'unreviewed'))}. Exact source provenance stays attached to each selection.</p>`;
  if (state.preparedDiscoveryFor !== `${run.id}:${decision.version}:${discovery.id}` && !$('modeling-retained').checked) {
    fillDiscoveredSequences(null, true);
  }
}

function fillDiscoveredSequences(replaceRole = null, automatic = false) {
  const discovery = selectedSequenceDiscovery();
  if (!discovery || (automatic && $('modeling-retained').checked)) return;
  const inventory = verifiedDiscoveredSequences(discovery), filled = [], kept = [];
  for (const slot of discoverySequenceRoles) {
    if (replaceRole && replaceRole !== slot.role) continue;
    const candidates = inventory.filter(item => item.role === slot.role);
    const selectedId = $(`discovered-${slot.role}`)?.value;
    const sequence = candidates.find(item => item.id === selectedId) || (!selectedId ? candidates[0] : null);
    if (!sequence) continue;
    const current = String($(slot.field).value || '').trim();
    if (current && replaceRole !== slot.role) {kept.push(slot.label.toLowerCase()); continue;}
    $(slot.field).value = sequence.sequence;
    filled.push({slot, sequence});
  }
  if (filled.length) {
    const originalNote = String($('modeling-source').value || '');
    const additions = filled.map(({sequence}) => discoverySequenceSource(sequence)).filter(note => !originalNote.includes(note));
    if (additions.length) $('modeling-source').value = [originalNote, `AI sequence discovery ${discovery.id}:`, discovery.scientific_rationale, ...additions].filter(Boolean).join('\n\n');
    $('modeling-retained').checked = false;
    $('manual-modeling').open = true;
  }
  state.preparedDiscoveryFor = `${state.run.id}:${selectedDecision()?.version}:${discovery.id}`;
  $('sequence-fill-status').textContent = `${filled.length ? `Prepared ${filled.map(item => item.slot.label.toLowerCase()).join(', ')} from verified source records.` : 'No empty qualified fields needed filling.'}${kept.length ? ` Preserved your existing ${kept.join(', ')}.` : ''} ${filled.length ? 'Your source notes were preserved and citations added. ' : ''}No NVIDIA inference was submitted; target retention requires your evidence.`;
}

async function requestSequenceDiscovery() {
  const decision = selectedDecision();
  if (!state.run || !decision || state.busy || isActive(state.run) || state.run.mode !== 'live' || String(decision.version) !== String(asArray(state.run.decisions).at(-1)?.version)) return;
  await mutateRun('sequence-discoveries', {decision_version: decision.version}, () => toast('AI sequence discovery queued. The agent will retrieve and qualify source-backed target and binder inputs.'));
}

function selectedResearchBrief(decision = selectedDecision()) {
  return asArray(state.run?.research_briefs).filter(item =>
    String(item.decision_version ?? item.source_decision_version) === String(decision?.version) &&
    item.content && !['failed', 'rejected', 'unknown', 'cancelled'].includes(item.status)).at(-1);
}

function briefSequenceInventory(brief) {
  return asArray(brief?.molecular_audit?.sequence_inventory).filter(item => item.verified === true &&
    typeof item.sequence === 'string' && /^[ACDEFGHIKLMNPQRSTVWY]+$/.test(item.sequence) &&
    item.sequence.length === Number(item.length) && /^[a-f0-9]{64}$/i.test(item.sequence_sha256 || ''));
}

function briefTextList(items) {
  return asArray(items).length ? `<ul>${asArray(items).map(item => `<li>${esc(textValue(item))}</li>`).join('')}</ul>` : '';
}

function renderMolecularAudit(brief) {
  const audit = brief?.molecular_audit;
  if (!audit) return '<p class="small muted">An exact-input audit will accompany the generated explanation.</p>';
  const sequences = briefSequenceInventory(brief), comparisons = asArray(audit.comparisons);
  if (!comparisons.length && !sequences.length) return '<p class="small muted">This investigation has no verified molecular prediction inputs to display. The next experiment can still use the other accepted evidence.</p>';
  return `<div class="molecular-audit"><div class="brief-heading"><h4>Exact inputs and returned predictions</h4>${badge(audit.status)}</div><p class="small muted">These are the sequences recovered by the server’s artifact audit. A target isoform is not a binder sequence.</p><div class="sequence-inventory">${sequences.map(item => `<details class="sequence-record"><summary><span>${esc(words(item.label || item.id))}</span><span class="pill pale">${esc(item.length)} aa · ${esc(item.role)}</span></summary><p class="small muted">${esc(item.provenance?.identity_basis || 'Identity checked against the recorded artifact.')} ${item.provenance?.scope ? esc(words(item.provenance.scope)) : ''}</p>${item.provenance?.mapping ? `<p class="small"><strong>Sequence mapping:</strong> ${esc(textValue(item.provenance.mapping))}</p>` : ''}<pre class="exact-sequence" tabindex="0" aria-label="Exact ${esc(item.label || item.id)} amino-acid sequence">${esc(item.sequence)}</pre><dl class="sequence-provenance"><dt>Sequence ID</dt><dd>${esc(item.id)}</dd><dt>SHA-256</dt><dd>${esc(item.sequence_sha256)}</dd><dt>Provider request</dt><dd>${esc(item.request_id || 'Not recorded')}</dd></dl>${evidenceLinks(item.evidence_id ? [item.evidence_id] : [])}${asArray(item.provenance?.sources).length ? `<details><summary>Source provenance</summary>${briefTextList(item.provenance.sources)}</details>` : ''}</details>`).join('')}</div>${comparisons.map(comparison => `<section class="audit-comparison"><h4>${esc(comparison.evidence_id || 'Recorded molecular comparison')}</h4>${briefTextList(comparison.what_this_adds)}<div class="prediction-receipts">${asArray(comparison.predictions).map(prediction => {const confidence = prediction.confidence || {}; return `<article><strong>${esc(words(prediction.label || 'Prediction'))}</strong><p class="small">${confidence.mean != null ? `Mean ${esc(confidence.metric || 'confidence')}: <strong>${esc(confidence.mean)}</strong>${confidence.native_scale ? ` · scale ${esc(textValue(confidence.native_scale))}` : ''}` : `Confidence audit: ${esc(words(confidence.status || 'not recorded'))}`}</p>${prediction.global_provider_confidence != null ? `<p class="small">Provider aggregate confidence: ${esc(prediction.global_provider_confidence)}</p>` : ''}${confidence.scale_note ? `<p class="confidence-scale-note">${esc(confidence.scale_note)}</p>` : ''}<p class="small muted">${esc(prediction.request_id || 'Request ID not recorded')}</p>${asArray(confidence.regions).length ? `<details><summary>Regional confidence</summary>${valueTable(confidence.regions)}</details>` : ''}<details><summary>Exact request settings and checks</summary>${valueTable(prediction.request_audit || {})}</details></article>`;}).join('')}</div>${comparison.settings_comparison ? `<details><summary>Were the prediction settings matched?</summary>${valueTable(comparison.settings_comparison)}</details>` : ''}${comparison.alignment_sensitivity ? `<details><summary>Sequence-aligned structural comparison</summary>${valueTable(comparison.alignment_sensitivity)}</details>` : ''}${asArray(comparison.limitations).length ? `<details><summary>Interpretation limits</summary>${briefTextList(comparison.limitations)}</details>` : ''}</section>`).join('')}</div>`;
}

function renderResearchBrief(decision) {
  const run = state.run, brief = selectedResearchBrief(decision);
  const operations = asArray(run?.research_brief_operations).filter(item => String(item.decision_version ?? item.source_decision_version ?? item.input?.decision_version) === String(decision?.version));
  const operation = operations.at(-1);
  const generating = Boolean(isActive(run) && run?.operation?.kind === 'research_brief') || ['queued', 'running', 'reviewing'].includes(operation?.status);
  const isLatest = Boolean(decision) && String(decision.version) === String(asArray(run?.decisions).at(-1)?.version);
  const eligible = Boolean(decision) && isLatest && run?.mode === 'live' && !isActive(run) && !state.busy;
  $('explain-results').disabled = !eligible || generating;
  $('explain-results').textContent = generating ? 'Writing and checking…' : brief ? 'Refresh explanation ↗' : 'Explain these results ↗';
  $('prepare-modeling').disabled = !decision || state.busy || (!brief && !eligible);
  $('prepare-modeling').textContent = brief ? 'Prepare from this investigation ↗' : generating ? 'Preparing explanation…' : 'Prepare from this investigation ↗';
  const model = asArray(brief?.provider_metadata?.returned_models).join(', ') || brief?.provider_metadata?.requested_model || '';
  $('research-brief-status').textContent = generating ? 'The model is synthesizing the accepted analyses and molecular audit. A separate model review checks the explanation; the original decisions stay preserved.' : brief ? `Model-written interpretation of decision v${decision.version}${model ? ` · ${model}` : ''} · Human review pending. ${isActive(run) ? 'A new operation is running; this explanation refers to the recorded decision.' : 'Original decisions and evidence are unchanged.'}` : operation && ['failed','unknown','cancelled','blocked','budget_exhausted'].includes(operation.status) ? `Explanation ${words(operation.status)}. ${operation.error || operation.reason || 'Inspect the execution trail before requesting another explanation.'}` : !decision ? '' : !isLatest ? 'Select the latest decision to generate a new explanation. Historical decisions stay preserved.' : run?.mode !== 'live' ? 'Live model interpretation is available for live investigations.' : 'Generate a concise, evidence-linked answer: what happened, why the team changed its view, what NVIDIA added, and the best next test.';
  if (!changed('researchBrief', [run?.id, decision?.version, brief?.id, brief?.content, brief?.molecular_audit?.audit_sha256])) return;
  const content = brief?.content;
  $('original-findings').open = !content;
  if (!content) {
    $('research-brief-content').innerHTML = '';
    $('molecular-preparation-content').innerHTML = '<p>The model can prepare this investigation’s recorded comparison and scientific rationale. Qualified inputs for a new binding-domain design remain available in the separate form below.</p>';
    $('molecular-preparation-status').textContent = '';
    return;
  }
  const answer = content.proposed_answer || {}, nvidia = content.nvidia || {}, next = content.recommended_next_step || {};
  const confidenceLabels = {leading_explanation:'Leading explanation', plausible:'Plausible explanation', probable_within_scope:'Probable within scope'};
  $('research-brief-content').innerHTML = `<div class="working-answer"><div>${badge('', confidenceLabels[answer.confidence_label] || words(answer.confidence_label || 'Proposed interpretation'))}<h3>${esc(content.headline || 'Our current best explanation')}</h3></div><p class="answer-statement">${esc(answer.statement || content.plain_summary)}</p>${content.plain_summary && content.plain_summary !== answer.statement ? `<p>${esc(content.plain_summary)}</p>` : ''}<p class="answer-scope"><strong>Applies to:</strong> ${esc(answer.scope || 'The evidence and inputs recorded in this investigation.')}</p><div class="insight-evidence">${evidenceLinks(answer.evidence_ids)}</div>${answer.caveat ? `<p class="answer-caveat"><strong>What could change this answer:</strong> ${esc(answer.caveat)}</p>` : ''}${answer.strongest_alternative ? `<p class="answer-alternative"><strong>Strongest competing explanation:</strong> ${esc(answer.strongest_alternative)}</p>` : ''}</div><div class="brief-findings">${asArray(content.findings).map((item,index) => `<article><span class="step-label">${String(index+1).padStart(2,'0')} / WHAT WE FOUND</span><h4>${esc(item.what)}</h4><p>${esc(item.why_it_matters)}</p><div class="insight-evidence">${evidenceLinks(item.evidence_ids)}</div></article>`).join('')}</div><section class="brief-story"><h3>Why the team made these decisions</h3><ol>${asArray(content.decision_story).map(item => `<li><span class="story-version">V${esc(item.decision_version)}</span><div><strong>${esc(item.what_changed)}</strong><p>${esc(item.why)}</p>${item.next_step ? `<p class="small"><strong>Then:</strong> ${esc(item.next_step)}</p>` : ''}${evidenceLinks(item.evidence_ids)}</div></li>`).join('')}</ol></section><section class="brief-nvidia"><span class="step-label">NVIDIA · WHAT THE CALLS ADDED</span><h3>${esc(nvidia.summary || 'What we learned from molecular prediction')}</h3><div class="brief-two-columns"><div><h4>What we learned</h4>${briefTextList(nvidia.learned)}</div><div><h4>What these calls did not test</h4>${briefTextList(nvidia.not_established)}</div></div>${evidenceLinks(nvidia.evidence_ids)}${renderMolecularAudit(brief)}</section><section class="brief-next"><span class="step-label">RECOMMENDED NEXT STEP</span><h3>${esc(next.action || 'Read the proposed research handoff')}</h3><p>${esc(next.why || '')}</p><div class="brief-two-columns"><p><strong>Supports the explanation</strong>${esc(next.positive_result || '')}</p><p><strong>Challenges the explanation</strong>${esc(next.negative_result || '')}</p></div>${asArray(next.prerequisites).length ? `<details><summary>What this test needs</summary>${briefTextList(next.prerequisites)}</details>` : ''}${evidenceLinks(next.evidence_ids)}</section><details class="brief-role-summaries"><summary>Specialist findings in plain language</summary><div class="brief-findings">${asArray(content.role_summaries).map(item => `<article><span class="step-label">${esc(roleLabel(item.role))}</span><h4>${esc(item.what_found)}</h4><p>${esc(item.why_it_matters)}</p>${evidenceLinks(item.evidence_ids)}</article>`).join('')}</div></details><p class="brief-provenance">Interpretation ${esc(brief.id || '')} · ${esc(prettyDate(brief.created_at))} · Human review: ${esc(words(brief.human_review_status || 'unreviewed'))}. This explanation supplements the immutable scientific decisions.</p>`;
  const draft = content.modeling_draft || {};
  $('molecular-preparation-content').innerHTML = `<h4>${esc(draft.objective || 'Recorded molecular comparison')}</h4><p>${esc(draft.scientific_rationale || nvidia.summary || '')}</p>${draft.qualification_note ? `<p class="small">${esc(draft.qualification_note)}</p>` : ''}${renderMolecularAudit(brief)}${asArray(draft.missing_inputs).length ? `<div class="binder-input-note"><h4>For a new binding-domain comparison</h4>${briefTextList(draft.missing_inputs)}</div>` : ''}`;
  if (state.prepareMolecularRequested === `${run.id}:${decision.version}`) {
    state.prepareMolecularRequested = null;
    prepareModelingFromBrief(brief);
  } else {
    preparePristineModelingForm(brief);
  }
}

function molecularPreparationKey(brief) {
  return `${state.run?.id}:${brief?.decision_version ?? brief?.source_decision_version}:${brief?.id || brief?.context_sha256 || 'unidentified'}`;
}

function preparePristineModelingForm(brief) {
  if (!brief || state.preparedMolecularFor === molecularPreparationKey(brief)) return;
  const pristine = ['modeling-target', 'modeling-reference', 'modeling-candidate', 'modeling-source']
    .every(id => !String($(id).value || '').trim()) && !$('modeling-retained').checked;
  // Refresh can restore verified draft inputs, but it must never replace a scientist's edits.
  if (pristine) prepareModelingFromBrief(brief);
}

function prepareModelingFromBrief(brief = selectedResearchBrief()) {
  if (!brief) return;
  const draft = brief.content?.modeling_draft || {}, inventory = briefSequenceInventory(brief);
  const resolve = (id, role) => inventory.find(item => item.id === id && item.role === role);
  const target = resolve(draft.target_sequence_id, 'target');
  const reference = resolve(draft.reference_binder_sequence_id, 'binder');
  const candidate = resolve(draft.candidate_binder_sequence_id, 'binder');
  // Only artifact-verified inventory bytes enter sequence fields; model text is never a sequence source.
  for (const [id, sequence] of [['modeling-target',target],['modeling-reference',reference],['modeling-candidate',candidate]]) {
    if (sequence) $(id).value = sequence.sequence;
  }
  $('modeling-source').value = [draft.scientific_rationale, draft.qualification_note,
    ...[target,reference,candidate].filter(Boolean).map(item => `${item.label || item.id}: ${item.id}; SHA-256 ${item.sequence_sha256}; evidence ${item.evidence_id}; request ${item.request_id}`)].filter(Boolean).join('\n\n');
  $('modeling-retained').checked = false;
  const missing = [!target && 'target', !reference && 'reference binder', !candidate && 'candidate binder'].filter(Boolean);
  $('molecular-preparation-status').textContent = `${target ? 'Verified target sequence and scientific rationale prepared.' : 'Scientific rationale prepared from this investigation.'} ${missing.length ? `Still needed for a new binding-domain comparison: ${missing.join(', ')}. The recorded target-isoform comparison is shown above.` : 'Verified sequence inputs prepared for your review.'} Target retention still needs your evidence and confirmation. No NVIDIA job was submitted.`;
  state.preparedMolecularFor = molecularPreparationKey(brief);
  if (!missing.length) $('manual-modeling').open = true;
}

async function requestResearchBrief(prepare = false) {
  const decision = selectedDecision();
  if (!state.run || !decision || state.busy || isActive(state.run) || state.run.mode !== 'live' || String(decision.version) !== String(asArray(state.run.decisions).at(-1)?.version)) return;
  if (prepare) state.prepareMolecularRequested = `${state.run.id}:${decision.version}`;
  await mutateRun('research-briefs', {decision_version: decision.version}, () => toast('Explanation queued. The model will summarize accepted results and audit the molecular evidence.'));
}

function renderFindingsOverview(decision) {
  $('findings-overview').hidden = !decision;
  $('main').classList.toggle('has-reviewed-decision', Boolean(decision) && !isActive(state.run));
  if (!decision) return;
  const live = state.run?.mode === 'live';
  const model = asArray(decision.metadata?.returned_models).join(', ') || decision.metadata?.requested_model;
  const explicit = asArray(decision.insights);
  const cards = explicit.length ? explicit : asArray(decision.claims).filter(c => c.kind !== 'limitation').slice(0, 3).map(c => ({title: words(c.kind || 'Recorded claim'), finding: c.text, evidence_ids: c.evidence_ids}));
  if (!changed('insights', [state.run?.id, decision, isActive(state.run)])) return;
  $('findings-version').textContent = `Decision v${decision.version}${String(decision.version) === String(state.run?.decisions?.at(-1)?.version) ? ' · latest reviewed' : ' · historical'}`;
  $('findings-title').textContent = live ? 'What the evidence tells us.' : 'The walkthrough’s recorded assessment.';
  $('findings-summary').textContent = decision.summary || 'The recorded assessment is available below.';
  $('findings-assessment').innerHTML = badge(decision.assessment, words(decision.assessment || 'Assessment recorded'));
  $('findings-context').textContent = `${live ? 'Model-produced assessment' + (model ? ` · ${model}` : '') : 'Scripted walkthrough · no model inference'}${isActive(state.run) ? ' · A new operation is running; this decision remains unchanged until review completes.' : ' · Open the evidence to inspect each finding’s support.'}`;
  $('insight-cards').innerHTML = cards.length ? cards.map((item, index) => `<article class="insight-card"><div class="insight-number">${String(index + 1).padStart(2, '0')} / ${explicit.length ? 'INSIGHT' : 'RECORDED CLAIM'}</div><h3>${esc(item.title || 'Recorded finding')}</h3><p class="insight-finding">${esc(item.finding || '')}</p>${item.why_it_matters ? `<div class="insight-meaning"><h4>Why it matters</h4><p>${esc(item.why_it_matters)}</p></div>` : ''}${item.next_step ? `<div class="insight-next"><h4>The next question</h4><p>${esc(item.next_step)}</p></div>` : ''}<div class="insight-evidence">${evidenceLinks(item.evidence_ids)}</div></article>`).join('') : '<div class="state-placeholder">This decision has no separately recorded insights or claims. Read the original assessment below.</div>';
}

async function refreshFollowups(decision) {
  const run = state.run, latest = run?.decisions?.at(-1);
  if (!run || !decision || String(decision.version) !== String(latest?.version)) return;
  const query = JSON.stringify([run.id, latest.version, run.status, run.operation?.id, asArray(run.followup_operations).map(operation => [operation.id, operation.status, operation.evidence_id, asArray(operation.artifacts).map(artifact => artifact.preview_url)])]);
  if (state.followupQuery === query && (!state.followupError || Date.now() < (state.followupRetryAt || 0))) return;
  state.followupQuery = query;
  state.followupLoading = true;
  state.followupError = '';
  renderFollowups(decision);
  try {
    const response = await api(`/api/runs/${encodeURIComponent(run.id)}/followups`);
    if (state.run?.id !== run.id || state.followupQuery !== query) return;
    state.followupData = {...response, run_id: response.run_id || run.id};
    updateStructureOptions();
  } catch (error) {
    if (state.run?.id !== run.id || state.followupQuery !== query) return;
    state.followupError = error.message;
    state.followupRetryAt = Date.now() + 15000;
    state.followupData = null;
  } finally {
    if (state.followupQuery === query) {state.followupLoading = false; renderFollowups(selectedDecision());}
  }
}

function renderFollowups(decision) {
  const run = state.run;
  const isLatest = decision && String(decision.version) === String(run?.decisions?.at(-1)?.version);
  const available = Boolean(state.followupData && run && decision) && state.followupData.run_id === run.id && String(state.followupData?.decision_version) === String(decision?.version);
  const records = available ? asArray(state.followupData.followups) : asArray(decision?.followups);
  const operations = available ? asArray(state.followupData.operations) : [];
  const active = isActive(run);
  if (!changed('followups-render', [run?.id, decision?.version, records, operations, active, state.busy, state.followupLoading, state.followupError, available])) return;
  $('followups-version').textContent = decision ? `From decision v${decision.version}` : 'Awaiting a decision';
  $('followups-status').textContent = !decision ? 'Recommendations appear after a reviewed decision is issued.' : !isLatest ? 'Historical recommendations are preserved. Select the latest decision to run a follow-up.' : active ? 'An operation is running. Its evidence and revised decision will appear here when accepted.' : state.followupLoading ? 'Checking which recommendations can run…' : state.followupError ? `Action readiness is unavailable: ${state.followupError}` : 'Run an approved follow-up to add evidence and request a new reviewed decision. Your original hypothesis stays pinned.';
  $('followup-cards').innerHTML = records.length ? records.map(item => {
    const modelRecommended = item.origin === 'model_recommendation';
    const latestOperation = operations.filter(op => op.recommendation_id === item.id).at(-1);
    const executable = item.executable === true && available && isLatest && !active && !state.busy && !state.followupLoading;
    const structure = item.kind === 'bionemo_public_structure';
    const artifacts = asArray(latestOperation?.artifacts).filter(artifact => previewOptions().some(option => option.url === artifact.preview_url));
    const label = structure ? 'Run NVIDIA structure' : 'Run this analysis';
    const reason = !isLatest ? 'Select the latest decision to execute.' : active ? 'Waiting for the current operation to finish.' : item.reason || (item.executable === false ? 'Required inputs or execution conditions are not met.' : !available ? 'Execution readiness has not been verified.' : '');
    return `<article class="card followup-card"><div class="followup-top"><span class="step-label">${modelRecommended ? 'MODEL-RECOMMENDED NEXT STEP' : 'REGISTERED ANALYSIS · AVAILABLE OPTION'}</span>${badge(item.status || 'unavailable')}</div><h4>${esc(item.title || 'Follow-up analysis')}</h4><p>${esc(item.rationale || '')}</p>${item.decision_it_could_change ? `<div class="followup-change"><strong>What it could change</strong><p>${esc(item.decision_it_could_change)}</p></div>` : ''}${asArray(item.prerequisites).length ? `<details class="followup-prerequisites"><summary>Required inputs &amp; scope</summary><ul>${asArray(item.prerequisites).map(value => `<li>${esc(textValue(value))}</li>`).join('')}</ul></details>` : ''}<div class="insight-evidence">${evidenceLinks(item.evidence_ids)}</div>${latestOperation ? `<p class="followup-receipt">Last operation: ${esc(words(latestOperation.status))}${latestOperation.new_decision_version != null ? ` · decision v${esc(latestOperation.new_decision_version)}` : ''}${latestOperation.evidence_id ? ` · ${esc(latestOperation.evidence_id)}` : ''}</p>` : ''}${artifacts.length ? `<div class="followup-structure-links">${artifacts.map(artifact => `<button type="button" class="evidence-link" data-view-structure="${esc(artifact.preview_url)}">View ${esc(structureLabel(artifact))} ↗</button>`).join('')}</div>` : ''}<div class="followup-footer"><p>${esc(reason || (structure ? 'Runs a real provider prediction in the declared scope.' : 'Executes a registered source-data recipe, then reviews the new evidence.'))}</p><button type="button" class="button primary small-button" data-run-followup="${esc(item.id)}" data-followup-version="${esc(decision.version)}" ${executable ? '' : 'disabled'}>${esc(label)} <span aria-hidden="true">↗</span></button></div></article>`;
  }).join('') : `<div class="state-placeholder">${decision ? 'No executable recommendations are recorded for this decision. You can still submit a scientific correction below.' : 'A reviewed finding will provide the starting point for the next analysis.'}</div>`;
}

async function runFollowup(id, version) {
  if (!state.run || state.busy || isActive(state.run)) return;
  const current = selectedDecision();
  const source = state.followupData;
  const item = asArray(source?.followups).find(value => value.id === id);
  if (source?.run_id !== state.run.id || String(source?.decision_version) !== String(version) || String(current?.version) !== String(version) || String(state.run.decisions?.at(-1)?.version) !== String(version) || item?.executable !== true) {
    toast('This recommendation is no longer ready. Refresh the current decision before running it.', true); return;
  }
  await mutateRun('followups', {decision_version: Number(version), recommendation_id: id}, () => {
    state.followupQuery = null;
    toast('Follow-up started. New evidence and the next reviewed decision will stay in this investigation.');
  });
}

function previewOptions() {
  const options = [], check = state.engineeringCheck;
  const links = check?.links;
  const preview = check?.preview_url || (Array.isArray(links) ? links.find(item => item.name === 'preview')?.url : links?.preview);
  const modeling = selectedDecision()?.rd_handoff?.modeling || state.run?.agent_modeling;
  asArray(modeling?.artifacts).forEach(artifact => {if (artifact?.preview_url) options.push({url: artifact.preview_url, label: `${structureLabel(artifact)} · decision v${selectedDecision()?.version || 'pending'}`});});
  const operations = Array.isArray(state.run?.followup_operations) ? state.run.followup_operations : state.followupData?.run_id === state.run?.id ? asArray(state.followupData?.operations) : [];
  operations.forEach(operation => {
    asArray(operation.artifacts).forEach(artifact => {if (artifact?.preview_url) options.push({url:artifact.preview_url, label:`${structureLabel(artifact)} · from v${operation.decision_version} · ${words(operation.status)}`});});
  });
  if (preview) options.push({url: preview, label: 'NVIDIA service check · engineering scope'});
  return options.filter((item, index, all) => {try {const u = new URL(item.url, location.origin); return u.origin === location.origin && all.findIndex(other => other.url === item.url) === index;} catch {return false;}});
}

function updateStructureOptions() {
  const options = previewOptions();
  if (!changed('structure-options', options)) return;
  const selection = (state.structureUserSelected && options.find(item => item.url === state.structureUrl)) || options[0];
  $('structure-select').hidden = options.length < 2;
  $('structure-select').innerHTML = options.map(item => `<option value="${esc(item.url)}">${esc(item.label)}</option>`).join('');
  if (!selection) {
    state.structureUrl = null; state.structureData = null; ++state.structureEpoch;
    $('structure-view').hidden = true; $('structure-empty').hidden = false;
    $('structure-empty').textContent = 'No validated structure preview is available.';
    $('structure-scope').textContent = 'A structure appears here only when the service returns validated coordinates from a real NVIDIA artifact.';
    return;
  }
  $('structure-select').value = selection.url;
  loadStructurePreview(selection.url);
}

async function loadStructurePreview(url) {
  state.structureUrl = url;
  const epoch = ++state.structureEpoch;
  $('structure-view').hidden = true; $('structure-empty').hidden = false;
  $('structure-empty').textContent = 'Loading validated NVIDIA coordinates…';
  try {
    const preview = state.structureCache.get(url) || await api(url);
    if (epoch !== state.structureEpoch) return;
    if (preview.status !== 'completed' || !/^[a-f0-9]{64}$/i.test(preview.receipt?.sha256 || '')) throw new Error('A completed, hash-validated structure receipt was not returned.');
    const chains = asArray(preview.chains).map(chain => ({id: String(chain.id), points: asArray(chain.points)}));
    const points = chains.flatMap(chain => chain.points);
    if (!points.length || points.length > 30000 || !chains.every(chain => chain.points.length && chain.points.every(point => ['x','y','z'].every(axis => Number.isFinite(point[axis]))))) throw new Error('The returned coordinate preview is empty or invalid.');
    state.structureCache.set(url, preview); state.structureData = {...preview, chains};
    state.structureRotation = {x: -.25, y: .45, zoom: 1};
    $('structure-scope').textContent = structureScope(preview.scope);
    const colors = structureColors;
    $('structure-legend').innerHTML = chains.map((chain,index) => `<span><i style="background:${colors[index % colors.length]}"></i>Chain ${esc(chain.id)} · ${chain.points.length} Cα</span>`).join('');
    const link = safeUrl(preview.cif_url);
    $('structure-cif-link').hidden = !link;
    if (link) $('structure-cif-link').href = link; else $('structure-cif-link').removeAttribute('href');
    $('structure-receipt').innerHTML = `<span>${esc(preview.receipt.model || 'NVIDIA prediction')}</span>${Number.isFinite(preview.receipt.confidence_score) ? `<span>Reported confidence ${esc(preview.receipt.confidence_score.toFixed(3))}</span>` : ''}<span class="mono">Request ${esc(preview.receipt.request_id || 'not supplied')}</span><details><summary>Artifact fingerprint</summary><span class="mono">SHA-256 ${esc(preview.receipt.sha256)}</span></details>`;
    $('structure-view').hidden = false; $('structure-empty').hidden = true;
    $('structure-canvas').setAttribute('aria-label', `NVIDIA-predicted C-alpha trace: ${chains.length} chains and ${points.length} coordinates. ${structureScope(preview.scope)}`);
    drawStructure();
  } catch (error) {
    if (epoch !== state.structureEpoch) return;
    state.structureData = null;
    $('structure-empty').textContent = `Structure preview unavailable: ${error.message}`;
  }
}

const structureColors = ['#a6df73','#77c9ea','#e7b2dd','#efbc77','#b6b6f0','#8bdbc3'];
function drawStructure() {
  const data = state.structureData, canvas = $('structure-canvas');
  if (!data || !canvas) return;
  const box = canvas.getBoundingClientRect(), width = box.width || 900, height = box.height || 420;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.fillStyle = '#10252b'; ctx.fillRect(0, 0, width, height);
  const all = data.chains.flatMap(chain => chain.points);
  const bounds = ['x','y','z'].map(axis => [Math.min(...all.map(point => point[axis])),Math.max(...all.map(point => point[axis]))]);
  const center = bounds.map(([min,max]) => (min + max) / 2);
  const extent = Math.max(...bounds.map(([min,max]) => max-min), 1);
  const {x: rx, y: ry, zoom} = state.structureRotation;
  const scale = Math.min(width,height) * .69 / extent * zoom;
  const project = point => {
    const [x,y,z] = [point.x-center[0],point.y-center[1],point.z-center[2]];
    const x1 = x*Math.cos(ry)+z*Math.sin(ry), z1=-x*Math.sin(ry)+z*Math.cos(ry);
    return {x:width/2+x1*scale,y:height/2+(y*Math.cos(rx)-z1*Math.sin(rx))*scale,z:y*Math.sin(rx)+z1*Math.cos(rx)};
  };
  const segments = [], dots=[];
  data.chains.forEach((chain,index) => {
    const points=chain.points.map(project), color=structureColors[index % structureColors.length];
    points.forEach((point,j) => {
      dots.push({...point,color});
      if (j && (!Number.isFinite(chain.points[j].residue_index) || !Number.isFinite(chain.points[j-1].residue_index) || chain.points[j].residue_index === chain.points[j-1].residue_index+1)) segments.push({a:points[j-1],b:point,z:(points[j-1].z+point.z)/2,color});
    });
  });
  ctx.lineCap='round';ctx.lineJoin='round';
  segments.sort((a,b)=>a.z-b.z).forEach(segment=>{ctx.globalAlpha=.55+.4*(segment.z/extent+.5);ctx.strokeStyle=segment.color;ctx.lineWidth=2.7;ctx.beginPath();ctx.moveTo(segment.a.x,segment.a.y);ctx.lineTo(segment.b.x,segment.b.y);ctx.stroke();});
  ctx.globalAlpha=.9;
  dots.sort((a,b)=>a.z-b.z).forEach(point=>{ctx.fillStyle=point.color;ctx.beginPath();ctx.arc(point.x,point.y,1.6,0,2*Math.PI);ctx.fill();});
  ctx.globalAlpha=1;
}

function installStructureControls() {
  const canvas=$('structure-canvas'); let drag=null, frame=null;
  const redraw=()=>{if(frame==null)frame=requestAnimationFrame(()=>{frame=null;drawStructure();});};
  canvas.addEventListener('pointerdown',event=>{if(!state.structureData)return;drag={x:event.clientX,y:event.clientY};canvas.setPointerCapture(event.pointerId);canvas.focus({preventScroll:true});});
  canvas.addEventListener('pointermove',event=>{if(!drag)return;state.structureRotation.y+=(event.clientX-drag.x)*.009;state.structureRotation.x+=(event.clientY-drag.y)*.009;drag={x:event.clientX,y:event.clientY};redraw();});
  const stop=()=>{drag=null;};canvas.addEventListener('pointerup',stop);canvas.addEventListener('pointercancel',stop);
  canvas.addEventListener('wheel',event=>{if(!state.structureData || document.activeElement!==canvas)return;event.preventDefault();state.structureRotation.zoom=Math.min(3,Math.max(.4,state.structureRotation.zoom*Math.exp(-event.deltaY*.001)));redraw();},{passive:false});
  canvas.addEventListener('keydown',event=>{if(!state.structureData)return;const r=state.structureRotation;let used=true;if(event.key==='ArrowLeft')r.y-=.12;else if(event.key==='ArrowRight')r.y+=.12;else if(event.key==='ArrowUp')r.x-=.12;else if(event.key==='ArrowDown')r.x+=.12;else if(event.key==='+'||event.key==='=')r.zoom=Math.min(3,r.zoom*1.1);else if(event.key==='-')r.zoom=Math.max(.4,r.zoom/1.1);else if(event.key==='0')state.structureRotation={x:-.25,y:.45,zoom:1};else used=false;if(used){event.preventDefault();redraw();}});
  $('structure-reset').addEventListener('click',()=>{state.structureRotation={x:-.25,y:.45,zoom:1};redraw();});
  $('structure-select').addEventListener('change',()=>{state.structureUserSelected=true;loadStructurePreview($('structure-select').value);});
  if(window.ResizeObserver)new ResizeObserver(redraw).observe(canvas);else window.addEventListener('resize',redraw);
}

init();
