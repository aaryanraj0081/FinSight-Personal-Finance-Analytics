from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    Core user account.
    Covers: registration/login, password encryption, role-based access,
    and profile setup fields (income sources & financial preferences).
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))

    # Role-based access control. Options: "user", "admin".
    role = db.Column(db.String(20), nullable=False, default="user")

    # --- Profile setup: income sources & financial preferences ---
    monthly_income = db.Column(db.Numeric(12, 2), default=0)
    income_source = db.Column(db.String(100))  # e.g. Salary, Business, Freelance
    currency = db.Column(db.String(10), default="INR")
    date_format = db.Column(db.String(20), default="DD/MM/YYYY")
    theme = db.Column(db.String(20), default="light")
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)

    # --- Account security / status ---
    is_active_account = db.Column(db.Boolean, default=True)
    profile_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ---- Password helpers (encryption via werkzeug's salted hashing) ----
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # Flask-Login expects an `is_active` property
    @property
    def is_active(self):
        return self.is_active_account

    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"


# Categories offered by default to every new user (seeded on first use).
DEFAULT_CATEGORIES = [
    "Food & Dining",
    "Transport",
    "Housing & Rent",
    "Utilities",
    "Healthcare",
    "Entertainment",
    "Shopping",
    "Other",
]

PAYMENT_METHODS = ["Cash", "Debit Card", "Credit Card", "UPI", "Bank Transfer", "Other"]


class Category(db.Model):
    """Expense category. Each user has their own set (defaults + custom)."""

    __tablename__ = "categories"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_category_user_name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    expenses = db.relationship("Expense", backref="category", lazy=True)
    budgets = db.relationship("Budget", backref="category", lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Expense(db.Model):
    """A single expense entry logged by a user."""

    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    payment_method = db.Column(db.String(30), default="Cash")
    note = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Expense {self.amount} on {self.expense_date}>"


class Budget(db.Model):
    """Monthly spending limit set by a user for a given category."""

    __tablename__ = "budgets"
    __table_args__ = (
        db.UniqueConstraint("user_id", "category_id", "month", "year", name="uq_budget_period"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    amount_limit = db.Column(db.Numeric(12, 2), nullable=False)

    def __repr__(self):
        return f"<Budget {self.category_id} {self.month}/{self.year}>"


def seed_default_categories(user: User) -> None:
    """Create the default category set for a user if they have none yet."""
    if Category.query.filter_by(user_id=user.id).first():
        return
    for name in DEFAULT_CATEGORIES:
        db.session.add(Category(user_id=user.id, name=name, is_default=True))
    db.session.commit()
