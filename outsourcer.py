from collections import defaultdict
from contextlib import contextmanager
import io
import textwrap
import types


__version__ = '0.0.1'

__all__ = ['CodeBuilder', 'Code', 'Val', 'Yield', 'sym']

OMITTED = object()


class CodeBuilder:
    def __init__(self, max_num_blocks=20):
        self.state = {}
        self._root = []
        self._statements = self._root
        self._num_blocks = 1
        self._max_num_blocks = max_num_blocks
        self._names = defaultdict(int)

    def current_num_blocks(self):
        return self._num_blocks

    def __iadd__(self, statement):
        return self.append(statement)

    def source_code(self):
        writer = _Writer()
        for statement in self._statements:
            writer.write_line(statement)
        return writer.getvalue()

    def compile(self, module_name='code', docstring=None, source_var=None):
        source_code = self.source_code()
        code_object = compile(source_code, f'<{module_name}>', 'exec', optimize=2)
        module = types.ModuleType(module_name, doc=docstring)
        exec(code_object, module.__dict__)

        # Optionally assign the source code to a variable in the module.
        if source_var is not None:
            setattr(module, source_var, source_code)

        return module

    def append(self, statement):
        self._statements.append(statement)
        return self

    def extend(self, statements):
        self._statements.extend(statements)
        return self

    def append_global(self, statement):
        self._root.append(statement)

    def has_available_blocks(self, num_blocks=1):
        return self._num_blocks + num_blocks <= self._max_num_blocks

    def var(self, base_name, initializer=OMITTED):
        result = self._reserve_name(base_name)
        if initializer is not OMITTED:
            self.append(result << initializer)
        return result

    def _reserve_name(self, base_name):
        self._names[base_name] += 1
        return Code(f'{base_name}{self._names[base_name]}')

    def add_comment(self, content):
        for line in content.split('\n'):
            self.append(Code('# ', line))

    def add_docstring(self, content):
        safe = content.replace('\\', '\\\\') .replace('"""', '\\"\\"\\"')
        indent = '    ' * (self._num_blocks - 1)
        body = textwrap.indent(safe, indent)
        self.append(Code(f'"""\n{body}\n{indent}"""'))

    def add_newline(self):
        self.append('')

    @contextmanager
    def CLASS(self, name, superclass=None):
        with self._new_block() as block:
            yield
        extra = f'({superclass})' if superclass else ''
        self.append(Code('class ', name, extra, ':'))
        self.append(_Block(block))
        self.add_newline()

    @contextmanager
    def DEF(self, name, params):
        with self._new_block() as block:
            yield
        self.append(Code('def ', name, '(', ', '.join(params), '):'))
        self.append(_Block(block))
        self.add_newline()

    def WHILE(self, condition):
        return self._control_block('while', condition)

    def IF(self, condition):
        return self._control_block('if', condition)

    def IF_NOT(self, condition):
        return self.IF(Code('not (', Val(condition), ')'))

    def ELIF(self, condition):
        return self._control_block('elif', condition)

    def ELIF_NOT(self, condition):
        return self.ELIF(Code('not (', Val(condition), ')'))

    def ELSE(self):
        return self._control_block('else')

    def WITH(self, condition, as_=OMITTED):
        if as_ is not OMITTED:
            condition = Code(Val(condition), ' as ', Code(as_))
        return self._control_block('with', condition)

    def TRY(self):
        return self._control_block('try')

    def EXCEPT(self, condition=OMITTED, as_=OMITTED):
        if condition is OMITTED and as_ is not OMITTED:
            raise TypeError('Missing exception specifier')
        if as_ is not OMITTED:
            condition = Code(Val(condition), ' as ', Code(as_))
        return self._control_block('except', condition)

    def FINALLY(self):
        return self._control_block('finally')

    def FOR(self, item, in_):
        return self._control_block('for', Code(Val(item), ' in ', Val(in_)))

    def RETURN(self, obj=OMITTED):
        return self._control_line('return', obj)

    def YIELD(self, obj=OMITTED):
        return self._control_line('yield', obj)

    def RAISE(self, obj=OMITTED):
        return self._control_line('raise', obj)

    def ASSERT(self, obj):
        return self._control_line('assert', obj)

    def _control_line(self, keyword, obj=OMITTED):
        return self.append(Code(keyword)
            if obj is OMITTED
            else Code(keyword, ' ', Val(obj)))

    @contextmanager
    def global_section(self):
        saved = self._statements, self._num_blocks
        self._statements = self._root
        self._num_blocks = 1
        try:
            yield
        finally:
            self._statements, self._num_blocks = saved

    @contextmanager
    def _control_block(self, keyword, condition=OMITTED):
        with self._new_block() as block:
            yield
        extra = () if condition is OMITTED else (' ', Val(condition))
        self.append(Code(keyword, *extra, ':'))
        self.append(_Block(block))

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
        saved = self._statements
        self._statements = []
        try:
            yield self._statements
        finally:
            self._statements = saved


class Code:
    def __init__(self, *parts):
        self._parts = parts

    def _write(self, writer):
        for part in self._parts:
            writer.write(part)

    def __repr__(self):
        writer = _Writer()
        self._write(writer)
        return writer.getvalue()

    def __lshift__(self, other):
        return Code(self, ' = ', Val(other))

    def __rlshift__(self, other):
        return Code(Val(other), ' = ', self)

    def __call__(self, *args, **kwargs):
        parts = [self, '(']

        for arg in args:
            parts.extend([Val(arg), ', '])

        for key, value in kwargs.items():
            parts.extend([key, '=', Val(value), ', '])

        # Remove a trailing comma.
        if args or kwargs:
            parts.pop()

        parts.append(')')
        return Code(*parts)

    def __getitem__(self, key):
        return Code(self, '[', Val(key), ']')

    def __getattr__(self, name):
        return Code(self, '.', name)

    def __neg__(self):
        return Code('(-', self, ')')

    def __pos__(self):
        return Code('(+', self, ')')

    def __invert__(self):
        return Code('(~', self, ')')

    def __abs__(self):
        return Code('abs(', self, ')')

    def __eq__(self, other):
        return _binop(self, '==', other)

    def __ne__(self, other):
        return _binop(self, '!=', other)

    def __add__(self, other):
        return _binop(self, '+', other)

    def __radd__(self, other):
        return _binop(other, '+', self)

    def __sub__(self, other):
        return _binop(self, '-', other)

    def __rsub__(self, other):
        return _binop(other, '-', self)

    def __mul__(self, other):
        return _binop(self, '*', other)

    def __rmul__(self, other):
        return _binop(other, '*', self)

    def __matmul__(self, other):
        return _binop(self, '@', other)

    def __rmatmul__(self, other):
        return _binop(other, '@', self)

    def __truediv__(self, other):
        return _binop(self, '/', other)

    def __rtruediv__(self, other):
        return _binop(other, '/', self)

    def __floordiv__(self, other):
        return _binop(self, '//', other)

    def __rfloordiv__(self, other):
        return _binop(other, '//', self)

    def __mod__(self, other):
        return _binop(self, '%', other)

    def __rmod__(self, other):
        return _binop(other, '%', self)

    def __pow__(self, other):
        return _binop(self, '**', other)

    def __rpow__(self, other):
        return _binop(other, '**', self)

    def __and__(self, other):
        return _binop(self, '&', other)

    def __rand__(self, other):
        return _binop(other, '&', self)

    def __or__(self, other):
        return _binop(self, '|', other)

    def __ror__(self, other):
        return _binop(other, '|', self)

    def __xor__(self, other):
        return _binop(self, '^', other)

    def __rxor__(self, other):
        return _binop(other, '^', self)

    def __gt__(self, other):
        return _binop(self, '>', other)

    def __ge__(self, other):
        return _binop(self, '>=', other)

    def __lt__(self, other):
        return _binop(self, '<', other)

    def __le__(self, other):
        return _binop(self, '<=', other)

    def __rshift__(self, other):
        return _binop(self, '>>', other)

    def __rrshift__(self, other):
        return _binop(other, '>>', self)


def Val(obj):
    return obj if isinstance(obj, Code) else Code(repr(obj))


def Yield(obj):
    return Code('(yield ', Val(obj), ')')


class _Block:
    def __init__(self, statements):
        self._statements = statements or ['pass']

    def _write_block(self, writer):
        with writer.indented():
            for statement in self._statements:
                writer.write_line(statement)


def _binop(a, op, b):
    assert isinstance(op, str)
    return Code('(', Val(a), f' {op} ', Val(b), ')')


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
        if isinstance(obj, _Block):
            obj._write_block(self)
        elif isinstance(obj, str) and obj == '':
            self.write('\n')
        else:
            self.write('    ' * self._indent)
            self.write(obj)
            self.write('\n')

    def write(self, obj):
        if hasattr(obj, '_write'):
            obj._write(self)
        else:
            self._out.write(str(obj))


class _SymbolFactory:
    def __call__(self, *a, **k):
        return Code(*a, **k)

    def __getattr__(self, name):
        return Code(name)


sym = _SymbolFactory()
