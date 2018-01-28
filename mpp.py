#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
from pathlib import Path
import heapq
import re
import sys


teststr = """
<!--settings 
    delimiters: { }, | |, % %, (! !)
    macro: Lorem Morel
-->
(include ./LICENSE)
    Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita
kasd gubergren, no sea (color red takimata sanctus) est Lorem ipsum dolor sit
amet. (it because better) are (!b your breasts than wine!) Lorem ipsum dolor sit amet,
consetetur |it sadipscing elitr|, |b sed diam nonumy eirmod tempor| invidunt ut labore et
dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est
Lorem ipsum dolor sit amet. """


class Expression:

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.delim = ['( )']

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

    def expr(self):
        """ return a compiled regex object that contains the groups 'head' and
            'body'
        """

        starts = []
        ends = []
        for p in self.delim:
            start, end = p.split()
            starts.append(f"{re.escape(start)}")
            ends.append(f"{re.escape(end)}")
        
        expr = [rf"({'|'.join(starts)})",
                rf"(?P<head>{self.key})",
                r"\s*",
                rf"(?P<body>.*?)",
                r"\s*?",
                rf"({'|'.join(ends)})"]

        return re.compile(''.join(expr), re.M | re.S)

    @abc.abstractmethod
    def repl(self):
        """ returns the replacement for body """    
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


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
    prio = 8

    def repl(self, m):
        return Path(m.group("body")).open().read()


class Settings(Expression):

    key = 'settings'
    prio = 9

    def __init__(self):
        self.delim = ['<!-- -->']
 
    def repl(self):
        pass
    
    def extract(self, text):
        
        settings = {}
        data = self.expr().search(text).group("body")
        if data.count('\n') > 0:
            for line in data.splitlines():
                key, _, body = line.partition(':')
                settings[key.strip()] = body.strip()
        else:
            key, _, body = data.partition(':')
            settings[key.strip()] = body.strip()
        return settings
        

class Macro(Expression):

    prio = 0

    def __init__(self, key, body):
        self.key = key
        self.body = body
    
    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, v):
        self._key = v

    def expr(self):
        """ return a compiled regex object that contains the groups 'head' and
            'body'
        """
        return re.compile(rf"(?P<head>{self.key})", re.M | re.S)
    
    def repl(self, m):
        return self.body


class Processor:

    """
    Process expressions like:
        (color red lorem ipsum dolor sit)
    """
    
    def __init__(self):
        self._expressions = []
        self._macros = []
        self._delim = []

    def settings(self, text):
        """ extracts a block of settings from the text. """
        s = Settings()
        for k, v in s.extract(text).items():
            print(k, v)
            if k == "delimiters":
                self.register_delimiters(*v.split(','))
            if k == "macro":
                self.register(Macro(*v.split()))

    def register(self, *expr): 
        for e in expr:
            self._expressions.append(e)

    def register_macros(self, *macros): 
        for m in macros:
            self._macros.append(m)

    def register_delimiters(self, *delimiters):
        for m in delimiters:
            self._delim.append(m)
        
    def _substitute(self, expr, text):
        return expr.expr().sub(expr.repl, text)

    def process(self, text):
        self.settings(text)
        for e in sorted(self._expressions, key=lambda x: x.prio, reverse=True):
            try:
                e.delim.extend(self._delim)
            except:
                pass
            text = self._substitute(e, text)

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
    p = Processor()
    p.register(Bold(), Include(), Italics(), Color())

    print(p._expressions)
    # print(p._macros)
    print(p.process(teststr))
    # s = Settings()
    # x = s.expr().search(teststr).group("body")
    # print(x.count('\n'))

    
    


