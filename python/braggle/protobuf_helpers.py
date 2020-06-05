from __future__ import annotations

from .protobuf import element_pb2
from dataclasses import dataclass
from typing import Mapping, Sequence, Union

from . import element
from .types import ElementId, TimeStep

def text(s: str) -> element_pb2.Element:
    return element_pb2.Element(text=s)

def ref(e: element.Element) -> element_pb2.Element:
    return element_pb2.Element(ref=e.id)

def tag(
    tagname: str,
    children: Sequence[Union[element_pb2.Element, element.Element]] = (),
    attributes: Mapping[str, str] = {},
) -> element_pb2.Element:
    return element_pb2.Element(tag=element_pb2.Tag(
        tagname=tagname,
        attributes=element_pb2.Attributes(misc=attributes),
        children=[ref(child) if isinstance(child, element.Element) else child for child in children],
    ))
