from fastapi import FastAPI

app = FastAPI(title="Cake Shop")


@app.get("/health")
def health_check():
    return {"status": "ok"}