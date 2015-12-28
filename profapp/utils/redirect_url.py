from flask import request, url_for, current_app
from ..controllers.errors import WrongNumberOfParameters, WrongMandatoryParametersPassedToFunction
from functools import reduce
from operator import or_
import inspect
import copy

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

    res_url = ''
    for elem in res_urls:
        res_url = res_url or elem
    return res_url


def url_page(endpoint=None, **kwargs):
    ep = endpoint if endpoint else request.endpoint
    kwargs_new = request.view_args
    kwargs_new.update(request.args)

    kwargs_new.update(kwargs)

    if ('search_text' in kwargs_new.keys()) and (not kwargs_new['search_text'] or not kwargs_new['search_text'][0]):
        kwargs_new.pop('search_text', None)

    return url_for(ep, **kwargs_new)
