import os
import shutil
from pathlib import Path
from typing import Callable, Optional

from pydantic import BaseModel

from kwiq.core.task import Task


class InputModel(BaseModel):
    directory: Path
    filter: Optional[Callable[[str], bool]]


class CleanDirectory(Task):
    name: str = "clean_directory"

    def fn(self, data: InputModel) -> None:
        for item in os.listdir(data.directory):
            path = os.path.join(data.directory, item)
            if os.path.isdir(path) and (data.filter is None or not data.filter(item)):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)
