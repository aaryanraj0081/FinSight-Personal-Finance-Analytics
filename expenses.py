from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from forms import BudgetForm, CategoryForm, ExpenseForm
from models import Budget, Category, Expense, db

expenses_bp = Blueprint("expenses", __name__)


def _user_categories():
    return Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()


def _set_category_choices(form):
    form.category_id.choices = [(c.id, c.name) for c in _user_categories()]


# ---------------------------------------------------------------- Expenses
@expenses_bp.route("/expenses")
@login_required
def list_expenses():
    month = request.args.get("month", type=int, default=date.today().month)
    year = request.args.get("year", type=int, default=date.today().year)
    category_id = request.args.get("category_id", type=int)

    query = Expense.query.filter_by(user_id=current_user.id).filter(
        db.extract("month", Expense.expense_date) == month,
        db.extract("year", Expense.expense_date) == year,
    )
    if category_id:
        query = query.filter_by(category_id=category_id)

    expenses = query.order_by(Expense.expense_date.desc(), Expense.id.desc()).all()
    total = sum((e.amount for e in expenses), start=0)

    return render_template(
        "expenses_list.html",
        expenses=expenses,
        categories=_user_categories(),
        total=total,
        month=month,
        year=year,
        selected_category_id=category_id,
    )


@expenses_bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    form = ExpenseForm()
    _set_category_choices(form)

    if not form.category_id.choices:
        flash("Add a category first before logging an expense.", "warning")
        return redirect(url_for("expenses.list_categories"))

    if form.validate_on_submit():
        expense = Expense(
            user_id=current_user.id,
            category_id=form.category_id.data,
            amount=form.amount.data,
            expense_date=form.expense_date.data,
            payment_method=form.payment_method.data,
            note=form.note.data.strip() if form.note.data else None,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense added.", "success")
        return redirect(url_for("expenses.list_expenses"))

    return render_template("expense_form.html", form=form, title="Add Expense")


@expenses_bp.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    form = ExpenseForm(obj=expense)
    _set_category_choices(form)

    if form.validate_on_submit():
        expense.category_id = form.category_id.data
        expense.amount = form.amount.data
        expense.expense_date = form.expense_date.data
        expense.payment_method = form.payment_method.data
        expense.note = form.note.data.strip() if form.note.data else None
        db.session.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("expenses.list_expenses"))

    return render_template("expense_form.html", form=form, title="Edit Expense")


@expenses_bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses.list_expenses"))


# --------------------------------------------------------------- Categories
@expenses_bp.route("/categories", methods=["GET", "POST"])
@login_required
def list_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        exists = Category.query.filter_by(user_id=current_user.id, name=name).first()
        if exists:
            flash("You already have a category with that name.", "warning")
        else:
            db.session.add(Category(user_id=current_user.id, name=name, is_default=False))
            db.session.commit()
            flash("Category added.", "success")
        return redirect(url_for("expenses.list_categories"))

    return render_template("categories.html", form=form, categories=_user_categories())


@expenses_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    if category.expenses or category.budgets:
        flash("Can't delete a category that already has expenses or budgets linked to it.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted.", "info")
    return redirect(url_for("expenses.list_categories"))


# ------------------------------------------------------------------ Budgets
@expenses_bp.route("/budgets", methods=["GET", "POST"])
@login_required
def list_budgets():
    form = BudgetForm()
    _set_category_choices(form)

    if not form.category_id.choices:
        flash("Add a category first before setting a budget.", "warning")
        return redirect(url_for("expenses.list_categories"))

    if request.method == "GET":
        form.month.data = date.today().month
        form.year.data = date.today().year

    if form.validate_on_submit():
        existing = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=form.category_id.data,
            month=form.month.data,
            year=form.year.data,
        ).first()
        if existing:
            existing.amount_limit = form.amount_limit.data
            flash("Budget updated.", "success")
        else:
            db.session.add(
                Budget(
                    user_id=current_user.id,
                    category_id=form.category_id.data,
                    month=form.month.data,
                    year=form.year.data,
                    amount_limit=form.amount_limit.data,
                )
            )
            flash("Budget set.", "success")
        db.session.commit()
        return redirect(url_for("expenses.list_budgets", month=form.month.data, year=form.year.data))

    month = request.args.get("month", type=int, default=date.today().month)
    year = request.args.get("year", type=int, default=date.today().year)

    budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()

    spent_by_category = dict(
        db.session.query(Expense.category_id, func.sum(Expense.amount))
        .filter(
            Expense.user_id == current_user.id,
            db.extract("month", Expense.expense_date) == month,
            db.extract("year", Expense.expense_date) == year,
        )
        .group_by(Expense.category_id)
        .all()
    )

    budget_rows = []
    for b in budgets:
        spent = spent_by_category.get(b.category_id, 0) or 0
        limit = b.amount_limit or 0
        pct = float(spent) / float(limit) * 100 if limit else 0
        budget_rows.append(
            {
                "budget": b,
                "spent": spent,
                "remaining": limit - spent,
                "pct": min(pct, 100),
                "over_budget": spent > limit,
            }
        )

    return render_template(
        "budgets.html",
        form=form,
        budget_rows=budget_rows,
        month=month,
        year=year,
    )


@expenses_bp.route("/budgets/<int:budget_id>/delete", methods=["POST"])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    month, year = budget.month, budget.year
    db.session.delete(budget)
    db.session.commit()
    flash("Budget removed.", "info")
    return redirect(url_for("expenses.list_budgets", month=month, year=year))
