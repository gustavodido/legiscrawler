#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bs4
import requests
import sys


class AssembleiaSCModel:
    def __init__(self, identification, description, link):
        self.identification = identification
        self.description = description
        self.link = "http://server03.pge.sc.gov.br" + link

    def content(self):
        return [self.identification, self.description, self.link]

    @staticmethod
    def header():
        return ["Identificação", "Ementa", "Link"]


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
        filehandle.write("<tr><th>Identificação</th><th>Emementa</th></tr>")
        for i in results:
            filehandle.write("<tr><td><a href='{}'>{}</a></td><td>{}</td></tr>".format(i.link, i.identification, i.description))
        filehandle.write("</table></body></html>")
        filehandle.close()


class AssembleiaSCParser:
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
        t = bs.find_all("tr", {'class': 'RecordTitle'})
        for cell in t:
            description = cell.next_sibling.next_sibling.td.next_sibling.next_sibling.font.text
            link = cell.findAll(text=lambda text: isinstance(text, bs4.Comment))[0].extract()[14:64]
            results.append(AssembleiaSCModel(self.parse_cell(cell.td.next_sibling.next_sibling.b.text),
                                             self.parse_cell(description), link))

        return results


class AssembleiaSC:
    def __init__(self, parser):
        self.session = requests.Session()
        self.parser = parser

    @staticmethod
    def build(term):
        return {
            'pTipoNorma': 'T',
            'pVigente': 'Sim',
            'pNumero': '',
            'pEmissaoInicio': '',
            'pEmissaoFim': '',
            'pArtigo': '',
            'pEmenta': '',
            'pIndex': '',
            'pCatalogo': '',
            'pConteudo': term,
            'Action': 'Pesquisar'
        }

    def crawl(self, terms, operator):
        if operator == "AND":
            payload = self.build(" ".join(terms))
            self.session.post("http://server03.pge.sc.gov.br/pge/normasjur.asp", headers=[], data=payload)
            return self.crawl_pages()
        else:
            results = []
            for term in terms:
                payload = self.build(term)
                self.session.post("http://server03.pge.sc.gov.br/pge/normasjur.asp", headers=[], data=payload)
                results.extend(self.crawl_pages())

            return results

    def crawl_pages(self):
        results = []
        with open('resources/assembleia_sc.url') as data_file:
            origurl = data_file.read()

        status_code = 200
        current_page = 1

        while status_code == 200:
            result = self.session.get(origurl.format(current_page))
            status_code = result.status_code
            current_page += 1
            results.extend(self.parser.parse(result.text))

        return results


class Application:
    def __init__(self, args):
        self.args = args

    def run(self):
        if self.has_args():
            filename = sys.argv[3]
            asssc = AssembleiaSC(AssembleiaSCParser())
            results = asssc.crawl(self.args[1].split(','), self.args[2].upper())
            HtmlGenerator.generate(filename, results)

            print 'Saved {} records to {}.'.format(len(results), filename)
        else:
            self.usage()

    def has_args(self):
        return len(self.args) == 4

    @staticmethod
    def usage():
        print 'Usage: python assembleia_sc.py "term1, term2" and|or file.csv'


app = Application(sys.argv)
app.run()
