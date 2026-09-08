from functools import wraps

from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Restrict a route to users whose `role` is in `roles`. Use after @login_required."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
