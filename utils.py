# utils.py
import json
import os

DATA_FILE = "assets.json"  # JSON 파일 경로

def load_assets():
    """assets.json을 로드하여 딕셔너리로 반환."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_assets(data):
    """수정된 자산 딕셔너리를 assets.json에 저장."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False → 한글이 유니코드 이스케이프가 안 되도록
        # indent=4 → 보기 좋게 줄바꿈
        json.dump(data, f, ensure_ascii=False, indent=4)