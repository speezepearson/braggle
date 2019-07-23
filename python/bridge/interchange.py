from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, NewType, Optional, Sequence, TYPE_CHECKING, Union

from . import element

@dataclass(frozen=True)
class Interaction:
    target: str
    type: str
    value: Optional[str] = None

BridgeJson = NewType('BridgeJson', Mapping[str, Any])
PollResponse = NewType('PollResponse', Mapping[str, Any])

def text_json(s: str) -> BridgeJson:
    return BridgeJson({'text': s})

def node_json(
    node_name: str,
    attributes: Mapping[str, str],
    children: Sequence[Union[BridgeJson, element.Element]]
) -> BridgeJson:
    return BridgeJson({
        'name': node_name,
        'attributes': attributes,
        'children': [{'ref': c.id} if isinstance(c, element.Element) else c for c in children],
    })

def poll_response(root: element.Element, time_step: int, elements: Iterable[element.Element]) -> PollResponse:
    return PollResponse({
        'root': root.id,
        'timeStep': time_step,
        'elements': {
            e.id: {"id": e.id, "subtree": e.subtree_json()}
            for e in elements
        }
    })
