from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest
import numpy as np

app = FastAPI()
model = IsolationForest()
model.fit(np.random.randn(100, 3))  # Dummy fit

class Handshake(BaseModel):
    features: list

@app.post("/detect")
def detect(hs: Handshake):
    score = model.decision_function([hs.features])[0]
    return {"anomaly_score": float(score)}
