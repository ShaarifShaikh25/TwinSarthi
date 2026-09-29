
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "POLAR-TWIN Backend Running"}

@app.post("/predict")
def predict(data: dict):
    return {"prediction": "healthy"}
