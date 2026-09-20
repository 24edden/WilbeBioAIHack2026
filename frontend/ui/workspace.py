"""The only three UI states. Navigation never submits or cancels an investigation."""
from copy import deepcopy
from uuid import uuid4
import os

STAGES = frozenset({'prompt', 'running', 'results'})


def normalized_stage(stage):
    return {'evidence':'prompt','question':'prompt','investigation':'running'}.get(stage,stage) if stage in STAGES|{'evidence','question','investigation'} else 'prompt'


def new_draft():
    return {'composer_id':uuid4().hex,'question':'','uploads':[],'config':{'task_mode':'auto'},
            'mode':'Live' if os.environ.get('TRACE_BACKEND_URL','').strip() else 'Demo',
            'backend':os.environ.get('TRACE_BACKEND_URL','http://localhost:8000').strip()}


def result_kind(state):
    if state.status=='cancelled':return 'cancelled'
    terminal=next((e for e in reversed(state.raw) if e.type=='run_complete'),None)
    fatal=any(e.type=='error' and e.payload.get('fatal') for e in state.raw)
    if not state.complete or state.status in {'error','failed'} or fatal or (terminal and terminal.payload.get('error')):
        return 'interrupted'
    return 'complete'


def save_result(session):
    state=session['run']
    if not (state.complete or state.errors):return
    history=session['previous_runs']
    if any(item['id']==session['result_id'] for item in history):return
    history.append({'id':session['result_id'],'run':deepcopy(state),'request':deepcopy(session['submitted'])})
    session['previous_runs']=history[-5:]


def collect_updates(session):
    """Always drain, including while the user is composing another question."""
    job=session.get('job')
    if not job:return False
    for event in job.drain():session['run'].apply(event)
    if not job.active and not job.completion_announced:
        job.completion_announced=True
        save_result(session)
        if session['stage']=='running':session['stage']='results'
        return True
    return False
