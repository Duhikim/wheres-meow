"""운영에서 빌드된 웹(web/dist)을 Flask 가 함께 제공한다. 컨테이너 하나로 화면과 API 를 낸다."""

from pathlib import Path

from flask import Flask, abort, send_from_directory

# 이 접두사로 시작하는 경로는 화면이 아니다. 없는 API 를 index.html 로 감추지 않는다.
NON_PAGE_PREFIXES = ("api/", "socket.io")


def register_static_site(app: Flask, static_dir: str) -> None:
    root = Path(static_dir).resolve()

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_page(path: str):
        if path.startswith(NON_PAGE_PREFIXES):
            abort(404)
        if path and (root / path).is_file():
            return send_from_directory(root, path)  # 자산 파일. 폴더 밖 경로는 send_from_directory 가 막는다
        return send_from_directory(root, "index.html")  # 화면 경로(/r/코드, /play/ID 등)는 SPA 가 처리한다
