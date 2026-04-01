
import datetime
import uuid
from hashlib import sha256
from typing import Self

from pydantic import BaseModel, Field

from jmapy.models import ID
from jmapy.orm.base import ListReference, NullReference, Reference
from jmapy.orm.get import GettableData


def make_device_id() -> str:
    machine_mac = uuid.getnode()
    return sha256(machine_mac.to_bytes() + b"jmapy").hexdigest()


class StateChange(BaseModel):
    type: str = Field(alias="@type")
    changed: dict[ID, dict[str, str]]


class EncyptionKeys:
    p256dh = Reference[Self, str]()
    oauth = Reference[Self, str]()

class PushSubscription(GettableData):
    id = Reference[Self, ID]()
    device_client_id = Reference[Self, str]()
    url = Reference[Self, str]()
    verification_code = NullReference[Self, str]()
    expires = Reference[Self, datetime.datetime]()
    types = ListReference[Self, str]()

