import spacy
from jurisAnalyze import jurisAnalyze
from erepAnalyze import erepAnalyze
import os
from kafka import KafkaConsumer
import json
import time

print("Conformity analyzer starting...")

nlp = spacy.load("fr_core_news_lg")

print("Loaded spacy model")

directory_of_script = os.path.dirname(os.path.abspath(__file__))
readyz_file_path = os.path.join(directory_of_script, 'readyz')

print("Creating readiness file...")

with open(readyz_file_path, "w") as file:
    file.write("ok")

print("Created readiness file")

kafka_sasl_password = os.getenv("KAFKA_SASL_PASSWORD")
kafka_sasl_user = os.getenv("KAFKA_SASL_USER")
kafka_service_dns = os.getenv("KAFKA_SERVICE_DNS")

print("Creating consumer...")

consumer = KafkaConsumer(
    group_id="entity-conformity-analyzer",
    bootstrap_servers=kafka_service_dns,
    security_protocol='SASL_PLAINTEXT',
    sasl_mechanism='PLAIN',
    sasl_plain_username=kafka_sasl_user,
    sasl_plain_password=kafka_sasl_password,
    enable_auto_commit=True
)

print("Created consumer:")
print(consumer)

consumer.subscribe(["jurisprudence", "erep"])

print("Subscribed to topics:")
print(consumer.topics())

for message in consumer:
    print("Received message:")
    print(message)
    topic = message.topic

    print("Topic:")
    print(topic)

    data = message.value.decode()
    parts = data.split(', ')
    companyName = parts[0].split(': ')[1]
    risk = parts[1].split(': ')[1]

    print("Analyzing message:")
    print(companyName)
    print(risk)
    output = None

    if topic == "jurisprudence":
        output = jurisAnalyze(companyName, risk, nlp)
        output_file = "juris.json"
    elif topic == "erep":
        output = erepAnalyze(companyName, risk)
        output_file = "erep.json"

    print("Finished analyzing")
    if output is not None:
        with open(output_file, "a") as file:
            json.dump(output, file)
            file.write("\n")

    time.sleep(5)
