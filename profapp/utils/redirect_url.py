from flask import request, url_for


def redirect_url(default=None):
    if not default:
        default = url_for('general.index')
    return request.args.get('next') or request.referrer or url_for(default)
