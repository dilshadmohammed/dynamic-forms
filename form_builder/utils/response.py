from typing import Any, Dict, List
from rest_framework import status
from rest_framework.response import Response



class CustomResponse:

    def __init__(
            self,
            message: Dict[str, Any] = None,
            general_message: List[str] = None,
            response: Dict[str, Any] = None,
    ) -> None:

        self.message = {} if message is None else message
        self.response = {} if response is None else response


    def get_success_response(self) -> Response:

        return Response(
            data={
                "hasError": False,
                "statusCode": status.HTTP_200_OK,
                "message": self.message,
                "response": self.response,
            },
            status=status.HTTP_200_OK,
        )

    def get_failure_response(
            self,
            status_code: int = 400,
            http_status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> Response:
        
        return Response(
            data={
                "hasError": True,
                "statusCode": status_code,
                "message": self.message,
                "response": self.response,
            },
            status=http_status_code,
        )

    def get_unauthorized_response(
            self
    ) -> Response:
        
        return Response(
            data={
                "hasError": True,
                "statusCode": 401,
                "message": self.message,
                "response": self.response,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
