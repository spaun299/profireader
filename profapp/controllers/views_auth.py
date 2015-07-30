from .blueprints import user_bp
from flask import jsonify, make_response, g, session, request, redirect, \
    url_for, render_template
from authomatic.adapters import WerkzeugAdapter
from ..models.users import User
from db_init import db_session
from ..constants.USER_REGISTERED import DB_ALIAS_UID, REGISTERED_WITH_FLIPPED
#from urllib.parse import quote
#import urllib.parse
from urllib.parse import quote

#def _session_saver():
#    session.modified = True

import re
from authomatic.adapters import WerkzeugAdapter

from flask import redirect, make_response
from flask.ext.login import login_user


EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')


#provider_name:
# 1) facebook +-
# 2) linkedin +
# 3) google +
# 4) twitter +
# 5) microsoft +
# 6) email !!!


@user_bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

@user_bp.route('/login/', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@user_bp.route('/login/<provider_name>', methods=['GET', 'POST'])
def login_particular(provider_name):
    response = make_response()
    try:
        result = g.authomatic.login(WerkzeugAdapter(request, response),
                                    provider_name)
        if result:
            if result.user:
                result.user.update()
                result_user = result.user
                pass
                #user = db_session.query(User).\
                #    filter(
                #    getattr(User, DB_ALIAS_UID[provider_name])
                #    == result_user.id
                #).first()
                #if not user:
    # email='guest@profireader.com', first_name=None,
    # second_name=None, password=None, pass_salt=None, fb_uid=None,
    # google_uid=None, twitter_uid=None, linkedin_uid=None,
    # email_conf_key=None, email_conf_tm=None, pass_reset_key=None,
    # pass_reset_conf_tm=None, registered_via=None, ):
                #    user = User(first_name=res_user_unified.first_name,
                #                second_name=res_user_unified.second_name,
                #                registered_via=
                #                REGISTERED_WITH_FLIPPED[provider_name]
                #                )
                #    setattr(user, DB_ALIAS_UID[provider_name], result_user.id)
                #    setattr(user, res_user_unified.email[attr],
                #            res_user_unified.email[value])
                #    db_session.add(user)
                #    db_session.commit()
                #session['user_id'] = user.id
                ##  create a flag showing the profile is not complete!!!
                return redirect('/')

                #  email = result.user.email
                #  if email and EMAIL_REGEX.match(email):
                #      user = User.query.filter_by(email=email).first()
                #      if user:
                #          login_user(user)
                #          return redirect(url_for('general.index'))
                #      return redirect(url_for('general.index'))  #  delete this redirect
    except:
        raise
    return response


#@user_bp.route('/login/fb/', methods=['GET', 'POST'])
#def login_fb():
#    response = make_response()
#    result = g.authomatic.login(WerkzeugAdapter(request, response), 'fb',
#                                session=session,
#                                session_saver=_session_saver)
#    if result:
#        if result.user:
#            result.user.update()
#            user = User.query.filter_by(fb_id=result.user.id).first()
#            if not user:
#                user = User(result.user.first_name,
#                            result.user.last_name,
#                            result.user.id,
#                            result.user.email)
#                #db.session.add(user)
#                #db.session.commit()
#            session['user_id'] = user.id
#            return redirect('/')
#
#        elif result.error:
#            redirect_path = '#/?msg={}'.format(quote('Facebook login failed.'))
#            return redirect(redirect_path)
#    return response


#
#
#@user_bp.route('/user-info/', methods=['GET'])  # user profile
#def user_info():
#    res = {}
#    if g.user:
#        res = (
#            {'id': g.user.id, 'first_name': g.user.fb_first_name,
#             'last_name': g.user.fb_last_name,
#             'fb_id': g.user.fb_id,
#             'email': g.user.email})
#    return jsonify(res)
#
#
#@user_bp.route('/logout/', methods=['GET'])
#def logout():
#    session.pop('authomatic:fb:state', None)
#    session.pop('user_id', None)
#    return jsonify({}), 200