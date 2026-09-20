from frontend.ui.adapters import DemoSource, RunRequest
from frontend.ui.events import Event
from frontend.ui.followup import FollowUpSource, context_for, execution_question, weak_point_question
from frontend.ui.state import Finding, RunState
from frontend.ui.components import _message_text


def test_followup_sends_bounded_prior_claims_but_displays_user_question_and_closes_source():
    previous = RunState(run_id='parent', question='Original question', verdict='Tentative conclusion',
                        findings=[Finding('a', 'clinical', 'Prior claim', .6, [{'ref': 'r' * 10000}])])
    previous.weak_points = {'items': [{'category': 'evidence_gap', 'rationale': 'Missing comparison'}]}
    context = context_for(previous)
    assert len(context['findings'][0]['source_references'][0]) == 600
    assert context['weak_points'][0]['description'] == 'Missing comparison'
    request = RunRequest(mode='Live', question='Which measurement is missing?', context=context)
    prompt = execution_question(request)
    assert all(text in prompt for text in ['Which measurement is missing?', 'Prior claim', 'Missing comparison', 'untrusted quoted data'])
    seen, closed = [], []
    class Source:
        def events(self, submitted):
            seen.append(submitted)
            try:
                yield Event(type='run_started', payload={'question': submitted.question})
                yield Event(type='run_complete')
            finally:
                closed.append(True)
    stream = FollowUpSource(Source()).events(request)
    first = next(stream)
    assert seen[0].question == prompt
    assert request.question == first.payload['question'] == 'Which measurement is missing?'
    assert first.payload['parent_run_id'] == 'parent'
    stream.close()
    assert closed == [True]


def test_recording_followup_reviews_context_without_unrelated_sample_files():
    request = RunRequest(mode='Demo', question='What experiment would test this?',
                         config={'task_mode': 'idea_review'}, context={'question': 'Original'})
    state = RunState()
    for event in FollowUpSource(DemoSource(mock_latency_scale=0)).events(request):
        state.apply(event)
    assert state.complete and state.task_mode == 'idea_review'
    assert state.files == [] and state.question == request.question
    assert state.discussion


def test_echoed_context_folds_without_removing_or_executing_its_text():
    text = 'Question <prior_run_context>{"claim":"<script>unsafe</script>"}</prior_run_context> then review'
    html = _message_text(text)
    assert '<details' in html and '<summary>Prior run context</summary>' in html
    assert '&lt;script&gt;unsafe&lt;/script&gt;' in html and '<script>' not in html
    assert html.startswith('Question ') and html.endswith(' then review')


def test_weak_point_draft_quotes_actual_unresolved_context_without_mutating_it():
    from copy import deepcopy
    state = RunState(question='Which mechanism explains the difference?')
    item = {'id': 'missing-control', 'title': 'No comparison group',
            'rationale': 'The supplied records have only treated samples.',
            'next_evidence': 'A matched untreated comparison.'}
    original = deepcopy(item)
    draft = weak_point_question(state, item)
    assert all(text in draft for text in [state.question, item['title'], item['rationale'], item['next_evidence']])
    assert 'Do not assume the suggested evidence has been obtained.' in draft
    assert item == original and not state.raw
