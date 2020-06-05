import contextlib
from typing import Iterator
from unittest.mock import patch

from braggle import Element, AbstractGUI

@contextlib.contextmanager
def assert_marks_dirty(element: Element):
    old_mark_dirty = element.mark_dirty
    with patch.object(element, 'mark_dirty', wraps=old_mark_dirty) as mock:
        yield
        assert mock.call_count > 0
