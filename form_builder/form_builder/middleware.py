
import json
import traceback
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            logger.error("Exception occurred", exc_info=True)
            if settings.DEBUG:
                response = self.process_exception_debug(e)
            else:
                response = self.process_exception(e)
        return response

    def process_exception_debug(self, exception):
        # Detailed error message with stack trace for debugging
        error_details = {
            'error': str(exception),
            'type': type(exception).__name__,
            'traceback': traceback.format_exc().split('\n')
        }
        return JsonResponse(error_details, status=500)

    def process_exception(self, exception):
        # Generic error message for production
        error_details = {
            'error': 'An unexpected error occurred. Please try again later.'
        }
        return JsonResponse(error_details, status=500)
