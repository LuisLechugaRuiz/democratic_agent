import requests

def get_pib_of_spain(year: int) -> float:
    """
    Get the PIB of Spain in a given year.

    Args:
        year (int): The year for which to get the PIB.

    Returns:
        float: The PIB of Spain in the given year.
    """
    url = f"http://api.worldbank.org/v2/country/esp/indicator/NY.GDP.MKTP.CD?date={year}&format=json"
    response = requests.get(url)
    data = response.json()
    pib = data[1][0]['value']
    return pib
