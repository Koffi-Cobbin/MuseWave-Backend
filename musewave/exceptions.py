from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response data
        custom_response_data = {
            'message': str(exc)
        }
        
        # If there are validation errors, include them
        if hasattr(response, 'data'):
            if isinstance(response.data, dict):
                if 'detail' in response.data:
                    custom_response_data['message'] = response.data['detail']
                elif 'error' in response.data:
                    custom_response_data = response.data
                else:
                    custom_response_data['errors'] = response.data
        
        response.data = custom_response_data
    else:
        # Handle non-DRF exceptions
        print(f"Internal Server Error: {exc}")
        response = Response(
            {'message': 'Internal Server Error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response
