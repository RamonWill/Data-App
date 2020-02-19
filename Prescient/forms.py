from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField ,PasswordField, BooleanField, TextAreaField, IntegerField, SelectField, DecimalField, validators
from Prescient.models import User, Available_Securities


class RegistrationForm(FlaskForm):
    username = StringField("Username", [validators.Length(min=4, max=25)])
    password = PasswordField("New Password", [validators.DataRequired(), validators.Length(min=5), validators.EqualTo("confirm", message="Passswords must match")])
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise validators.ValidationError('That username is already registered.')


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[validators.DataRequired()])
    password = PasswordField("Password", validators=[validators.DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class WatchlistForm(FlaskForm):

    ticker = StringField("Ticker", validators=[validators.Length(min=3, max=20), validators.Optional()])
    quantity = IntegerField("Quantity", validators=[validators.InputRequired(), validators.NumberRange(min=-10000000, max=10000000)])
    price = DecimalField("Price", validators=[validators.InputRequired(), validators.NumberRange(min=0, max=100000)])
    sector = SelectField("Sector",  validators=[validators.InputRequired()])  # From database
    comments = TextAreaField("Comments", validators=[validators.Optional(), validators.Length(max=140)])
    submit = SubmitField("Add to Watchlist")

    def validate_ticker(self, ticker):
        ticker_check = Available_Securities.query.filter_by(ticker=ticker.data).first()
        if ticker_check is None:
            raise validators.ValidationError(f'The ticker {ticker} is not available.')


class ChartForm(FlaskForm):
    ticker = SelectField("Sector",  validators=[validators.InputRequired()])
    submit = SubmitField("Plot")
