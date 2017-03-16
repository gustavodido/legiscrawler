#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bs4
import requests
import sys
import re


class CamaraSCModel:
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


class CamaraSCParser:
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
        link = re.search(r"Gstr_filaDocumentos = \'(.*)\'", html)

        search = link.group(1).split("|||")
        for r in search:
            partials = r.split("###")

            link = re.search(r"title=\"(.*)\" onclick", partials[0]).group(1)

            line = re.search(r"<b><u>(.*)</u></b>", partials[1]).group(1)
            title = bs4.BeautifulSoup(line, 'html.parser').text

            line = re.search(r"Resumo: </i></b>(.*)</font></p>", partials[2]).group(1)
            description = bs4.BeautifulSoup(line, 'html.parser').text

            results.append(CamaraSCModel(self.parse_cell(title), self.parse_cell(description), self.parse_cell(link)))

        return results


class CamaraSC:
    def __init__(self, parser):
        self.session = requests.Session()
        self.parser = parser

    @staticmethod
    def build(term):
        return  {
            'hdn_str_ordenacao': '',
            'hdn_int_totalRegistrosPagina': '',
            'hdn_int_totalRegistrosFila': '0',
            'hdn_bol_controlePesquisa': 'true',
            'hdn_str_filaDocumentos': 'e:\sites\sistemas.sc.gov.br\cmf\pesquisa\doc',
            'lst_str_de_tipoLegislacao': '',
            'lst_str_de_tipoLegislacao2': '',
            'lst_str_de_tipoLei': '0',
            'txt_str_de_palavrasChaves': term,
            'txt_str_nu_ano': '',
            'lst_str_ordenacao': 'DocTitle[a]',
            'lst_int_totalRegistrosPagina': '3000',
            'lst_int_totalRegistrosFila': '3000'
        }

    def crawl(self, terms, operator):
        self.session.get("http://www.cmf.sc.gov.br/legislacao")
        if operator == "AND":
            payload = self.build(" ".join(terms))
            result = self.session.post("http://sistemas.sc.gov.br/cmf/pesquisa/PesquisaDocumentos.asp", headers=[], data=payload)
            return self.crawl_pages(result)
        else:
            results = []
            for term in terms:
                payload = self.build(term)
                result = self.session.post("http://sistemas.sc.gov.br/cmf/pesquisa/PesquisaDocumentos.asp", headers=[], data=payload)
                results.extend(self.crawl_pages(result))

            return results

    def crawl_pages(self, result):
        return self.parser.parse(result.text)


class Application:
    def __init__(self, args):
        self.args = args

    def run(self):
        if self.has_args():
            filename = sys.argv[3]
            asssc = CamaraSC(CamaraSCParser())
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


