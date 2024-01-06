import spacy
from jurisAnalyze import jurisAnalyze
from erepAnalyze import erepAnalyze
import os
import json
import asyncio
from nats.aio.client import Client as NATS
from datetime import datetime
from pymongo import MongoClient

print("Conformity analyzer starting...")

nlp = spacy.load("fr_core_news_lg")

print("Loaded spacy model")

directory_of_script = os.path.dirname(os.path.abspath(__file__))
readyz_file_path = os.path.join(directory_of_script, 'readyz')

print("Creating readiness file...")

with open(readyz_file_path, "w") as file:
    file.write("ok")

print("Created readiness file")

print("Connecting to Mongo...")

mongo_service_dns = os.getenv("MONGO_SERVICE_DNS")
mongo_user = os.getenv("MONGO_USER")
mongo_password = os.getenv("MONGO_PASSWORD")

print(f"Connecting to Mongo at {mongo_service_dns} with user {mongo_user} and password {mongo_password}")

client = MongoClient(f"mongodb://{mongo_user}:{mongo_password}@{mongo_service_dns}:27017/")
db = client['anoti']
jurisCollection = db['juris']
erepCollection = db['erep']
print(db.command("ping"))
print("Connected to Mongo")

nats_service_dns = os.getenv("NATS_SERVICE_DNS")

async def run():
    nats = NATS()

    await nats.connect(f"nats://{nats_service_dns}:4222")

    print("Connected to NATS")

    async def resubscribeJuris():
        await asyncio.sleep(1)
        return await nats.subscribe("jurisprudence", queue="juris_group", cb=juris_handler)

    async def resubscribeErep():
        await asyncio.sleep(1)
        return await nats.subscribe("erep", queue="erep_group", cb=erep_handler)

    async def juris_handler(msg):
        print(f"{datetime.now()} Starting: {msg.data.decode()}")
        data = json.loads(msg.data.decode())
        output = jurisAnalyze(data['companyName'], data['risk'], nlp)
        query = {"companyName": data['companyName'], "risk": data['risk']}
        new_data = {"$set": {"analysis": output}, "$setOnInsert": {"createdAt": datetime.now()}}
        jurisCollection.update_one(query, new_data, upsert=True)
        print(f"{datetime.now()} Finished: {msg.data.decode()}")
        status = { "topic": "jurisprudence", "companyName": data['companyName'], "risk": data['risk'], "status": "done" }
        await nats.publish("analysis_status", json.dumps(status).encode())
        global jurisSub
        jurisSub = await resubscribeJuris()

    async def erep_handler(msg):
        print(f"{datetime.now()} Starting: {msg.data.decode()}")
        print(f"{datetime.now()} Starting: {msg.data.decode()}")
        data = json.loads(msg.data.decode())
        status = { "topic": "erep", "companyName": data['companyName'], "risk": data['risk'], "status": "ongoing" }
        await nats.publish("analysis_status", json.dumps(status).encode())
        output = erepAnalyze(data['companyName'], data['risk'])
        query = {"companyName": data['companyName'], "risk": data['risk']}
        new_data = {"$set": {"analysis": output}, "$setOnInsert": {"createdAt": datetime.now()}}
        erepCollection.update_one(query, new_data, upsert=True)
        print(f"{datetime.now()} Finished: {msg.data.decode()}")
        status = { "topic": "erep", "companyName": data['companyName'], "risk": data['risk'], "status": "done" }
        await nats.publish("analysis_status", json.dumps(status).encode())
        global erepSub
        erepSub = await resubscribeErep()

    jurisSub = await nats.subscribe("jurisprudence", queue="juris_group", cb=juris_handler)
    erepSub = await nats.subscribe("erep", queue="erep_group", cb=erep_handler)


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
loop.run_forever()