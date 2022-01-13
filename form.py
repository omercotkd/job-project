from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, AnyOf
from flask_wtf.file import FileField, FileRequired, FileAllowed


# the class that makes the register form
class InfoForm(FlaskForm):
    name = StringField("Enter your name", validators=[DataRequired()])
    last_name = StringField("Enter your last name", validators=[DataRequired()])
    # files input fields with format validation
    pdf_file = FileField("Upload a pdf file", validators=[FileRequired(), FileAllowed(["pdf", "doc", "docx"], "wrong format!")])
    img_file = FileField("Upload a img file", validators=[FileRequired(), FileAllowed(["jpg", "png", "pdf"], "wrong format!")])

    free_field = TextAreaField("Have anything to add? write it here")
    submit = SubmitField("Send")


# the class for the email form
class EmailForm(FlaskForm):
    email = StringField("Enter your email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send")
