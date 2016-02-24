from flask import url_for, session


def back_to_url(endpoint, host='profireader.com', **endpoint_params):
    back_to = '//{host}{endpoint}'.format(host=host, endpoint=url_for(endpoint, **endpoint_params))
    session['back_to'] = back_to
    return back_to
