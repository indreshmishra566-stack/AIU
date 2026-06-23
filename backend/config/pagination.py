"""
AIU — Custom REST Framework utilities
"""

import logging
import uuid

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class StandardResultsPagination(PageNumberPagination):
    """Consistent pagination across all list endpoints."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "status": "success",
                "pagination": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "page": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                },
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "pagination": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "page": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                    },
                },
                "results": schema,
            },
        }


def custom_exception_handler(exc, context):
    """
    Centralised error response format.
    All API errors return: { status, code, message, errors, request_id }
    """
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "request_id", str(uuid.uuid4()))

    if response is not None:
        error_data = {
            "status": "error",
            "code": response.status_code,
            "message": _extract_message(response.data),
            "errors": response.data if isinstance(response.data, (list, dict)) else None,
            "request_id": request_id,
        }
        logger.warning(
            "API error",
            extra={
                "status_code": response.status_code,
                "path": getattr(request, "path", ""),
                "request_id": request_id,
                "errors": str(response.data)[:500],
            },
        )
        response.data = error_data
    else:
        # Unhandled exception — return 500
        logger.exception(
            "Unhandled exception",
            exc_info=exc,
            extra={"request_id": request_id},
        )
        response = Response(
            {
                "status": "error",
                "code": 500,
                "message": "An internal error occurred.",
                "errors": None,
                "request_id": request_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _extract_message(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("detail", "message", "non_field_errors"):
            if key in data:
                val = data[key]
                return str(val[0]) if isinstance(val, list) else str(val)
        first_key = next(iter(data))
        val = data[first_key]
        return f"{first_key}: {val[0] if isinstance(val, list) else val}"
    if isinstance(data, list) and data:
        return str(data[0])
    return "Request failed."
