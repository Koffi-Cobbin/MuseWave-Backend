import time
import json
from django.utils.deprecation import MiddlewareMixin
from datetime import datetime


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log API requests similar to Express logging"""
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = int((time.time() - request._start_time) * 1000)
            
            if request.path.startswith('/api'):
                # Format timestamp
                now = datetime.now()
                formatted_time = now.strftime('%I:%M:%S %p')
                
                # Build log line
                log_line = f"{formatted_time} [django] {request.method} {request.path} {response.status_code} in {duration}ms"
                
                # Add response data if JSON
                if hasattr(response, 'data') and response.get('Content-Type', '').startswith('application/json'):
                    try:
                        if isinstance(response.content, bytes):
                            content = response.content.decode('utf-8')
                            data = json.loads(content)
                            log_line += f" :: {json.dumps(data)}"
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                
                print(log_line)
        
        return response
