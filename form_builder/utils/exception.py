from rest_framework.exceptions import APIException

class UnauthorizedAccessException(APIException):
    def __init__(self, detail="Something went wrong", status_code=401):
        self.detail = detail
        self.status_code = status_code
