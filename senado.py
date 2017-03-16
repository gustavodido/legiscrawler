#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
import bs4
import csv
import sys
import re


class SenadoModel:
    def __init__(self, source, identification, date, description, publication, code, link):
        self.source = source
        self.identification = identification
        self.date = date
        self.description = description
        self.publication = publication
        self.code = code
        self.link = link

    def content(self):
        return [self.source, self.identification, self.date, self.description, self.publication, self.code]

    @staticmethod
    def header():
        return ["Origem", "Identificação", "Data", "Ementa", "Publicação", "Código"]


class CsvGenerator:
    def __init__(self):
        pass

    @staticmethod
    def generate(filename, results):
        filehandle = open(filename, 'wb')
        wr = csv.writer(filehandle, quoting=csv.QUOTE_ALL)
        wr.writerow(SenadoModel.header())
        for i in results:
            wr.writerow(i.content())


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

        filehandle.write("<tr>")
        for h in SenadoModel.header():
            filehandle.write("<th>{}</th>".format(h))

        filehandle.write("</tr>")
        for i in results:
            filehandle.write("<tr>")
            filehandle.write("<td>{}</td>".format(i.source))
            filehandle.write("<td><a href='{}'>{}</a></td>".format(i.link, i.identification))
            filehandle.write("<td>{}</td>".format(i.date))
            filehandle.write("<td>{}</td>".format(i.description))
            filehandle.write("<td>{}</td>".format(i.publication))
            filehandle.write("<td>{}</td>".format(i.code))
            filehandle.write("</tr>")

        filehandle.write("</table></body></html>")
        filehandle.close()


class SenadoParser:
    def __init__(self):
        pass

    @staticmethod
    def parse_cell(row, index):
        return row[index].findChildren(recursive=False)[1].text \
            .replace('\n', ' ') \
            .replace('\r', '') \
            .encode('utf-8') \
            .strip()

    @staticmethod
    def parse_link(child):
        obj = child.find("div", {"class": "hidden-print"})
        html = str(obj.button.next_sibling.next_sibling.next_sibling.next_sibling)
        link = re.search(r"abrePopup\(\'(.*)\',", html)
        if link:
            return link.group(1).replace("&amp;", "&")
        return ""

    def parse(self, html):
        bs = bs4.BeautifulSoup(html, 'html.parser')
        root = bs.find("div", {'xmlns:sf': 'http://www.senado.gov.br'})
        result = []
        for child in root.findChildren(recursive=False):
            rows = child.findChildren(recursive=False)
            result.append(SenadoModel(self.parse_cell(rows, 1),
                                      self.parse_cell(rows, 2),
                                      self.parse_cell(rows, 3),
                                      self.parse_cell(rows, 4),
                                      self.parse_cell(rows, 7),
                                      self.parse_cell(rows, 12),
                                      self.parse_link(child)))
        return result


class Senado:
    def __init__(self, parser):
        self.parser = parser

    @staticmethod
    def build_count(terms, operator):
        with open('resources/senado_count.json') as data_file:
            payload = json.load(data_file)
        payload["termos"] = map(lambda t: {u'termo': t, u'operadorLogico': operator}, terms)

        return payload

    @staticmethod
    def build_crawl(searchid):
        with open('resources/senado_crawl.json') as data_file:
            payload = json.load(data_file)
        payload['idConsulta'] = searchid

        return payload

    def count(self, terms, operator):
        payload = self.build_count(terms, operator)
        url = 'http://legis.senado.gov.br/sicon/pesquisa/contarDocumentos'
        headers = {'content-type': 'application/json'}
        result = requests.post(url, data=json.dumps(payload), headers=headers).json()
        return result['quantidade'], result['idConsulta']

    def crawl(self, terms, operator):
        c = self.count(terms, operator)
        return self.crawl_by_id(c[1])

    def crawl_by_id(self, searchid):
        payload = self.build_crawl(searchid)
        url = 'http://legis.senado.gov.br/sicon/pesquisa/listarDocumentos'
        headers = {'content-type': 'application/json'}
        return self.parser.parse(requests.post(url, data=json.dumps(payload), headers=headers).text)


class Application:
    def __init__(self, args):
        self.args = args

    def run(self):
        if self.has_args():
            filename = sys.argv[3]
            senado = Senado(SenadoParser())
            results = senado.crawl(self.args[1].split(','), self.args[2].upper())
            HtmlGenerator.generate(filename, results)

            print 'Saved {} records to {}.'.format(len(results), filename)
        else:
            self.usage()

    def has_args(self):
        return len(self.args) == 4

    @staticmethod
    def usage():
        print 'Usage: python senado.py "term1, term2" and|or file.csv'


app = Application(sys.argv)
app.run()
