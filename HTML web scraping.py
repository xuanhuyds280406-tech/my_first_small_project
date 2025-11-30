import httpx
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup

url = "https://books.toscrape.com/" # the main link
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
              "image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

# Send the request to the server
response = httpx.get(url, headers=headers, timeout=60)

# Parse HTML
tree = HTMLParser(response.text)

# Identify the location to get links of other kinds
links = tree.css("div.page_inner div.side_categories ul li a ")

# list of types' links and types' names
links_list = ["https://books.toscrape.com/" + link.attributes['href'] for link in links]
types_list = [link.text() for link in links]
type_link = {types_list[i].strip() : [links_list[i].strip()] for i in range(1, len(types_list))}
for type, link in type_link.items():
    #new_response = httpx.get(link, headers=headers, timeout=60)
    #new_tree = HTMLParser(new_response.text)
    link = link[0]
    try:
        while True:
            new_response = httpx.get(link, headers=headers, timeout=60)
            new_tree = HTMLParser(new_response.text)
            new_links = tree.css("li.next > a[\' href\']")
            new_link = link.replace('index.html', new_links[0].attributes['href'].strip())
            type_link[type].append(new_link.strip())
            link = new_link
    except:
        None

def get_book_data(book_url, type_book):
    data_response = httpx.get(book_url, headers = headers, timeout=60)
    data_tree = HTMLParser(data_response.text)
    data_rating = BeautifulSoup(data_response.text, "html.parser")

    # book's description
    data_node_description = data_tree.css("meta[name = \"description\"][content]")
    data_book_description = data_node_description[0].attributes["content"].strip()

    # book's title
    data_node_title = data_tree.css("article.product_page > div.row div.product_main > h1")
    data_book_title = data_node_title[0].text().strip()

    # book's price
    data_node_price = data_tree.css("article.product_page > div.row p.price_color")
    data_book_price = data_node_price[0].text().strip()

    # book's stock
    data_node_stock = data_tree.css("p.availability")
    data_book_stock_old = data_node_stock[0].text().strip()
    data_book_stock_new = int(data_book_stock_old[data_book_stock_old.find("(") + 1: data_book_stock_old.find("(") + 3])

    # book's rating
    data_node_rating_old = data_rating.select_one("article.product_page p.star-rating")
    data_node_rating_new = data_node_rating_old["class"]
    data_book_rating = data_node_rating_new[1].strip()

    # create a dict
    dct = {
        ' title': data_book_title,
        ' price': data_book_price, ' stock': data_book_stock_new,
        ' rating': data_book_rating, 'type': type_book
    }

    return dct

def get_book_link(type_url, type_book):
    summary_new = {}
    for type_url in type_url:
        type_response = httpx.get(type_url, headers = headers, timeout=60)
        type_tree = HTMLParser(type_response.text)
        type_node = type_tree.css("article.product_pod h3 > a")
        book_name = [i.text() for i in type_node]
        book_link = [i.attributes['href'].replace("../../../", "https://books.toscrape.com/catalogue/") for i in type_node]
        summary_old = {book_name[i] : book_link[i] for i in range(len(book_name))}
        for name, link in summary_old.items():
            summary_new[name] = get_book_data(link, type_book)
    return summary_new
# implement a loop
a = {}
for key, value in type_link.items():
    b = get_book_link(value, key)
    a = {**a,**b}
c = a.keys()
print(len(c))
for i in c:
    print(i, "   ", a[i]['type'])

