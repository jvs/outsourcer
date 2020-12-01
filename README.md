# Outsourcer

A micro library for generating Python source code.


## Installation

```console
pip install outsourcer
```

Outsourcer requires Python 3.6 or later.


## Why does this exist?

Sometimes you have to generate some Python code, and sometimes it's a bit too
complicated for using string templates. This is a small library you can use in
those cases.


## Example

### Hello, World

```python
>>> from outsourcer import sym
>>> sym.print('hello, world')
print('hello, world')
```

This example uses `sym` to create a code fragment.

### Control Flow

Here's a longer example:

```python
>>> from outsourcer import CodeBuilder, sym
>>> b = CodeBuilder()
>>> item = sym.item
>>> with b.FOR(item, in_=sym.some_collection):
...     with b.IF(item % 2 == 0):
...         b += sym.print('even')
...     with b.ELSE():
...         b += sym.skipped.append(item)
...
>>> print(b.source_code())
for item in some_collection:
    if ((item % 2) == 0):
        print('even')
    else:
        skipped.append(item)
```
