#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import bs4
import requests


class AssembleiaSPModel:
    def __init__(self, title, description, link):
        self.title = title
        self.description = description
        self.link = link

    def content(self):
        return [self.title, self.description, self.link]

    @staticmethod
    def header():
        return ["Título", "Descrição", "Link"]


class HtmlGenerator:
    def __init__(self):
        pass

    @staticmethod
    def generate(filename, results):
        bootstrap = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css"
        filehandle = open(filename, 'wb')
        filehandle.write("<html>")
        filehandle.write("<head>")
        filehandle.write(
            '<link rel="stylesheet" type="text/css" href="{}">'.format(bootstrap))
        filehandle.write("<meta charset=utf-8></head>")
        filehandle.write("<body><table class='table table-bordered'>")
        filehandle.write("<tr><th>Título</th><th>Descrição</th></tr>")
        for i in results:
            filehandle.write("<tr><td><a href='{}'>{}</a></td><td>{}</td></tr>".format(i.link, i.title, i.description))
        filehandle.write("</table></body></html>")
        filehandle.close()


class AssembleiaSPParser:
    def __init__(self):
        pass

    @staticmethod
    def parse_cell(cell):
        return cell \
            .replace('\n', ' ') \
            .replace('\r', '') \
            .replace('EMENTA:', '') \
            .encode('utf-8') \
            .strip()

    def parse(self, html):
        results = []

        bs = bs4.BeautifulSoup(html, 'html.parser')
        ul = bs.find_all("ul", {'class': 'lista_navegacao'})
        for li in ul[2].findChildren(recursive=False):
            title = self.parse_cell(li.a.text)
            results.append(AssembleiaSPModel(title, self.parse_cell(li.p.text),
                                             "http://www.al.sp.gov.br{}".format(li.a["href"])))
        return results


class AssembleiaSP:
    def __init__(self, parser):
        self.session = requests.Session()
        self.parser = parser

    @staticmethod
    def build(terms):
        with open('resources/assembleia_sp.url') as data_file:
            payload = data_file.read()
        return payload.format(terms)

    def crawl(self, terms):
        url = self.build(" ".join(terms))
        result = self.session.get(url)
        return self.parser.parse(result.text)


class Application:
    def __init__(self, args):
        self.args = args

    def run(self):
        if self.has_args():
            filename = sys.argv[3]
            asssc = AssembleiaSP(AssembleiaSPParser())
            results = asssc.crawl(self.args[1].split(','))
            HtmlGenerator.generate(filename, results)

            print 'Saved {} records to {}.'.format(len(results), filename)
        else:
            self.usage()

    def has_args(self):
        return len(self.args) == 4

    @staticmethod
    def usage():
        print 'Usage: python assembleia_sp.py "term1, term2" and|or file.csv'


app = Application(sys.argv)
app.run()
