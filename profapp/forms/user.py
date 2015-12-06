from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..constants.TABLE_TYPES import TABLE_TYPES
#from wtforms import ValidationError
#from ..models.users import User


class EditProfileForm(Form):
    name = StringField('Display name', validators=[Length(0, TABLE_TYPES['name'].length)])
    first_name = StringField('First name', validators=[Length(0, TABLE_TYPES['name'].length)])
    last_name = StringField('Last name', validators=[Length(0, TABLE_TYPES['name'].length)])
    gender = StringField('Gender', validators=[Length(0, TABLE_TYPES['gender'].length)])
    link = StringField('Gender')
    phone = StringField('Phone', validators=[Length(0, TABLE_TYPES['name'].length)])
    location = StringField('Location', validators=[Length(0, TABLE_TYPES['location'].length)])
    about_me = StringField('About me', validators=[Length(0, TABLE_TYPES['text'].length)])
    language = StringField('Language', validators=[Length(0, TABLE_TYPES['language'].length)])
    submit = SubmitField('Submit')
