"""Live progress and advisory budgeting without external calls."""
import asyncio
import uuid
import pytest
from app import worker as module
from app.cases import get_case
from app.store import Store
from app.worker import Worker


def setup_run(tmp_path):
    store = Store(tmp_path / 'activity.sqlite')
    case = get_case('cd19-car-t')
    run = store.create(case, {'hypothesis':'A different user-supplied research hypothesis.', 'source_name':'User message', 'mode':'live', 'idempotency_key':uuid.uuid4().hex})
    return store, run['id'], Worker(store)


def test_advisory_wall_and_tool_thresholds_warn_once_then_complete(tmp_path, monkeypatch):
    monkeypatch.setenv('TEAM_TBD_BUDGET_MODE','advisory')
    monkeypatch.setattr(module,'MAX_SECONDS',0.01)
    monkeypatch.setattr(module,'MAX_TOOL_CALLS',1)
    store, rid, worker = setup_run(tmp_path)
    async def work(_):
        await worker.emit(rid,'statistician','Reading accepted data','Testing progress', 'running','agent')
        assert store.get(rid)['active_agent']=='statistician'
        assert store.get(rid)['stage']=='statistician'
        await worker.emit(rid,'statistician','Read evidence','First')
        await worker.emit(rid,'statistician','Check units','Second')
        await worker.emit(rid,'statistician','Review diagnostics','Third')
        await asyncio.sleep(.03)
        store.mutate(rid,lambda r:r.update(status='completed',stage='completed'))
    monkeypatch.setattr(worker,'investigation',work)
    asyncio.run(worker.execute(rid))
    run=store.get(rid)
    assert run['status']=='completed' and run['active_agent'] is None
    assert run['usage']['tool_calls']==3
    assert sorted(a['category'] for a in run['budget_alerts'])==['elapsed_seconds','worker_tool_operations']
    assert len([e for e in run['events'] if e['type']=='budget'])==2
    assert run['worker_budget_policy']['mode']=='advisory'


def test_enforced_worker_time_budget_still_stops(tmp_path, monkeypatch):
    monkeypatch.setenv('TEAM_TBD_BUDGET_MODE','enforced')
    monkeypatch.setattr(module,'MAX_SECONDS',0.01)
    store,rid,worker=setup_run(tmp_path)
    async def work(_): await asyncio.sleep(.2)
    monkeypatch.setattr(worker,'investigation',work)
    asyncio.run(worker.execute(rid))
    assert store.get(rid)['status']=='budget_exhausted'


def test_worker_budget_mode_is_pinned_for_operation(tmp_path, monkeypatch):
    monkeypatch.setenv('TEAM_TBD_BUDGET_MODE','advisory')
    monkeypatch.setattr(module,'MAX_TOOL_CALLS',0)
    store,rid,worker=setup_run(tmp_path)
    async def work(_):
        monkeypatch.setenv('TEAM_TBD_BUDGET_MODE','enforced')
        worker.check(rid)
        store.mutate(rid,lambda r:r.update(status='completed'))
    monkeypatch.setattr(worker,'investigation',work)
    asyncio.run(worker.execute(rid))
    assert store.get(rid)['status']=='completed'
    assert store.get(rid)['worker_budget_policy']['mode']=='advisory'


def test_budget_alert_does_not_hide_current_agent(tmp_path, monkeypatch):
    monkeypatch.setenv('TEAM_TBD_BUDGET_MODE','advisory')
    store,rid,worker=setup_run(tmp_path)
    async def work(_):
        await worker.emit(rid,'reviewer','Independent review started','Review', 'running','agent')
        await worker.emit(rid,'model','Budget threshold crossed','Continues', 'warning','budget')
        assert store.get(rid)['active_agent']=='reviewer'
        store.mutate(rid,lambda r:r.update(status='completed'))
    monkeypatch.setattr(worker,'investigation',work)
    asyncio.run(worker.execute(rid))
    assert store.get(rid)['budget_alerts'][0]['detail']=='Continues'
