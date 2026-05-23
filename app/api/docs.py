from fastapi.openapi.utils import get_openapi

def custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Doriot AI Agent API",
        version="1.0.0",
        
        routes=app.routes,
    )

    # Update security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "DoriotAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            # "description": "JWT token from Doriot.ai authentication"
            "description":"""
            # Authentication Flow
            
            This API uses Django's authentication system. Follow these steps:

            1. Get CSRF token and login:
            ```bash
            # Get CSRF token
            curl -c cookies.txt https://doriot.ai/api/login/
            CSRF_TOKEN=$(grep csrftoken cookies.txt | cut -f 7)

            # Login and get access token
            curl -X POST https://doriot.ai/api/login/ \\
            -H "Content-Type: application/json" \\
            -H "X-CSRFToken: $CSRF_TOKEN" \\
            -H "Referer: https://doriot.ai" \\
            -b cookies.txt \\
            -d '{"email": "your@email.com", "password": "your_password"}'
            ```

            2. The response will include:
            ```json
            {
                "access_token": "your.jwt.token",
                "refresh_token": "your.refresh.token",
                "isAuthenticated": true,
                ...
            }
            ```

            3. Use the access token in subsequent requests:
            ```bash
            curl -X POST "http://localhost:8000/api/v1/chat" \\
            -H "Authorization: Bearer your.jwt.token" \\
            -H "Content-Type: application/json" \\
            -d '{"messages": [{"role": "user", "content": "Hello"}]}'
            ```
            """
        }
    }

    openapi_schema["security"] = [{"DoriotAuth": []}]

    return openapi_schema