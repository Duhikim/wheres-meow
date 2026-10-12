"""개발 서버: python -m wheresmeow (기본 포트 5000)."""

import logging
import os

from wheresmeow.bootstrap.app_factory import create_app

logging.basicConfig(level=logging.INFO)
app, socketio = create_app()

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), allow_unsafe_werkzeug=True)
