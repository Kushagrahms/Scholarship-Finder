import scrapy


class UgcSpider(scrapy.Spider):

    name = "ugc"

    allowed_domains = [
        "ugc.gov.in"
    ]

    start_urls = [
        "https://www.ugc.gov.in/Home/student_Corner"
    ]

    def parse(self, response):

        # Find ALL scholarship rows on the listing page.
        rows = response.css(
            "#v-pills-2022 table tbody tr"
        )

        print("\n================================")
        print("UGC SCHOLARSHIP SCRAPER")
        print("================================")
        print("Scholarship rows found:", len(rows))

        for row in rows:

            # Scholarship name
            title = row.css(
                "td:nth-child(2)::text"
            ).get()

            if title:
                title = " ".join(
                    title.split()
                )

            # Detail page URL
            href = row.css(
                "td:nth-child(3) a::attr(href)"
            ).get()

            if not href:
                continue

            detail_url = response.urljoin(href)

            print("\nScholarship:", title)
            print("Detail URL:", detail_url)

            # Follow the detail page automatically
            yield response.follow(
                detail_url,
                callback=self.parse_detail,
                meta={
                    "listing_title": title,
                    "detail_url": detail_url
                }
            )

    def parse_detail(self, response):

        listing_title = response.meta.get(
            "listing_title"
        )

        detail_url = response.meta.get(
            "detail_url"
        )

        print("\n--------------------------------")
        print("DETAIL PAGE")
        print("Title:", listing_title)
        print("--------------------------------")

        fields = {}

        # Find every label/value pair.
        label_containers = response.css(
            ".row.text-container.left-margin > .col-md-3.info"
        )

        for label_container in label_containers:

            # Get field label
            label = label_container.css(
                "span::text"
            ).get()

            if not label:
                continue

            label = " ".join(
                label.split()
            ).rstrip(":")

            # Find the value belonging to this label
            value_container = label_container.xpath(
                "following-sibling::div"
                "[contains(@class, 'col-md-9')][1]"
            )

            # string(.) gets text even when the value contains
            # <br>, <i>, <strong>, etc.
            value = value_container.xpath(
                "string(.)"
            ).get()

            if value:
                value = " ".join(
                    value.split()
                )

            # Convert the label into a predictable key
            field_key = label.lower()

            fields[field_key] = value

        # Create our standardized scholarship record
        yield {
            "source": "University Grants Commission",

            "title": fields.get(
                "name of the scheme",
                listing_title
            ),

            "objective": fields.get(
                "objective of scheme"
            ),

            "eligibility": fields.get(
                "eligibility"
            ),

            "slots": fields.get(
                "slots"
            ),

            "tenure": fields.get(
                "tenure"
            ),

            "financial_assistance": fields.get(
                "financial assistance"
            ),

            "remark": fields.get(
                "remark"
            ),

            "detail_url": detail_url,

            "source_url": response.url
        }