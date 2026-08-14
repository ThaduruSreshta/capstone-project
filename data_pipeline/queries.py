import sqlite3
conn =sqlite3.connect("books.db")
cursor =conn.cursor()
#filter books with price greater than £30
cursor.execute("""
SELECT title, price_gbp
FROM books
WHERE price_gbp>30""") 
print("\n1.Books costing greater than £30  ")
for row in cursor.fetchall():
    print(row)
#2.Aggregate :average price
cursor.execute("""
SELECT AVG (price_gbp)
FROM books
""")  
print("\n2.Average price")
print(cursor.fetchone()[0])
#3. GROUP BY: number of books in each category
cursor.execute("""
SELECT c.category_name,COUNT(b.book_id)
FROM categories c
JOIN books b 
ON c.category_id=b.category_id
GROUP BY c.category_name""")
print("\n3.books per category:")
for row in cursor.fetchall():
    print(row)
#4. ORDER BY :most espensive books 
cursor.execute("""
SELECT title ,price_gbp
FROM books
ORDER BY price_gbp DESC
LIMIT 10""")
print("\n4.Most expensive books:")
for row in cursor.fetchall():
    print(row)
#5.JOIN:books with their categories
cursor.execute("""
SELECT b.title, c.category_name,b.price_gbp
FROM books b 
JOIN categories c 
ON b.category_id=c.category_id
LIMIT 10""")
print("\n5.Books with categories:")
for row in cursor.fetchall():
    print(row)
conn.close()