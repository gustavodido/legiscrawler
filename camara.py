# coding=utf-8
import requests
import bs4


class CamaraFederalModel:
    def __init__(self, identification, link, description, source, date):
        self.identification = identification
        self.link = link
        self.description = description
        self.source = source
        self.date = date

    def content(self):
        return [self.source, self.identification, self.date, self.description, self.link]

    @staticmethod
    def header():
        return ['Origem', 'Identificação', 'Data', 'Ementa', 'Link']


class CamaraFederalParser:
    def __init__(self):
        pass

    @staticmethod
    def parse_cell(cell):
        return cell.replace('\n', ' ') \
            .replace('\r', '') \
            .encode('utf-8') \
            .strip()

    @staticmethod
    def get_next_page(bs):
        nextpage = bs.find('li', { 'class': 'proxima'}).find('a')
        print nextpage

        if nextpage is not None:
            return "http://www2.camara.leg.br/busca/" + nextpage["href"]

        return ''

    def parse(self, html):
        bs = bs4.BeautifulSoup(html, 'html.parser')
        root = bs.find("ul", {'class': 'visualNoMarker'})
        result = []
        for row in root.findChildren(recursive=False):
            result.append(CamaraFederalModel(self.parse_cell(row.find("a").text),
                                             self.parse_cell(row.find("a")["href"]),
                                             self.parse_cell(row.find("p").text),
                                             self.parse_cell(row.find("p", {'class': 'info'}).find("strong").text),
                                             self.parse_cell(row.find("p", {'class': 'info'}).find("span").text)))

        return result, self.get_next_page(bs)

with open('resources/camara_federal.url') as data_file:
    url = data_file.read()

url = url.format("pis")
r = requests.get(url)
print r.text
parser, p = CamaraFederalParser().parse(r.text)
print p

