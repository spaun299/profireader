from profapp import create_app

app_profi = create_app(front='n')

if __name__ == '__main__':
    app_profi.run(host='0.0.0.0', port=8080, debug=True)  # app.run(debug=True)

# import argparse
# import os, sys

    # app.run()
# ['/home/oles/prof', '/usr/local/opt/python-3.4.2/lib/python34.zip', '/usr/local/opt/python-3.4.2/lib/python3.4',
#  '/usr/local/opt/python-3.4.2/lib/python3.4/plat-linux', '/usr/local/opt/python-3.4.2/lib/python3.4/lib-dynload',
#  '/home/oles/prof/.venv/lib/python3.4/site-packages']

# ['/home/oles/prof', '/usr/local/opt/python-3.4.2/lib/python34.zip', '/usr/local/opt/python-3.4.2/lib/python3.4',
#  '/usr/local/opt/python-3.4.2/lib/python3.4/plat-linux', '/usr/local/opt/python-3.4.2/lib/python3.4/lib-dynload',
#  '/home/oles/prof/.venv/lib/python3.4/site-packages']
