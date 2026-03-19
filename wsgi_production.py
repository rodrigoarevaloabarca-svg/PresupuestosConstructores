import os
import sys

sys.path.insert(0, '/home/rodrigocl/PresupuestosConstructores')

# Activar entorno virtual
activate_this = '/home/rodrigocl/PresupuestosConstructores/.venv/bin/activate_this.py'
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

# Cargar .env
env_path = '/home/rodrigocl/PresupuestosConstructores/.env'
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