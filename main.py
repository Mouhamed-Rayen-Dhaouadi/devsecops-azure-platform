from fastapi import FastAPI
import subprocess

app = FastAPI()
items = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/items")
def list_items():
    return items

@app.post("/items")
def add_items(name:str):
    items.append(name)
    return {"added" : name}
