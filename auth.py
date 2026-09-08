from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from forms import ChangePasswordForm, LoginForm, RegistrationForm
from models import User, db, seed_default_categories

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # First registered user becomes admin; everyone else is a standard user.
        is_first_user = User.query.count() == 0
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role="admin" if is_first_user else "user",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        seed_default_categories(user)

        flash("Account created successfully! Please complete your profile setup.", "success")
        login_user(user)
        return redirect(url_for("main.profile_setup"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)

        if not user.is_active_account:
            flash("This account has been deactivated. Contact support.", "danger")
            return render_template("login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("change_password.html", form=form)
