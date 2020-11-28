from outsourcer import Code, CodeBuilder


def test_simple_program():
    foo, bar, PRINT = Code('foo'), Code('bar'), Code('print')
    b = CodeBuilder()

    with b.IF(foo + 1 < bar):
        b += PRINT('ok')

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
    foo, bar = Code('foo'), Code('bar')
    assert _render([foo + 1, bar('ok')]) == "[(foo + 1), bar('ok')]"
    assert _render([foo({'key': bar / 2})]) == "[foo({'key': (bar / 2)})]"


def test_function_calls():
    foo, bar = Code('foo'), Code('bar')
    assert _render(foo(bar, 'baz')) == "foo(bar, 'baz')"
    assert _render(foo(bar(foo))) == 'foo(bar(foo))'
    assert _render(foo(True, msg='hi', count=1)) == "foo(True, msg='hi', count=1)"


def test_simple_operators():
    foo, bar = Code('foo'), Code('bar')

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
    foo, bar, PRINT = Code('foo'), Code('bar'), Code('print')
    b = CodeBuilder()

    b += bar << Code('baz()')
    with b.FOR(foo, in_=bar):
        b += PRINT(foo)

    result = b.write_source().strip()
    assert result == 'bar = baz()\nfor foo in bar:\n    print(foo)'


def test_extend_method():
    fiz, buz = Code('fiz'), Code('buz')

    b = CodeBuilder()
    b.extend([
        fiz << 'ok',
        buz << fiz.upper(),
    ])
    result = b.write_source().strip()
    assert result == "fiz = 'ok'\nbuz = fiz.upper()"


def test_tuple_assignment():
    zim, zam, zoom = Code('zim'), Code('zam'), Code('zoom')
    assign = (zim, zam) << zoom()
    assert _render(assign) == '(zim, zam) = zoom()'


def test_slice_expression():
    foo, bar = Code('foo'), Code('bar')
    assert _render(foo[bar : 10]) == 'foo[slice(bar, 10, None)]'
    assert _render(bar[11 : foo]) == 'bar[slice(11, foo, None)]'
