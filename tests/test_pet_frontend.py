"""Pet presentation must preserve source events, immutable requests and TRACE results."""
from copy import deepcopy
from pathlib import Path
import importlib
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def pet_app(monkeypatch):
    monkeypatch.setenv('TRACE_START_SCREEN','pets')
    monkeypatch.syspath_prepend(str(ROOT/'frontend'))
    adapters=importlib.import_module('ui.adapters')
    Event=importlib.import_module('ui.events').Event
    class Source:
        requests=[]
        def capabilities(self,backend):
            return {'run_mode':'mock','defaults':{},'specialist_roles':[]}
        def events(self,request):
            self.requests.append(deepcopy(request))
            yield Event(type='run_started',run_id='pet-test',payload={'question':request.question})
            yield Event(type='agent_spawned',agent_id='g1',agent_role='genomics',payload={'message':'Reviewing supplied evidence.'})
            yield Event(type='finding',agent_id='g1',agent_role='genomics',payload={'text':'A source-linked finding. A material limitation remains.','provenance':[{'file':'example.vcf','line':3}]})
            yield Event(type='agent_spawned',agent_id='c1',agent_role='critic',payload={'message':'Checking the interpretation.'})
            yield Event(type='run_complete',payload={'verdict':'Preserved TRACE result','confidence':0.6,'abstained':False})
    source=Source();source.requests=[]
    monkeypatch.setattr(adapters,'source_for',lambda mode:source)
    st.cache_data.clear()
    start_module=importlib.import_module('ui.pet_start')
    def browser_component(draft,**kwargs):
        action=st.session_state.pop('_test_composer_action',None)
        if action:
            draft['question']=action['question'];draft['uploads']=action['uploads']
        return action
    monkeypatch.setattr(start_module,'render_composer',browser_component)
    app=AppTest.from_file(str(ROOT/'frontend/app.py'),default_timeout=15).run()
    assert not app.exception
    yield app,source
    st.cache_data.clear()


def test_prompt_first_submission_preserves_files_and_results(pet_app):
    app,source=pet_app
    assert not app.get('file_uploader') and not app.text_area
    assert not app.multiselect and not source.requests
    files=[('case.vcf',b'##fileformat=VCFv4.2\n')]
    app.session_state['_test_composer_action']={'type':'start','question':'Does this evidence support the hypothesis?','uploads':files}
    app.run()
    assert not app.exception
    assert len(source.requests)==1
    assert source.requests[0].question=='Does this evidence support the hypothesis?'
    assert source.requests[0].uploads==files and not source.requests[0].sample
    assert app.session_state['run'].complete
    assert app.session_state['stage']=='investigation'
    assert app.session_state['pet_activity'].current.role=='genomics'
    assert any('scientist-pet' in m.value for m in app.markdown)
    app.button(key='pet_results').click().run()
    assert app.session_state['stage']=='results'
    assert [t.label for t in app.tabs]==['Evidence','Weak points','Agent activity','Run details']
    assert any('Preserved TRACE result' in m.value for m in app.markdown)
    assert app.session_state['run'].findings[0].provenance==[{'file':'example.vcf','line':3}]
    assert len(source.requests)==1 and not app.exception


def test_quick_demo_and_advanced_setup_are_explicit(pet_app):
    app,source=pet_app
    app.session_state['_test_composer_action']={'type':'demo','question':'','uploads':[]}
    app.run()
    assert source.requests[0].mode=='Demo' and source.requests[0].sample
    assert source.requests[0].uploads==[]
    app.button(key='pet_results').click().run()
    app.button(key='results_new').click().run()
    assert not app.get('file_uploader') and not app.text_area
    app.button(key='pet_advanced').click().run()
    assert app.button(key='evidence_next')
    assert len(source.requests)==1 and not app.exception


def test_pet_queue_pause_step_and_future_data_do_not_change_report():
    from frontend.ui.pet_activity import PetActivity,excerpt
    from frontend.ui.events import Event
    from frontend.ui.state import RunState
    now=[0.]
    p=PetActivity(clock=lambda:now[0])
    events=[Event(type='agent_spawned',agent_id='a',agent_role='genomics'),
            Event(type='finding',agent_id='a',agent_role='genomics',payload={'text':'First observation. Important limitation. Extra detail.'}),
            Event(type='agent_spawned',agent_id='b',agent_role='critic'),
            Event(type='finding',agent_id='b',agent_role='critic',payload={'text':'Critique of the first observation.'}),
            Event(type='run_complete',payload={'verdict':'Original verdict'})]
    state=RunState()
    for e in events:state.apply(e)
    original=deepcopy(state)
    p.ingest(events,complete=True)
    assert p.current.agent_id=='a' and p.current.text=='First observation. Important limitation.'
    p.pause();now[0]=100;p.advance();assert p.current.agent_id=='a'
    p.step();assert p.current.agent_id=='b'
    p.resume();now[0]+=5;p.advance();assert p.finished
    assert state==original
    assert excerpt('Estimated value is 0.78. A caveat applies. Third sentence.')=='Estimated value is 0.78. A caveat applies.'


def test_unknown_role_uses_saved_right_facing_generic_and_escapes_content():
    from frontend.ui.pets import pet_picture,pet_key
    assert pet_key('../../unknown')=='generic-scientist'
    html=pet_picture('<script>alert(1)</script>',True)
    assert '<script>' not in html and 'generic-scientist.webp' in html
    assert 'prefers-reduced-motion: reduce' in html and 'generic-scientist.png' in html
    import json
    manifest=json.loads((ROOT/'frontend/static/scientist-pets/manifest.json').read_text())
    assert manifest['horizontalMirrorApplied'] is True


def test_composer_validates_attachment_bytes_before_submission():
    import base64
    from frontend.ui.composer import validate_action
    payload={'id':'test','type':'start','question':'  Check this evidence  ','files':[{'name':'sample.csv','size':4,'data':base64.b64encode(b'a,b\n').decode()}]}
    parsed=validate_action(payload)
    assert parsed['question']=='Check this evidence' and parsed['uploads']==[('sample.csv',b'a,b\n')]
    for change in [{'name':'../sample.csv'},{'size':3},{'data':'not base64!!'},{'name':'execute.exe'}]:
        bad=deepcopy(payload);bad['files'][0].update(change)
        with pytest.raises(ValueError):validate_action(bad)
    with pytest.raises(ValueError):validate_action({**payload,'question':'   '})
    assert validate_action({**payload,'type':'untrusted_command'}) is None
