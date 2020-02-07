from wtforms import Form, StringField, PasswordField, TextAreaField, IntegerField, SelectField, DecimalField, validators

class RegistrationForm(Form):
    username = StringField("Username", [validators.Length(min=4, max=25)])
    password = PasswordField("New Password", [validators.DataRequired(), validators.EqualTo("confirm", message="Passswords must match")])
    confirm = PasswordField("Repeat Password")


class LoginForm(Form):
    username = StringField("Username", validators=[validators.DataRequired()])
    password = PasswordField("Password", validators=[validators.DataRequired()])


class WatchlistForm(Form):

    ticker = StringField("Ticker", validators=[validators.Length(min=3, max=20), validators.Optional()])
    quantity = IntegerField("Quantity", validators=[validators.InputRequired(), validators.NumberRange(min=-10000000, max=10000000)])
    price = DecimalField("Price", validators=[validators.InputRequired(), validators.NumberRange(min=0, max=100000)])
    sector = SelectField("Sector",  validators=[validators.InputRequired()])  # From database
    comments = TextAreaField("Comments", validators=[validators.Optional(), validators.Length(max=140)])
