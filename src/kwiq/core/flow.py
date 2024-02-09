from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from kwiq.core.typed import Typed


class Flow(Typed, BaseModel):
    name: str

    @abstractmethod
    def fn(self, *args, **kwargs) -> Any:
        pass
