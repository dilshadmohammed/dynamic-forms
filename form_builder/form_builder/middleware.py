# import json
# from django.http import JsonResponse
# from django.utils.deprecation import MiddlewareMixin

# class ExceptionMiddleware(MiddlewareMixin):
#     def process_exception(self, request, exception):
#         # Log the exception if needed
#         # logger.error(f"Exception occurred: {exception}")

#         response_data = {
#             "error": "An unexpected error occurred.",
#             "message": str(exception)
#         }
#         return JsonResponse(response_data, status=500)

