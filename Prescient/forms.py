from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, PasswordField, BooleanField,
                     TextAreaField, IntegerField, HiddenField, SelectField,
                     DecimalField, DateTimeField)
from wtforms import validators as v
from Prescient.models import (User, Available_Securities, Watchlist_Group,
                              default_date, WatchlistItems)
from datetime import timedelta, date
from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField("Username", [v.Length(min=4, max=25)])
    password = PasswordField("New Password", [v.DataRequired(),
                                              v.Length(min=5),
                                              v.EqualTo("confirm", message="Passwords must match")])
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise v.ValidationError('That username is already registered.')


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[v.DataRequired()])
    password = PasswordField("Password", validators=[v.DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class WatchlistItemsForm(FlaskForm):
    order_id = HiddenField("")
    watchlist = SelectField("Watchlist",  validators=[v.InputRequired()])
    ticker = StringField("Ticker", validators=[v.Length(min=2, max=20),
                                               v.InputRequired()])
    quantity = IntegerField("Quantity", validators=[v.InputRequired(),
                                                    v.NumberRange(min=-10000000, max=10000000)])
    price = DecimalField("Price", validators=[v.InputRequired(),
                                              v.NumberRange(min=0, max=100000)])
    trade_date = DateTimeField("Trade Date", default=default_date)
    sector = SelectField("Sector",  validators=[v.InputRequired()])
    comments = TextAreaField("Comments", validators=[v.Optional(),
                                                     v.Length(max=140)])
    submit = SubmitField("Add to Watchlist")

    def validate_ticker(self, ticker):
        ticker_check = Available_Securities.query.\
                       filter_by(ticker=ticker.data).\
                       first()

        if ticker_check is None:
            raise v.ValidationError(f'The ticker {ticker.data} is unavailable.')

    def validate_trade_date(self, trade_date):
        # Check if the trade exists.
        timestamp = WatchlistItems.query.\
                    with_entities(WatchlistItems.created_timestamp).\
                    filter_by(id=self.order_id.data).\
                    first()
        if timestamp is None:
            return True
        trade_date = trade_date.data
        max_date = default_date()

        # Users can amend dates up to 100 days prior to the created_timestamp.
        lowest_date = timestamp[0] - timedelta(days=100)

        try:
            day_of_week = date.isoweekday(trade_date)
        except TypeError:
            raise v.ValidationError("Not a valid datetime value.")

        if trade_date > max_date:
            raise v.ValidationError("The trade and time cannot be a "
                                    "date in the future")
        elif trade_date < lowest_date:
            raise v.ValidationError("The trade and time must be within 100 "
                                    "days of the order creation date")
        elif day_of_week == 6 or day_of_week == 7:
            raise v.ValidationError("The trade date cannot fall on weekends.")


class WatchlistGroupForm(FlaskForm):
    name = StringField("Watchlist Name", validators=[v.InputRequired(),
                                                     v.Length(min=1, max=25)])
    submit = SubmitField("Create Watchlist")

    def validate_name(self, name):
        name = name.data
        user_id = current_user.id
        name_check = Watchlist_Group.query.\
                     filter_by(name=name, user_id=user_id).\
                     first()

        if name_check is not None:
            raise v.ValidationError("You can not create two watchlists "
                                    "with the same name!")


class ChartForm(FlaskForm):
    ticker = SelectField("Ticker",  validators=[v.InputRequired()])
    submit = SubmitField("Plot")
