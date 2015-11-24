from .blueprints_declaration import user_bp
from flask import url_for, render_template, abort, request, flash, redirect, \
    request, g
# from db_init import db_session
from ..models.users import User
from flask.ext.login import current_user, login_required
from utils.db_utils import db
from ..constants.UNCATEGORIZED import AVATAR_SIZE, AVATAR_SMALL_SIZE
from ..forms.user import EditProfileForm


@user_bp.route('/profile/<user_id>')
@login_required
def profile(user_id):
    user = g.db.query(User).filter(User.id == user_id).first()
    if not user:
        abort(404)
    return render_template('general/user_profile.html', user=user, avatar_size=AVATAR_SIZE)


# TODO (AA to AA): Here admin must have the possibility to change user profile
@user_bp.route('/edit-profile/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    if current_user.get_id() != user_id:
        abort(403)

    user_query = db(User, id=user_id)

    #form = EditProfileForm()
    #if form.validate_on_submit():
    #    pass

    user = user_query.first()

    if request.method == 'GET':
        return render_template('general/user_edit_profile.html',  user=user, avatar_size=AVATAR_SIZE)

    if 'avatar' in request.form.keys():
        if request.form['avatar'] == 'Upload Image':
            user = user_query.first()
            image = request.files['avatar']
            user.avatar_update(image)
        else:  # request.form['avatar'] == 'Use Gravatar':
            user.profireader_avatar_url = user.avatar(size=AVATAR_SIZE)
            user.profireader_small_avatar_url = user.avatar(size=AVATAR_SMALL_SIZE)
        g.db.add(user)
        g.db.commit()

    else:
        user_fields = dict()
        user_fields['profireader_name'] = request.form['name']
        user_fields['profireader_first_name'] = request.form['first_name']
        user_fields['profireader_last_name'] = request.form['last_name']
        user_fields['profireader_gender'] = request.form['gender']
        user_fields['profireader_link'] = request.form['link']
        user_fields['profireader_phone'] = request.form['phone']
        user_fields['location'] = request.form['location']
        user_fields['about_me'] = request.form['about_me']

        user_query.update(user_fields)
        flash('You have successfully updated you profile.')

    #return redirect(url_for('user.profile', user_id=user_id, avatar_size=2*AVATAR_SIZE))
    return render_template('general/user_edit_profile.html',  user=user, avatar_size=AVATAR_SIZE)
