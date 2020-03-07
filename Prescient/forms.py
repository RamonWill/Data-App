from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField ,PasswordField, BooleanField, TextAreaField, IntegerField, HiddenField, SelectField, DecimalField, DateTimeField, validators
from Prescient.models import User, Available_Securities, Watchlist_Group, default_date, WatchlistItems
from datetime import timedelta, date
from flask_login import current_user


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


class WatchlistItemsForm(FlaskForm):
    order_id = HiddenField("")
    watchlist = SelectField("Watchlist",  validators=[validators.InputRequired()])
    ticker = StringField("Ticker", validators=[validators.Length(min=2, max=20), validators.InputRequired()])
    quantity = IntegerField("Quantity", validators=[validators.InputRequired(), validators.NumberRange(min=-10000000, max=10000000)])
    price = DecimalField("Price", validators=[validators.InputRequired(), validators.NumberRange(min=0, max=100000)])
    trade_date = DateTimeField("Trade Date", default=default_date)
    sector = SelectField("Sector",  validators=[validators.InputRequired()])  # From database
    comments = TextAreaField("Comments", validators=[validators.Optional(), validators.Length(max=140)])
    submit = SubmitField("Add to Watchlist")

    def validate_ticker(self, ticker):
        ticker_check = Available_Securities.query.filter_by(ticker=ticker.data).first()
        if ticker_check is None:
            raise validators.ValidationError(f'The ticker {ticker.data} is unavailable.')

    def validate_trade_date(self, trade_date):
        timestamp = WatchlistItems.query.with_entities(WatchlistItems.created_timestamp).filter_by(id=self.order_id.data).first()
        if timestamp is None:  # Instrument is new and doesnt have trade date
            return True
        trade_date = trade_date.data
        max_date = default_date()
        lowest_date = timestamp[0] - timedelta(days=100)  # instead of trade date this should be created_timestamp
        try:
            day_of_week = date.isoweekday(trade_date)
        except TypeError:
            raise validators.ValidationError("Not a valid datetime value.")

        if trade_date > max_date:
            raise validators.ValidationError("The trade and time cannot be a date in the future")
        elif trade_date < lowest_date:
            raise validators.ValidationError("The trade and time must be within 100 days of the order creation date")
        elif day_of_week == 6 or day_of_week == 7:
            raise validators.ValidationError("The trade date cannot fall on weekends.")


class WatchlistGroupForm(FlaskForm):
    name = StringField("Watchlist Name", validators=[validators.InputRequired(), validators.Length(min=1, max=25)])
    submit = SubmitField("Create Watchlist")

    def validate_name(self, name):
        name = name.data
        user_id = current_user.id
        name_check = Watchlist_Group.query.filter_by(name=name, user_id=user_id).first()
        if name_check is not None:
            raise validators.ValidationError("You can not create two watchlists with the same name!")


class ChartForm(FlaskForm):
    ticker = SelectField("Ticker",  validators=[validators.InputRequired()])
    submit = SubmitField("Plot")
