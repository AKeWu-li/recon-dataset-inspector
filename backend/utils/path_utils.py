from pathlib import Path
from fastapi import HTTPException

from backend.config import PROJECT_ROOT


def resolve_project_path(path_str: str) -> Path:
    """
    将数据库中保存的路径解析为绝对路径。

    如果 path_str 是绝对路径，就直接 resolve。
    如果 path_str 是相对路径，就认为它相对于项目根目录。
    """
    path = Path(path_str)

    if path.is_absolute():
        return path.resolve()

    return (PROJECT_ROOT / path).resolve()


def ensure_path_inside(base_path: Path, target_path: Path):
    """
    确保 target_path 位于 base_path 内部，防止路径穿越。
    """
    try:
        target_path.relative_to(base_path)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )