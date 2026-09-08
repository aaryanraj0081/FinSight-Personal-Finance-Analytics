from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from models import PAYMENT_METHODS, User


class RegistrationForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])

    monthly_income = DecimalField(
        "Monthly Income", validators=[Optional(), NumberRange(min=0)], places=2, default=0
    )
    income_source = SelectField(
        "Primary Income Source",
        choices=[
            ("Salary", "Salary"),
            ("Business", "Business"),
            ("Freelance", "Freelance"),
            ("Investments", "Investments"),
            ("Other", "Other"),
        ],
        validators=[Optional()],
    )
    currency = SelectField(
        "Currency",
        choices=[("INR", "INR (₹)"), ("USD", "USD ($)"), ("EUR", "EUR (€)"), ("GBP", "GBP (£)")],
        validators=[DataRequired()],
    )
    date_format = SelectField(
        "Date Format",
        choices=[("DD/MM/YYYY", "DD/MM/YYYY"), ("MM/DD/YYYY", "MM/DD/YYYY"), ("YYYY-MM-DD", "YYYY-MM-DD")],
        validators=[DataRequired()],
    )
    theme = SelectField("Theme", choices=[("light", "Light"), ("dark", "Dark")], validators=[DataRequired()])
    email_notifications = BooleanField("Email Notifications")
    push_notifications = BooleanField("Push Notifications")
    submit = SubmitField("Save Profile")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8, message="Must be at least 8 characters.")]
    )
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Update Password")


class ExpenseForm(FlaskForm):
    """Category choices are populated dynamically per-user in the route."""

    amount = DecimalField(
        "Amount", validators=[DataRequired(), NumberRange(min=0.01)], places=2
    )
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    expense_date = DateField("Date", validators=[DataRequired()], default=date.today)
    payment_method = SelectField(
        "Payment Method",
        choices=[(m, m) for m in PAYMENT_METHODS],
        validators=[DataRequired()],
    )
    note = TextAreaField("Note", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save Expense")


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(min=2, max=60)])
    submit = SubmitField("Add Category")


class BudgetForm(FlaskForm):
    """Category choices are populated dynamically per-user in the route."""

    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    month = SelectField(
        "Month",
        coerce=int,
        choices=[
            (1, "January"), (2, "February"), (3, "March"), (4, "April"),
            (5, "May"), (6, "June"), (7, "July"), (8, "August"),
            (9, "September"), (10, "October"), (11, "November"), (12, "December"),
        ],
        validators=[DataRequired()],
    )
    year = IntegerField("Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    amount_limit = DecimalField(
        "Monthly Limit", validators=[DataRequired(), NumberRange(min=0.01)], places=2
    )
    submit = SubmitField("Save Budget")
