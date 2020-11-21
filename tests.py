from outsourcer import Builder, Src, Str


def test_simple_program():
    foo = Src('foo')
    bar = Src('bar')
    PRINT = Src('print')

    b = Builder()
    with b.IF(foo + 1 < bar):
        b(PRINT(Str('ok')))

    result = b.write_source().strip()
    assert result == "if ((foo + 1) < bar):\n    print('ok')"
