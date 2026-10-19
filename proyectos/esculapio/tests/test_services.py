import asyncio,hashlib,hmac,json,threading
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Appointment,ConversationState,ScheduleSettings
from app.database import make_engine
from app.scheduler import book_slot,get_slots_for_date,reschedule_slot
from app.human_mode import mark_human_request,mark_human_activity,auto_resume_if_due,pause_manually
from app.integrations import split_events
from app.main import _verify_webhook_signature
from app.time_utils import local_today,local_now
from conftest import start,database,db_path


def test_concurrent_booking_only_one_succeeds(client):
    start(client)
    day=local_today()+timedelta(days=1)
    with database(client) as db:
        for _ in range(8):
            slots=get_slots_for_date(db,day)
            if slots:break
            day+=timedelta(days=1)
        slot=slots[0]
    path=db_path(client);barrier=threading.Barrier(2)
    def reserve(patient):
        engine=make_engine('sqlite:///'+str(path))
        try:
            with Session(engine) as db:
                barrier.wait();result=book_slot(db,patient,day,slot,'Demostración administrativa');return result.id if result else None
        finally:engine.dispose()
    with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(reserve,[2,3]))
    assert sum(r is not None for r in results)==1


def test_slots_respect_grid_overrides_horizon_and_stale_version(client):
    start(client)
    from datetime import time
    from app.models import DateOverride
    with database(client) as db:
        original=db.get(Appointment,1)
        assert reschedule_slot(db,1,original.date,time(9,1),expected_version=original.version) is None
        assert get_slots_for_date(db,local_today()+timedelta(days=91))==[]
        db.add(DateOverride(date=original.date,is_blocked=True));db.commit()
        assert get_slots_for_date(db,original.date)==[]


def test_human_auto_resume_only_after_activity_and_never_manual_pause(client):
    start(client)
    with database(client) as db:
        cfg=db.query(ScheduleSettings).first();cfg.human_auto_resume_minutes=15
        state=db.query(ConversationState).first()
        mark_human_request(db,state)
        assert not auto_resume_if_due(db,state)
        mark_human_activity(db,state)
        state.last_human_activity_at=local_now().replace(tzinfo=None)-timedelta(minutes=16)
        assert auto_resume_if_due(db,state)
        pause_manually(state);state.last_human_activity_at=local_now().replace(tzinfo=None)-timedelta(days=1)
        assert not auto_resume_if_due(db,state)


def envelope(messages):return {'entry':[{'changes':[{'field':'messages','value':{'messages':messages}}]}]}

def test_webhook_batch_and_signature(monkeypatch):
    payload=envelope([{'id':'demo-a','from':'00000001','type':'text','text':{'body':'hola'}},{'id':'demo-b','from':'00000002','type':'text','text':{'body':'hola'}}])
    events=split_events(payload)
    assert len(events)==2
    monkeypatch.setattr(settings,'META_APP_SECRET','unit-test-signature-secret-not-a-real-provider')
    raw=json.dumps(payload).encode()
    signature='sha256='+hmac.new(settings.META_APP_SECRET.encode(),raw,hashlib.sha256).hexdigest()
    assert _verify_webhook_signature(raw,signature)
    assert not _verify_webhook_signature(raw+b' ',signature)
    assert not _verify_webhook_signature(raw,None)

@pytest.mark.parametrize('payload',[[],{}, {'entry':['invalid']},envelope([{'id':'demo','from':'real-person','type':'text','text':{'body':'hola'}}]),envelope([{'id':'demo','from':'00000001','type':'text','text':{'body':'x'*4001}}])])
def test_malformed_webhooks_rejected(payload):
    with pytest.raises((ValueError,TypeError)):split_events(payload)


def test_all_external_transport_forbidden_in_demo(client,monkeypatch):
    start(client)
    import app.whatsapp_client as transport
    from app.database import workspace
    token=workspace.set(db_path(client))
    def fail(*args,**kwargs):raise AssertionError('No external network allowed')
    monkeypatch.setattr(transport.httpx,'AsyncClient',fail)
    try:
        assert asyncio.run(transport.send_text('00000001','Demostración: confirmación administrativa de horario.'))
        assert asyncio.run(transport.upload_media('missing.pdf')) is None
        assert asyncio.run(transport.download_media('fake-id')) is None
    finally:workspace.reset(token)
