import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict


@dataclass
class Response:
    """
    A standard response class to structure API responses.

    This class provides a consistent way to return responses from API methods.

    Attributes:
        status (str): The status of the response ('success' or 'error').
        message (str): A message providing details about the response.
        data (Optional[Dict]): Additional data related to the response, if any.

    Methods:
        success(message: str, data: Optional[Dict] = None) -> "Response":
            Factory method that creates a success response.

        error(message: str, data: Optional[Dict] = None) -> "Response":
            Factory method that creates an error response.
    """

    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"

    status: str
    message: str
    data: Optional[Dict] = field(default=None)

    @staticmethod
    def success(message: str, data: Optional[Dict] = None) -> "Response":
        """Factory method for success responses."""
        return Response(status=Response.STATUS_SUCCESS, message=message, data=data)

    @staticmethod
    def error(message: str, data: Optional[Dict] = None) -> "Response":
        """Factory method for error responses."""
        return Response(status=Response.STATUS_ERROR, message=message, data=data)

    def to_json(self) -> str:
        """Converts the response to a JSON string."""
        return json.dumps(asdict(self))
