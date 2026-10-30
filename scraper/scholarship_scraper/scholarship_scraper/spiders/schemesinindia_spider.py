import scrapy
from datetime import datetime
from urllib.parse import urlparse

class SchemesinIndiaSpider(scrapy.Spider):
    name = "schemesinindia"

    allowed_domains = ["schemesinindia.in"]

    start_urls=["https://schemesinindia.in/scholarships"]


    def clean_text(self, selector):
        text = selector.xpath("string(.)").get()
        if not text:
            return None
        return " ".join(text.split()) or None

    def parse(self,response):
        links = response.css('a[href^="/scholarships/"]')

        seen_urls = set()
        for link in links:
            href = link.attrib.get("href","").strip()

            if not href:
                continue
            detail_url = response.urljoin(href).split("#")[0]

            if detail_url in seen_urls:
                continue
            seen_urls.add(detail_url)

            title = self.clean_text(link.css("h3"))
            description = self.clean_text(link.css("p"))

            yield response.follow(
                detail_url,
                callback=self.parse_detail,
                meta={
                    "listing_title": title,
                    "listing_description": description,
                },
            )
        self.logger.info(
            "Unique scholarships links discovered: %d",len(seen_urls),
        )

    def parse_detail(self,response):
        sections = response.css("main section")

        def section_by_heading(heading):
            for section in sections:
                heading_text = self.clean_text(section.css("h2"))

                if heading_text and heading.lower() in heading_text.lower():
                    return section
            return None

        def section_text(section):
            if section is None:
                return None

            paragraphs = [self.clean_text(p) for p in section.css("p")]
            paragraphs = [p for p in paragraphs if p]

            return " ".join(paragraphs) or None

        def list_items(section):
            if section is None:
                return []

            return [
                text 
                for item in section.css("ul>li")
                if(text := self.clean_text(item))
            ]

        overview_section = None
        for section in sections:
            if section.css("h2") and section.css("p"):
                overview_section = section
                break

        title = response.meta.get("listing_title")
        if not title and overview_section is not None:
            headings = overview_section.css("h2::text").getall()
            headings = [h.strip() for h in headings if h.strip()]
            title = next(
                (h for h in reversed(headings) if h.lower() != "about"),
                None,
            )

        description = (
            section_text(overview_section)
            if overview_section is not None
            else response.meta.get("listing_description")
        )

        key_facts_section = section_by_heading("Key Facts")
        key_facts = {}

        if key_facts_section is not None:
            for row in key_facts_section.css("dl>div"):
                label = self.clean_text(row.css("dt"))
                value = self.clean_text(row.css("dd"))

                if label and value:
                    key_facts[label] = value

        eligibility_section = section_by_heading("Eligibility")
        documents_section = section_by_heading("Documents Required")

        eligibility = list_items(eligibility_section)
        documents_required = list_items(documents_section)

        self.logger.info( "Detail page: %s", response.url)
        self.logger.info(  "Eligibility section found: %s",eligibility_section is not None)
        self.logger.info(  "Eligibility list items: %s",len(eligibility_section.css("ul li"))
        if eligibility_section is not None else 0
        )
        self.logger.info( "Documents section found: %s", documents_section is not None)
        self.logger.info( "All section headings: %s",sections.css("h2::text").getall())

        faqs = []
        for section in sections:
            heading = self.clean_text(section.css("h2"))
            if heading and "faq" in heading.lower():
                for details in section.css("details"):
                    question = self.clean_text(details.css("summary"))
                    answer = self.clean_text(details.css("div"))

                    if question and answer:
                        faqs.append({
                            "question":question,
                            "answer":answer,
                        })

        external_links = []
        application_url_candidate = None

        for link in response.css("main section a[href]"):
            href = link.attrib.get("href", "").strip()
            if not href:
                continue

            absolute_url = response.urljoin(href)
            parsed = urlparse(absolute_url)
            hostname = (parsed.hostname or "").lower()

            if parsed.scheme not in ("http","https"):
                continue

            if hostname == "schemesinindia.in" or hostname.endswith(".schemesinindia.in"):
                continue

            link_text = self.clean_text(link)

            external_links.append({
                "text":link_text, "url":absolute_url,
            })

            if application_url_candidate is None:
                application_url_candidate = absolute_url

        amount = next(
           ( value for label, value in key_facts.items()
            if "amount" in label.lower()
        ),
        None,
        )
        income_requirement = next(
            ( value for label,value in key_facts.items()
            if "income" in label.lower()
            ),
            None,
        )
        duration = next(
            (value for label,value in key_facts.items()
             if "duration" in label.lower()
             ),
             None,
         )
        yield {
            "source": "Schemes in India",
            "title": title,
            "description": description,
            "objective": None,
            "eligibility": eligibility,
            "documents_required": documents_required,
            "amount_text": amount,
            "income_requirement": income_requirement,
            "tenure": duration,
            "key_facts": key_facts,
            "faqs": faqs,
            "opening_date": None,
            "deadline": None,
            "application_url": None,
            "application_url_candidate": application_url_candidate,
            "external_links": external_links,
            "source_url": "https://schemesinindia.in/scholarships",
            "detail_url": response.url,
            "scraped_at": None,
        }




