# ✅ Optional pip install comments (for README or user help)
# pip install --upgrade pip
# pip install beautifulsoup4 requests pandas numpy matplotlib tabulate
# python3 -m pip install --upgrade pip
# python3 -m pip install pandas numpy requests beautifulsoup4 matplotlib tabulate

import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from tabulate import tabulate

# ========== Directory Setup ==========
os.makedirs('./data', exist_ok=True)
os.makedirs('./output', exist_ok=True)
os.makedirs('./db', exist_ok=True)

# ========== Constants ==========
url = "https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks"
table_attribs = ["Name", "MC_USD_Billion"]
csv_path = './data/exchange_rate.csv'
output_csv = './data/Largest_banks_data.csv'
db_path = './db/Banks.db'
log_file_path = './output/code_log.txt'
chart_output_path = './output/top5_banks_chart.png'
table_name = "Largest_banks"
sql_connection = sqlite3.connect(db_path)

# ========== Logging ==========
def log_progress(message):
    """Logs progress messages with timestamps to a file and prints them."""
    timestamp_format = '%Y-%b-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{timestamp} : {message}\n")
    print(f"{timestamp} : {message}")

# ========== Extract ==========
def extract(url, table_attribs):
    """Scrape the largest banks table from Wikipedia."""
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    rows = soup.find_all('tbody')[0].find_all('tr')
    for row in rows:
        if row.find('td'):
            col = row.find_all('td')
            data = {
                "Name": col[1].text.strip(),
                "MC_USD_Billion": col[2].text.strip()
            }
            df1 = pd.DataFrame(data, index=[0])
            df = pd.concat([df, df1], ignore_index=True)
    return df

# ========== Transform ==========
def transform(df, csv_path):
    """Transform USD market cap into GBP, EUR, INR using exchange rates."""
    exchange_df = pd.read_csv(csv_path)
    rates = exchange_df.set_index('Currency').to_dict()['Rate']
    df['MC_USD_Billion'] = df['MC_USD_Billion'].str.replace(',', '').astype(float)
    df['MC_GBP_Billion'] = np.round(df['MC_USD_Billion'] * rates['GBP'], 2)
    df['MC_EUR_Billion'] = np.round(df['MC_USD_Billion'] * rates['EUR'], 2)
    df['MC_INR_Billion'] = np.round(df['MC_USD_Billion'] * rates['INR'], 2)
    return df

# ========== Load ==========
def load_to_csv(df, output_csv):
    """Save DataFrame to CSV."""
    df.to_csv(output_csv, index=False)
    print(f"✅ Data saved to CSV: {output_csv}")

def load_to_db(df, connection, table_name):
    """Save DataFrame to SQLite DB."""
    df.to_sql(table_name, connection, if_exists='replace', index=False)

# ========== Query ==========
def run_query(connection, query):
    """Run SQL query and print results."""
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"\n📌 Query: {query}")
    for row in results:
        print(row)
    return results

# ========== Visualization ==========
def visualize(df):
    """Generate and save a bar chart for top 5 banks."""
    top5 = df.sort_values(by='MC_USD_Billion', ascending=False).head(5)
    plt.figure(figsize=(10, 6))
    plt.bar(top5['Name'], top5['MC_USD_Billion'], color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Market Cap (USD Billion)")
    plt.title("Top 5 Banks by Market Cap (USD)")
    plt.tight_layout()
    plt.savefig(chart_output_path)
    plt.show()
    print(f"📊 Chart saved to: {chart_output_path}")

# ========== Table Formatter ==========
def print_table(df):
    """Prints the DataFrame in a fancy terminal table."""
    print("\n📋 Top 10 Banks (Formatted Table):\n")
    print(tabulate(df.head(10), headers='keys', tablefmt='fancy_grid', showindex=False))

# ========== Main ETL Pipeline ==========
log_progress('Preliminaries complete. Initiating ETL process')
df = extract(url, table_attribs)
print(df)

log_progress('Data extraction complete. Initiating transformation')
df = transform(df, csv_path)
print(df['MC_EUR_Billion'][4])
print_table(df)

log_progress('Transformation complete. Loading data to CSV & DB')
load_to_csv(df, output_csv)
load_to_db(df, sql_connection, table_name)
log_progress('Data saved successfully')

log_progress('Executing SQL queries')
run_query(sql_connection, "SELECT * FROM Largest_banks")
run_query(sql_connection, "SELECT AVG(MC_GBP_Billion) FROM Largest_banks")
run_query(sql_connection, "SELECT Name FROM Largest_banks LIMIT 5")

log_progress('Generating chart')
visualize(df)

log_progress('ETL Process Complete ✅')
sql_connection.close()
