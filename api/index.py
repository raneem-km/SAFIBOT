import sys
import os
import traceback

# Add root directory to sys.path so backend imports work properly
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

init_error = None
app = None

try:
    # Auto-initialize database & seed data on serverless cold-start
    from backend.database.db import init_db, seed_demo_data
    init_db()
    seed_demo_data()
    from backend.main import app as fastapi_app
    app = fastapi_app
except Exception as e:
    init_error = f"{type(e).__name__}: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"

if init_error:
    async def app(scope, receive, send):
        if scope['type'] == 'http':
            body = f"Vercel Python Function Startup Error:\n\n{init_error}".encode('utf-8')
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [
                    [b'content-type', b'text/plain; charset=utf-8'],
                    [b'content-length', str(len(body)).encode('utf-8')]
                ]
            })
            await send({
                'type': 'http.response.body',
                'body': body
            })
