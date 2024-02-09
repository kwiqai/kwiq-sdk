from abc import ABC

from pydantic import BaseModel

from kwiq.core.flow import Flow


class Step(ABC, BaseModel):
    name: str
    flow: Flow
