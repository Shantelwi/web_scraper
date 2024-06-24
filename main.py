#Import the necessary libraries

import pandas as pd
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup 
import csv
import html
from collections import Counter


#Specify the URL of the webpage you want to scrape

listing_url = "https://www.amazon.com/s?k=apple+watch&crid=26780829U6VL2&sprefix=applewa%2Caps%2C152&ref=nb_sb_ss_w_hit-vc-lth_apple-watch_k0_1_7"
url = "https://www.amazon.com/Apple-Smartwatch-Midnight-Aluminum-Detection/dp/B0CHXCXKPD/ref=sr_1_1_sspa?crid=26780829U6VL2&dib=eyJ2IjoiMSJ9._tZ6a_nFfBQwbV97vNcwAP5sZqfr-LMQw78ihB0YTyPg81kqqBKAu_xvhCLCDo8Zf5zbazP1Z1eQfcrGA7XmTAFioofwR3fcOO1xAiXq6hCQTbThPm2stQT88ajSFgXq88oOBNepc9JpSYKzWebkIRl9c5qp_UFFTLo6yObvFyVOdkqUBvB7hVpN34oxM1sE_AaGhL5eUSlM1DSw9F8JgTvbkcW1TRYE4cw-wOK_MLI.FY_PFZzpRtn3lAXTwbi-DEqwZo_CxX49MNvKQgJacFY&dib_tag=se&keywords=apple+watch&qid=1719251718&sprefix=applewa%2Caps%2C152&sr=8-1-spons&ufe=app_do%3Aamzn1.fos.9f2cdd2d-df47-45ac-9666-580d6bb0ee10&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1"
custom_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
    'accept-language': 'en-US,en;q=0.9'
}

#Send a HTTP request to the specified URL and save the response from server in a response object called r
def get_product_info(url):
    resp = requests.get(url, headers=custom_headers)

    soup = BeautifulSoup(resp.text, 'html.parser')

    title_element = soup.select_one('#productTitle')

    title = title_element.text.strip()

    rating_element = soup.select_one('#acrPopover')

    rating_text = rating_element.attrs.get('title')

    price_element = soup.select_one('span.a-price').select_one('span.a-offscreen')

    image_element = soup.select_one('#landingImage')

    image = image_element.attrs.get('src')

    description_element = soup.select_one('#feature-bullets')

    reviews_element = soup.select_one('div.review')

    scraped_reviews = []

    for review in reviews_element:
        r_author_element = review.select_one('span.a-profile-name')
        r_author = r_author_element.text if r_author_element else None

        r_rating_element = review.select_one('i.review-rating')
        r_rating = r_rating_element.text.replace("out of 5 stars", '')

        r_title_element = review.select_one('a.review_title')

        r_title_span_element = r_title_element.select_one("span:not([class])") if r_title_element else None
        r_title = r_title_span_element.text if r_title_span_element else None

        r_content_element = review.select_one('span.review-text')
        r_content = r_content_element.text if r_content_element else None

        r_date_element = review.select_one('span.review-date')
        r_date = r_date_element.text if r_date_element else None

        r_verified_element = review.select_one('span.a-size-mini')
        r_verified = r_verified_element.text if r_verified_element else None

        r = {
            "author": r_author,
            "rating": r_rating,
            "title": r_title,
            "content": r_content,
            "date": r_date,
            "verified": r_verified
        }

        scraped_reviews.append(r)

        product_info = {
            "Title": title,
            "Rating": rating_text,
            "Price": price_element.text,
            "Image URL": image,
            "Description": description_element.text,
            "Reviews": scraped_reviews
        }

        return product_info

def parse_listing(listing_url):
    resp = requests.get(listing_url,headers=custom_headers)
    soup_search = BeautifulSoup(resp.text, "html.parser")
    link_elements = soup_search.select('[data-asin] h2 a')
    page_data = []
    for link in link_elements:
        full_url = urljoin(listing_url, link.attrs.get("href"))
        product_info = get_product_info(full_url)
        page_data.append(product_info)

    next_page_el = soup_search.select_one('a:contains("Next")')
    if next_page_el:
        next_page_url = next_page_el.attrs.get('href')
        next_page_url = urljoin(listing_url,next_page_url)

    # df = pd.DataFrame(page_data)
    # df.to_json("applewatches.json", orient = 'records')

    with open("applewatches.csv", "w", newline="", encoding="utf-8") as file:
        fieldnames = ["Title", "Rating", "Price", "Image URL", "Description", "Reviews"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(page_data)

    df = pd.DataFrame(page_data)
    num_items = len(df)
    df["Price"] = df["Price"].replace('[\$,]', '', regex=True).astype(float)  # Use a raw string for the regular expression
    average_price = round(df["Price"].mean(), 2)
    all_keywords = " ".join(df["Description"]).split()
    keyword_frequency = Counter(all_keywords)  # Use the Counter class to count the frequency of keywords
    most_common_keywords = keyword_frequency.most_common(5)

    # Reporting
    report_html = "<html><body>"
    report_html += "<h1>Data Analysis Report</h1>"
    report_html += "<h2>Number of Items: " + str(num_items) + "</h2>"
    report_html += "<h2>Average Price: $" + str(average_price) + "</h2>"
    report_html += "<h2>Most Common Keywords in Descriptions:</h2>"
    report_html += "<ul>"
    for keyword, frequency in most_common_keywords:
        report_html += "<li>" + html.escape(keyword) + ": " + str(frequency) + "</li>"
    report_html += "</ul>"
    report_html += "</body></html>"

    # Save the HTML report to a file
    with open("report.html", "w", encoding="utf-8") as file:
        file.write(report_html)

parse_listing("https://www.amazon.com/s?k=apple+watch&crid=26780829U6VL2&sprefix=applewa%2Caps%2C152&ref=nb_sb_ss_w_hit-vc-lth_apple-watch_k0_1_7")






