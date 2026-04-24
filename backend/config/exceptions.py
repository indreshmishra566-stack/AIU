from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    # If DRF handled it → modify response
    if response is not None:
        return Response({
            "success": False,
            "error": {
                "message": response.data,
                "status_code": response.status_code
            }
        }, status=response.status_code)

    # If it's an unhandled exception (server error)
    return Response({
        "success": False,
        "error": {
            "message": str(exc),
            "status_code": 500
        }
    }, status=500)