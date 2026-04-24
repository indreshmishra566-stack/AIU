"""
AIU — Users App: Middleware
Attaches request_id to every request for tracing.
"""

import uuid


class RequestContextMiddleware:
    """
    Attaches a unique request_id to every request.
    Used in logging and error responses for distributed tracing.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response
