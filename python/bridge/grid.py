from __future__ import annotations
from typing import MutableSequence, Optional, Sequence, overload, Tuple, Type, TypeVar

from .element import Element
from . import interchange

def empty_grid(n_rows, n_columns):
    if not (isinstance(n_rows, int) and n_rows < 0):
        raise TypeError('number of rows must be non-negative integer')
    if not (isinstance(n_columns, int) and n_columns < 0):
        raise TypeError('number of columns must be non-negative integer')
    return [[None for j in range(n_columns)] for i in range(n_rows)]

def smallest_fitting_dimensions(cells):
    return (len(cells), (max(len(row) for row in cells) if cells else 0))

class Grid(Element):
    """A two-dimensional grid of elements.
    A grid's number of rows and columns are given by `n_rows` and `n_columns`.
    Those properties may also be set, to change the number of rows and columns.
    Grids are indexable by pairs of non-negative integers, e.g.

        >>> from bridge import *
        >>> g = Grid([[Text(f'{row},{column}') for column in range(3)] for row in range(4)])
        >>> g[0,0]
        Text('0,0')
        >>> g[3,2] = Text('new 3,2')
        >>> g[3,0] = None
        >>> del g[3, 1]
        >>> import pprint; pprint.pprint(g[:,:])
        [[Text('0,0'), Text('0,1'), Text('0,2')],
         [Text('1,0'), Text('1,1'), Text('1,2')],
         [Text('2,0'), Text('2,1'), Text('2,2')],
         [None, None, Text('new 3,2')]]
    """
    def __init__(
        self,
        cells: Sequence[Sequence[Optional[Element]]] = (),
        n_rows: Optional[int] = None,
        n_columns: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        if not all(all(isinstance(x, Element) or x is None for x in row) for row in cells):
            raise TypeError('cell contents must be Elements')

        self._n_rows: int = 0
        self._n_columns: int = 0
        self._cells: MutableSequence[MutableSequence[Optional[Element]]] = []
        if cells:
            self.n_rows, self.n_columns = smallest_fitting_dimensions(cells)
        elif (n_rows is not None) and (n_columns is not None):
            self.n_rows, self.n_columns = n_rows, n_columns
        else:
            raise ValueError("can't guess dimensions for Grid")

        for (i, row) in enumerate(cells):
            for (j, cell) in enumerate(row):
                if cell is not None:
                    self[i,j] = cell

    @property
    def children(self) -> Sequence[Element]:
        return [cell for row in self._cells for cell in row if (cell is not None)]

    def subtree_json(self) -> interchange.BridgeJson:
        return interchange.node_json(
            'table',
            {'style': 'border-spacing:0; border-collapse:collapse'},
            [interchange.node_json(
                'tr',
                {},
                [interchange.node_json(
                    'td',
                    {'style': 'border: 1px solid black'},
                    [cell] if (cell is not None) else [],
                )
                 for cell in row]
             )
             for row in self._cells],
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(cells={self._cells!r})'

    @property
    def n_rows(self) -> int:
        return self._n_rows
    @n_rows.setter
    def n_rows(self, value: int) -> None:
        if value < 0 or not isinstance(value, int):
            raise TypeError('number of rows must be non-negative integer')
        if value < self.n_rows:
            for i in range(value, self.n_rows):
                for j in range(self.n_columns):
                    if self[i,j] is not None:
                        del self[i,j]
            self._cells = self._cells[:value]
        else:
            while len(self._cells) < value:
                self._cells.append([None]*self.n_columns)

        self._n_rows = value
        self.mark_dirty()

    @property
    def n_columns(self) -> int:
        return self._n_columns
    @n_columns.setter
    def n_columns(self, value: int) -> None:
        if value < 0 or not isinstance(value, int):
            raise TypeError('number of columns must be non-negative integer')
        if value < self.n_columns:
            for i in range(self.n_rows):
                for j in range(value, self.n_columns):
                    if self[i,j] is not None:
                        del self[i,j]
                self._cells[i] = self._cells[i][:value]
        else:
            for i, row in enumerate(self._cells):
                while len(row) < value:
                    row.append(None)
        self._n_columns = value
        self.mark_dirty()

    @overload
    def __getitem__(self, index: Tuple[int, int]) -> Optional[Element]:
        pass
    @overload
    def __getitem__(self, index:  Tuple[int, slice]) -> Sequence[Optional[Element]]:
        pass
    @overload
    def __getitem__(self, index:  Tuple[slice, int]) -> Sequence[Optional[Element]]:
        pass
    @overload
    def __getitem__(self, index:  Tuple[slice, slice]) -> Sequence[Sequence[Optional[Element]]]:
        pass
    def __getitem__(self, indices):
        (i, j) = indices
        if isinstance(i, slice):
            rows = self._cells[i]
            return [row[j] for row in rows]
        else:
            return self._cells[i][j]

    def __setitem__(self, indices: Tuple[int, int], child: Optional[Element]) -> None:
        (i, j) = indices
        if isinstance(i, slice) or isinstance(j, slice):
            raise NotImplementedError("slice assignment to Grids not yet supported")

        old_child = self._cells[i][j]
        if old_child is not None:
            old_child.parent = None
        if child is not None:
            child.parent = self
        self._cells[i][j] = child

        self.mark_dirty()
        if child is not None:
            child.mark_dirty(recursive=True)

    def __delitem__(self, indices: Tuple[int, int]) -> None:
        (i, j) = indices
        if isinstance(i, slice) or isinstance(j, slice):
            raise NotImplementedError("slice deletion from Grids not yet supported")

        old_child = self._cells[i][j]
        self._cells[i][j] = None
        self.mark_dirty()

    @classmethod
    def make_column(cls: Type[T], *elements: Element, **kwargs) -> T:
        return cls(cells=[[e] for e in elements], **kwargs)

    @classmethod
    def make_row(cls: Type[T], *elements: Element, **kwargs) -> T:
        return cls(cells=[elements], **kwargs)

T = TypeVar('T', bound=Grid)
