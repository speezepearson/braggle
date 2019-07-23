from dataclasses import dataclass
from typing import Any, Mapping, NewType, Optional, Sequence, TYPE_CHECKING, Union

from . import element

@dataclass(frozen=True)
class Interaction:
    target: str
    type: str
    value: Optional[str] = None

BridgeJson = NewType('BridgeJson', Mapping[str, Any])

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
