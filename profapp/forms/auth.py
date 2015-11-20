from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models.users import User
from flask import g


# read the doc: http://wtforms.readthedocs.org/en/latest/validators.html#custom-validators
# We aliased the Length class back to the original length name in the above example.
# This allows you to keep API compatibility as you move your validators from factories to classes, and thus we
# recommend this for those writing validators they will share.
class ValidateEmail(object):
    def __init__(self, message):
        self.message = message

    def __call__(self, form, field):
        if g.db.query(User).filter_by(profireader_email=field.data).first():
            raise ValidationError(self.message)

validate_email = ValidateEmail


class ValidateDisplayname(object):
    def __init__(self, message):
        self.message = message

    def __call__(self, form, field):
        if g.db.query(User).filter_by(profireader_name=field.data).first():
            raise ValidationError(self.message)
            # pass

validate_displayname = ValidateDisplayname


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
#    remember_me = BooleanField('Keep me logged in')
    submit_login = SubmitField('Log In')


class RegistrationForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email(),
                                             validate_email('Email already registered')])
    displayname = StringField('displayname', validators=[
        DataRequired(), Length(1, 64), validate_displayname('Username already in use. Please choose another name.'),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'User names must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit_register = SubmitField('Register')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[DataRequired()])
    password2 = PasswordField('Confirm new password',
                              validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email(),
                                             validate_email('Unknown email address.')
                                             ])
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 64), Email(),
                                                 validate_email('Email already registered.')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')
