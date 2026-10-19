"""Validate and split batches before invoking the existing event processor."""
import re

def split_events(payload,expected_phone_id=None):
    if not isinstance(payload,dict) or not isinstance(payload.get('entry'),list):raise ValueError('Invalid envelope')
    result=[]
    for entry in payload['entry']:
        if not isinstance(entry,dict) or not isinstance(entry.get('changes'),list):raise ValueError('Invalid entry')
        for change in entry['changes']:
            if not isinstance(change,dict):raise ValueError('Invalid change')
            if change.get('field') not in (None,'messages','smb_message_echoes'):continue
            value=change.get('value')
            if not isinstance(value,dict):raise ValueError('Invalid value')
            if expected_phone_id is not None and value.get('metadata',{}).get('phone_number_id')!=expected_phone_id:raise ValueError('Wrong business channel')
            for key in ('messages','statuses','message_echoes'):
                items=value.get(key,[])
                if not isinstance(items,list):raise ValueError('Invalid items')
                for item in items:
                    if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not 1<=len(item['id'])<=180:raise ValueError('Invalid event identifier')
                    if key=='messages' and not re.fullmatch('[0-9]{8,15}',str(item.get('from',''))):raise ValueError('Invalid sender')
                    if key=='message_echoes' and not re.fullmatch('[0-9]{8,15}',str(item.get('to',''))):raise ValueError('Invalid recipient')
                    if key=='statuses' and item.get('status') not in ('sent','delivered','read','failed'):raise ValueError('Invalid status')
                    if key=='messages' and item.get('type')=='text':
                        text=item.get('text',{}).get('body') if isinstance(item.get('text'),dict) else None
                        if not isinstance(text,str) or len(text)>4000:raise ValueError('Invalid text')
                    result.append({'entry':[{'changes':[{'field':change.get('field','messages'),'value':{key:[item]}}]}]})
                    if len(result)>50:raise ValueError('Too many events')
    return result
