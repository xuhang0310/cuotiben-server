from app.core.config import settings
print(f"Configured HOST: {settings.HOST}")
print(f"Configured PORT: {settings.PORT}")

import os
print(f"Environment HOST: {os.environ.get('HOST', 'Not set')}")
print(f"Environment PORT: {os.environ.get('PORT', 'Not set')}")