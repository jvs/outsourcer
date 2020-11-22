from outsourcer import Code, CodeBuilder


def test_simple_program():
    foo = Code('foo')
    bar = Code('bar')
    PRINT = Code('print')

    b = CodeBuilder()
    with b.IF(foo + 1 < bar):
        b(PRINT('ok'))

    result = b.write_source().strip()
    assert result == "if ((foo + 1) < bar):\n    print('ok')"


def _render(expr):
    b = CodeBuilder()
    b(expr)
    return b.write_source().strip()


def test_simple_literals():
    assert _render([]) == '[]'
    assert _render(()) == '()'
    assert _render(['ok']) == "['ok']"
    assert _render(('ok',)) == "('ok',)"
    assert _render([1, 2, 3]) == '[1, 2, 3]'
    assert _render((1, 2, 3)) == '(1, 2, 3)'


def test_collections_with_expressions():
    foo = Code('foo')
    bar = Code('bar')
    assert _render([foo + 1, bar('ok')]) == "[(foo + 1), bar('ok')]"
    assert _render([foo({'key': bar / 2})]) == "[foo({'key': (bar / 2)})]"


def test_function_calls():
    foo = Code('foo')
    bar = Code('bar')
    assert _render(foo(bar, 'baz')) == "foo(bar, 'baz')"
