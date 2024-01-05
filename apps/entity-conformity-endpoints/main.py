from fastapi import FastAPI
from typing import List
import riskToArticle
import os
from pydantic import BaseModel
from nats.aio.client import Client as NATS
import json

app = FastAPI()

# NATS connection setup
nats_url = os.getenv("NATS_SERVICE_DNS")  # Replace with your NATS server URL

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
async def jurisprudence(request: JurisprudenceRequest) -> str:
    message = {"companyName": request.companyName, "risk": request.risk}
    await nc.publish("jurisprudence", json.dumps(message).encode())
    return "Message sent to NATS"

class ErepRequest(BaseModel):
    companyName: str
    risk: str

@app.post("/erep")
async def erep(request: ErepRequest) -> str:
    message = {"companyName": request.companyName, "risk": request.risk}
    await nc.publish("erep", json.dumps(message).encode())
    return "Message sent to NATS"

@app.get("/risks")
async def risks() -> List[str]:
    return list(riskToArticle.map.keys())

@app.get("/healthz")
async def healthz() -> str:
    return "ok"

@app.get("/readyz")
async def readiness() -> str:
    return "ok"
