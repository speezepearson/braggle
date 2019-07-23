import contextlib
from typing import Iterator
from unittest.mock import Mock

from bridge import Element, AbstractGUI

@contextlib.contextmanager
def assert_marks_dirty(e: Element) -> Iterator[None]:
    gui = Mock(spec=AbstractGUI)
    e.gui = gui
    yield
    gui.mark_dirty.assert_called_with(e)
