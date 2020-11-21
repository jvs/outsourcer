from collections import defaultdict
from contextlib import contextmanager
import io


__version__ = '0.0.1'

__all__ = ['Builder', 'Src', 'Str']


class Builder:
    def __init__(self):
        self._statements = []
        self._num_blocks = 1
        self._max_num_blocks = 19
        self._names = defaultdict(int)

    def __call__(self, statement):
        self.append(statement)

    def write_source(self):
        writer = _Writer()
        for statement in self._statements:
            writer.write_line(statement)
        return writer.getvalue()

    def append(self, statement):
        self._statements.append(statement)

    def extend(self, statements):
        self._statements.extend(statements)

    def has_available_blocks(self, num_blocks):
        return self._num_blocks + num_blocks <= self._max_num_blocks

    def var(self, base_name, initializer=None):
        self._names[base_name] += 1
        result = Src(f'{base_name}{self._names[base_name]}')
        if initializer is not None:
            self.append(result << initializer)
        return result

    def WHILE(self, condition):
        return self._control_block('while', condition)

    def IF(self, condition):
        return self._control_block('if', condition)

    def IF_NOT(self, condition):
        return self.IF(Src('not', condition))

    @contextmanager
    def ELSE(self):
        with self._new_block() as else_body:
            yield
        self.extend([
            'else:',
            _Block(else_body),
        ])

    @contextmanager
    def breakable(self):
        with self.loop():
            yield
            self.append('break')

    def loop(self):
        return self.WHILE(True)

    @contextmanager
    def _control_block(self, keyword, condition):
        with self._new_block() as body:
            yield
        self.extend([
            Src(keyword, ' ', condition, ':'),
            _Block(body),
        ])

    @contextmanager
    def _new_block(self):
        with self._sandbox() as new_buffer:
            self._num_blocks += 1
            try:
                yield new_buffer
            finally:
                self._num_blocks -= 1

    @contextmanager
    def _sandbox(self):
        prev = self._statements
        self._statements = []
        try:
            yield self._statements
        finally:
            self._statements = prev


class Src:
    def __init__(self, *parts):
        parts = [_conv(x) for x in parts]
        self._parts = parts

    def _write(self, writer):
        for part in self._parts:
            writer.write(part)

    def __lshift__(self, other):
        return Src(self, ' = ', other)

    def __rshift__(self, other):
        return Src(self, ' : ', other)

    def __call__(self, *args, **kwargs):
        parts = [self, '(']

        for arg in args:
            parts.extend([arg, ', '])

        for key, value in kwargs.items():
            parts.extend([key, '=', value, ', '])

        # Remove a trailing comma.
        if args or kwargs:
            parts.pop()

        parts.append(')')
        return Src(*parts)

    def __getitem__(self, key):
        return Src(self, '[', key, ']')

    def __getattr__(self, name):
        return Src(self, '.', key)

    def __eq__(self, other):
        return _binop(self, '==', other)

    def __ne__(self, other):
        return _binop(self, '!=', other)

    def __add__(self, other):
        return _binop(self, '+', other)

    def __gt__(self, other):
        return _binop(self, '>', other)

    def __ge__(self, other):
        return _binop(self, '>=', other)

    def __lt__(self, other):
        return _binop(self, '<', other)

    def __le__(self, other):
        return _binop(self, '<=', other)


class _Block:
    def __init__(self, statements):
        if not isinstance(statements, (list, tuple)):
            raise TypeError('Expected list of tuple')
        self._statements = statements or ['pass']

    def _write(self, writer):
        with writer.indented():
            for statement in self._statements:
                writer.write_line(statement)


def Str(string_value):
    return Src(repr(string_value))


def _binop(a, op, b):
    return Src('(', a, f' {op} ', b, ')')


def _conv(x):
    if isinstance(x, (list, tuple)):
        return _seq(x, )
    elif isinstance(x, dict):
        return _dict(x)
    else:
        return x


def _dict(x):
    parts = ['{']
    for k, v in x.items():
        parts.extend([k, ':', v, ', '])

    # Remove trailing comma if it's non-empty.
    if len(x) > 1:
        parts.pop()

    parts.append('}')
    return Src(*parts)


def _seq(elements):
    is_list = isinstance(elements, list)

    parts = ['[' if is_list else '(']
    for element in elements:
        parts.extend([element, ', '])

    # Remove trailing comma if it's not necessary.
    if is_list or len(elements) > 1:
        parts.pop()

    parts.append(']' if is_list else ')')
    return Src(*parts)


class _Writer:
    def __init__(self):
        self._indent = 0
        self._out = io.StringIO()

    def getvalue(self):
        return self._out.getvalue()

    @contextmanager
    def indented(self):
        was = self._indent
        self._indent += 1
        try:
            yield
        finally:
            self._indent = was

    def write_line(self, obj):
        self.write('    ' * self._indent)
        self.write(obj)
        self.write('\n')

    def write(self, obj):
        if hasattr(obj, '_write'):
            obj._write(self)
        else:
            self._out.write(str(obj))
