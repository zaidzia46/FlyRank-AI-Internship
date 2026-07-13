from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Flyrank AI Intern"
    }

@app.get("/name")
def get_name():
    return {
        "name": "Muhammad Zaid Zia"
    }