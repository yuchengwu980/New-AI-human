import json
import os
import subprocess
import sys
from pathlib import Path


def pretty_json(payload: dict) -> str:
    return json.dumps(payload or {}, ensure_ascii=False, indent=2)


def open_in_file_manager(path: str | Path) -> None:
    target = Path(path).resolve()
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        os.startfile(str(target))  # type: ignore[attr-defined]
        return
    if sys.platform == 'darwin':
        subprocess.Popen(['open', str(target)])
    else:
        subprocess.Popen(['xdg-open', str(target)])


def open_parent_folder(path: str | Path) -> None:
    p = Path(path)
    open_in_file_manager(p.parent)
