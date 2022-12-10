from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, HiddenField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo, Email
import json

with open("insts.json", "r") as f:
    inst_list = json.load(f)

class SearchForm(FlaskForm):
    institution = SelectField('Select an institution', choices=inst_list, validators=[DataRequired()])
    # year = SelectField('Select a year for prediction', choices=["2020", "2021", "2022", "2023"], validators=[DataRequired()])
    search_btn = SubmitField('Search')