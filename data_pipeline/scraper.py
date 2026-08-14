import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import sqlite3
#print('everything works')
url="https://books.toscrape.com/"
response = requests.get(url)
print(response.status_code)
soup=BeautifulSoup(response.text,"html.parser")
category_links=soup.select('ul.nav-list ul li a')
all_books=[]
for link in category_links[:3]:
    category_name=link.text.strip()
    category_url=urljoin(url,link["href"])
    while category_url:
        category_response=requests.get(category_url)
        category_soup=BeautifulSoup(category_response.text,"html.parser")
        books=category_soup.find_all("article",class_="product_pod")
        for book in books:
            title= book.h3.a['title']
            price=book.find("p",class_="price_color").text.strip()
            availability_element=book.find("p",class_="availability")
            availability=availability_element.get_text(strip=True)
            rating_element=book.find("p",claass_="star-rating")
            if rating_element:
                rating=rating_element["class"][1]
            else:
                rating="unknown"
            all_books.append({"title":title,"category":category_name,"price":price,"availability":availability,"rating":rating})
        next_button=category_soup.select_one("li.next a")
        if next_button:
            category_url=urljoin(category_url,next_button["href"])
        else:
            category_url=None    
print("Total books:",len(all_books))   
df=pd.DataFrame(all_books)
df["price_gbp"]=(df["price"].str.replace("£","",regex=False).str.replace("Â","",regex=False).str.strip().astype(float))
#covert text to integer
rating_map={
    "One":1,"Two":2,"Three":3,"Four":4,"Five":5}
df["rating"]=df["rating"].map(rating_map)
#converting availability into boolean
df["in_stock"]=df["availability"].str.contains("In stock",case=False,na=False)
#Fixed project conversion rate
df["price_inr"]=df["price_gbp"]*105.50
print(df.head())
print(df.dtypes)
print("Rows:",len(df))
conn=sqlite3.connect("books.db")
cursor=conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price_gbp REAL,
    price_inr REAL,
    in_stock BOOLEAN,
    rating INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
)
""")

for category in df["category"].unique():
    cursor.execute("INSERT OR IGNORE INTO categories(category_name)VALUES(?)",(category,))
for _, row in df.iterrows():
    cursor.execute("SELECT category_id FROM categories WHERE category_name = ?",(row["category"],)   
    )
    category_id=cursor.fetchone()[0]
    cursor.execute("""INSERT INTO books(
    title,category_id,price_gbp,price_inr,in_stock ,rating)VALUES(?,?,?,?,?,?)""",
    (
        row["title"],
        category_id,
        row["price_gbp"],
        row["price_inr"],
        row["in_stock"],
        row["rating"]
    ))
conn.commit()
conn.close()
print("Database created successfully!")