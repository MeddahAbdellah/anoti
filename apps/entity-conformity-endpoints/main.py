from fastapi import FastAPI
from typing import List
import riskToArticle
import os
from pydantic import BaseModel
from nats.aio.client import Client as NATS
import json
from pymongo import MongoClient
from typing import Any
from bson import json_util

app = FastAPI()

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

# NATS connection setup
nats_url = os.getenv("NATS_SERVICE_DNS")

async def get_nats_client():
    nc = NATS()
    await nc.connect(nats_url)
    return nc

@app.on_event("startup")
async def startup_event():
    global nc
    nc = await get_nats_client()

class JurisprudenceRequest(BaseModel):
    companyName: str
    risk: str

@app.post("/jurisprudence")
async def jurisprudence(request: JurisprudenceRequest) -> Any:
    query = {"companyName": request.companyName, "risk": request.risk}

    documents = list(jurisCollection.find(query))
    if len(documents) > 0:
        return json.loads(json_util.dumps(documents))
    else:
        message = {"companyName": request.companyName, "risk": request.risk}
        await nc.publish("jurisprudence", json.dumps(message).encode())
        return "analyzing"

class ErepRequest(BaseModel):
    companyName: str
    risk: str

@app.post("/erep")
async def erep(request: ErepRequest) -> Any:
    query = {"companyName": request.companyName, "risk": request.risk}

    documents = list(erepCollection.find(query))
    if len(documents) > 0:
        return json.loads(json_util.dumps(documents))
    else:
        message = {"companyName": request.companyName, "risk": request.risk}
        await nc.publish("erep", json.dumps(message).encode())
        return "analyzing"

@app.get("/risks")
async def risks() -> List[str]:
    return list(riskToArticle.map.keys())

@app.get("/healthz")
async def healthz() -> str:
    return "ok"

@app.get("/readyz")
async def readiness() -> str:
    return "ok"
