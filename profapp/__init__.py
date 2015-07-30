from flask import Flask, session, g
from profapp.controllers.blueprints import user_bp, article_bp, filemanager_bp
import profapp.controllers.views_article as views_art
import profapp.controllers.views_auth as views_auth
import profapp.controllers.views_filemanager as views_fileman
import profapp.controllers.views_index as views_ind
import profapp.controllers.views_image_editor as views_imged
from authomatic.providers import oauth2
from authomatic import Authomatic
from profapp.models.users import User


def setup_authomatic(app):
    # authomatic = Authomatic(Config.OAUTH_CONFIG, Config.SECRET_KEY, report_errors=True)
    authomatic = Authomatic(app.config['OAUTH_CONFIG'],
                            app.config['SECRET_KEY'], report_errors=True)

    # authomatic = Authomatic(
    #     {'fb': {'consumer_key': app.config['CONSUMER_KEY'],
    #             'consumer_secret': app.config['CONSUMER_SECRET'],
    #             'class_': oauth2.Facebook,
    #             'scope': [], }},
    #     app.config['SECRET_KEY'], report_errors=False)

    def func():
        g.authomatic = authomatic
    return func


def load_user():
    g.user = None
    if 'user_id' in session.keys():
        g.user = User.query.filter_by(id=session['user_id']).first()


def create_app(config='config.ProductionDevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config)

    app.before_request(setup_authomatic(app))
    app.before_request(load_user)

    app.register_blueprint(views_ind.general_bp, url_prefix='/')
    app.register_blueprint(views_art.article_bp, url_prefix='/articles')
    app.register_blueprint(views_auth.user_bp, url_prefix='/users')
    app.register_blueprint(views_fileman.filemanager_bp, url_prefix='/filemanager')
    app.register_blueprint(views_fileman.static_bp, url_prefix='/static')
    app.register_blueprint(views_imged.image_editor_bp, url_prefix='/image_editor')


    # see: http://flask.pocoo.org/docs/0.10/patterns/sqlalchemy/
    # Flask will automatically remove database sessions at the end of the request
    # or when the application shuts down:
    from db_init import db_session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
