import os

# Cargar .env desde el directorio del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'constructor_express.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
