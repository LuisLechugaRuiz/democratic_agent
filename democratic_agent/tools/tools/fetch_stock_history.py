import yfinance as yf

def fetch_stock_history(ticker: str, start_date: str, end_date: str):
    """
    Fetch the historical stock data of a specific company.

    Args:
        ticker (str): The ticker symbol of the company.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
        pandas.DataFrame: A DataFrame containing the historical stock data.
    """
    # Fetch the data
    data = yf.download(ticker, start=start_date, end=end_date)

    return data
