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

import collections
import enum
import typing as t

from dataclasses import dataclass

from . import ast, debug

_ExprStack = t.Deque['ast.Expression']
_OpStack = t.Deque[t.Union['_Paren', '_Operator']]
_Token = t.Union['_Paren', '_Operator', 'ast.Polynomial']


class ParseError(Exception):
    pass


class ParenError(ParseError):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__('Unbalanced parentheses', *args, **kwargs)


class _Assoc(enum.IntEnum):
    LEFT = enum.auto()
    RIGHT = enum.auto()


@dataclass
class _Operator:
    repr: str
    arity: int
    assoc: _Assoc
    prec: int
    eval: t.Callable[..., ast.Expression]

    def __repr__(self) -> str:
        return self.repr

    def __lt__(self, other: '_Operator') -> bool:
        return self.prec > other.prec or (
            self.prec == other.prec and self.assoc == _Assoc.LEFT
        )


_OPERATORS = {
    '=': _Operator(
        repr='=', arity=2, assoc=_Assoc.LEFT, prec=0, eval=ast.Equation
    ),
    '+': _Operator(
        repr='+', arity=2, assoc=_Assoc.LEFT, prec=1, eval=lambda x, y: x + y
    ),
    '-': _Operator(
        repr='-', arity=2, assoc=_Assoc.LEFT, prec=1, eval=lambda x, y: x + -y
    ),
    '*': _Operator(
        repr='*', arity=2, assoc=_Assoc.LEFT, prec=2, eval=lambda x, y: x * y
    ),
    '/': _Operator(
        repr='/', arity=2, assoc=_Assoc.LEFT, prec=2, eval=lambda x, y: x / y
    ),
}


class _Paren(enum.IntEnum):
    LEFT = enum.auto()
    RIGHT = enum.auto()


def _skip_spaces(expr: str, i: int) -> int:
    l = len(expr)

    while i < l and expr[i].isspace():
        i += 1

    return i


def _read_symbol(expr: str, i: int) -> t.Tuple[int, ast.Polynomial]:
    l = len(expr)
    j = i

    while j < l:
        c = expr[j]

        if c.isalnum() or c == '_':
            j += 1
        else:
            break

    return j, ast.Polynomial(expr[i:j])


def _read_number(expr: str, i: int) -> t.Tuple[int, ast.Polynomial]:
    l = len(expr)
    j = i

    while j < l and expr[j].isdigit():
        j += 1

    if j < l and expr[j] == '.':
        j += 1

    while j < l and expr[j].isdigit():
        j += 1

    return j, ast.Polynomial(expr[i:j])


def _read_token(expr: str, i: int) -> t.Tuple[int, _Token]:
    c = expr[i]

    if c == '(':
        return i + 1, _Paren.LEFT

    if c == ')':
        return i + 1, _Paren.RIGHT

    if c in _OPERATORS:
        return i + 1, _OPERATORS[c]

    if c.isalpha():
        return _read_symbol(expr, i)

    if c.isdigit():
        return _read_number(expr, i)

    raise ParenError()


def tokenize(expr: str) -> t.Iterator[_Token]:
    l = len(expr)
    i = 0

    while i < l:
        i = _skip_spaces(expr, i)

        if i >= len(expr):
            return

        i, token = _read_token(expr, i)

        yield token


def _pop_operator(expr_stack: _ExprStack, op_stack: _OpStack) -> None:
    operator = op_stack.pop()

    if not isinstance(operator, _Operator):
        raise ParenError()

    try:
        args = reversed([expr_stack.pop() for _ in range(operator.arity)])
    except IndexError:
        raise ParseError(f'Unexpected operator')

    expr_stack.append(operator.eval(*args))


def _pop_until_lower_precedence(
    expr_stack: _ExprStack, op_stack: _OpStack, operator: _Operator
) -> None:
    while (
        op_stack
        and not isinstance(op_stack[-1], _Paren)
        and op_stack[-1] < operator
    ):
        _pop_operator(expr_stack, op_stack)


def _pop_until_left_paren(expr_stack: _ExprStack, op_stack: _OpStack) -> None:
    while op_stack and op_stack[-1] != _Paren.LEFT:
        _pop_operator(expr_stack, op_stack)

    if not op_stack:
        raise ParenError()

    op_stack.pop()


def parse(expr: str) -> ast.Expression:
    expr_stack: _ExprStack
    op_stack: _OpStack

    expr_stack = collections.deque()
    op_stack = collections.deque()

    for token in tokenize(expr):
        if isinstance(token, ast.Polynomial):
            expr_stack.append(token)

        elif isinstance(token, _Operator):
            _pop_until_lower_precedence(expr_stack, op_stack, token)
            op_stack.append(token)

        elif token == _Paren.LEFT:
            op_stack.append(token)

        elif token == _Paren.RIGHT:
            _pop_until_left_paren(expr_stack, op_stack)

        else:
            raise ParseError(f'Unknown token: {token}')

        debug.debug('Expression stack: {}', expr_stack)
        debug.debug('Operator stack:   {}', op_stack)

    while op_stack:
        _pop_operator(expr_stack, op_stack)
        debug.debug('Expression stack: {}', expr_stack)
        debug.debug('Operator stack:   {}', op_stack)

    assert len(expr_stack) == 1 and len(op_stack) == 0

    return expr_stack[0]
