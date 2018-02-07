#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
from pathlib import Path
import re
import sys


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
        """ prio: mandatory attribute. Determines replacement order"""
        raise NotImplementedError

    @abc.abstractmethod
    def repl(self):
        """ returns the replacement for body """    
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
                # rf"(\s*?)",   
                rf"(?P<head>{self.key})",
                r"\s+",
                rf"(?P<body>.*?)",
                r"\s*",
                rf"({'|'.join(ends)})"]

        return re.compile(''.join(expr), re.M | re.S)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.__dict__}>"


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


class Underline(Expression):

    key = 'ul'
    prio = 0

    def repl(self, m):
        return f"\\underline{{{m.group('body')}}}"


class Include(Expression):

    key = 'include'
    prio = 8

    def repl(self, m):
        try:
            return Path(m.group("body")).open().read()
        except FileNotFoundError:
            return f"Error: {m.group('body')} - File not Found"


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
        return re.compile(rf"(?P<head>{re.escape(self._key)})", re.M | re.S)
    
    def repl(self, m):
        return self.body


class Settings(Expression):

    key = 'settings'
    prio = 9

    def __init__(self):
        self.delim = ['<!-- -->']
 
    def repl(self, m):
        return m.groups("body")
    
    def extract(self, text):
        settings = {}

        data = self.expr().search(text)
        if data:
            settings['end'] = data.end()

            for line in data.group("body").splitlines():
                key, _, body = line.partition(':')
                settings.setdefault(key.strip(), []).append(body.strip())

        return settings


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

        rules = Settings().extract(text)
        first_line = 0
        if rules: 
            if "delimiters" in rules:
                line = rules["delimiters"][0].split(',')
                self.register_delimiters(*[x.strip() for x in line])
            if "macro" in rules:
                for line in rules["macro"]:
                    key, body = line.split(maxsplit=1)
                    self._macros.append(Macro(key, body))
            first_line = rules['end']

        return text[first_line:]    # cuts off the settings block

    def register(self, *expr): 
        for e in expr:
            self._expressions.append(e)

    def register_delimiters(self, *delimiters):

        """ 
        Ik kon niet kiezen dus we nemen ze allemaal!
        (vooral bedoeld voor ingebedde Expressions, maar dat maakt eigenlijk
        niet omdat ze niet matchen zonder key)
        """

        for m in delimiters:
            self._delim.append(m)
        
    def _substitute(self, expr, text):
        return expr.expr().sub(expr.repl, text)

    def process(self, text):
        text = self.settings(text)
        for e in sorted(self._expressions, key=lambda x: x.prio, reverse=True):
            e.delim.extend(self._delim)
            text = self._substitute(e, text)

        for m in self._macros:
            text = self._substitute(m, text)

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
    
    inf, outf = get_files()

    p = Processor()
    p.register(Bold(), Include(), Italics(), Color(), Underline())

    with open(inf, 'r') as i:
        text = i.read()

    if inf == outf:
        with open(f".{inf}~", 'w') as b:
            b.write(text)

    text = p.process(text)

    with open(outf, 'w') as o:
        o.write(text)


    
