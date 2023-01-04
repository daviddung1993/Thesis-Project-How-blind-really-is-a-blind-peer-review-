import time

import requests
from bs4 import BeautifulSoup
import selenium as se
import random
import xmltodict
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class Crawler:
    def __init__(self):
        options = se.webdriver.ChromeOptions()
        #options.add_argument('headless')
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15")
        self.browser = se.webdriver.Chrome(options=options)
        self.springer_api_key = "f348a138cc36520c1cce97b4efe86dfb"

        self.science_direct_api_key = {"APIKey": "87c5683fd947b252f6ca2d1d922aad7d"}
        self.science_direct_headers = {"Accept": "application/json"}

    # PubMed Crawler
    def pubmed_request(self, pmcId, doi=None):

        if doi:
            pmcId = self.convert_doi_to_pmc(doi)

        if not pmcId:
            return ""

        response = xmltodict.parse(requests.get(
            f"https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:{pmcId}&metadataPrefix=pmc_fm").content)
        contribution_group = response['OAI-PMH']['GetRecord']["record"]["metadata"]["article"]["front"]["article-meta"]
        all_affiliations = []
        for auth in contribution_group["contrib-group"]["contrib"]:
            name = f"{auth['name']['given-names']} {auth['name']['surname']}"
            affiliations = []
            if "xref" not in auth:
                continue
            for aff_meta in auth["xref"]:
                if aff_meta["@ref-type"] == "aff":
                    aff_id = int(aff_meta["@rid"][-1])
                    affiliations.append(contribution_group["aff"][aff_id - 1]["#text"])
                else:
                    continue
            if affiliations:
                all_affiliations.append((name, ";".join(affiliations)))
        return all_affiliations

    # ResearchGate Crawler
    def research_gate_request(self, title, author):
        href = self.rg_query(title, author)
        if not href:
            return []

        link = f"https://www.researchgate.net/{href}"
        self.browser.get(link)
        time.sleep(1)
        html = self.browser.page_source
        soup_author = BeautifulSoup(html, 'html.parser')

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
        return author_affiliation

    def rg_query(self, title, author):
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

    # Springer Crawler
    def springer_request(self, doi, scrape=False):
        if scrape:
            return self.springer_scrape_request(doi)
        return self.springer_api_request(doi)

    def springer_scrape_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "springer.com" not in url:
            new_url = url.split("/")[2]
            return new_url

        author_links = self.browser.find_elements(By.XPATH, '//a[@data-track-action="open author"]')
        for author_link in author_links:
            author_link.click()
        try:
            html = self.browser.page_source
            soup = BeautifulSoup(html, 'html.parser')
            all_affiliations = []


            author_div = soup.findAll("div", {"class": "c-author-popup"})
            for node in author_div:
                name = node.find("h3", {"class": "c-author-popup__subheading"}).find(text=True)
                information = node.find("ul", {"class": "c-author-popup__author-list"})
                affiliation = information.find(text=True).strip()
                all_affiliations.append((name,self.parse_affiliation(affiliation)))
            return all_affiliations
        except AttributeError:
            return []


    def springer_api_request(self, doi):
        response = ""
        # Springer Meta library
        try:
            response = requests.get(
                    f"https://api.springernature.com/meta/v2/jsonld?q=doi:{doi}&api_key={self.springer_api_key}").json()

            if response["records"][0]["jsonld"]:
                return [(f"{info['givenName']} {info['familyName']}",
                         self.parse_affiliation(info["affiliation"]["alternateName"])) for info in
                        response["records"][0]["jsonld"]["author"]]
        except KeyError:
            pass

        # Springer Open Access library
        response = xmltodict.parse(requests.get(
            f"https://api.springernature.com/openaccess/jats?q=doi:{doi}&api_key={self.springer_api_key}").content)
        if response["response"]["records"]:
            contrib_group = response["response"]["records"]["article"]["front"]["article-meta"]["contrib-group"]
            all_affiliations = []
            for x in contrib_group["contrib"]:
                name = f"{x['name']['given-names']} {x['name']['surname']}"
                affiliation = []
                if isinstance(x["xref"], dict):
                    x["xref"] = [x["xref"]]
                for aff in x["xref"]:
                    if aff["@ref-type"] == "aff":
                        ref_id = int(aff["@rid"][-1])
                        institution_information = contrib_group["aff"][ref_id - 1]["institution-wrap"][
                            "institution"]
                        if isinstance(institution_information, dict):
                            institution_information = [institution_information]
                        for information in institution_information:
                            print(information)
                            if information["@content-type"] == "org-name":
                                affiliation.append(information["#text"])
                affiliations = ";".join(affiliation)
                all_affiliations.append((name, affiliations))
            return all_affiliations
        return ""

    # IEEE Crawler
    def ieee_request(self, doi, scrape=False):
        if scrape:
            return self.ieee_scrape_request(doi)
        return self.ieee_api_request(doi)

    def ieee_scrape_request(self, doi):
        all_affiliations = []
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "ieee.org" not in url:
            return ""

        self.browser.get(f"{url}/authors#authors")
        source = self.browser.page_source
        soup = BeautifulSoup(source, 'html.parser')

        for node in soup.find_all("div", {"class": "authors-accordion-container"}):
            all_text = node.findAll(text=True)
            all_affiliations.append((all_text[1], self.parse_affiliation(all_text[7])))

        return all_affiliations

    def ieee_api_request(self, doi):
        request_link = f"http://ieeexploreapi.ieee.org/api/v1/search/articles?apikey=wcwernpubhe2zeynca7bb83q&" \
                       f"format=json&max_records=25&start_record=1&sort_order=asc&sort_field=article_number&" \
                       f"doi={doi}"

        affiliations = requests.get(request_link).json()

        if not affiliations["total_records"]:
            return []

        affiliations = affiliations["articles"][0]["authors"]["authors"]
        processed_affiliations = [(affiliation["full_name"], self.parse_affiliation(
            affiliation["affiliation"] if "affiliation" in affiliation else "")) for affiliation in
                                  affiliations]

        return processed_affiliations

    # Science Direct Crawler
    def science_direct_request(self, doi, scrape=False, authors=[]):
        if scrape:
            return self.science_direct_scrape_request(doi)
        return self.science_direct_api_request(doi, authors)

    def science_direct_api_request(self, doi, authors):
        affiliations = []
        response = requests.get(f"https://api.elsevier.com/content/abstract/doi/{doi}",
                                headers=self.science_direct_headers, params=self.science_direct_api_key).json()
        if "service-error" in response \
                or "affiliation" not in response['abstracts-retrieval-response'] \
                or not isinstance(response['abstracts-retrieval-response']['affiliation'], dict):
            return affiliations

        affiliation_name = response['abstracts-retrieval-response']['affiliation']['affilname']
        country = response['abstracts-retrieval-response']['affiliation']['affiliation-country']

        return [(author, affiliation_name, country) for author in authors]

    def science_direct_scrape_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "sciencedirect.com" not in url:
            return -1

        time.sleep(0.2)
        try:
            bt = self.browser.find_element(By.ID, "show-more-btn")
        except NoSuchElementException:
            return []
        bt.click()
        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        author_div = soup.find("div", {"id": "author-group"})

        author_refs = {}
        affiliation_refs = {}
        all_affiliations = []
        try:
            for node in author_div.find_all("a", {"class": "author"}):
                author_information = node.findAll(text=True)
                name = " ".join(author_information[:2])
                refs = [ref for ref in author_information[2:] if str.isalpha(ref) and len(ref) == 1]
                author_refs[name] = refs

            for node in author_div.find_all("dl", {"class": "affiliation"}):
                affiliation_information = node.findAll(text=True)
                affiliation_refs[affiliation_information[0]] = affiliation_information[1]

            for author, refs in author_refs.items():
                affiliation = ";;".join([self.parse_affiliation(affiliation_refs[ref]) for ref in refs])
                all_affiliations.append((author, affiliation))
            time.sleep(1)
            return all_affiliations
        except (KeyError, ValueError, IndexError, AttributeError):
            print("error")

        author_div = soup.findAll("div", {"class": "author-group"})

        try:
            for x in author_div:
                for node in x.findAll("a", {"class": "author"}):
                    author_information = node.findAll(text=True)
                    for aff in x.findAll("dl", {"class": "affiliation"}):
                        affiliation_information = aff.findAll(text=True)
                        name = " ".join(author_information)
                        affiliation = ";;".join(affiliation_information)
                        all_affiliations.append((name,affiliation))
            return all_affiliations
        except (KeyError, ValueError, IndexError, AttributeError):
            print("error")
            return []

    # ACM Crawler
    def acm_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "acm.org" not in url:
            return -1

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        author_links = soup.findAll("li", {"class": "loa__item"})
        all_affiliations = []

        for node in author_links:
            author_information = node.findAll(text=True)
            all_affiliations.append((author_information[1], self.parse_affiliation(author_information[3])))

        return all_affiliations

    # Wiley Crawler
    def wiley_request(self, doi):

        while True:
            self.browser.get(f"https://doi.org/{doi}")
            url = self.browser.current_url

            if "wiley.com" not in url:
                new_url = url.split("/")[2]
                return new_url

            html = self.browser.page_source
            soup = BeautifulSoup(html, 'html.parser')
            all_affiliations = []

            if not soup.find("h2", {"id": "challenge-running"}):
                break
            self.browser.close()
            self.__init__()


        author_table = soup.findAll("div", {"class": "author-info accordion-tabbed__content"})
        for node in author_table[:len(author_table)-1]:
            name = node.find("p", {"class", "author-name"}).findAll(text=True)[0]

            information_elements = node.findAll("p", class_=None)
            information = [element.find(text=True) for element in information_elements]

            if not information:
                break

            affiliation = information[0] if not information[0] == "Correspondence" else information[1]
            all_affiliations.append((name, affiliation))

        return all_affiliations

    # Informa Crawler
    def informa_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "tandfonline.com" not in url:
            new_url = url.split("/")[2]
            return new_url

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        all_affiliations = []

        try:
            author_information = soup.findAll("div", {"class": "entryAuthor"})
            for node in author_information:
                author = node.find("a", {"class", "author"}).find(text=True).strip()
                affiliation = node.find("span", {"class", "overlay"}).find(text=True).strip()
                all_affiliations.append((author, affiliation))
            return all_affiliations

        except AttributeError:
            return []


    # SPIE Crawler
    def spie_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "spiedigitallibrary.org/" not in url:
            new_url = url.split("/")[2]
            return new_url

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        author_links = {}
        prev_author = ""
        try:
            information = soup.find("div", {"id": "affiliations"})
            author_information = information.find("b", class_=None).findAll(text=True)

            for author_info in author_information:
                for author in author_info.split(","):
                    if not author.strip() or author.strip() == "," or "orcid" in author:
                        continue
                    if len(author) > 2:
                        prev_author = author.lstrip().rstrip(",")
                        author_links[prev_author] = []
                    else:
                        author_links[prev_author].append(author)

            information.b.clear()
            aff_information = information.findAll(text=True)
            affiliations = list(filter(lambda aff: aff.strip and len(aff) > 2 and aff != "\n", aff_information))
            affiliations = [aff.strip("\t") for aff in affiliations]

            all_affiliations = []
            #print(author_links)
            for key, value in author_links.items():
                affi = []
                for ref in value:
                    affi.append(affiliations[int(ref)-1])
                all_affiliations.append((key,";;".join(affi)))

            return all_affiliations
        except (AttributeError, KeyError) as e:
            print(e)
            return []

    # Optica Crawler
    def optica_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "optica.org" not in url:
            new_url = url.split("/")[2]
            return new_url

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        all_affiliations = []
        author_links = {}
        prev_author = ""
        link_amounts = 0

        try:
            affiliation_element = soup.find("div", {"id": "authorAffiliations"})
            information = affiliation_element.find("strong", class_=None).findAll(text=True)
            #information = " ".join(information).split(",")
            affiliation_element.strong.clear()
            #print(information)
            for info in information:

                info = info.lstrip("\n").rstrip(",").lstrip("and ")
                if info.isnumeric():
                    link_amounts += 1
                    author_links[prev_author].append(info)
                elif len(info) > 2:
                    prev_author = info
                    author_links[prev_author] = []

            print(author_links)
            aff_information = affiliation_element.findAll("p", class_=None)
            affiliations = []
            for aff in aff_information:
                aff_text = aff.findAll(text=True)
                if "Corresponding author: " in aff_text:
                    break

                for aff in aff_text:
                    if aff.strip() and len(aff) > 2:
                        affiliations.append(aff.rstrip("\n"))

            if link_amounts:
                for key, value in author_links.items():
                    affi = []
                    for ref in value:
                        affi.append(affiliations[int(ref) - 1])
                    all_affiliations.append((key, ";;".join(affi)))
            else:
                information = " ".join(information).split(",")
                all_affiliations = [(name.strip(" * ").strip("\n"), affiliations[0]) for name in information]


            return all_affiliations
        except (AttributeError, KeyError, IndexError) as e:
            print(e)
            return []

    def oxford_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "oup.com" not in url:
            new_url = url.split("/")[2]
            return new_url

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        all_affiliations = []
        try:
            information = soup.findAll("div", {"class": "info-card-author"})

            for node in information:
                author_name = node.find("div", {"class": "info-card-name"}).find(text=True).strip("\n").strip()
                affiliations = []
                for aff in node.findAll("div", {"class": "aff"}):
                    affiliations.append(aff.find(text=True))
                all_affiliations.append((author_name, ";;".join(affiliations)))
            return all_affiliations
        except (AttributeError, KeyError, IndexError) as e:
            print(e)
            return []

    # IOP Crawler
    def iop_request(self, doi):
        self.browser.get(f"https://doi.org/{doi}")
        url = self.browser.current_url

        if "iop.org" not in url:
            new_url = url.split("/")[2]
            return new_url

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        all_affiliations = []

        for author_info in soup.findAll("span", {"itemprop": "author"}):
            author_name = author_info.find("span", {"itemprob": "name"}).find(text=True)
            for ref in author_info.findAll("sup", class_=None):
                print(author_name)
                print(ref.find(text=True))

    @staticmethod
    def convert_doi_to_pmc(doi):
        response = requests.get(
            f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={doi}&idtype=doi&format=json&versions=yes&showaiid=no&tool=affiliation&email=david1.le@tum.de").json()
        if "status" in response["records"][0]:
            return ""
        else:
            return response["records"][0]["pmcid"][3:]

    @staticmethod
    def parse_affiliation(affiliation):
        if not affiliation:
            return "None"
        split_affiliation = affiliation.split(",")
        if len(split_affiliation) == 1:
            return affiliation
        return ",".join(split_affiliation[0:-1])




