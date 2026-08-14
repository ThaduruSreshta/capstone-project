@"
# Data Pipeline – Q1
This folder contains the web scraping and database pipeline developed for Question 1 of the capstone project.
## Installation
Install the required Python packages using:
pip install requests beautifulsoup4 pandas
## Run
Run the scraper from the repository root:
python data_pipeline/scraper.py
The scraper collects book information from the Books to Scrape website and processes the extracted data.
The SQL/query workflow can be run using:
python data_pipeline/queries.py
## Parsing Decisions
- HTML pages are parsed using BeautifulSoup.
- Book titles, prices, availability, ratings, and other required fields are extracted from the relevant HTML elements.
- Pagination is handled to collect data across the required book listing pages.
- Rating text is converted into a consistent representation.
- Availability text is cleaned before storage.
- Price values are parsed into numeric values for analysis and database storage.
## Cleaning Decisions
- Missing or malformed HTML values are handled safely.
- Text fields are stripped of unnecessary whitespace.
- Price fields are converted from scraped text into numeric values.
- Availability values are normalized.
- Duplicate or invalid records are avoided before database insertion.
## Output
The pipeline stores the processed book data in the project database and provides SQL queries for validation and analysis.
"@ | Set-Content .\data_pipeline\README.md
