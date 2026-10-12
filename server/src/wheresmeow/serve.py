"""운영 서버: python -m wheresmeow.serve

gevent 로 0.0.0.0:$PORT 에서 대기한다. 진행 중 대국이 메모리에 있으므로 프로세스는 하나만 띄운다.
필요한 환경 변수: WHERESMEOW_ENV=production, WHERESMEOW_SECRET_KEY, WHERESMEOW_ASYNC_MODE=gevent,
WHERESMEOW_STATIC_DIR(빌드된 웹 폴더).
"""

from gevent import monkey

monkey.patch_all()  # 다른 import 보다 먼저 해야 threading·socket 이 gevent 용으로 바뀐다

import logging  # noqa: E402
import os  # noqa: E402

from wheresmeow.bootstrap.app_factory import create_app  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app, socketio = create_app()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))


if __name__ == "__main__":
    main()
