from fastapi import FastAPI
from typing import List
import riskToArticle
import os
from kafka import KafkaProducer
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic, NewPartitions
from kafka.errors import TopicAlreadyExistsError
from pydantic import BaseModel

kafka_sasl_password = os.getenv("KAFKA_SASL_PASSWORD")
kafka_sasl_user = os.getenv("KAFKA_SASL_USER")
kafka_service_dns = os.getenv("KAFKA_SERVICE_DNS")

admin_client = KafkaAdminClient(
    bootstrap_servers=kafka_service_dns,
    security_protocol='SASL_PLAINTEXT',
    sasl_mechanism='PLAIN',
    sasl_plain_username=kafka_sasl_user,
    sasl_plain_password=kafka_sasl_password
)

def create_or_update_topic(topic_name, num_partitions, replication_factor):
    print(f"Checking if topic '{topic_name}' exists...")
    existing_topics = admin_client.list_topics()
    if topic_name in existing_topics:
        print(f"Topic '{topic_name}' exists. Checking partitions...")
        topic_metadata = admin_client.describe_topics([topic_name])
        current_partitions = len(topic_metadata[0]['partitions'])
        if current_partitions < num_partitions:
            print(f"Updating topic '{topic_name}' to have {num_partitions} partitions...")
            additional_partitions = NewPartitions(total_count=num_partitions)
            admin_client.create_partitions(
                topic_partitions={topic_name: additional_partitions},
                validate_only=False
            )
            print(f"Partitions updated for topic '{topic_name}'.")
        else:
            print(f"No update needed. Topic '{topic_name}' already has the desired number of partitions.")
    else:
        try:
            print(f"Creating topic '{topic_name}' with {num_partitions} partitions...")
            topic_list = [NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)]
            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            print(f"Topic '{topic_name}' created.")
        except TopicAlreadyExistsError:
            print(f"Topic '{topic_name}' already exists. No action taken.")



print('Creating jurisprudence topic partitions...')
create_or_update_topic("jurisprudence", num_partitions=10, replication_factor=1)

print('Creating erep topic partitions...')
create_or_update_topic("erep", num_partitions=10, replication_factor=1)

app = FastAPI()

producer = KafkaProducer(
    bootstrap_servers=kafka_service_dns,
    security_protocol='SASL_PLAINTEXT',
    sasl_mechanism='PLAIN',
    sasl_plain_username=kafka_sasl_user,
    sasl_plain_password=kafka_sasl_password
)

@app.get("/risks")
async def risks() -> List[str]:
    return list(riskToArticle.map.keys())

class JurisprudenceRequest(BaseModel):
    companyName: str
    risk: str

@app.post("/jurisprudence")
async def jurisprudence(request: JurisprudenceRequest) -> str:
    message = f"Company: {request.companyName}, Risk: {request.risk}"
    producer.send("jurisprudence", value=message.encode())
    return "Message sent to the producer"

class ErepRequest(BaseModel):
    companyName: str
    risk: str

@app.get("/erep")
async def erep(request: ErepRequest) -> str:
    message = f"Company: {request.companyName}, Risk: {request.risk}"
    producer.send("erep", value=message.encode())
    return "Message sent to the producer"

@app.get("/healthz")
async def healthz() -> str:
    return "ok"

@app.get("/readyz")
async def readiness() -> str:
    return "ok"
