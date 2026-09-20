"""Three-state UI acceptance matrix. No navigation path exposes the old wizard."""
from copy import deepcopy
from pathlib import Path
from threading import Event as Signal
import importlib
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

FRONTEND=Path(__file__).resolve().parents[1]/'frontend'

@pytest.fixture
def workspace(monkeypatch):
    monkeypatch.delenv('TRACE_BACKEND_URL',raising=False)
    monkeypatch.setenv('TRACE_START_SCREEN','classic')  # Obsolete switch must not resurrect the old UI.
    monkeypatch.syspath_prepend(str(FRONTEND))
    adapters=importlib.import_module('ui.adapters')
    Event=importlib.import_module('ui.events').Event
    release=Signal();release.set()
    class Source:
        def __init__(self):self.requests=[];self.failure=False;self.incomplete=False;self.fatal=False;self.review=False
        def capabilities(self,backend):return {'cancellation_supported':True,'run_mode':'mock'}
        def events(self,request):
            self.requests.append(deepcopy(request))
            yield Event(type='run_started',run_id='test-'+str(len(self.requests)),payload={'question':request.question})
            yield Event(type='agent_spawned',agent_id='a',agent_role='clinical',payload={'message':'Reviewing the supplied evidence.'})
            release.wait(8)
            yield Event(type='finding',agent_id='a',agent_role='clinical',payload={'text':'Original finding. A limitation remains.','provenance':[{'file':'input.csv','line':2}]})
            if self.failure:raise RuntimeError('Simulated service error')
            if self.fatal:
                yield Event(type='error',payload={'message':'Unavailable execution','fatal':True})
                yield Event(type='run_complete',payload={'verdict':'No result','error':'Unavailable execution','abstained':True})
            elif not self.incomplete:
                yield Event(type='run_complete',payload={'verdict':'Original result','confidence':.6})
    source=Source()
    monkeypatch.setattr(adapters,'source_for',lambda mode:source)
    pet_start=importlib.import_module('ui.pet_start')
    def composer(draft,**kwargs):
        action=st.session_state.pop('_test_composer_action',None)
        if action:draft.update(question=action['question'],uploads=deepcopy(action['uploads']))
        return action
    monkeypatch.setattr(pet_start,'render_composer',composer)
    app=AppTest.from_file(str(FRONTEND/'legacy_app.py'),default_timeout=12).run()
    assert not app.exception
    yield app,source,release
    release.set()
    job=app.session_state.get('job') if hasattr(app.session_state,'get') else app.session_state['job']
    if job:job.thread.join(1)


def submit(app,question='My research question',files=None,kind='start'):
    app.session_state['_test_composer_action']={'type':kind,'question':question,'uploads':files or []}
    app.run()
    assert not app.exception


def finish(app,release):
    release.set();app.session_state['job'].thread.join(2);app.run()
    assert not app.exception


def assert_simple(app):
    assert app.session_state['stage'] in {'prompt','running','results'}
    keys=[b.key for b in app.button]
    assert not any(k and (k.startswith('nav_') or k.startswith('replay_') or k in {'pet_advanced','evidence_next','results_edit'}) for k in keys)
    assert not app.radio and not app.multiselect
    assert app.button(key='home').label=='TRACE'
    assert app.button(key='theme_toggle')


def test_initial_page_has_only_composer_and_shared_header(workspace):
    app,source,_=workspace
    assert app.session_state['stage']=='prompt'
    assert app.get('file_uploader')[0].key=='setup_uploads' and not app.text_area and not source.requests
    assert_simple(app)


def test_prompt_to_running_to_results_follows_execution_not_a_replay_timer(workspace):
    app,source,release=workspace;release.clear()
    submit(app,files=[('input.csv',b'a,b\n')])
    assert app.session_state['stage']=='running'
    assert any('scientist-pet' in m.value for m in app.markdown)
    assert len(source.requests)==1
    assert not any(b.key in {'pet_pause','pet_step','pet_results'} for b in app.button)
    assert_simple(app)
    finish(app,release)
    assert app.session_state['stage']=='results'
    assert any('Original result' in m.value for m in app.markdown)
    assert app.session_state['run'].findings[0].provenance==[{'file':'input.csv','line':2}]
    assert not app.tabs
    assert_simple(app)


def test_rerender_and_theme_never_resubmit_or_change_submitted_files(workspace):
    app,source,release=workspace;release.clear();files=[('input.csv',b'a,b\n')]
    submit(app,files=files)
    original=deepcopy(source.requests[0]);job=app.session_state['job']
    app.button(key='theme_toggle').click().run();app.run()
    assert app.session_state['ui_theme']=='dark' and app.session_state['job'] is job
    assert len(source.requests)==1 and source.requests[0]==original
    finish(app,release)
    report=deepcopy(app.session_state['run'])
    app.button(key='theme_toggle').click().run()
    assert app.session_state['run']==report and len(source.requests)==1


def test_trace_home_during_run_preserves_job_and_draft(workspace):
    app,source,release=workspace;release.clear()
    submit(app,'Original question',[('input.csv',b'one')]);job=app.session_state['job']
    app.button(key='home').click().run()
    assert app.session_state['stage']=='prompt' and app.session_state['job'] is job
    assert app.session_state['draft']['question']=='Original question'
    assert app.button(key='return_running')
    submit(app,'Draft of next question',[('new.csv',b'two')])
    assert len(source.requests)==1 and source.requests[0].question=='Original question'
    assert app.session_state['draft']['question']=='Draft of next question'
    finish(app,release)
    assert app.session_state['stage']=='prompt'  # Completion cannot override an explicit Home click.
    app.button(key='view_last_results').click().run()
    assert app.session_state['stage']=='results' and app.session_state['run'].question=='Original question'
    app.button(key='home').click().run()
    assert app.session_state['draft']['uploads']==[('new.csv',b'two')]


def test_return_to_running_and_home_from_results_do_not_create_new_attempts(workspace):
    app,source,release=workspace;release.clear();submit(app)
    app.button(key='home').click().run();app.button(key='return_running').click().run()
    assert app.session_state['stage']=='running'
    finish(app,release);saved=deepcopy(app.session_state['run'])
    app.button(key='home').click().run();app.button(key='view_last_results').click().run()
    assert app.session_state['run']==saved and len(source.requests)==1
    app.button(key='new_question').click().run()
    assert app.session_state['stage']=='prompt' and app.session_state['draft']['question']==''
    assert app.session_state['run']==saved


def test_cancel_waits_for_cleanup_and_is_not_a_scientific_abstention(workspace):
    app,source,release=workspace;release.clear();submit(app)
    app.button(key='cancel_run').click().run()
    assert app.session_state['stage']=='running'
    assert app.session_state['job'].cancel_requested
    finish(app,release)
    assert app.session_state['stage']=='results' and app.session_state['run'].status=='cancelled'
    assert any('canceled' in i.value.lower() for i in app.info)
    assert not any('ABSTAIN' in m.value for m in app.markdown)


@pytest.mark.parametrize('problem',['failure','incomplete','fatal'])
def test_failed_sources_end_in_results_with_retry_and_no_fake_conclusion(workspace,problem):
    app,source,release=workspace;setattr(source,problem,True)
    submit(app);finish(app,release)
    assert app.session_state['stage']=='results'
    assert app.error and app.button(key='retry_run')
    assert not any('ABSTAIN' in m.value for m in app.markdown)
    app.run();assert len(source.requests)==1
    setattr(source,problem,False);app.button(key='retry_run').click().run();finish(app,release)
    assert len(source.requests)==2 and app.session_state['run'].complete
    assert len(app.session_state['previous_runs'])==2


def test_followup_uses_the_same_evidence_and_preserves_prior_result(workspace):
    app,source,release=workspace;files=[('input.csv',b'a,b\n')]
    submit(app,'Original question',files);finish(app,release)
    app.text_input(key='followup_prompt').set_value('Which measurement would distinguish the alternatives?')
    next(b for b in app.button if b.label=='Run follow-up').click().run();finish(app,release)
    assert len(source.requests)==2 and source.requests[-1].uploads==files
    assert app.session_state['submitted'].question=='Which measurement would distinguish the alternatives?'
    assert 'Original result' in source.requests[-1].question
    assert app.session_state['previous_runs'][0]['run'].question=='Original question'
    app.button(key='open_saved_result').click().run()
    assert app.session_state['stage']=='results' and app.session_state['run'].question=='Original question'
    assert len(source.requests)==2 and not app.exception


def test_empty_question_cannot_dispatch(workspace):
    app,source,_=workspace;submit(app,'  ')
    assert app.session_state['stage']=='prompt' and not source.requests and app.error


def test_network_replay_never_dispatches_or_changes_saved_result(workspace):
    app,source,release=workspace;submit(app);finish(app,release)
    saved=deepcopy(app.session_state['run']);request=deepcopy(app.session_state['submitted'])
    app.button(key='network_replay_start').click().run()
    assert len(source.requests)==1 and app.session_state['run']==saved
    app.button(key='network_replay_end').click().run()
    assert app.session_state['network_playback'] is None
    assert app.session_state['submitted']==request and app.session_state['run']==saved
    assert not app.exception


def test_setup_changes_do_not_rewrite_an_active_request(workspace):
    app,source,release=workspace;release.clear();submit(app,'Original',[('old.csv',b'a')])
    request=deepcopy(app.session_state['submitted']);job=app.session_state['job']
    app.selectbox(key='setup_source').select('Live').run()
    app.text_input(key='setup_backend').set_value('http://localhost:9999').run()
    assert app.session_state['submitted']==request and app.session_state['job'] is job
    assert len(source.requests)==1
    finish(app,release)


def test_quick_demo_is_explicit_and_does_not_analyze_draft_attachments(workspace):
    app,source,release=workspace
    submit(app,'',[('input.csv',b'my draft')],kind='demo');finish(app,release)
    assert source.requests[0].mode=='Demo' and source.requests[0].sample
    assert source.requests[0].uploads==[]
    assert app.session_state['stage']=='results'


def test_burst_keeps_every_event_without_artificial_completion_delay(workspace):
    app,source,release=workspace
    Event=importlib.import_module('ui.events').Event
    def events(request):
        source.requests.append(request)
        yield Event(type='run_started',payload={'question':request.question})
        for i in range(300):yield Event(type='tool_result',ts=i,payload={'result':i})
        yield Event(type='run_complete',payload={'verdict':'Finished'})
    source.events=events
    submit(app);finish(app,release)
    assert len(app.session_state['run'].raw)==302 and app.session_state['stage']=='results'
    assert len(source.requests)==1


def test_startup_error_requires_explicit_retry(workspace,monkeypatch):
    app,source,release=workspace
    adapters=importlib.import_module('ui.adapters')
    def unavailable(mode):raise RuntimeError('Source configuration is unavailable')
    monkeypatch.setattr(adapters,'source_for',unavailable)
    submit(app)
    assert app.session_state['stage']=='results' and app.error and not source.requests
    monkeypatch.setattr(adapters,'source_for',lambda mode:source)
    app.button(key='retry_run').click().run();finish(app,release)
    assert app.session_state['run'].complete and len(source.requests)==1


def test_configured_service_uses_the_same_prompt_and_running_screens(workspace,monkeypatch):
    app,source,release=workspace;release.clear()
    # Setup stays in the shared drawer, not a second set of pages.
    app.selectbox(key='setup_source').select('Live').run()
    app.text_input(key='setup_backend').set_value('http://127.0.0.1:9999').run()
    submit(app,'My question',[('evidence.csv',b'a,b\n')])
    assert source.requests[0].mode=='Live' and source.requests[0].backend=='http://127.0.0.1:9999'
    assert source.requests[0].uploads==[('evidence.csv',b'a,b\n')]
    assert_simple(app)
    assert 'cancel_run' not in [b.key for b in app.button]  # This test source has no cancellation method.
    finish(app,release)
    assert app.session_state['stage']=='results'


def test_legacy_session_states_cannot_reopen_old_pages():
    from frontend.ui.workspace import normalized_stage,STAGES
    assert STAGES=={'prompt','running','results'}
    for old in ['evidence','question','invalid','settings']:
        assert normalized_stage(old)=='prompt'
    assert normalized_stage('investigation')=='running'


def test_followup_draft_survives_theme_and_home(workspace):
    app,source,release=workspace;submit(app);finish(app,release)
    app.text_input(key='followup_prompt').set_value('Keep this unfinished follow-up')
    app.button(key='theme_toggle').click().run()
    assert app.text_input(key='followup_prompt').value=='Keep this unfinished follow-up'
    app.button(key='home').click().run();app.button(key='view_last_results').click().run()
    assert app.text_input(key='followup_prompt').value=='Keep this unfinished follow-up'
    assert len(source.requests)==1 and not app.exception
