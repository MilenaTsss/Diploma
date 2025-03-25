from rest_framework.pagination import PageNumberPagination

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

class CustomPageNumberPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE
