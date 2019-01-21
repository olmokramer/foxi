# Copyright (c) 2019 Olmo Kramer <olmo.kramer@protonmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import typing as t

if t.TYPE_CHECKING:

    class SympyExpr:
        def __neg__(self) -> 'SympyExpr':
            ...

        def __add__(self, other: 'SympyExpr') -> 'SympyExpr':
            ...

        def __mul__(self, other: 'SympyExpr') -> 'SympyExpr':
            ...

        def __truediv__(self, other: 'SympyExpr') -> 'SympyExpr':
            ...

        def factor(self) -> 'SympyExpr':
            ...

        def subs(
            self, sub: t.Mapping['SympyExpr', t.Union[int, 'SympyExpr']]
        ) -> 'SympyExpr':
            ...

        def as_terms(self) -> t.Tuple[t.Any, t.Sequence['SympyExpr']]:
            ...

        @property
        def free_symbols(self) -> t.Set['Symbol']:
            ...

        @property
        def is_number(self) -> bool:
            ...

        @property
        def is_zero(self) -> bool:
            ...

    class Add(SympyExpr):
        ...

    class Mul(SympyExpr):
        ...

    class Pow(SympyExpr):
        ...

    class Number(SympyExpr):
        def __init__(self, num: t.Union[float, int]) -> None:
            ...

    class Symbol(SympyExpr):
        def __init__(self, name: str) -> None:
            ...

    def sympify(term: t.Union[float, int, str]) -> SympyExpr:
        ...


else:
    from sympy import Add, Mul, Pow, Number, Symbol, sympify

    SympyExpr = t.Union[Add, Mul, Pow, Number, Symbol]

SympyExprTypes = (Add, Mul, Pow, Number, Symbol)
