import spacy
from jurisAnalyze import jurisAnalyze
from erepAnalyze import erepAnalyze
import os

nlp = spacy.load("fr_core_news_lg")

directory_of_script = os.path.dirname(os.path.abspath(__file__))
readyz_file_path = os.path.join(directory_of_script, 'readyz')

with open(readyz_file_path, "w") as file:
    file.write("ok")

