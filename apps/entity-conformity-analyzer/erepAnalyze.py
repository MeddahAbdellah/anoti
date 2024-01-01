import requests
import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import unquote
from fuzzywuzzy import fuzz

def get_article_content(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        return text
    except Exception as e:
        print(f"Error getting content from {url}: {e}")
        return ""

def is_relevant_article(url, company_name, threshold=70):
    article_content = get_article_content(url)
    if not article_content:
        return False
    match_score = fuzz.partial_ratio(company_name.lower(), article_content.lower())
    return match_score >= threshold

def process_link(link, company):
    href = link['href']
    if 'uddg=' in href:
        decoded_url = unquote(href.split('uddg=')[1])
        clean_url = decoded_url.split('&rut=')[0]
        if is_relevant_article(decoded_url, company):
            return clean_url
    return None

def company_to_web_articles_for_risk(company, risk):
    try:
        search_query = f"{company} {risk}"
        url = f"https://html.duckduckgo.com/html/?q={search_query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)

        soup = BeautifulSoup(response.text, 'html.parser')

        links = soup.find_all('a', attrs={'href': True})

        urls = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            urls = [url for url in executor.map(process_link, links, company) if url]

        return list(set(urls))
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def erep_for_entity_and_risk_pair(company, condemnation):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(company_to_web_articles_for_risk, company, f"{condemnation} {i}"): i for i in range(1, 6)}
        results = []
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                results.extend(future.result())
            except Exception as exc:
                print(f'Generated an exception: {exc}')
        return list(set(results))
    
def erepAnalyze(companyName, risk): 
    condemnations = erep_for_entity_and_risk_pair(companyName, risk)
    return condemnations