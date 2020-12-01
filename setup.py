import os
import re
import setuptools


def long_description():
    with open('README.md') as f:
        return f.read()


def version():
    with open('outsourcer.py') as f:
        regex = re.compile('\\n__version__\\s*=\\s*[\'"]+([\\d\\.]+)[\'"]\n')
        return regex.search(f.read()).group(1)


setuptools.setup(
    name='outsourcer',
    version=version(),
    author='jvs',
    author_email='vonseg@protonmail.com',
    url='https://github.com/jvs/outsourcer',
    description='Build and test your Python examples',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    data_files=[('', ['README.md', 'requirements-dev.txt'])],
    python_requires='>=3.6',
    install_requires=[],
    py_modules=['outsourcer'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    platforms='any',
    license='MIT License',
    keywords=['code-generation'],
)
