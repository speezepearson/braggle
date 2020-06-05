import random

from braggle import Element
from braggle import protobuf_helpers

class SimpleElement(Element):
    def __repr__(self):
        return f'<id={self.id}>'
    def to_protobuf(self):
        return protobuf_helpers.text('')

def permutation(rng, xs):
    result = list(xs)
    rng.shuffle(result)
    return result

def test_child_parent_consistency_fuzzer():
    rng = random.Random(1)
    for _ in range(30):
        elements = [SimpleElement() for _ in range(20)]
        for i in range(1, len(elements)):
            parent_i = min(len(elements)-1, int(rng.expovariate(i/4)))
            elements[i].parent = elements[parent_i]

        for e in elements:
            for child in e.children:
                assert child.parent is e
            if e.parent is not None:
                assert e in e.parent.children

        for e in permutation(rng, elements):
            old_parent = e.parent
            e.parent = None
            if old_parent is not None:
                assert e not in old_parent.children
