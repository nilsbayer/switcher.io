from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, HiddenField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo, Email

class SearchForm(FlaskForm):
    institution = SelectField('Select an institution', choices=["A"], validators=[DataRequired()])
    # year = SelectField('Select a year for prediction', choices=["2020", "2021", "2022", "2023"], validators=[DataRequired()])
    search_btn = SubmitField('Search')