from pydantic import BaseModel
from typing import Any
from abc import abstractmethod

from kwiq.core.typed import Typed


class Task(Typed, BaseModel):
    name: str

    @abstractmethod
    def fn(self, *args, **kwargs) -> Any:
        pass
