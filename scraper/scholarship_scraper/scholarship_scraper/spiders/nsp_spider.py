import scrapy
from datetime import datetime


class NspSpider(scrapy.Spider):

    name = "nsp"

    allowed_domains = [
        "scholarships.gov.in"
    ]

    start_urls = [
        "https://scholarships.gov.in/All-Scholarships"
    ]

    def parse_date(self, text):

        if not text:
            return None

        try:
            date_text = text.split(":")[-1].strip()

            return datetime.strptime(
                date_text,
                "%d-%m-%Y"
            ).strftime("%Y-%m-%d")

        except:
            return None

    def parse(self, response):

        sections = response.css(
            "#accordionExample > .accordion-item"
        )

        print("\nSECTIONS FOUND:", len(sections))

        for section in sections:

            scholarships = section.css(
                ".accordion-body > div.row.mb-4.border-1.border-bottom"
            )

            # Skip empty sections
            if not scholarships:
                continue

            section_name = section.css(
                ".accordion-header button"
            ).xpath("string(.)").get()

            if section_name:
                section_name = " ".join(
                    section_name.split()
                )

            print("\n==============================")
            print("SECTION:", section_name)
            print("==============================")

            print(
                "Scholarships found:",
                len(scholarships)
            )

            for scholarship in scholarships:

                # --------------------------------
                # TITLE
                # --------------------------------

                title = scholarship.css(
                    "h6::text"
                ).get()

                if title:
                    title = " ".join(
                        title.split()
                    )

                # --------------------------------
                # TIMELINE
                # --------------------------------

                spans = scholarship.css(
                    "span::text"
                ).getall()

                # --------------------------------
                # NORMALIZED DATES
                # --------------------------------

                scheme_open_date = None
                application_deadline = None
                defective_verification_deadline = None
                institute_verification_deadline = None
                dno_sno_mno_verification_deadline = None

                for timeline in spans:

                    timeline_clean = " ".join(
                        timeline.split()
                    )

                    if "Scheme Open from" in timeline_clean:

                        scheme_open_date = self.parse_date(
                            timeline_clean
                        )

                    elif "Student Application Open till" in timeline_clean:

                        application_deadline = self.parse_date(
                            timeline_clean
                        )

                    elif (
                        "Defective" in timeline_clean
                        and
                        "Verification Open till" in timeline_clean
                    ):

                        defective_verification_deadline = self.parse_date(
                            timeline_clean
                        )

                    elif "Institute Verification Open till" in timeline_clean:

                        institute_verification_deadline = self.parse_date(
                            timeline_clean
                        )

                    elif "DNO/SNO/MNO Verification Open till" in timeline_clean:

                        dno_sno_mno_verification_deadline = self.parse_date(
                            timeline_clean
                        )

                # --------------------------------
                # LINKS
                # --------------------------------

                links = scholarship.css("a")

                specifications_url = None
                faq_url = None

                for link in links:

                    href = link.attrib.get("href")
                    text = link.xpath(
                        "string(.)"
                    ).get()

                    if not href or not text:
                        continue

                    text = " ".join(
                        text.split()
                    ).lower()

                    # Clean whitespace
                    href = href.strip()

                    # Ignore missing/null links
                    if href.lower() in [
                        "null",
                        "none",
                        "#",
                        "javascript:void(0)"
                    ]:
                        full_url = None

                    else:
                        full_url = response.urljoin(href)

                    if "specification" in text:
                        specifications_url = full_url

                    elif "faq" in text:
                        faq_url = full_url

                # --------------------------------
                # OUTPUT
                # --------------------------------

                yield {
                    "source": "National Scholarship Portal",

                    "section": section_name,

                    "title": title,

                    # Original raw timeline
                    "timeline": spans,

                    # Normalized dates
                    "scheme_open_date": scheme_open_date,

                    "application_deadline": application_deadline,

                    "defective_verification_deadline":
                        defective_verification_deadline,

                    "institute_verification_deadline":
                        institute_verification_deadline,

                    "dno_sno_mno_verification_deadline":
                        dno_sno_mno_verification_deadline,

                    # Links
                    "specifications_url":
                        specifications_url,

                    "faq_url":
                        faq_url,

                    "source_url":
                        response.url,
                }