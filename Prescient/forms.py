from wtforms import Form, StringField, PasswordField, TextField, SubmitField, DecimalField, validators


class RegistrationForm(Form):
    username = StringField("Username", [validators.Length(min=4, max=25)])
    password = PasswordField("New Password", [validators.DataRequired(), validators.EqualTo("confirm", message="Passswords must match")])
    confirm = PasswordField("Repeat Password")


class LoginForm(Form):
    username = StringField("Username", validators=[validators.DataRequired()])
    password = PasswordField("Password", validators=[validators.DataRequired()])
