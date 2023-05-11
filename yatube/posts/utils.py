from django.conf import settings as s
from django.core.paginator import Paginator


def get_paginator(request, posts):
    paginator = Paginator(posts, s.PAGINATOR)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
