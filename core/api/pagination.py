from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def paginate_list(request, items: list, serialize) -> Response:
    """Pagina una lista en memoria y devuelve el formato estándar de DRF."""
    paginator = StandardResultsPagination()
    page = paginator.paginate_queryset(items, request)
    if page is None:
        return Response(serialize(items))
    return paginator.get_paginated_response(serialize(page))
