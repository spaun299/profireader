from profapp import create_app
import argparse
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware




# if __name__ == '__main__':
parser = argparse.ArgumentParser(description='profireader application type')
parser.add_argument("apptype", default='profi')
args = parser.parse_args()
app = create_app(apptype=args.apptype)
if __name__ == '__main__':

    session_opts = {
    'session.type': 'ext:memcached',
    'session.url': 'memcached.profi:11211'
    }

    class BeakerSessionInterface(SessionInterface):
        def open_session(self, app, request):
            session = request.environ['beaker.session']
            return session

        def save_session(self, app, session, response):
            session.save()


    # app.run(host='127.40.71.198', port=8080)  #app.run(debug=True)
    if args.apptype == 'front':
        port = 8888
    elif args.apptype == 'file':
        port = 9001
    else:
        port = 8080
    app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
    app.session_interface = BeakerSessionInterface()
    app.run(port=port, host='0.0.0.0', debug=True)  # app.run(debug=True)







