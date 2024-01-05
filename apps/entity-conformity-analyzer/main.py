import spacy
from jurisAnalyze import jurisAnalyze
from erepAnalyze import erepAnalyze
import os
import json
import asyncio
from nats.aio.client import Client as NATS
from datetime import datetime


print("Conformity analyzer starting...")

nlp = spacy.load("fr_core_news_lg")

print("Loaded spacy model")

directory_of_script = os.path.dirname(os.path.abspath(__file__))
readyz_file_path = os.path.join(directory_of_script, 'readyz')

print("Creating readiness file...")

with open(readyz_file_path, "w") as file:
    file.write("ok")

print("Created readiness file")

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
        with open('juris.json', "a") as file:
            json.dump(output, file)
            file.write("\n")
        print(f"{datetime.now()} Finished: {msg.data.decode()}")
        global jurisSub
        jurisSub = await resubscribeJuris()

    async def erep_handler(msg):
        print(f"{datetime.now()} Starting: {msg.data.decode()}")
        data = json.loads(msg.data.decode())
        output = erepAnalyze(data['companyName'], data['risk'])
        with open('erep.json', "a") as file:
            json.dump(output, file)
            file.write("\n")
        print(f"{datetime.now()} Finished: {msg.data.decode()}")
        global erepSub
        erepSub = await resubscribeErep()

    jurisSub = await nats.subscribe("jurisprudence", queue="juris_group", cb=juris_handler)
    erepSub = await nats.subscribe("erep", queue="erep_group", cb=erep_handler)


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
loop.run_forever()