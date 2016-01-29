from config import Config
import math
from flask import request
from .request_wrapers import ok

def pagination(query, page=1, items_per_page=Config.ITEMS_PER_PAGE, object=None):
    """ Pagination for pages. For use this function you have to pass subquery with all filters,
     number of current page. Also you can change page_size(items per page) from config.
     Return query with pagination parameters, all pages, current page"""

    count = query.count()

    pages = math.ceil(count/items_per_page)
    page -= 1
    if object and tuple(query).index(object)+1 > items_per_page:
        page = math.ceil(tuple(query).index(object)+1/items_per_page)-1
        print(page)
    if items_per_page:
        query = query.limit(items_per_page)
    if page:
        print(page)
        query = query.offset(page*items_per_page) if int(page) in range(
                0, int(pages)) else query.offset(pages*items_per_page)

    return query, pages, page+1, count


def get_request_page_filter_order_seek(json):

    search = json.get('search')
    page = json.get('page')
    filter_by = json.get('filter')
    order = json.get('order')
    seek = json.get('seek')
    return {'filter_by': filter_by, 'search': search, 'page': page, 'order': order, 'seek': seek}
