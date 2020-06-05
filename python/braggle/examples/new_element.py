import typing
from braggle import *
from braggle.protobuf import element_pb2
import braggle.protobuf_helpers

class Details(Element):
    def __init__(self, summary: Element, contents: Element) -> None:
        super().__init__()
        self._summary = summary; summary.parent = self
        self._contents = contents; contents.parent = self

    @property
    def children(self) -> typing.Sequence[Element]:
        return (self.summary, self.contents)

    @property
    def summary(self) -> Element:
        return self._summary
    @summary.setter
    def summary(self, value: Element) -> None:
        self._summary.parent = None
        self._summary = value
        value.parent = self

    @property
    def contents(self) -> Element:
        return self._contents
    @contents.setter
    def contents(self, value: Element) -> None:
        self._contents.parent = None
        self._contents = value
        value.parent = self

    def to_protobuf(self) -> element_pb2.Element:
        return protobuf_helpers.tag(
            'details',
            children=[
                protobuf_helpers.tag('summary', children=[self.summary]),
                self.contents
            ]
        )

if __name__ == '__main__':
    serve(GUI(Details(summary=Text("Short summary"), contents=List(Text(str(n)) for n in range(100)))))
