from copy import deepcopy
from threading import Event as Signal
from frontend.ui.demo_pacing import PacedDemoSource,DEMO_DURATION_SECONDS
from frontend.ui.events import Event
from frontend.ui.adapters import RunRequest
from frontend.ui.runtime import BackgroundRun
from frontend.ui.followup import FollowUpSource


def events():
    return [Event(type='run_started',payload={'question':'Question'}),
            Event(type='agent_spawned',agent_id='lead',agent_role='orchestrator'),
            Event(type='agent_message',agent_id='lead',payload={'message':'Initial plan.'}),
            Event(type='agent_spawned',agent_id='bio',agent_role='genomics'),
            Event(type='finding',agent_id='bio',payload={'text':'A source observation.','provenance':[{'file':'x','line':2}]}),
            Event(type='agent_spawned',agent_id='critic',agent_role='critic'),
            Event(type='agent_message',agent_id='critic',payload={'text':'The limitation remains.'}),
            Event(type='run_complete',payload={'verdict':'Original outcome','confidence':.4})]


class Source:
    def __init__(self,items):self.items=items;self.closed=False;self.calls=0
    def events(self,request):
        self.calls+=1
        try:yield from self.items
        finally:self.closed=True


def test_demo_takes_25_seconds_without_changing_events_or_reexecuting():
    now=[0.];items=events();before=deepcopy(items);source=Source(items)
    def wait(seconds):now[0]+=seconds;return False
    paced=PacedDemoSource(source,clock=lambda:now[0],wait=wait)
    delivered=[]
    for event in paced.events(RunRequest(mode='Demo',question='Question')):
        delivered.append((now[0],event))
    assert delivered[0][0]==0
    assert delivered[-1][0]==DEMO_DURATION_SECONDS==25
    assert [e for _,e in delivered]==before and items==before
    assert source.calls==1 and source.closed
    assert len({time for time,_ in delivered})>=4


def test_demo_errors_do_not_wait_for_the_display_timer():
    now=[0.]
    source=Source([Event(type='error',payload={'message':'Bad input','fatal':True}),
                   Event(type='run_complete',payload={'error':'Bad input','status':'error'})])
    def wait(seconds):raise AssertionError('Failure should be returned immediately')
    result=list(PacedDemoSource(source,clock=lambda:now[0],wait=wait).events(RunRequest(mode='Demo',question='Question')))
    assert result[-1].payload['status']=='error' and now[0]==0


def test_cancel_interrupts_a_demo_wait_including_followups():
    for followup in [False,True]:
        entered=Signal();paced=PacedDemoSource(Source(events()))
        def wait(seconds):entered.set();return paced.stopped.wait(3)
        paced.wait=wait
        source=FollowUpSource(paced) if followup else paced
        job=BackgroundRun(source,RunRequest(mode='Demo',question='Question',context={'question':'Earlier'} if followup else {}),can_cancel=True)
        assert entered.wait(1)
        job.request_cancel();job.thread.join(1)
        assert job.finished.is_set()
        delivered=job.drain()
        assert delivered[-1].type=='run_complete' and delivered[-1].payload['status']=='cancelled'
