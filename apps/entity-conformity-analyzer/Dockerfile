FROM python:3.8
COPY . .
RUN pip install -r requirements.txt
RUN python -m spacy download fr_core_news_lg
WORKDIR /
ENTRYPOINT ["python"]
CMD ["main.py"]
