import yfinance as yf
import pandas as pd

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import timedelta
from datetime import datetime, timedelta

import requests


symbol = "RELIANCE.NS"
start_date = "2023-01-01"
end_date = "2023-12-31"

# Fetch historical data
data = yf.download(symbol, start=start_date, end=end_date)

# Print the first few rows to verify
init_capital = 100000
print(data.head())


API_KEY = 'PK844AXXBJDO2YMPFDTK'
BASE_URL = 'https://data.alpaca.markets/v1beta1/news'

# Define the headers with your API key
headers = {
    'Apca-Api-Key-Id': API_KEY,
    'Apca-Api-Secret-Key': 'pedhi4YL6F2DQ0YCqKUnC4lmXPo5lomS4rE0hISE'
}

# Parameters for the request (example: getting news related to "AAPL" ticker)
params = {
    'symbols': 'AAPL',  # You can specify multiple symbols separated by commas
    'start': '2023-01-01T00:00:00Z',  # Start date for the news
    'end': '2023-06-30T00:00:00Z',    # End date for the news
    'limit': 50                       # Limit the number of news articles
}

# Make the request
response = requests.get(BASE_URL, headers=headers, params=params)

# Check if the request was successful
if response.status_code == 200:
    news_data = response.json()
    # Print the news articles
    for news in news_data['news']:
        print(f"Headline: {news['headline']}")
        print(f"Summary: {news['summary']}")
        print(f"Source: {news['source']}")
        print(f"Published At: {news['created_at']}")
        print('-' * 80)
else:
    print(f"Failed to fetch news. Status code: {response.status_code}")
    print(response.text)
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

def fetch_news(date):
    start_date = f"{date}T00:00:00Z"
    end_date = f"{date}T23:59:59Z"
    params = {
        'start': start_date,
        'end': end_date,
        'limit': 5  # Limit to top 5 news articles
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('news', [])
    else:
        print(f"Failed to fetch news for {date}. Status code: {response.status_code}")
        return []

# Function to analyze sentiment
def analyze_sentiment(news):
    scores = []
    for article in news:
        sentiment = sia.polarity_scores(article.get('headline', '') + ' ' + article.get('summary', ''))
        scores.append(sentiment['compound'])
    return sum(scores) / len(scores) if scores else 0

# Create a list to store the results
results = []

# Define start and end dates
start_date = datetime.strptime("2020-01-01", '%Y-%m-%d')
end_date = datetime.strptime("2023-12-31", '%Y-%m-%d')

# Fetch and analyze news for the specified date range
current_date = start_date
while current_date <= end_date:
    try:
        formatted_date = current_date.strftime('%Y-%m-%d')
        print(f"Processing date: {formatted_date}")  # Debugging output
        news = fetch_news(formatted_date)
        avg_sentiment = analyze_sentiment(news)
        results.append({'Date': formatted_date, 'Average Sentiment': avg_sentiment})
        current_date += timedelta(days=1)
        print(results)
         # Delay to avoid hitting rate limits
    except Exception as e:
        print(f"Error processing date {formatted_date}: {e}")
        current_date += timedelta(days=1)  # Ensure the loop progresses

# Convert the results list to a DataFrame
df = pd.DataFrame(results)


def generate_signals(data):
    data['signal'] = 0
    data['positions'] = 0
    buy_price = 0

    for i in range(1, len(data)):
        # Check if we should buy (signal 1)
        if data['signal'].iloc[i - 1] == 0:
            data.at[data.index[i], 'signal'] = 1  # Buy signal
            buy_price = data['Adj Close'].iloc[i]
        # Check if we should sell (signal -1)
        elif data['signal'].iloc[i - 1] == 1 and data['Adj Close'].iloc[i] >= buy_price * 1.05:
            data.at[data.index[i], 'signal'] = -1  # Sell signal
            buy_price = 0
        else:
            data.at[data.index[i], 'signal'] = data['signal'].iloc[i - 1]  # Hold position

    data['positions'] = data['signal'].diff()
    return data

def backtest(data, initial_capital=100000.0):
    positions = pd.DataFrame(index=data.index).fillna(0.0)
    positions['Position'] = 100 * data['signal']

    portfolio = positions.multiply(data['Adj Close'], axis=0)
    pos_diff = positions.diff()
    print(pos_diff.value_counts())

    portfolio['holdings'] = (positions.multiply(data['Adj Close'], axis=0)).sum(axis=1)
    portfolio['cash'] = initial_capital - (pos_diff.multiply(data['Adj Close'], axis=0)).sum(axis=1).cumsum()
    portfolio['total'] = portfolio['cash'] + portfolio['holdings']
    portfolio['returns'] = portfolio['total'].pct_change()

    return portfolio


def real_test(data, init_capital=100000.0):
    data['signal'] = 0
    data['positions'] = 0
    portfolio = pd.DataFrame(index=data.index).fillna(0.0)
    portfolio['cash'] = init_capital
    portfolio['holdings'] = 0.0
    portfolio['total'] = init_capital
    buy_price = data['Adj Close'].iloc[0]
    shares = 20
    data.at[data.index[0], 'signal'] = 1
    portfolio.at[portfolio.index[0], 'cash'] = init_capital - (shares * data['Adj Close'].iloc[0])
    portfolio.at[portfolio.index[0], 'holdings'] = shares * data['Adj Close'].iloc[0]
    portfolio.at[portfolio.index[0], 'total'] = portfolio.at[portfolio.index[0], 'cash'] + portfolio.at[
        portfolio.index[0], 'holdings']
    curr_shares = shares;
    for i in range(1, len(data)):
        if (curr_shares > 0 and df['Average Sentiment'].iloc[i] < -0.2):
            data.at[data.index[i], 'signal'] = -1
            portfolio.at[portfolio.index[i], 'cash'] = portfolio.at[portfolio.index[i - 1], 'cash'] + curr_shares * \
                                                       data['Adj Close'].iloc[i]
            portfolio.at[portfolio.index[i], 'holdings'] = 0
            curr_shares = 0
        elif df['Average Sentiment'].iloc[i] > 0.5 and portfolio.at[portfolio.index[i - 1], 'cash'] >= shares * \
                data['Adj Close'].iloc[i]:
            data.at[data.index[i], 'signal'] = 1
            curr_shares = curr_shares + shares
            portfolio.at[portfolio.index[i], 'holdings'] = curr_shares * data['Adj Close'].iloc[i]
            portfolio.at[portfolio.index[i], 'cash'] = portfolio.at[portfolio.index[i - 1], 'cash'] - shares * \
                                                       data['Adj Close'].iloc[i]

        else:
            data.at[data.index[i], 'signal'] = 0
            portfolio.at[portfolio.index[i], 'holdings'] = curr_shares * data['Adj Close'].iloc[i]
            portfolio.at[portfolio.index[i], 'cash'] = portfolio.at[portfolio.index[i - 1], 'cash']

        portfolio.at[portfolio.index[i], 'total'] = portfolio.at[portfolio.index[i], 'holdings'] + portfolio.at[
            portfolio.index[i], 'cash']

    return data, portfolio


data, portfolio = real_test(data)
print(portfolio.tail())
print(data['signal'].value_counts())

data = generate_signals(data)

# Backtest the strategy
portfolio = backtest(data)

# Print the portfolio and plot the results
print(portfolio.tail())
print(data['signal'].value_counts())