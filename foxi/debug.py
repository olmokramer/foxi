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

import contextlib
import enum
import typing as t


class DebugLevel(enum.IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    TEST = 4
    NONE = 5


_debug_level = DebugLevel.WARNING
_indent_level = 0


def set_level(level: DebugLevel) -> None:
    global _debug_level
    _debug_level = level


class indent(contextlib.ContextDecorator):
    def __enter__(self) -> None:
        global _indent_level
        _indent_level += 1

    def __exit__(self, *exc: Exception) -> None:
        global _indent_level
        _indent_level -= 1


def printf(level: DebugLevel, fmt: str, *args: t.Any) -> None:
    if level < _debug_level:
        return

    print(':   ' * _indent_level, end='')
    print(fmt.format(*args))


def debug(fmt: str, *args: t.Any) -> None:
    printf(DebugLevel.DEBUG, fmt, *args)


def info(fmt: str, *args: t.Any) -> None:
    printf(DebugLevel.INFO, fmt, *args)


def warning(fmt: str, *args: t.Any) -> None:
    printf(DebugLevel.WARNING, 'WARNING ' + fmt, *args)


def error(fmt: str, *args: t.Any) -> None:
    printf(DebugLevel.ERROR, 'ERROR ' + fmt, *args)


def test(fmt: str, *args: t.Any) -> None:
    printf(DebugLevel.TEST, fmt, *args)
