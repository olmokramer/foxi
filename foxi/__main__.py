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

import sys
import types
import typing as t

import foxi
from foxi import debug


def _prove(expr: str) -> t.Optional[bool]:
    try:
        parsed = foxi.parse(expr)
    except (foxi.AlgebraError, foxi.ParseError) as e:
        debug.error('{}', e)
        return None

    if isinstance(parsed, foxi.Algebraic):
        debug.info('{}', parsed)
        return None

    eval = parsed.eval()

    if eval.is_zero:
        debug.info('Proven to be TRUE: {}', expr)
        return True
    else:
        debug.info('Proven to be FALSE: {}', expr)
        debug.info('Resulting expression: {} = 0', eval)
        return False


def _test_expr(expr: str) -> bool:
    expect_map = {'TRUE': True, 'FALSE': False, 'ERROR': None}

    expect, _, expr = expr.partition(' ')
    assert expect in expect_map

    result = _prove(expr)

    if result != expect_map[expect]:
        debug.test('ERROR Expression "{}" expected to be {}', expr, expect)
        return False
    else:
        return True


def _loop_files(files: t.Sequence[str], test: bool = False) -> int:
    exprs = [
        l
        for f in files
        for l in map(lambda l: l.strip(), open(f).readlines())
        if l and l[0] != '#'
    ]

    if test:
        total = len(exprs)
        success = 0

        for i, expr in enumerate(exprs, 1):
            result = int(_test_expr(expr))
            success += result
            debug.test('{}/{}\t{}  {}', i, total, 'succ' if result else 'fail', expr)

        debug.test('{} / {} tests succeeded!'.format(success, total))

        return total - success
    else:
        for expr in exprs:
            _prove(expr)

        return 0


def _loop_input() -> None:
    prompt = 'Expression (^D to quit): ' if sys.stdin.isatty() else ''

    while True:
        try:
            expr = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if expr:
            _prove(expr)

        print()


def main() -> None:
    import argparse

    readline: t.Optional[types.ModuleType] = None
    try:
        import readline  # type: ignore
    except ModuleNotFoundError:
        pass

    argparser = argparse.ArgumentParser(prog='foxi')
    argparser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        default=False,
        help='output intermediary steps, generates a lot of extra output',
    )
    argparser.add_argument(
        '-H',
        '--histfile',
        type=str,
        default='./.foxi-history',
        help=(
            'file to write expression input history to (default:'
            ' ./.foxi-history)'
        ),
    )
    argparser.add_argument(
        '-t',
        '--test',
        action='store_true',
        default=False,
        help=(
            'each line of the input files is expected to start with the string'
            ' TRUE, FALSE, or ERROR, indicating the expected outcome of the'
            ' expression'
        ),
    )
    argparser.add_argument(
        'files',
        metavar='FILE',
        type=str,
        nargs='*',
        help=(
            'file to read expressions from, one per line. empty lines and '
            'lines starting with a # are ignored'
        ),
    )

    args = argparser.parse_args()

    if args.debug:
        debug.set_level(debug.DebugLevel.DEBUG)
    elif args.test:
        debug.set_level(debug.DebugLevel.TEST)
    else:
        debug.set_level(debug.DebugLevel.INFO)

    if readline is not None:
        readline.read_init_file()
        try:
            readline.read_history_file(args.histfile)
        except FileNotFoundError:
            pass

    if args.files:
        ret = _loop_files(args.files, args.test)
    else:
        _loop_input()
        ret = 0

    if readline is not None:
        readline.write_history_file(args.histfile)

    sys.exit(ret)


if __name__ == '__main__':
    main()
