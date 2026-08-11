# Catalog Competitive Intelligence Data Pipeline (`/data_pipeline`)

## Overview

This module is built for Zepto's data engineering benchmarking process. It scrapes live product data from `books.toscrape.com`, cleans and validates all fields, converts prices using a fixed baseline INR conversion rate, loads the data into a normalized SQLite relational database, and executes benchmarking SQL queries along with pandas comparisons.

# Project Overview & Folder Structure


/data_pipeline
│

├── Capstone_project_module1.ipynb       # Main script (Scrape -> Clean -> Convert -> SQLite -> SQL Queries -> Pandas Merge)

├── data_base.db       	   				 # Generated SQLite relational database

├── requirements.txt       				 # Project dependencies

└── README.md              				 # Documentation and execution guide


### Requirements
- `Python 3.8+`
- `requests`
- `beautifulsoup4`
- `pandas`
- `numpy`

### Installation
!pip3 install requests beautifulsoup4 pandas numpy


### Execution
This project was build and tested in google colab notebook. So open the .ipynb file and execute it cell by cell.

### Strategy
The urls for each category with category name is passed as input in the code and fetched the data for 4 Categories and 80 book details from it.

### Currency Conversion Rate
Fixed Baseline Rate: 1 GBP = 105.50 INR

Specification: As per project guidelines, price_inr is derived via this exact fixed exchange rate (price_gbp * 105.50).

### Justification

Chosen Strategy: Median / Mode Imputation

Why Median Imputation for price_gbp?

Preserves Sample Size: Web scraping pipelines frequently encounter minor HTML variations or missing elements. Dropping rows reduces dataset size unnecessarily.

Robust Against Outliers: Real-world retail prices are often right-skewed (a few very expensive books can skew the mean). The median provides a stable, representative baseline for missing price estimates without distorting aggregate statistical metrics.

Why Mode Imputation for rating?

Star ratings are discrete ordinal numbers (1 to 5). Taking a continuous mean or median could yield non-integer values (e.g., 3.5). Assigning the mode (most frequent rating) keeps the column clean as a valid 1–5 integer.

When would Dropping Rows be preferred?

If a row is missing critical non-numeric identifiers (like title or category), imputation is not meaningful. In those rare edge cases, dropping the row (df.dropna(subset=['title'])) is the safer choice.