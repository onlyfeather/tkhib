import os
from pathlib import Path


def get_data_dir(*parts: str) -> Path:
    base_dir = Path(os.getenv("TKHIB_DATA_DIR", "data")).expanduser()
    path = base_dir.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_path(*parts: str) -> Path:
    path = get_data_dir(*parts[:-1]) if len(parts) > 1 else get_data_dir()
    return path / parts[-1]
