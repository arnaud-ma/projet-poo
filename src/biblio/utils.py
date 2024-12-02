from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import TypeAlias

StrPath: TypeAlias = str | PathLike[str]


class RealPath(Path):
    """Comme Path mais lance une ValueError si le fichier n'existe pas"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.exists():
            msg = f"Le chemin {self} n'existe pas."
            raise ValueError(msg)
