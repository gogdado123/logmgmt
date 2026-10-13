from fastapi import FastAPI

app = FastAPI(title="Log Management Demo")

@app.get("/health")
def health():
    return {"status": "ok"}