from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, ValidationError
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, InputRequired, Email, Length, EqualTo
from wtforms.widgets.core import TextArea

from flask_ckeditor import CKEditorField


class LoginForm(FlaskForm):

    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired()])

    submit = SubmitField('Submit')
    remember = BooleanField('Remember me')

class RegisterForm(FlaskForm):

    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message='Passwords Must Match!')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    chapter_letters = StringField("Chapter")
    class_year = StringField("Class Year (YYYY)")

    submit = SubmitField("Submit")


class TipForm(FlaskForm):

    title = StringField("Topic", validators=[DataRequired()])
    topic = StringField("Company", validators=[DataRequired()])
    author = StringField("Author")
    body = CKEditorField('Body', validators=[DataRequired()])

    submit = SubmitField("Submit")

class SearchForm(FlaskForm):

    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")

class CommentForm(FlaskForm):

    author = StringField("Author")
    body = CKEditorField("Comment")

    submit = SubmitField("Submit")