from pathlib import Path

from pydantic import BaseModel
from typing import Union, Type

IteratorResult = Union[
    BaseModel,
    int,
    float,
    str,
    bool,
    list,
    set,
    Path,
    dict[str, 'IteratorResult'],
    list['IteratorResult'],
    set['IteratorResult'],
    tuple
]
