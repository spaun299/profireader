import os
import sys

# Install venv by `virtualenv --distribute venv`
# Then install depedencies: `source venv/bin/active`
# `pip install -r requirements.txt`

activate_this = '/var/www/profireader/.venv/bin/activate_this.py'
# execfile(activate_this, dict(__file__=activate_this))
exec(open(activate_this).read())

path = os.path.join(os.path.dirname(__file__), os.pardir)
if path not in sys.path:
    sys.path.append(path)

sys.path.insert(0, '/var/www/profireader')
sys.path.insert(0, '/var/www/profireader/.venv/lib/python3.4/site-packages/')

from profapp import create_app

application=create_app(front='n')

