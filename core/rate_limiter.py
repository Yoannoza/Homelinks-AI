"""
Simple rate limiting implementation for the API
"""
import time
from collections import defaultdict
from functools import wraps
from flask import request, jsonify

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory leak"""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            cutoff_time = now - 3600  # Keep last hour of requests
            for ip in list(self.requests.keys()):
                self.requests[ip] = [ts for ts in self.requests[ip] if ts > cutoff_time]
                if not self.requests[ip]:
                    del self.requests[ip]
            self.last_cleanup = now
    
    def is_allowed(self, ip, limit=60, window=3600):
        """Check if request is allowed (default: 60 requests per hour)"""
        now = time.time()
        self.cleanup_old_requests()
        
        # Get requests from this IP in the time window
        window_start = now - window
        recent_requests = [ts for ts in self.requests[ip] if ts > window_start]
        
        if len(recent_requests) >= limit:
            return False
        
        # Add current request
        self.requests[ip].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit=60, window=3600):
    """Decorator to add rate limiting to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                ip = request.environ['REMOTE_ADDR']
            else:
                ip = request.environ['HTTP_X_FORWARDED_FOR']
            
            if not rate_limiter.is_allowed(ip, limit, window):
                return jsonify({
                    "error": "Rate limit exceeded. Please try again later."
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator