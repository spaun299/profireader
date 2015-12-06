from flask import request, url_for
from ..controllers.errors import WrongNumberOfParameters
from functools import reduce
from operator import or_


# def redirect_url(default=None):
#     if not default:
#         default = url_for('general.index')
#     return request.args.get('next') or request.referrer or default


def redirect_url(*args):
    urls = [request.args.get('next'), url_for('general.index'), request.referrer]
    res_urls = []

    for elem in args:
        res_urls.append(elem)
        urls.remove(elem)

    res_urls += urls
    print(res_urls)

    res_url = ''
    for elem in res_urls:
        res_url = res_url or elem
    return res_url
