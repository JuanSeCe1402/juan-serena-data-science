import re,time,json,io,os
from datetime import timedelta
from html.parser import HTMLParser
from fastapi.testclient import TestClient
from pypdf import PdfReader
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app import app
from app.config import settings
from app.models import Patient,Appointment,ConversationState,MessageLog,AuditLog
from app.time_utils import local_today
from conftest import start,post,csrf,database,db_path,cookie_data

@pytest.mark.parametrize('path',['/','/features','/case-study','/architecture','/demo','/privacy','/health'])
def test_public_routes(client,path):assert client.get(path).status_code==200

def test_public_presentation_has_required_sections_and_no_claimed_metrics(client):
    page=client.get('/case-study').text
    for title in ('Contexto','Problema','Solución construida','Arquitectura general','Funcionalidades principales','Resultados'):assert title in page
    assert 'Back to WUNSCE' in page and 'no constituyen mediciones' in page
    assert client.get('/panel',follow_redirects=False).status_code==303
    assert client.get('/openapi.json').status_code==404
    assert client.get('/webhook').status_code==404
    assert client.post('/webhook',json={}).status_code==404

@pytest.mark.parametrize('path',['/panel','/panel/calendar','/panel/patients','/panel/messages','/panel/settings','/panel/patients/1','/panel/patients/1/edit','/panel/appointment/1/reschedule'])
def test_protected_routes_with_doctor_demo(client,path):
    start(client)
    response=client.get(path)
    assert response.status_code==200 and 'DEMO AISLADA' in response.text
    assert 'Back to WUNSCE' in response.text

@pytest.mark.parametrize('path',['/demo/start','/demo/reset','/panel/appointment/create','/panel/settings','/panel/messages/send','/panel/messages/bot-mode'])
def test_csrf_required(client,path):
    start(client)
    assert client.post(path,data={}).status_code==400

@pytest.mark.parametrize('path,data',[('/panel/settings',dict(work_start='09:00',work_end='14:00',consult_minutes='30',work_days='0,1,2,3,4')),('/panel/block-day',dict(day=(local_today()+timedelta(days=3)).isoformat(),note='')),('/panel/patients/1/delete',dict(confirm_delete='ELIMINAR')),('/panel/messages/1/delete',{}),('/panel/messages/delete-conversation',dict(phone='00000002')),('/panel/messages/bot-mode',dict(phone='00000002',action='resume'))])
def test_assistant_forbidden_server_side(client,path,data):
    start(client,'assistant')
    assert post(client,path,data).status_code==403

def test_assistant_can_read_and_register_demo_reply(client):
    start(client,'assistant')
    assert client.get('/panel/settings').status_code==403
    assert post(client,'/panel/messages/send',dict(phone='00000002',body='Demostración: recibimos tu solicitud; una persona dará seguimiento.')).status_code==303
    with database(client) as db:
        message=db.query(MessageLog).filter(MessageLog.direction=='outgoing').one()
        assert message.source=='demo' and message.delivery_status=='simulated'
        state=db.query(ConversationState).filter(ConversationState.phone=='00000002').one()
        assert state.bot_paused and not state.human_requested

@pytest.mark.parametrize('changes',[dict(patient_name='Real Name'),dict(patient_phone='5215555555555'),dict(patient_age='22'),dict(patient_age='120'),dict(reason='Clinical free text'),dict(day='bad-date'),dict(start_time='25:00'),dict(appointment_type='unknown')])
def test_real_or_invalid_data_rejected(client,changes):
    start(client)
    values=dict(patient_name='Paciente Demo 04',patient_phone='00000004',day=(local_today()+timedelta(days=1)).isoformat(),start_time='09:30',reason='Demostración administrativa')
    values.update(changes)
    response=post(client,'/panel/appointment/create',values)
    assert response.status_code in (422,303)
    with database(client) as db:assert db.query(Appointment).count()==1


def available(client,day=None):
    day=day or local_today()+timedelta(days=1)
    for i in range(8):
        r=client.get('/panel/slots',params=dict(day=day.isoformat(),appointment_type='consulta'))
        if r.json()['slots']:return day,r.json()['slots']
        day+=timedelta(days=1)
    raise AssertionError('No available demo day')

def test_create_reschedule_cancel_and_stale_form(client):
    start(client)
    day,slots=available(client)
    values=dict(patient_name='Paciente Demo 04',patient_phone='00000004',day=day.isoformat(),start_time=slots[0],reason='Demostración administrativa')
    assert post(client,'/panel/appointment/create',values).status_code==303
    with database(client) as db:
        appt=db.query(Appointment).filter(Appointment.patient_id==4).one();identifier=appt.id;version=appt.version
    # A second reservation cannot overlap the interval.
    values.update(patient_name='Paciente Demo 05',patient_phone='00000005')
    post(client,'/panel/appointment/create',values)
    with database(client) as db:assert db.query(Appointment).count()==2
    new_day,new_slots=available(client,day+timedelta(days=1))
    assert post(client,f'/panel/appointment/{identifier}/reschedule',dict(day=new_day.isoformat(),start_time=new_slots[0],expected_version=str(version))).status_code==303
    assert post(client,f'/panel/appointment/{identifier}/cancel',dict(expected_version=str(version),reason='Demostración administrativa')).status_code==409
    with database(client) as db:new_version=db.get(Appointment,identifier).version
    assert post(client,f'/panel/appointment/{identifier}/cancel',dict(expected_version=str(new_version),reason='Demostración administrativa')).status_code==303
    with database(client) as db:assert db.get(Appointment,identifier).status=='cancelada'

def test_invalid_settings_and_query_ranges(client):
    start(client)
    settings_data=dict(work_start='14:00',work_end='09:00',consult_minutes='0',work_days='9')
    assert post(client,'/panel/settings',settings_data).status_code==422
    assert client.get('/panel/calendar/events',params={'start':'2026-01-01','end':'2027-01-01'}).status_code==400
    assert client.get('/panel/slots',params={'day':'invalid'}).status_code==400
    assert post(client,'/panel/messages/send',{'phone':'00000002','body':'Some real or clinical information'}).status_code==422


def test_handoff_stays_paused_on_message_and_clear_then_explicit_resume(client):
    start(client)
    assert post(client,'/panel/demo-incoming',dict(phone='00000001',event='human')).status_code==303
    assert post(client,'/panel/demo-incoming',dict(phone='00000001',event='message')).status_code==303
    with database(client) as db:
        state=db.query(ConversationState).filter_by(phone='00000001').one();assert state.bot_paused and state.human_requested
        assert db.query(MessageLog).filter_by(phone='00000001',direction='outgoing').count()==0
    assert post(client,'/panel/messages/delete-conversation',dict(phone='00000001')).status_code==303
    with database(client) as db:
        state=db.query(ConversationState).filter_by(phone='00000001').one();assert state.bot_paused and state.pause_reason=='manual'
    assert post(client,'/panel/messages/bot-mode',dict(phone='00000001',action='resume')).status_code==303
    with database(client) as db:
        assert not db.query(ConversationState).filter_by(phone='00000001').one().bot_paused
        assert all(row.details is None for row in db.query(AuditLog))


def test_session_isolation_reset_and_tampered_cookie(client):
    start(client)
    other=TestClient(app);start(other,'assistant')
    assert db_path(client)!=db_path(other)
    post(client,'/panel/patients/1/edit',dict(patient_name='Paciente Demo 09',patient_phone='00000009',patient_age=''))
    assert 'Paciente Demo 09' in client.get('/panel/patients').text
    assert 'Paciente Demo 09' not in other.get('/panel/patients').text
    old=db_path(client);other_path=db_path(other)
    assert post(client,'/demo/reset').status_code==303
    assert not old.exists() and other_path.exists()
    assert other.get('/panel').status_code==200
    other.cookies.set('esculapio_session','tampered-cookie')
    assert other.get('/panel',follow_redirects=False).status_code==303


def test_expiration_capacity_payload_and_headers(client):
    start(client)
    path=db_path(client);os.utime(path,(time.time()-1900,time.time()-1900))
    assert client.get('/panel',follow_redirects=False).status_code==303
    assert not path.exists()
    settings.MAX_SPACES=0
    assert client.post('/demo/start',data=dict(role='doctor',csrf_token=csrf(client))).status_code==503
    settings.MAX_SPACES=50;start(client)
    assert client.post('/panel/settings',content=b'x'*17000,headers={'Content-Type':'application/x-www-form-urlencoded'}).status_code==413
    assert client.get('/panel').headers['Cache-Control']=='no-store'
    assert "frame-ancestors 'none'" in client.get('/').headers['Content-Security-Policy']
    assert client.get('/health').json()=={'status':'ok','service':'esculapio-web'}


def test_database_foreign_keys_and_constraints(client):
    start(client)
    with database(client) as db:
        assert db.execute(text('PRAGMA foreign_keys')).scalar()==1
        with pytest.raises(IntegrityError):db.execute(text("INSERT INTO appointments(patient_id,date,start_time,end_time,duration_minutes,status,version) VALUES(999,'2026-10-25','09:00','09:30',30,'confirmada',1)"));db.commit()
        db.rollback()
        with pytest.raises(IntegrityError):db.execute(text("UPDATE appointments SET status='invalid'"));db.commit()


def test_demo_pdf_and_media_protection(client):
    start(client)
    with database(client) as db:day=db.query(Appointment).first().date.isoformat()
    response=client.get('/panel/agenda/pdf',params={'day':day})
    assert response.status_code==200 and response.headers['Content-Type']=='application/pdf'
    pdf=PdfReader(io.BytesIO(response.content));text_pdf=''.join(p.extract_text() for p in pdf.pages)
    assert 'SOLO DATOS FICTICIOS' in text_pdf and 'Paciente Demo 01' in text_pdf
    assert client.get('/panel/media/999').status_code==404
    assert client.get('/panel/agenda/pdf',params={'day':'bad-date'}).status_code==400
    assert post(client,'/panel/agenda/send').status_code==404

class Tags(HTMLParser):
    def __init__(self):super().__init__();self.tags=[]
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))

def test_templates_assets_csrf_no_inline_handlers(client):
    start(client)
    for path in ('/','/case-study','/demo','/panel','/panel/messages','/panel/calendar','/panel/patients','/panel/settings','/panel/patients/1/edit','/panel/appointment/1/reschedule'):
        r=client.get(path);assert r.status_code==200
        parsed=Tags();parsed.feed(r.text)
        assert len([1 for tag,a in parsed.tags if tag=='h1'])==1
        for tag,a in parsed.tags:
            assert not any(k.startswith('on') for k in a)
            if tag=='script':assert 'src' in a
            if tag in ('script','img','link'):
                url=a.get('src') or a.get('href')
                if url and url.startswith('/static/'):assert client.get(url).status_code==200
        if 'method="post"' in r.text:assert 'name="csrf_token"' in r.text


def test_chunked_body_limit_without_content_length(client):
    start(client)
    def chunks():
        for _ in range(20):yield b'x'*1000
    assert client.post('/panel/settings',content=chunks(),headers={'Content-Type':'application/x-www-form-urlencoded'}).status_code==413


def test_demo_cannot_enable_notifications_or_implicit_auto_resume(client):
    start(client)
    data=dict(work_start='09:00',work_end='14:00',consult_minutes='30',work_days='0,1,2,3,4')
    assert post(client,'/panel/settings',data).status_code==303
    with database(client) as db:
        from app.models import ScheduleSettings
        assert db.query(ScheduleSettings).one().human_auto_resume_minutes==0
    data['alert_whatsapp_enabled']=''
    assert post(client,'/panel/settings',data).status_code==422
    assert client.get('/panel/patients/'+('9'*100)).status_code==422
    assert client.get('/panel',params={'patient_id':'9'*100}).status_code==422


def test_doctor_attendance_and_patient_deletion_lifecycle(client):
    start(client)
    assert post(client,'/panel/appointment/1/mark',dict(expected_version='1',result='atendida')).status_code==409
    with database(client) as db:
        appt=db.get(Appointment,1);appt.date=local_today()-timedelta(days=1);appt.status='pendiente_revision';db.commit();version=appt.version
    assert post(client,'/panel/appointment/1/mark',dict(expected_version=str(version),result='atendida')).status_code==303
    assert post(client,'/panel/patients/1/delete',dict(confirm_delete='wrong')).status_code==303
    with database(client) as db:assert db.get(Patient,1) is not None
    deleted=post(client,'/panel/patients/1/delete',dict(confirm_delete='ELIMINAR'))
    assert deleted.status_code==303 and 'Demo' not in deleted.headers['location']
    with database(client) as db:
        assert db.get(Patient,1) is None
        assert db.query(Appointment).filter_by(patient_id=1).count()==0
