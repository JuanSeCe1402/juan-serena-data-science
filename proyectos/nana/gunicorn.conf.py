import os
port=int(os.environ.get('PORT') or '8000')
if not 1<=port<=65535: raise ValueError('PORT must be between 1 and 65535')
bind=f'0.0.0.0:{port}'
workers=1
threads=2
timeout=60
accesslog='-'
errorlog='-'
# Preload shares the ephemeral local development key across workers if scaled.
preload_app=True
