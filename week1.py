from fastapi import FastAPI

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