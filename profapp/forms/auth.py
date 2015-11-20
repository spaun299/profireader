from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models.users import User
from flask import g


# class LoginForm(Form):
#     email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
#     password = PasswordField('Password', validators=[DataRequired()])
# #    remember_me = BooleanField('Keep me logged in')
#     submit = SubmitField('Log In')


# class RegistrationForm(Form):
#     email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    # displayname = StringField('displayname', validators=[
    #     DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
    #                                           'Usernames must have only '
    #                                           'letters, numbers, dots or '
    #                                           'underscores')])
    # password = PasswordField('Password', validators=[
    #     DataRequired(), EqualTo('password2', message='Passwords must match.')])
    # password2 = PasswordField('Confirm password', validators=[DataRequired()])
    # submit = SubmitField('Register')

    # def validate_email(self, field):
    #     if g.db.query(User).\
    #             filter_by(profireader_email=field.data).first():
    #         raise ValidationError('Email already registered.')

    # # def validate_displayname(self, field):
    # #     if g.db.query(User).\
    # #             filter_by(profireader_name=field.data).first():
    # #         pass
    # #         raise ValidationError('Username already in use.')

def f():
    x = 5
    y = False
    if x == 5:
        y = True
    return y


def validate_email(field):
    if g.db.query(User).filter_by(profireader_email=field.data).first():
        raise ValidationError('Email already registered.')


def validate_displayname(field):
    if g.db.query(User).filter_by(profireader_name=field.data).first():
        # pass
        raise ValidationError('Username already in use. Please choose another name')


class DataRequiredCustom(object):
    def __init__(self, login_signup='signup', message='Data should be provided'):
        self.login_signup = login_signup
        self.message = message

    def __call__(self, form, field):
        if self.login_signup == 'signup':
            return DataRequiredCustom(message=self.message)

# We aliased the Length class back to the original length name in the above example.
# This allows you to keep API compatibility as you move your validators from factories to classes, and thus we
# recommend this for those writing validators they will share.
data_required_custom = DataRequiredCustom


class LoginRegistrationForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    displayname = StringField('displayname', validators=[data_required_custom(self.login_signup),
                                                         Length(1, 64),
                                                         Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                                'Usernames must have only '
                                                                'letters, numbers, dots or '
                                                                'underscores')
                                                         ])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm password', validators=[EqualTo('password', message='Passwords must match.'),
                                                              data_required_custom(self.login_signup)])

    submit_register = SubmitField('Register')
    submit_login = SubmitField('Log In')

    def __init__(self, login_signup='signup'):
        super(LoginRegistrationForm, self).__init__()
        self.login_signup = login_signup


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[DataRequired(),
                                                         EqualTo('password2', message='Passwords must match')
                                                         ])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if g.db.query(User).filter_by(profireader_email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if g.db.query(User).filter_by(profireader_email=field.data).first():
            raise ValidationError('Email already registered.')
