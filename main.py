from datetime import date

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from decorators import role_required
from forms import ProfileForm
from models import Budget, Expense, User, db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()

    total_spent = (
        db.session.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == current_user.id,
            db.extract("month", Expense.expense_date) == today.month,
            db.extract("year", Expense.expense_date) == today.year,
        )
        .scalar()
    ) or 0

    total_budget = (
        db.session.query(func.sum(Budget.amount_limit))
        .filter_by(user_id=current_user.id, month=today.month, year=today.year)
        .scalar()
    ) or 0

    return render_template(
        "dashboard.html",
        user=current_user,
        total_spent=total_spent,
        total_budget=total_budget,
        month_label=today.strftime("%B %Y"),
    )


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile_setup():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        current_user.monthly_income = form.monthly_income.data or 0
        current_user.income_source = form.income_source.data
        current_user.currency = form.currency.data
        current_user.date_format = form.date_format.data
        current_user.theme = form.theme.data
        current_user.email_notifications = form.email_notifications.data
        current_user.push_notifications = form.push_notifications.data
        current_user.profile_completed = True
        db.session.commit()

        flash("Profile saved successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("profile.html", form=form)


@main_bp.route("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users)


@main_bp.route("/admin/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@role_required("admin")
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
    else:
        user.is_active_account = not user.is_active_account
        db.session.commit()
        state = "activated" if user.is_active_account else "deactivated"
        flash(f"{user.name}'s account has been {state}.", "success")
    return redirect(url_for("main.admin_users"))
