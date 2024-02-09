import os
import shutil
from pathlib import Path
from typing import Optional, Callable

from pydantic import BaseModel

from kwiq.core.task import Task


class InputModel(BaseModel):
    src_directory: Path
    dest_directory: Path
    filter: Optional[Callable[[str], bool]]


class CopyDirectory(Task):
    name: str = "copy_directory"

    def fn(self, data: InputModel) -> None:
        print(f"Copy Directory: {data}")

        for item in os.listdir(data.src_directory):
            if data.filter is not None and data.filter(item):
                continue

            s = os.path.join(data.src_directory, item)
            d = os.path.join(data.dest_directory, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, False, None)
            else:
                shutil.copy2(s, d)
