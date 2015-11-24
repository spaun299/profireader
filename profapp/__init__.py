from flask import Flask, session, g, request, redirect, current_app
from authomatic.providers import oauth2
from authomatic import Authomatic
from profapp.controllers.blueprints_register import register as register_blueprints
from profapp.controllers.blueprints_register import register_front as register_blueprints_front
from profapp.controllers.blueprints_register import register_file as register_blueprints_file

from flask import url_for
from profapp.controllers.errors import csrf
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.login import LoginManager, \
    login_user, logout_user, current_user, \
    login_required
from flask.ext.mail import Mail
import hashlib
from flask.ext.login import AnonymousUserMixin
from .constants.SOCIAL_NETWORKS import INFO_ITEMS_NONE, SOC_NET_FIELDS
from .constants.USER_REGISTERED import REGISTERED_WITH
from flask import globals
import re
from flask.ext.babel import Babel, gettext
import jinja2
from .models.users import User
from .models.config import Config
from profapp.controllers.errors import BadDataProvided
from .models.translate import TranslateTemplate
import json


def req(name, allowed=None, default=None, exception=True):
    ret = request.args.get(name)
    if allowed and (ret in allowed):
        return ret
    elif default is not None:
        return default
    elif exception:
        raise BadDataProvided
    else:
        return None


def filter_json(json, *args, prefix='', NoneTo='', ExceptionOnNotPresent=False):
    ret = {}
    req_columns = {}
    req_relationships = {}

    for arguments in args:
        for argument in re.compile('\s*,\s*').split(arguments):
            columnsdevided = argument.split('.')
            column_names = columnsdevided.pop(0)
            for column_name in column_names.split('|'):
                if len(columnsdevided) == 0:
                    req_columns[column_name] = NoneTo if (column_name not in json or json[column_name] is None) else \
                        json[column_name]
                else:
                    if column_name not in req_relationships:
                        req_relationships[column_name] = []
                    req_relationships[column_name].append(
                        '.'.join(columnsdevided))

    for col in json:
        if col in req_columns or '*' in req_columns:
            ret[col] = NoneTo if (col not in json or json[col] is None) else json[col]
            if col in req_columns:
                del req_columns[col]
    if '*' in req_columns:
        del req_columns['*']

    if len(req_columns) > 0:
        columns_not_in_relations = list(set(req_columns.keys()) - set(json.keys()))
        if len(columns_not_in_relations) > 0:
            if ExceptionOnNotPresent:
                raise ValueError(
                    "you requested not existing json value(s) `%s%s`" % (
                        prefix, '`, `'.join(columns_not_in_relations),))
            else:
                for notpresent in columns_not_in_relations:
                    ret[notpresent] = NoneTo

        else:
            raise ValueError("you requested for attribute(s) but "
                             "relationships found `%s%s`" % (
                                 prefix, '`, `'.join(set(json.keys()).
                                     intersection(
                                     req_columns.keys())),))

    for relationname, relation in json.items():
        if relationname in req_relationships or '*' in \
                req_relationships:
            if relationname in req_relationships:
                nextlevelargs = req_relationships[relationname]
                del req_relationships[relationname]
            else:
                nextlevelargs = req_relationships['*']
            related_obj = relation
            if type(json) is dict:
                ret[relationname] = [
                    child.filter_json(*nextlevelargs,
                                      prefix=prefix + relationname + '.'
                                      ) for child in
                    related_obj]
            else:
                ret[relationname] = None if related_obj is None else related_obj.filter_json(*nextlevelargs,
                                                                                             prefix=prefix + relationname + '.')

    if '*' in req_relationships:
        del req_relationships['*']

    if len(req_relationships) > 0:
        relations_not_in_columns = list(set(
            req_relationships.keys()) - set(json))
        if len(relations_not_in_columns) > 0:
            raise ValueError(
                "you requested not existing json(s) `%s%s`" % (
                    prefix, '`, `'.join(relations_not_in_columns),))
        else:
            raise ValueError("you requested for json deeper than json is(s) but "
                             "column(s) found `%s%s`" % (
                                 prefix, '`, `'.join(set(json).intersection(
                                     req_relationships)),))

    return ret


def db_session_func(db_config):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    engine = create_engine(db_config)
    g.sql_connection = engine.connect()
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    return db_session


def load_database(db_config):
    def load_db():
        db_session = db_session_func(db_config)
        g.db = db_session
        g.req = req
        g.filter_json = filter_json
        g.get_url_adapter = get_url_adapter

    return load_db


def close_database(exception):
    db = getattr(g, 'db', None)
    sql_connection = getattr(g, 'sql_connection', None)
    if sql_connection:
        sql_connection.close()
    if db is not None:
        if exception:
            db.rollback()
        else:
            db.commit()
            db.close()


def setup_authomatic(app):
    authomatic = Authomatic(app.config['OAUTH_CONFIG'],
                            app.config['SECRET_KEY'],
                            report_errors=True)

    def func():
        g.authomatic = authomatic

    return func


def load_user():
    user_init = current_user
    user = None

    user_dict = INFO_ITEMS_NONE.copy()
    user_dict['logged_via'] = None
    user_dict['registered_tm'] = None
    user_dict['lang'] = 'uk'
    #  ['id', 'email', 'first_name', 'last_name', 'name', 'gender', 'link', 'phone']

    if user_init.is_authenticated():
        from profapp.models.users import User

        id = user_init.get_id()
        # user = g.db.query(User).filter_by(id=id).first()
        user = current_user
        logged_via = REGISTERED_WITH[user.logged_in_via()]
        user_dict['logged_via'] = logged_via

        user_dict['profile_completed'] = user.profile_completed()

        for attr in SOC_NET_FIELDS:
            if attr == 'link' or attr == 'phone':
                user_dict[attr] = \
                    str(user.attribute_getter(logged_via, attr))
            else:
                user_dict[attr] = \
                    user.attribute_getter(logged_via, attr)
        user_dict['id'] = id
        user_dict['registered_tm'] = user.registered_tm
        user_dict['lang'] = user.lang
        # name = user.user_name


    # user_dict = {'id': id, 'name': name, 'logged_via': logged_via}

    g.user_init = user_init
    g.user = user
    g.user_dict = user_dict

    for variable in g.db.query(Config).filter_by(server_side=1).all():

        var_id = variable.id
        if variable.type == 'int':
            current_app.config[var_id] = int(variable.value)
        elif variable.type == 'bool':
            current_app.config[var_id] = False if int(variable.value) == 0 else True
        else:
            current_app.config[var_id] = '%s' % (variable.value,)


# def load_user():
#    g.user = None
#    if 'user_id' in session.keys():
#        g.user = g.db.query(User).\
#            query.filter_by(id=session['user_id']).first()


def load_portal_id(app):
    from profapp.models.portal import Portal

    def func():
        g.portal_id = g.db.query(Portal.id).filter_by(host=app.config['SERVER_NAME']).one()[0]
        # g.portal_id = db_session_func(app.config['SQLALCHEMY_DATABASE_URI']).\
        #             query(Portal.id).filter_by(host=app.config['SERVER_NAME']).one()[0]

    return func


def flask_endpoint_to_angular(endpoint, **kwargs):
    options = {}
    for kw in kwargs:
        options[kw] = "{{" + "{0}".format(kwargs[kw]) + "}}"
    url = url_for(endpoint, **options)
    import urllib.parse

    url = urllib.parse.unquote(url)
    url = url.replace('{{', '{{ ').replace('}}', ' }}')
    return url


# TODO OZ by OZ rename this func and add two parameters
def file_url(id):
    if not id:
        return ''
    server = re.sub(r'^[^-]*-[^-]*-4([^-]*)-.*$', r'\1', id)
    return 'http://file' + server + '.profireader.com/' + id + '/'


def translates(template):
    #     pass
    phrases = g.db.query(TranslateTemplate).filter_by(template=template).all()
    ret = {ph.name: ph.uk for ph in phrases}
    return json.dumps(ret)


@jinja2.contextfunction
def translate_phrase(context, phrase, dictionary=None):
    template = context.name

    translated = TranslateTemplate.getTranslate(template, phrase)

    r = re.compile("%\\(([^)]*)\\)s")

    def getFromContext(context, indexes, default):
        d = context
        for i in indexes:
            if i in d:
                d = d[i]
            else:
                return default
        return d

    def replaceinphrase(match):
        indexes = match.group(1).split('.')
        return str(getFromContext(context if dictionary is None else dictionary, indexes, match.group(1)))

    return r.sub(replaceinphrase, translated)


def config_variables():
    variables = g.db.query(Config).filter_by(client_side=1).all()
    ret = {}
    for variable in variables:
        var_id = variable.id
        if variable.type == 'int':
            ret[var_id] = '%s' % (int(variable.value),)
        elif variable.type == 'bool':
            ret[var_id] = 'false' if int(variable.value) == 0 else 'true'
        else:
            ret[var_id] = '\'' + variable.value + '\''
    return "<script>\nConfig = {};\n" + ''.join(
        [("Config['%s']=%s;\n" % (var_id, ret[var_id])) for var_id in ret]) + '</script>'


def get_url_adapter():
    appctx = globals._app_ctx_stack.top
    reqctx = globals._request_ctx_stack.top
    if reqctx is not None:
        url_adapter = reqctx.url_adapter
    else:
        url_adapter = appctx.url_adapter
    return url_adapter


# TODO: OZ by OZ: add kwargs just like in url_for
def raw_url_for(endpoint):
    url_adapter = get_url_adapter()

    rules = url_adapter.map._rules_by_endpoint.get(endpoint, ())

    if len(rules) < 1:
        return ''

    ret = re.compile('<[^:]*:').sub('<',
                                    url_adapter.map._rules_by_endpoint.get(endpoint, ())[0].rule)

    return "function (dict) { var ret = '" + ret + "'; " \
                                                   " for (prop in dict) ret = ret.replace('<'+prop+'>',dict[prop]); return ret; }"


def pre(value):
    res = []
    for k in dir(value):
        res.append('%r %r\n' % (k, getattr(value, k)))
    return '<pre>' + '\n'.join(res) + '</pre>'


mail = Mail()
moment = Moment()
bootstrap = Bootstrap()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
#  The login_view attribute sets the endpoint for the login page.
#  I am not sure that it is necessary
login_manager.login_view = 'auth.login'


class AnonymousUser(AnonymousUserMixin):
    id = 0
    # def gravatar(self, size=100, default='identicon', rating='g'):
    # if request.is_secure:
    #    url = 'https://secure.gravatar.com/avatar'
    # else:
    #    url = 'http://www.gravatar.com/avatar'
    # hash = hashlib.md5(
    #    'guest@profireader.com'.encode('utf-8')).hexdigest()
    # return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
    #    url=url, hash=hash, size=size, default=default, rating=rating)
    # return '/static/no_avatar.png'

    @staticmethod
    def check_rights(permissions):
        return False

    @staticmethod
    def is_administrator():
        return False

    @staticmethod
    def is_banned():
        return False

    def get_id(self):
        return self.id

    @staticmethod
    @property
    def user_name():
        return 'Guest'

    @staticmethod
    def avatar(size=0):
        pass

    def __repr__(self):
        return "<User(id = %r)>" % self.id


login_manager.anonymous_user = AnonymousUser


def create_app(config='config.ProductionDevelopmentConfig',
               front='n',
               host='localhost'):
    app = Flask(__name__)

    app.config.from_object(config)
    app.config['SERVER_NAME'] = host

    babel = Babel(app)

    app.teardown_request(close_database)
    app.before_request(load_database(app.config['SQLALCHEMY_DATABASE_URI']))
    app.config['DEBUG'] = True

    app.before_request(load_user)
    app.before_request(setup_authomatic(app))

    if front == 'y':
        app.before_request(load_portal_id(app))
        register_blueprints_front(app)
        my_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader('templates_front'),
        ])
        app.jinja_loader = my_loader
    if front == 'f':
        register_blueprints_file(app)
    else:
        register_blueprints(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)

    # if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
    #    from flask.ext.sslify import SSLify
    #    sslify = SSLify(app)

    @login_manager.user_loader
    def load_user_manager(user_id):
        return g.db.query(User).get(user_id)

    csrf.init_app(app)

    # read this: http://stackoverflow.com/questions/6036082/call-a-python-function-from-jinja2
    app.jinja_env.globals.update(flask_endpoint_to_angular=flask_endpoint_to_angular)
    app.jinja_env.globals.update(raw_url_for=raw_url_for)
    app.jinja_env.globals.update(pre=pre)
    app.jinja_env.globals.update(translates=translates)
    app.jinja_env.globals.update(file_url=file_url)
    app.jinja_env.globals.update(config_variables=config_variables)
    app.jinja_env.globals.update(_=translate_phrase)


    # see: http://flask.pocoo.org/docs/0.10/patterns/sqlalchemy/
    # Flask will automatically remove database sessions at the end of the
    # request or when the application shuts down:
    # from db_init import db_session

    # @app.teardown_appcontext
    # def shutdown_session(exception=None):
    #     try:
    #         db_session.commit()
    #     except Exception:
    #         session.rollback()
    #         raise
    #     finally:
    #         session.close()  # optional, depends on use case
    #     # db_session.remove()

    return app
