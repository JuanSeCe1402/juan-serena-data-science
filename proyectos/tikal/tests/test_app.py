from app import app

def test_health():
 c=app.test_client();assert c.get('/health').status_code==200
