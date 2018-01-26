#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys


teststr = """ Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita
kasd gubergren, no sea (color red takimata sanctus) est Lorem ipsum dolor sit
amet. (it because better are your breasts than wine) Lorem ipsum dolor sit amet,
consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et
dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est
Lorem ipsum dolor sit amet. """


class Processor:

    """
    Process expressions like:
        (color red lorem ipsum dolor sit)
    """
    
    def __init__(self):
        self.start = r"("
        self.end = r")"
        self.keys = {}

    def _expression(self, key):
        expr = rf"(?P<head>{key})\s(?P<body>.*?)"
        return re.compile(re.escape(self.start) + expr + re.escape(self.end), re.M | re.S)

    def sub(self, key, func, text):
        return re.sub(self._expression(key), func, text)

    def register(self, key, func):
        self.keys[key] = func 

    def delimiters(self, delim):
            self.start, self.end = delim

    def extract(self, text):
        for key, func in self.keys.items():
            expr = self._expression(key)
            return func(expr.search(text))

    def process(self, text):
        processed = text
        if 'include' in self.keys:
            processed = self.sub('include', self.keys['include'], processed)

        for key, func in self.keys.items():
            processed = self.sub(key, func, processed)

        return processed


def it_repl(m):
    line = m.group("body")
    return f"\\textit{{{line}}}"


def color_repl(m):
    col, line = m.group("body").split(maxsplit=1)
    return f"\\textcolor{{{col}}}{{{line}}}"


def include_repl(m):
    return Path(m.group("body")).open().read()


def preamble_func(m):
    exprs = m.group('body')
    data = {}
    head, _, body = exprs.partition(': ')
    data[head.strip()] = body.strip()
    return data


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
    
    preamble = Processor()
    preamble.delimiters(('<!--', '-->'))
    preamble.register("preamble", preamble_func)
    
    keys = {"it": it_repl, "color": color_repl, "include": include_repl}

    with open(inf, 'r') as source:
        text = source.read()
        if outf == inf:
            backup = "." + inf + "~"
            with open(backup, 'w') as backup:
                backup.write(text)

    settings = preamble.extract(text)

    x = Processor()
    for pair in keys.items():
        x.register(*pair)
    for pair in settings['delimiters'].split():
        x.delimiters(pair.split('-'))
        text = x.process(text)

    with open(outf, 'w') as target:
        target.write(text)
