#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
from pathlib import Path
import heapq
import re
import sys


teststr = """
(include ./LICENSE)
    Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita
kasd gubergren, no sea (color red takimata sanctus) est Lorem ipsum dolor sit
amet. (it because better are your breasts than wine) Lorem ipsum dolor sit amet,
consetetur |it sadipscing elitr|, |b sed diam nonumy eirmod tempor| invidunt ut labore et
dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est
Lorem ipsum dolor sit amet. """


class Expression:

    __metaclass__ = abc.ABCMeta

    def __init__(self, delim='( )'):
        self.delim = delim

    @property
    @abc.abstractmethod
    def key(self):
        """ key: mandatory attribute """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def prio(self):
        """ key: mandatory attribute """
        raise NotImplementedError

    @property
    def delim(self):
        """ delim: mandatory attribute """
        return self._delim

    @delim.setter
    def delim(self, val):
        self._delim = val.split()

    def expr(self):
        """ return a compiled regex object that contains the groups 'head' and
            'body'
        """

        exprs = [re.escape(self.delim[0]),
                 rf"(?P<head>{self.key})",
                 r"\s",
                 rf"(?P<body>.*?)",
                 re.escape(self.delim[1])]
        
        return re.compile(''.join(exprs), re.M | re.S)

    @abc.abstractmethod
    def repl(self):
        """ returns the replacement for body """    
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}({self.key}, delimiters='{self.delim}')"


class Bold(Expression):

    key = 'b'
    prio = 0

    def repl(self, m):
        return f"\\textbf{{{m.group('body')}}}"


class Italics(Expression):
    
    key = 'it'
    prio = 0

    def repl(self, m):
        return f"\\textit{{{m.group('body')}}}"


class Color(Expression):

    key = 'color'
    prio = 0

    def repl(self, m):
        col, line = m.group("body").split(maxsplit=1)
        return f"\\textcolor{{{col}}}{{{line}}}"


class Include(Expression):

    key = 'include'
    prio = 9

    def repl(self, m):
        return Path(m.group("body")).open().read()


class Processor:

    """
    Process expressions like:
        (color red lorem ipsum dolor sit)
    """
    
    def __init__(self):
        self._expressions = []
        self._extra_delim = ["{ }", "| |"]

    def register(self, expr): 
        self._expressions.append(expr)
        for d in self._extra_delim:
            expr.delim = d
            self._expressions.append(expr)
        
    def _substitute(self, expr, text):
        return expr.expr().sub(expr.repl, text)

    def process(self, text):
        for e in sorted(self._expressions, key=lambda x: x.prio, reverse=True):
            text = self._substitute(e, text)
            # for i in self._extra_delim:
            #     e.delim = i
            #     text = self._substitute(e, text)

        return text


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
    # p = Processor()
    # p.register(Bold())
    # p.register(Include())
    # p.register(Italics())
    # p.register(Color())

    # print(p._expressions)

    delim = ['( )', '{ }']
    delim.append('| |')

    starts = []
    ends = []
    for p in delim:
        start, end = p.split()
        starts.append(f"({re.escape(start)})")
        ends.append(f"({re.escape(end)})")
    
    expr = ['(' + '|'.join(starts) + ')',
            rf"(?P<head>it)",
            r"\s",
            rf"(?P<body>.*?)",
            '(' + '|'.join(ends) + ')']

    x = re.compile(''.join(expr), re.M | re.S)
    print(re.sub(x, lambda m: f"\\textit{{{m.group('body')}}}", teststr))

