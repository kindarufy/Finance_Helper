"""Тест проверки наличия обязательных файлов релизной поставки."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_assets_exist():
    """Проверяет наличие обязательных файлов релизной поставки."""
    expected = [
        ROOT / "scripts" / "seed_demo.py",
        ROOT / "Makefile",
        ROOT / ".env.example",
    ]
    missing = [str(p.relative_to(ROOT)) for p in expected if not p.exists()]
    assert not missing, f"Missing release assets: {missing}"
