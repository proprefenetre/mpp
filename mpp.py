#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
from pathlib import Path
import re
import sys


teststr = """<!--preamble
    (define Lorem Morel)
    (delimiters { })
    -->
    Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita
kasd gubergren, no sea (color red takimata sanctus) est Lorem ipsum dolor sit
amet. (it because better are your breasts than wine) Lorem ipsum dolor sit amet,
consetetur {it sadipscing elitr}, sed diam nonumy eirmod tempor invidunt ut labore et
dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est
Lorem ipsum dolor sit amet. """


class Expression:

    __metaclass__ = abc.ABCMeta

    def __init__(self, key=None, delimiters=None):
        if key:
            self.key = key
        if delimiters:
            self.start, self.end = delimiters.split()

    @property
    @abc.abstractmethod
    def key(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def start(self):
        raise NotImplementedError

    @abc.abstractproperty
    def end(self):
        raise NotImplementedError

    def expr(self):
        """ return a compiled regex object that contains the groups 'head' and
            'body'
        """
        exprs = [re.escape(self.start),
                 rf"(?P<head>{self.key})",
                 r"\s",
                 rf"(?P<body>.*?)",
                 re.escape(self.end)]
        
        return re.compile(''.join(exprs), re.M | re.S)

    @abc.abstractmethod
    def sub(self):
        """ returns the replacement for body """    
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}({self.key}, delimiters='{self.start} {self.end}')"


class ItalicsExpr(Expression):
    
    key = 'it'
    start = '('
    end = ')'

    def sub(self, m):
        line = m.group("body")
        return f"\\textit{{{line}}}"


class ColorExpr(Expression):

    key = 'color'
    start = '('
    end = ')'

    def sub(self, m):
        col, line = m.group("body").split(maxsplit=1)
        return f"\\textcolor{{{col}}}{{{line}}}"


class Settings(Expression):
    
    key = 'preamble'
    start = '<!--'
    end = '-->'
    
    def sub(self):
        pass

    def extract(self, text):
        m = re.search(self.expr(), text)
        return m.groupdict()


class Processor:

    """
    Process expressions like:
        (color red lorem ipsum dolor sit)
    """
    
    def __init__(self):
        self.expressions = []
        self.defaults = ['set', 'define']

    def sub(self, key, func, text):
        return re.sub(self._expression(key), func, text)

    def register(self, expr): 
        self.expressions.append(expr)

    def extract(self, text):
        s = Settings()
        return s.extract(text)

    def process(self, text):
        processed = text
        if 'include' in self.keys:
            processed = self.sub('include', self.keys['include'], processed)

        for key, func in self.keys.items():
            processed = self.sub(key, func, processed)

        return processed


def usage():
    print(f"Error: file not found\n\nusage: {sys.argv[0]} [file] [file]")
    sys.exit(1)


def get_files():
    n_args = len(sys.argv)
    if n_args < 2:
        usage()
    elif n_args > 2:
        inf, outf = sys.argv[1:]
    else:
        inf = sys.argv[1]
        outf = inf
    return inf, outf


if __name__ == "__main__":

    # inf, outf = get_files()
    p = Processor()
    p.register(ItalicsExpr('{ }'))
    p.register(ItalicsExpr())
    p.register(ColorExpr())
    for e in p.expressions:
        print(re.sub(e.expr(), e.sub, teststr))
    print(p.extract(teststr))
