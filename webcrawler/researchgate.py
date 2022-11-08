import time

import requests
from bs4 import BeautifulSoup
import selenium as se
import random
import xmltodict

class Crawler():
    def __init__(self):
        pass

class PubMedCrawler(Crawler):
    def __init__(self):
        pass

    def convert_doi(self, doi):
        response = requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={doi}&idtype=doi&format=json&versions=yes&showaiid=no&tool=affiliation&email=david1.le@tum.de").json()
        if "status" in response["records"][0]:
            return ""
        else:
            return response["records"][0]["pmcid"][3:]

    def make_request(self, doi):
        self.make_request(doi=doi)

    def make_request(self, doi=None, title=None, author=None):
        pmcid=None
        if doi:
            pmcid = self.convert_doi(doi)
            print(pmcid)
        else:
            pass

        if not pmcid:
            return ""

        response = xmltodict.parse(requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:{pmcid}&metadataPrefix=pmc_fm").content)
        contribution_group = response['OAI-PMH']['GetRecord']["record"]["metadata"]["article"]["front"]["article-meta"]
        all_affiliations = []
        print(response)
        for auth in contribution_group["contrib-group"]["contrib"]:
            name = f"{auth['name']['given-names']} {auth['name']['surname']}"
            # print(auth["xref"])
            affiliations = []
            if "xref" not in auth:
                continue
            for aff_meta in auth["xref"]:
                try:
                    if aff_meta["@ref-type"] == "aff":
                        aff_id = int(aff_meta["@rid"][-1])
                        affiliations.append(contribution_group["aff"][aff_id - 1]["#text"])
                    else:
                        continue
                except TypeError:
                    continue
            if affiliations:
                all_affiliations.append((name, ";".join(affiliations)))
        return all_affiliations


class ResearchGateCrawler(Crawler):
    def __init__(self):
        options = se.webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15")
        self.browser = se.webdriver.Chrome(options=options)

    def request_query(self, title, author):
        url = f"https://www.researchgate.net/search/publication?q={title} {author}"
        time.sleep(1)
        self.browser.get(url)
        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        titles = []
        publications = []
        for node in soup.find_all("div", {"class": "nova-legacy-v-publication-item__title"}):
            titles.append(''.join(node.findAll(text=True)))
        for node in soup.find_all("a", {"class": "nova-legacy-e-link--theme-bare"}):
            publications.append(node["href"])

        if not titles or not title.lower().replace(".", "") in titles[0].lower():
            return None
        return publications[0]

    def extract_doi(self, title, author):
        href = self.request_query(title, author)
        if not href:
            return ""

        link = f"https://www.researchgate.net/{href}"
        self.browser.get(link)
        time.sleep(0.5)
        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')

        for node in soup.find_all("a", {"class": "nova-legacy-e-link nova-legacy-e-link--color-inherit nova-legacy-e-link--theme-decorated"}):
            text = node.find(text=True)
            if "/" in text:
                return text
        return ""


    def make_request(self, title, author):
        href = self.request_query(title, author)
        doi = "NA"
        if not href:
            return [], doi


        link = f"https://www.researchgate.net/{href}"
        self.browser.get(link)
        time.sleep(1)
        html = self.browser.page_source
        soup_author = BeautifulSoup(html, 'html.parser')

        for node in soup_author.find_all("a", {"class": "nova-legacy-e-link nova-legacy-e-link--color-inherit nova-legacy-e-link--theme-decorated"}):
            text = node.find(text=True)
            if "/" in text:
                doi = text

        author_affiliation = []
        for node in soup_author.find_all("div", {"class": "nova-legacy-v-person-list-item__body"}):
            author_name = node.find_all("div", {"class": "nova-legacy-v-person-list-item__title"})[0].find(
                text=True)
            aff_element = node.find_all("li", {"class", "nova-legacy-v-person-list-item__meta-item"})
            if aff_element:
                author_aff = aff_element[0].find(text=True)
            else:
                author_aff = ""
            author_affiliation.append((author_name, author_aff))
        return author_affiliation, doi


class SpringerCrawler(Crawler):
    def __init__(self):
        self.api_key = "4d550573ce69005bbdb3fc40e70a3b2c"

    def make_request(self, title, author):
        self.__make_request(title=title, author=author)

    def make_request(self, doi):
        self.__make_request(doi=doi)

    def __make_request(self, doi=None, title=None, author=None):
        response = ""
        try:
            if doi:
                # Springer Meta library
                response = requests.get(f"https://api.springernature.com/meta/v2/jsonld?q=doi:{doi}&api_key={self.api_key}").json()
            else:
                pass
            if response["records"][0]["jsonld"]:
                return [(f"{info['givenName']} {info['familyName']}", info["affiliation"]["alternateName"]) for info in
                        response["records"][0]["jsonld"]["author"]]
        except:
            pass
        #print(response)
        try:
            # Springer OpenAccess library
            response = xmltodict.parse(requests.get(f"https://api.springernature.com/openaccess/jats?q=doi:{doi}&api_key={self.api_key}").content)
            if response["response"]["records"]:
                contrib_group = response["response"]["records"]["article"]["front"]["article-meta"]["contrib-group"]
                all_affiliations = []
                for x in contrib_group["contrib"]:
                    name = f"{x['name']['given-names']} {x['name']['surname']}"
                    affiliation = []
                    for aff in x["xref"]:
                        if aff["@ref-type"] == "aff":
                            ref_id = int(aff["@rid"][-1])
                            affiliation.append(contrib_group["aff"][ref_id - 1]["institution-wrap"]["institution"]["#text"])
                    affiliations = ";".join(affiliation)
                    all_affiliations.append((name, affiliations))
                return all_affiliations
        except:
            pass
        return ""

class IeeeCrawler(Crawler):
    def __init__(self):
        self.api_key = "wcwernpubhe2zeynca7bb83q"
        self.browser = "fasdf"

    def __make_api_request(self, title, author):
        try:
            request_link = f"http://ieeexploreapi.ieee.org/api/v1/search/articles?apikey=wcwernpubhe2zeynca7bb83q&" \
                           f"format=json&max_records=25&start_record=1&sort_order=asc&sort_field=article_number&" \
                           f"article_title={title}&author={author}"

            affiliations = requests.get(request_link).json()
            print(affiliations)
            if not affiliations["total_records"]:
                return []
            affiliations = affiliations["articles"][0]["authors"]["authors"]
            processed_affiliations = [(affiliation["full_name"], self.parse_affiliation(affiliation["affiliation"] if "affiliation" in affiliation else "")) for affiliation in
                                      affiliations]

            return processed_affiliations
        except:
            raise ValueError

    def __make_selenium_request(self, title, author):
        pass

    def parse_affiliation(self, affiliation):
        if not affiliation:
            return "None"
        split_affiliation = affiliation.split(",")
        if len(split_affiliation) == 1:
            return affiliation
        return ",".join(split_affiliation[0:-1])

    def make_request(self, title, author):
        try:
            return self.__make_api_request(title, author)
        except ValueError as err:
            raise ValueError

    def print_hello(self):
        print("fasdfa")

