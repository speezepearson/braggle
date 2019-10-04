from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, NewType, Optional, Sequence, TYPE_CHECKING, Union
from typing_extensions import TypedDict

from . import element
from .types import ElementId, TimeStep

@dataclass(frozen=True)
class Interaction:
    target: str
    type: str
    value: Optional[str] = None

TextSpec = TypedDict('TextSpec', {'text': str})
ElementRefSpec = TypedDict('ElementRefSpec', {'ref': ElementId})
NodeSpec = TypedDict('NodeSpec', {
    'name': str,
    'attributes': Mapping[str, str],
    'children': Sequence[Any] # TODO: refine this type if possible
})
BridgeJson = Union[TextSpec, ElementRefSpec, NodeSpec]

ElementDescription = TypedDict('ElementDescription', {'id': ElementId, 'subtree': BridgeJson})
PollResponse = TypedDict('PollResponse', {
    'root': ElementId,
    'timeStep': TimeStep,
    'elements': Mapping[ElementId, ElementDescription],
})

def text_json(s: str) -> BridgeJson:
    return TextSpec({'text': s})

def node_json(
    node_name: str,
    attributes: Mapping[str, str],
    children: Sequence[Union[BridgeJson, element.Element]]
) -> BridgeJson:
    return NodeSpec({
        'name': node_name,
        'attributes': attributes,
        'children': [{'ref': c.id} if isinstance(c, element.Element) else c for c in children],
    })

def poll_response(root: element.Element, time_step: TimeStep, elements: Iterable[element.Element]) -> PollResponse:
    return PollResponse({
        'root': root.id,
        'timeStep': time_step,
        'elements': {
            e.id: {"id": e.id, "subtree": e.subtree_json()}
            for e in elements
        }
    })
