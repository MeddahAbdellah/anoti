import riskToArticle
import requests
import concurrent.futures
from fuzzywuzzy import fuzz

def condemnations_for_article(name, article):
    page = 0
    pageSize = 10
    searchQuery = f"https://api.piste.gouv.fr/cassation/judilibre/v1.0/search?query={name},{article}&resolve_references=true&page={0 if page is None else page}&page_size={10 if pageSize is None else pageSize}&operator=and"

    response = requests.get(
        searchQuery,
        headers={"KeyId": "36ddcb98-9be4-409a-a42f-12818c51699a"}
    )
    return response.json().get('results', [])


def condemnations_for_entity_and_risk_pair(entityName, risk):
    articles = riskToArticle.map[risk]
    condemnations = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_article = {executor.submit(condemnations_for_article, entityName, article): article for article in articles}
        for future in concurrent.futures.as_completed(future_to_article):
            article = future_to_article[future]
            try:
                data = future.result()
                condemnations.extend(data)
            except Exception as exc:
                print(f"{article} generated an exception: {exc}")
    return condemnations

def is_fuzzy_match_entity(text, company_name, nlp, threshold=80):
    doc = nlp(text)
    entities = [ent.text.encode('unicode_escape').decode().replace('"', "'") 
            for ent in doc.ents if ent.label_ == "ORG"]
    return any(fuzz.partial_ratio(entity.lower(), company_name.lower()) >= threshold for entity in entities)

def is_article_present(article, text):
    cleaned_article = article.replace('.', '').replace(',', '').replace(' ', '')
    cleaned_text = text.replace('.', '').replace(',', '').replace(' ', '')
    return cleaned_article.lower() in cleaned_text.lower()

def condemnation_to_detailed(condemnation):
    url = f"https://api.piste.gouv.fr/cassation/judilibre/v1.0/decision?id={condemnation['id']}&resolve_references=true"
    headers = {"KeyId": "36ddcb98-9be4-409a-a42f-12818c51699a"}

    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
    
def process_details(condemnation, company_name, articles, nlp):
    try:
        data = condemnation.result()
        text = data.get('text', '')
        if is_fuzzy_match_entity(text, company_name, nlp) and any(is_article_present(article, text) for article in articles):
            return data
    except Exception as exc:
        print(f"{condemnation['id']} generated an exception: {exc}")
    return None

def condemnations_to_detailed(condemnations, company_name, risk, nlp):
    articles = riskToArticle.map[risk]
    condemnations_detailed = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_condemnation = {executor.submit(condemnation_to_detailed, condemnation): condemnation for condemnation in condemnations}
        futures = [executor.submit(process_details, future, company_name, articles, nlp) for future in future_to_condemnation.keys()]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                condemnations_detailed.append(result)
    return condemnations_detailed



def jurisAnalyze(companyName, risk, nlp): 
    cons = condemnations_for_entity_and_risk_pair(companyName, risk)
    result = condemnations_to_detailed(cons, companyName, risk, nlp)
    return result