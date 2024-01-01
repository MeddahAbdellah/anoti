from fastapi import FastAPI, Body
from typing import List
import riskToArticle

app = FastAPI()

@app.get("/risks")
async def risks() -> List[str]:
    return list(riskToArticle.map.keys())

@app.get("/jurisprudence")
async def jurisprudence(text: str = Body(..., embed=True)) -> List[str]:
    return text

@app.get("/erep")
async def erep(text: str = Body(..., embed=True)) -> List[str]:
    return text

@app.get("/healthz")
async def healthz() -> str:
    return "ok"

@app.get("/readyz")
async def readiness() -> str:
    return "ok"
