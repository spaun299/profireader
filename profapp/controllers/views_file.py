from .blueprints_declaration import file_bp
from flask import request, make_response, g, abort
from ..models.files import File, FileContent, ImageCroped
from io import BytesIO
from .errors import BadCoordinates
from PIL import Image
from time import gmtime, strftime
import sys
import re
from ..models.articles import Article, ArticlePortalDivision
from ..models.portal import MemberCompanyPortal, PortalDivision, Portal
from config import Config
from utils.db_utils import db
from ..models.company import Company
from flask import current_app
from werkzeug.datastructures import Headers
import mimetypes
import os
from time import time
from zlib import adler32
from flask._compat import string_types, text_type
try:
    from werkzeug.wsgi import wrap_file
except ImportError:
    from werkzeug.utils import wrap_file

@file_bp.route('<string:file_id>')
def download(file_id):
    file = file_query(File, file_id)
    file_c = file_query(FileContent, file_id)
    content = file_c.content
    response = make_response(content)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = 'attachment; filename=%s' % file.name
    return response

def send_file(filename_or_fp, mimetype=None, as_attachment=False,
              attachment_filename=None, add_etags=True,
              cache_timeout=None, conditional=False, headers={}):
    """Sends the contents of a file to the client.  This will use the
    most efficient method available and configured.  By default it will
    try to use the WSGI server's file_wrapper support.  Alternatively
    you can set the application's :attr:`~Flask.use_x_sendfile` attribute
    to ``True`` to directly emit an `X-Sendfile` header.  This however
    requires support of the underlying webserver for `X-Sendfile`.

    By default it will try to guess the mimetype for you, but you can
    also explicitly provide one.  For extra security you probably want
    to send certain files as attachment (HTML for instance).  The mimetype
    guessing requires a `filename` or an `attachment_filename` to be
    provided.

    Please never pass filenames to this function from user sources without
    checking them first.  Something like this is usually sufficient to
    avoid security problems::

        if '..' in filename or filename.startswith('/'):
            abort(404)

    .. versionadded:: 0.2

    .. versionadded:: 0.5
       The `add_etags`, `cache_timeout` and `conditional` parameters were
       added.  The default behavior is now to attach etags.

    .. versionchanged:: 0.7
       mimetype guessing and etag support for file objects was
       deprecated because it was unreliable.  Pass a filename if you are
       able to, otherwise attach an etag yourself.  This functionality
       will be removed in Flask 1.0

    .. versionchanged:: 0.9
       cache_timeout pulls its default from application config, when None.

    :param filename_or_fp: the filename of the file to send.  This is
                           relative to the :attr:`~Flask.root_path` if a
                           relative path is specified.
                           Alternatively a file object might be provided
                           in which case `X-Sendfile` might not work and
                           fall back to the traditional method.  Make sure
                           that the file pointer is positioned at the start
                           of data to send before calling :func:`send_file`.
    :param mimetype: the mimetype of the file if provided, otherwise
                     auto detection happens.
    :param as_attachment: set to `True` if you want to send this file with
                          a ``Content-Disposition: attachment`` header.
    :param attachment_filename: the filename for the attachment if it
                                differs from the file's filename.
    :param add_etags: set to `False` to disable attaching of etags.
    :param conditional: set to `True` to enable conditional responses.

    :param cache_timeout: the timeout in seconds for the headers. When `None`
                          (default), this value is set by
                          :meth:`~Flask.get_send_file_max_age` of
                          :data:`~flask.current_app`.
    """
    mtime = None
    if isinstance(filename_or_fp, string_types):
        filename = filename_or_fp
        file = None
    else:
        from warnings import warn
        file = filename_or_fp
        filename = getattr(file, 'name', None)

        # XXX: this behavior is now deprecated because it was unreliable.
        # removed in Flask 1.0
        if not attachment_filename and not mimetype \
           and isinstance(filename, string_types):
            warn(DeprecationWarning('The filename support for file objects '
                'passed to send_file is now deprecated.  Pass an '
                'attach_filename if you want mimetypes to be guessed.'),
                stacklevel=2)
        if add_etags:
            warn(DeprecationWarning('In future flask releases etags will no '
                'longer be generated for file objects passed to the send_file '
                'function because this behavior was unreliable.  Pass '
                'filenames instead if possible, otherwise attach an etag '
                'yourself based on another value'), stacklevel=2)

    if filename is not None:
        if not os.path.isabs(filename):
            filename = os.path.join(current_app.root_path, filename)
    if mimetype is None and (filename or attachment_filename):
        mimetype = mimetypes.guess_type(filename or attachment_filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'

    default_headers = Headers()
    if as_attachment:
        if attachment_filename is None:
            if filename is None:
                raise TypeError('filename unavailable, required for '
                                'sending as attachment')
            attachment_filename = os.path.basename(filename)
        default_headers.add('Content-Disposition', 'attachment',
                    filename=attachment_filename)

    if current_app.use_x_sendfile and filename:
        if file is not None:
            file.close()
        default_headers['X-Sendfile'] = filename
        default_headers['Content-Length'] = os.path.getsize(filename)
        data = None
    else:
        if file is None:
            file = open(filename, 'rb')
            mtime = os.path.getmtime(filename)
            default_headers['Content-Length'] = os.path.getsize(filename)
        data = wrap_file(request.environ, file)

    for headername in headers:
        default_headers[headername] = headers[headername]

    rv = current_app.response_class(data, mimetype=mimetype, headers=default_headers,
                                    direct_passthrough=True)

    # if we know the file modification date, we can store it as the
    # the time of the last modification.
    if mtime is not None:
        rv.last_modified = int(mtime)

    rv.cache_control.public = True
    if cache_timeout is None:
        cache_timeout = current_app.get_send_file_max_age(filename)
    if cache_timeout is not None:
        rv.cache_control.max_age = cache_timeout
        rv.expires = int(time() + cache_timeout)

    if add_etags and filename is not None:
        rv.set_etag('flask-%s-%s-%s' % (
            os.path.getmtime(filename),
            os.path.getsize(filename),
            adler32(
                filename.encode('utf-8') if isinstance(filename, text_type)
                else filename
            ) & 0xffffffff
        ))
        if conditional:
            rv = rv.make_conditional(request)
            # make sure we don't send x-sendfile for servers that
            # ignore the 304 status code for x-sendfile.
            if rv.status_code == 304:
                rv.headers.pop('x-sendfile', None)
    return rv

def allowed_referrers(domain):
    return True if domain == 'http://profireader.com' or \
                   'http://rodynnifirmy.profireader.com' else False

@file_bp.route('<string:file_id>/')
def get(file_id):
    image_query = file_query(File, file_id)
    image_query_content = g.db.query(FileContent).filter_by(id=file_id).first()

    allowedreferrer = re.sub(r'^(https?://[^/]+).*$', r'\1', request.headers.environ['HTTP_REFERER'])
    if allowed_referrers(allowedreferrer):
        return send_file(BytesIO(image_query_content.content),
                         mimetype=image_query.mime, as_attachment=False,
                         headers={
                             'Content-Disposition': 'filename=%s' % (image_query.name,),
                             'Access-Control-Allow-Origin': allowedreferrer}
                         )
    else:
        return abort(403)


def file_query(table, file_id):
    query = g.db.query(table).filter_by(id=file_id).first()
    return query


def crop_image(image_id, coordinates):

    image_query = db(File, id=image_id).one()

    company_owner = db(Company, journalist_folder_file_id=image_query.root_folder_id).one()
    bytes_file = crop_with_coordinates(image_query, coordinates)
    if bytes_file:
        croped = File()
        croped.md_tm = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        croped.size = sys.getsizeof(bytes_file.getvalue())
        croped.name = image_query.name + '_croped'
        croped.parent_id = company_owner.system_folder_file_id
        croped.root_folder_id = company_owner.system_folder_file_id
        croped.mime = image_query.mime
        fc = FileContent(content=bytes_file.getvalue(), file=croped)
        copy_original_image_to_system_folder = \
            File(parent_id=company_owner.system_folder_file_id, name=image_query.name+'_original',
                 mime=image_query.mime, size=image_query.size, user_id=g.user.id,
                 root_folder_id=company_owner.system_folder_file_id, author_user_id=g.user.id)
        cfc = FileContent(content=image_query.file_content.content,
                          file=copy_original_image_to_system_folder)
        g.db.add_all([croped, fc, copy_original_image_to_system_folder, cfc])
        g.db.flush()
        ImageCroped(original_image_id=copy_original_image_to_system_folder.id,
                    croped_image_id=croped.id,
                    x=int(coordinates['x']), y=int(coordinates['y']),
                    width=int(coordinates['width']),
                    height=int(coordinates['height']), rotate=int(coordinates['rotate'])).save()
        return croped.id
    else:
        return image_query.id


def update_croped_image(original_image_id, coordinates):
    image_croped_assoc = db(ImageCroped, original_image_id=original_image_id).one()
    croped = db(File, id=image_croped_assoc.croped_image_id).one()

    image_query = file_query(File, image_croped_assoc.original_image_id)
    bytes_file = crop_with_coordinates(image_query, coordinates, )
    if bytes_file:
        croped.size = sys.getsizeof(bytes_file.getvalue())
        croped.file_content.content = bytes_file.getvalue()
        image_croped_assoc.x = int(coordinates['x'])
        image_croped_assoc.y = int(coordinates['y'])
        image_croped_assoc.width = int(coordinates['width'])
        image_croped_assoc.height = int(coordinates['height'])
        image_croped_assoc.rotate = int(coordinates['rotate'])
    return croped.id


def crop_with_coordinates(image, coordinates,  ratio=Config.IMAGE_EDITOR_RATIO,
                          height=Config.HEIGHT_IMAGE):
    size = (int(ratio*height), height)
    image_pil = Image.open(BytesIO(image.file_content.content))
    try:
        area = [int(a) for a in (coordinates['x'], coordinates['y'], coordinates['width'],
                             coordinates['height'])
            if int(a) in range(0, max(image_pil.size))]
        angle = int(coordinates["rotate"])*-1
        area[2] = (area[0]+area[2])
        area[3] = (area[1]+area[3])
        rotated = image_pil.rotate(angle)
        cropped = rotated.crop(area).resize(size)
        bytes_file = BytesIO()
        cropped.save(bytes_file, image.mime.split('/')[-1].upper())
        return bytes_file
    except ValueError:
        return False
