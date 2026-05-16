from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def branch_access_required(get_branch_id_fn):
    """Decorator factory. get_branch_id_fn receives (kwargs) and returns branch_id."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.is_admin:
                return f(*args, **kwargs)
            branch_id = get_branch_id_fn(kwargs)
            if current_user.branch_id != branch_id:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator
