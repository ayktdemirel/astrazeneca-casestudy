from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
from .logger import correlation_id_ctx

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-Id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        token = correlation_id_ctx.set(correlation_id)
        
        response = await call_next(request)
        
        response.headers["X-Correlation-Id"] = correlation_id
        
        correlation_id_ctx.reset(token)
        return response
