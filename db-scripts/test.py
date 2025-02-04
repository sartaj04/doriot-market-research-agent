import requests

def fetch_funding_news():
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "funding OR acquisition OR IPO",
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": "b907a8dfb4e744cc978ff4c803b212bf"
    }
    response = requests.get(url, params=params)
    return response.json()

print(fetch_funding_news())


