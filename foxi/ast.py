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

import abc
import typing as t

from . import debug
from .sympy_types import (
    Mul,
    Number,
    Pow,
    Symbol,
    SympyExpr,
    SympyExprTypes,
    sympify,
)


class AlgebraError(Exception):
    """Raised when an operation is invalid.
    """


class Expression(abc.ABC):
    @abc.abstractmethod
    def __repr__(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def free_variables(self) -> t.Set[Symbol]:
        """Get the variables in this expression.
        """
        ...

    def eval(
        self, zeros: t.Set[SympyExpr] = None, nonzeros: t.Set[SympyExpr] = None
    ) -> 'Algebraic':
        """ Wrapper for ``_eval`` to make sure ``zeros`` and ``nonzeros`` are
        not the empty set.
        """

        if zeros is None:
            zeros = set()

        if nonzeros is None:
            nonzeros = set()

        return self._eval(zeros, nonzeros)

    @abc.abstractmethod
    def _eval(
        self, zeros: t.Set[SympyExpr], nonzeros: t.Set[SympyExpr]
    ) -> 'Algebraic':
        """
        Evaluate this expression in the given zeros and nonzeros.

        >>> x = sympy.Symbol('x')
        >>> y = sympy.Symbol('y')
        >>> p = Polynomial(x + y)
        >>> p._eval({x}, set())
        y
        """
        ...


class Equation(Expression):
    lhs: 'Algebraic'
    rhs: 'Algebraic'

    def __init__(self, lhs: 'Algebraic', rhs: 'Algebraic') -> None:
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self) -> str:
        return f'{self.lhs} = {self.rhs}'

    @property
    def free_variables(self) -> t.Set[Symbol]:
        return self.lhs.free_variables | self.rhs.free_variables

    def _eval(
        self, zeros: t.Set[SympyExpr], nonzeros: t.Set[SympyExpr]
    ) -> 'Algebraic':
        diff = self.lhs - self.rhs
        variables = diff.free_variables

        debug.info('Checking equation: {}', self)
        debug.debug('SMF: {} = 0', diff)
        debug.debug('Variables {}', variables)

        var_bits = {v: (1 << i) for i, v in enumerate(variables)}

        for i in range(pow(2, len(variables))):
            cur_zeros = zeros | {v for v, k in var_bits.items() if not i & k}
            cur_nonzeros = nonzeros | {v for v, k in var_bits.items() if i & k}

            debug.debug(
                'Checking with zeros {}, nonzeros {}', cur_zeros, cur_nonzeros
            )

            eval = diff.eval(cur_zeros, cur_nonzeros)

            if not isinstance(eval, Polynomial) or not eval.is_zero:
                debug.info(
                    'Counterexample: {}',
                    {
                        v: 'zero' if v in cur_zeros else 'nonzero'
                        for v in variables
                    },
                )
                break

        return eval


class Algebraic(Expression, abc.ABC):
    """Superclass for classes that support algebraic operations, specifically

    - ``__neg__``
    - ``__add__``
    - ``__sub__``
    - ``__mul__``
    - ``__truediv__``

    Some constant folding is implemented in those methods, which should run
    before calling the corresponding methods on the subclasses. Subclasses must
    implement ``neg``, ``add``, ``mul``, and ``div`` methods.
    """

    @abc.abstractmethod
    def __eq__(self, other: t.Any) -> bool:
        ...

    @property
    def is_zero(self) -> bool:
        return False

    @property
    def is_one(self) -> bool:
        return False

    @property
    def is_constant(self) -> bool:
        return False

    def __neg__(self) -> 'Algebraic':
        return self.neg()

    @abc.abstractmethod
    def neg(self) -> 'Algebraic':
        ...

    def __add__(self, other: 'Algebraic') -> 'Algebraic':
        if self.is_zero:
            return other

        if other.is_zero:
            return self

        return self.add(other)

    @abc.abstractmethod
    def add(self, other: 'Algebraic') -> 'Algebraic':
        ...

    def __sub__(self, other: 'Algebraic') -> 'Algebraic':
        if self.is_zero:
            return -other

        if other.is_zero:
            return self

        return self + -other

    def __mul__(self, other: 'Algebraic') -> 'Algebraic':
        if self.is_zero or other.is_zero:
            return Polynomial(0)

        if self.is_one:
            return other

        if other.is_one:
            return self

        return self.mul(other)

    @abc.abstractmethod
    def mul(self, other: 'Algebraic') -> 'Algebraic':
        ...

    def __truediv__(self, other: 'Algebraic') -> 'Algebraic':
        if self.is_zero or other.is_zero:
            return Polynomial(0)

        if other.is_one:
            return self

        return self.div(other)

    @abc.abstractmethod
    def div(self, other: 'Algebraic') -> 'Algebraic':
        ...


class Polynomial(Algebraic):
    _factorized: bool
    terms: SympyExpr

    def __init__(self, term: t.Union[float, int, str, SympyExpr]) -> None:
        self._factorized = False

        if isinstance(term, SympyExprTypes):
            self.terms = term
        else:
            # Mypy can't determine that ``term`` is not of type ``SympyExpr`` here.
            self.terms = sympify(term)  # type: ignore

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, Polynomial):
            return False

        return self.terms == other.terms

    def __repr__(self) -> str:
        if self.is_constant:
            return repr(self.terms)
        else:
            return f'({self.terms.factor()})'

    @property
    def factors(self) -> t.Sequence[SympyExpr]:
        if not self._factorized:
            self._factorized = True
            self.terms = self.terms.factor()

        if isinstance(self.terms, (Mul, Pow)):
            return self.terms.as_terms()[1]
        else:
            return [self.terms]

    @property
    def free_variables(self) -> t.Set[Symbol]:
        return self.terms.free_symbols

    @property
    def is_zero(self) -> bool:
        return self.terms.is_zero

    @property
    def is_one(self) -> bool:
        return self.terms == Number(1)

    @property
    def is_constant(self) -> bool:
        return self.terms.is_number

    def neg(self) -> Algebraic:
        return Polynomial(-self.terms)

    def add(self, other: Algebraic) -> Algebraic:
        if isinstance(other, Polynomial):
            return Polynomial(self.terms + other.terms)

        if isinstance(other, SMF0):
            return SMFN.make(
                other.rhs, (self * other.rhs + other.lhs) / other.rhs, self
            )

        if isinstance(other, SMFN):
            return SMFN.make(other.cond, self + other.P, self + other.Q)

        raise AlgebraError(f'Can\'t add types {type(self)} and {type(other)}.')

    def mul(self, other: Algebraic) -> Algebraic:
        if isinstance(other, Polynomial):
            return Polynomial(self.terms * other.terms)

        if isinstance(other, SMF0):
            return SMF0(Polynomial(self.terms * other.lhs.terms), other.rhs)

        if isinstance(other, SMFN):
            return SMFN.make(other.cond, self * other.P, self * other.Q)

        raise AlgebraError(
            f'Can\'t multiply types {type(self)} and {type(other)}.'
        )

    def div(self, other: Algebraic) -> Algebraic:
        if isinstance(other, Polynomial):
            if other.is_constant:
                return Polynomial(self.terms / other.terms)

            return SMF0(self, other)

        if isinstance(other, SMF0):
            return SMF0(Polynomial(self.terms * other.rhs.terms), other.lhs)

        if isinstance(other, SMFN):
            return SMFN.make(other.cond, self / other.P, self / other.Q)

        raise AlgebraError(
            f'Can\'t divide types {type(self)} and {type(other)}.'
        )

    @debug.indent()  # type: ignore
    def _eval(  # type: ignore
        self, zeros: t.Set[SympyExpr], nonzeros: t.Set[SympyExpr]
    ) -> 'Algebraic':
        debug.debug(
            'Evaluating Polynomial {} in zeros {}, nonzeros {}',
            self,
            zeros,
            nonzeros,
        )

        if self.is_constant:
            ret = self.terms
        else:
            factors = set(self.factors)

            ret = factors.pop()
            for f in factors:
                if f not in nonzeros:
                    ret *= f

            ret = ret.subs({zero: 0 for zero in zeros})

        debug.debug('Result: {}', ret)
        return Polynomial(ret)


class SMF(Algebraic):
    pass


class SMF0(SMF):
    lhs: Polynomial
    rhs: Polynomial

    def __init__(self, lhs: Polynomial, rhs: Polynomial) -> None:
        self.lhs = lhs
        self.rhs = rhs

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, SMF0):
            return False

        return self.lhs == other.lhs and self.rhs == other.rhs

    def __repr__(self) -> str:
        return f'({self.lhs} / {self.rhs})'

    @property
    def free_variables(self) -> t.Set[Symbol]:
        return self.lhs.free_variables | self.rhs.free_variables

    def neg(self) -> Algebraic:
        return -self.lhs / self.rhs

    def add(self, other: Algebraic) -> Algebraic:
        if isinstance(other, Polynomial):
            return other + self

        if isinstance(other, SMF0):
            if self.rhs == other.rhs:
                return (self.lhs + other.lhs) / self.rhs
            else:
                return SMFN.make(
                    self.rhs,
                    SMFN.make(
                        other.rhs,
                        (self.lhs * other.rhs + self.rhs * other.lhs)
                        / (self.rhs * other.rhs),
                        self,
                    ),
                    other,
                )

        if isinstance(other, SMFN):
            if self.rhs == other.cond:
                return SMFN.make(self.rhs, self + other.P, other.Q)
            else:
                return SMFN.make(
                    other.cond,
                    SMFN.make(self.rhs, self + other.P, other.P),
                    SMFN.make(self.rhs, self + other.Q, other.Q),
                )

        raise AlgebraError(f'Can\'t add types {type(self)} and {type(other)}.')

    def mul(self, other: Algebraic) -> Algebraic:
        if isinstance(other, Polynomial):
            return other * self

        if isinstance(other, SMF0):
            return (self.lhs * other.lhs) / (self.rhs * other.rhs)

        if isinstance(other, SMFN):
            if self.rhs == other.cond:
                return SMFN.make(other.cond, other.P, Polynomial(0))
            else:
                return SMFN.make(other.cond, self * other.P, self * other.Q)

        raise AlgebraError(
            f'Can\'t multiply types {type(self)} and {type(other)}.'
        )

    def div(self, other: Algebraic) -> Algebraic:
        if isinstance(other, Polynomial):
            return self.lhs / (self.rhs * other)

        if isinstance(other, SMF0):
            return (self.lhs * other.rhs) / (self.rhs * other.lhs)

        if isinstance(other, SMFN):
            if self.rhs == other.cond:
                return SMFN.make(
                    other.cond,
                    Polynomial(1) / (self.rhs * other.P),
                    Polynomial(0),
                )
            else:
                return SMFN.make(other.cond, self / other.P, self / other.Q)

        raise AlgebraError(
            f'Can\'t divide types {type(self)} and {type(other)}.'
        )

    @debug.indent()  # type: ignore
    def _eval(  # type: ignore
        self, zeros: t.Set[SympyExpr], nonzeros: t.Set[SympyExpr]
    ) -> 'Algebraic':
        debug.debug(
            'Evaluating SMF0 {} in zeros {}, nonzeros {}',
            self,
            zeros,
            nonzeros,
        )

        lhs = self.lhs.eval(zeros, nonzeros)
        rhs = self.rhs.eval(zeros, nonzeros)

        debug.debug('Result: {}', lhs * rhs)
        return lhs * rhs


class SMFN(SMF):
    cond: Polynomial
    P: Algebraic
    Q: Algebraic

    def __init__(self, cond: Polynomial, P: Algebraic, Q: Algebraic) -> None:
        """DO NOT call this method directly! Call SMFN.make() instead.
        """

        self.cond = cond
        self.P = P
        self.Q = Q

    @classmethod
    def make(cls, cond: Polynomial, P: Algebraic, Q: Algebraic) -> Algebraic:
        """Wrapper for the class constructor. We need to wrap it to implement
        some optimizations that we cannot perform in the constructor, because
        they don't yield a new SMFN but another already existing object.

        First, remove duplicate prime factors from cond. Because we need cond
        only to check if it is equal to zero, we can ignore duplicate prime
        factors of the polynomial.

        Let cond = c_1 * c_1 * ... * c_n
        Then (c_1 * c_1 = 0) -> (cond = 0)
        But (c_1 = 0) -> (cond = 0) is sufficient

        Then apply the optimizations described in section 2.4.
        """

        factors = cond.factors
        is_monomial = len(factors) == 1

        if not is_monomial:
            c = factors[0]
            for f in factors[1:]:
                c *= f
            cond = Polynomial(c)
        else:
            cond = Polynomial(factors[0])

        if isinstance(P, SMFN) and P.cond == cond:
            P = P.P

        if isinstance(Q, SMFN) and Q.cond == cond:
            Q = Q.Q
        elif (
            (isinstance(Q, SMF0) and (cond in (Q.lhs, Q.rhs)))
            or (isinstance(Q, Polynomial) and Q == cond)
        ):
            Q = Polynomial(0)

        if P == Q:
            return P
        elif cond.is_zero:
            return Q
        elif cond.is_constant:
            return P
        else:
            return cls(cond, P, Q)

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, SMFN):
            return False

        return (
            self.cond == other.cond and self.P == other.P and self.Q == other.Q
        )

    def __repr__(self) -> str:
        cond = self.cond
        return f'(({cond}/{cond}) * {self.P} + (1 - {cond}/{cond}) * {self.Q})'

    @property
    def free_variables(self) -> t.Set[Symbol]:
        return (
            self.cond.free_variables
            | self.P.free_variables
            | self.Q.free_variables
        )

    def neg(self) -> Algebraic:
        return SMFN.make(self.cond, -self.P, -self.Q)

    def add(self, other: Algebraic) -> Algebraic:
        if isinstance(other, (Polynomial, SMF0)):
            return other + self

        if isinstance(other, SMFN):
            if self.cond == other.cond:
                return SMFN.make(self.cond, self.P + other.P, self.Q + other.Q)
            else:
                return SMFN.make(self.cond, self.P + other, self.Q + other)

        raise AlgebraError(f'Can\'t add types {type(self)} and {type(other)}.')

    def mul(self, other: Algebraic) -> Algebraic:
        if isinstance(other, (Polynomial, SMF0)):
            return other * self

        if isinstance(other, SMFN):
            if self.cond == other.cond:
                return SMFN.make(self.cond, self.P * other.P, self.Q * other.Q)
            else:
                return SMFN.make(self.cond, self.P * other, self.Q * other)

        raise AlgebraError(
            f'Can\'t multiply types {type(self)} and {type(other)}.'
        )

    def div(self, other: Algebraic) -> Algebraic:
        if isinstance(other, (Polynomial, SMF0)):
            return SMFN.make(self.cond, self.P / other, self.Q / other)

        if isinstance(other, SMFN):
            if self.cond == other.cond:
                return SMFN.make(self.cond, self.P / other.P, self.Q / other.Q)
            else:
                return SMFN.make(self.cond, self.P / other, self.Q / other)

        raise AlgebraError(f'Can\'t add types {type(self)} and {type(other)}.')

    @debug.indent()  # type: ignore
    def _eval(  # type: ignore
        self, zeros: t.Set[SympyExpr], nonzeros: t.Set[SympyExpr]
    ) -> 'Algebraic':
        """
        Evaluate in the given zero terms and nonzero terms. First the condional
        part of the SMF is evaluated. If it is equal to zero, only Q has to be
        evaluated. If it is another constant, only P is evaluated. Otherwise, P
        must be equal to zero, and Q must be equal to zero in the roots of cond.

        If any of the roots of cond are also included in the nonzero set, Q is not
        evaluated in that root.
        """

        debug.debug(
            'Evaluating SMFN {} in zeros {}, nonzeros {}',
            self,
            zeros,
            nonzeros,
        )

        cond = t.cast(Polynomial, self.cond.eval(zeros, nonzeros))
        roots = cond.factors

        if cond.is_zero or zeros.intersection(roots):
            ret = self.Q.eval(zeros, nonzeros)
            debug.debug('Result: {}', ret)
            return ret

        P = self.P.eval(zeros, nonzeros | set(roots))

        if cond.is_constant or nonzeros.issuperset(roots):
            debug.debug('Result: {}', P)
            return P

        if not P.is_zero:
            ret = SMFN.make(cond, P, self.Q.eval(zeros, nonzeros))
            debug.debug('Result: {}', ret)
            return ret

        for root in roots:
            if root in nonzeros:
                continue

            ret = self.Q.eval(zeros | {root}, nonzeros)

            if not ret.is_zero:
                break
        else:
            ret = Polynomial(0)

        debug.debug('Result: {}', ret)
        return ret
