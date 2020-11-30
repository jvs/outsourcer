from contextlib import ExitStack
from textwrap import dedent
import types

from outsourcer import Code, CodeBuilder, Yield, sym

import pytest


def test_simple_program():
    b = CodeBuilder()

    with b.IF(sym.foo + 1 < sym.bar):
        b += sym.print('ok')

    result = b.write_source().strip()
    assert result == "if ((foo + 1) < bar):\n    print('ok')"


def _render(expr):
    b = CodeBuilder()
    b += expr
    return b.write_source().strip()


def test_simple_literals():
    assert _render([]) == '[]'
    assert _render(()) == '()'
    assert _render(['ok']) == "['ok']"
    assert _render(('ok',)) == "('ok',)"
    assert _render([1, 2, 3]) == '[1, 2, 3]'
    assert _render((1, 2, 3)) == '(1, 2, 3)'


def test_collections_with_expressions():
    assert _render([sym.foo + 1, sym.bar('ok')]) == "[(foo + 1), bar('ok')]"
    assert _render([sym.foo({'key': sym.bar / 2})]) == "[foo({'key': (bar / 2)})]"


def test_function_calls():
    foo, bar = sym.foo, sym.bar
    assert _render(foo(bar, 'baz')) == "foo(bar, 'baz')"
    assert _render(foo(bar(foo))) == 'foo(bar(foo))'
    assert _render(foo(True, msg='hi', count=1)) == "foo(True, msg='hi', count=1)"


def test_simple_operators():
    foo, bar = sym.foo, sym.bar

    assert _render(foo + bar) == '(foo + bar)'
    assert _render(foo + 'bar') == "(foo + 'bar')"
    assert _render('foo' + bar) == "('foo' + bar)"

    assert _render(foo - bar) == '(foo - bar)'
    assert _render(foo - 10) == '(foo - 10)'
    assert _render(20 - bar) == '(20 - bar)'

    assert _render(foo * 30) == '(foo * 30)'
    assert _render(40 * foo) == '(40 * foo)'

    assert _render(bar @ 50) == '(bar @ 50)'
    assert _render(60 @ bar) == '(60 @ bar)'

    assert _render(foo / 70) == '(foo / 70)'
    assert _render(80 / foo) == '(80 / foo)'

    assert _render(bar // 90) == '(bar // 90)'
    assert _render(11 // bar) == '(11 // bar)'

    assert _render(foo & 12) == '(foo & 12)'
    assert _render(13 & foo) == '(13 & foo)'

    assert _render(bar | 14) == '(bar | 14)'
    assert _render(15 | bar) == '(15 | bar)'

    assert _render(foo ^ 16) == '(foo ^ 16)'
    assert _render(17 ^ foo) == '(17 ^ foo)'

    assert _render(foo > 18) == '(foo > 18)'
    assert _render(19 > foo) == '(foo < 19)'

    assert _render(bar < 20) == '(bar < 20)'
    assert _render(21 < bar) == '(bar > 21)'

    assert _render(foo >= 22) == '(foo >= 22)'
    assert _render(23 >= foo) == '(foo <= 23)'

    assert _render(bar <= 24) == '(bar <= 24)'
    assert _render(25 <= bar) == '(bar >= 25)'

    assert _render(foo == 26) == '(foo == 26)'
    assert _render(27 == foo) == '(foo == 27)'

    assert _render(bar != 28) == '(bar != 28)'
    assert _render(29 != bar) == '(bar != 29)'

    assert _render(foo % 10) == '(foo % 10)'
    assert _render(11 % foo) == '(11 % foo)'

    assert _render(bar ** 12) == '(bar ** 12)'
    assert _render(13 ** bar) == '(13 ** bar)'

    assert _render(foo >> 14) == '(foo >> 14)'
    assert _render(15 >> bar) == '(15 >> bar)'

    assert _render(foo.baz) == 'foo.baz'
    assert _render(foo[30]) == 'foo[30]'
    assert _render(foo.baz[31].fiz[32]) == 'foo.baz[31].fiz[32]'

    assert _render(-bar) == '(-bar)'
    assert _render(+bar) == '(+bar)'
    assert _render(~bar) == '(~bar)'

    assert _render(abs(foo)) == 'abs(foo)'


def test_for_statement():
    foo, bar = Code('foo'), Code('bar')
    b = CodeBuilder()

    b += bar << sym.baz()
    with b.FOR(foo, in_=bar):
        b += sym.print(foo)

    result = b.write_source().strip()
    assert result == 'bar = baz()\nfor foo in bar:\n    print(foo)'


def test_extend_method():
    fiz, buz = sym('fiz'), sym('buz')

    b = CodeBuilder()
    b.extend([
        fiz << 'ok',
        buz << fiz.upper(),
    ])
    result = b.write_source().strip()
    assert result == "fiz = 'ok'\nbuz = fiz.upper()"


def test_unpacking_assignment():
    zim, zam, zoom = Code('zim'), Code('zam'), Code('zoom')
    assert _render((zim, zam) << zoom()) == '(zim, zam) = zoom()'
    assert _render([zim, zam] << zoom[0]) == '[zim, zam] = zoom[0]'


def test_slice_expression():
    foo, bar = sym.foo, sym.bar
    assert _render(foo[bar : 10]) == 'foo[slice(bar, 10, None)]'
    assert _render(bar[11 : foo]) == 'bar[slice(11, foo, None)]'
    assert _render(foo[1:9]) == 'foo[slice(1, 9, None)]'


def test_add_global_method():
    fiz, baz, buz = Code('fiz'), Code('baz'), Code('buz')
    b = CodeBuilder()
    with b.DEF('foo', ['bar', 'bam']):
        bar, bam = Code('bar'), Code('bam')
        b += fiz << bar + 1
        b.append_global(baz << 100)
        b.RETURN(bam < baz - fiz)
        b.append_global(Code('assert baz > 50'))
    assert b.write_source().strip() == dedent('''
        baz = 100
        assert baz > 50
        def foo(bar, bam):
            fiz = (bar + 1)
            return (bam < (baz - fiz))
    ''').strip()


def test_has_available_blocks():
    b = CodeBuilder()
    with ExitStack() as stack:
        for i in range(1, 20):
            assert b.current_num_blocks() == i
            assert b.has_available_blocks()
            stack.enter_context(b.IF(True))
        assert not b.has_available_blocks()

    assert b.current_num_blocks() == 1
    assert b.has_available_blocks()

    # Make sure that we can compile a source with 20 blocks.
    source = b.write_source()
    name = 'test_has_available_blocks'
    code = compile(source, f'<{name}>', 'exec', optimize=2)
    module = types.ModuleType(name)
    exec(code, module.__dict__)


def test_var_method():
    b = CodeBuilder()
    b.var('foo', 1)
    b.var('foo', 2)
    foo = b.var('foo')
    b += foo << 3
    bar = b.var('bar')
    assert b.write_source().strip() == dedent('''
        foo1 = 1
        foo2 = 2
        foo3 = 3
    ''').strip()


def test_comment_methods():
    b = CodeBuilder()
    b.add_docstring('This is a docstring.\nTry using """triple quotes"""...')
    b.add_newline()
    with b.CLASS('Foo'):
        b.add_docstring('This is another docstring.')
        b.add_newline()
        with b.DEF('bar', ['self', 'baz', 'fiz']):
            fiz, baz, buz = Code('fiz'), Code('baz'), Code('buz')
            b.add_docstring('One more docstring.')
            b += Code('buz') << 123
            b.add_comment('This is a normal comment.\nThis is a second line.')
            b.RETURN(fiz + baz + buz)

    assert b.write_source().strip() == dedent(r'''
        """
        This is a docstring.
        Try using \"\"\"triple quotes\"\"\"...
        """

        class Foo:
            """
            This is another docstring.
            """

            def bar(self, baz, fiz):
                """
                One more docstring.
                """
                buz = 123
                # This is a normal comment.
                # This is a second line.
                return ((fiz + baz) + buz)
    ''').strip()


def test_control_flow_statements():
    zim, zam, zom = Code('zim'), Code('zam'), Code('zom')

    b = CodeBuilder()
    with b.WHILE(True): pass
    assert b.write_source().strip() == dedent('''
        while True:
            pass
    ''').strip()


    b = CodeBuilder()
    with b.WITH(zim(True), as_='fiz'): pass
    assert b.write_source().strip() == dedent('''
        with zim(True) as fiz:
            pass
    ''').strip()

    b = CodeBuilder()
    with b.WHILE(zim() > 0):
        with b.IF(zam(1, 2, 3) == 'ok'):
            b.ASSERT(Code('something') == Code('value'))
            b += zom('hi')
        with b.ELIF(zam(4, 5, 6) == 'fine'):
            b += zom('well')
        with b.ELSE():
            b += zom('bye')

    assert b.write_source().strip() == dedent('''
        while (zim() > 0):
            if (zam(1, 2, 3) == 'ok'):
                assert (something == value)
                zom('hi')
            elif (zam(4, 5, 6) == 'fine'):
                zom('well')
            else:
                zom('bye')
    ''').strip()

    b = CodeBuilder()
    with b.FOR(zim, in_=[1, 2, 3]):
        with b.IF_NOT(zam('ok')):
            with b.IF(zom('so')):
                b.YIELD('waiting')
        with b.ELIF_NOT(zam('fine')):
            with b.WHILE(zom('continue')):
                b.YIELD('running')

    assert b.write_source().strip() == dedent('''
        for zim in [1, 2, 3]:
            if not (zam('ok')):
                if zom('so'):
                    yield 'waiting'
            elif not (zam('fine')):
                while zom('continue'):
                    yield 'running'
    ''').strip()

    b = CodeBuilder()
    Foo, Bar = Code('Foo'), Code('Bar')
    with b.TRY():
        b.RAISE(Foo('fail'))
    with b.EXCEPT((Foo, Bar), as_='exc'):
        b += zim(1, 2, 3)
    with b.FINALLY():
        b.RETURN(zam(True))

    assert b.write_source().strip() == dedent('''
        try:
            raise Foo('fail')
        except (Foo, Bar) as exc:
            zim(1, 2, 3)
        finally:
            return zam(True)
    ''').strip()


def test_except_without_type_but_with_name():
    b = CodeBuilder()
    with pytest.raises(TypeError):
        b.EXCEPT(as_='foo')


def test_global_section():
    b = CodeBuilder()
    with b.DEF('foo', ['bar', 'baz']):
        with b.IF(Code('fiz')):
            with b.global_section():
                b += Code('bam') << 100
            b += Code('zim')(1, 2, 3)
        with b.ELSE():
            with b.global_section():
                b += Code('buz') << 200
            b += Code('zam')(4, 5, 6)

    assert b.write_source().strip() == dedent('''
        bam = 100
        buz = 200
        def foo(bar, baz):
            if fiz:
                zim(1, 2, 3)
            else:
                zam(4, 5, 6)
    ''').strip()


def test_yield_expression():
    expr = sym.foo << Yield(sym.bar(1, 2, 3))
    assert _render(expr) == 'foo = (yield bar(1, 2, 3))'
