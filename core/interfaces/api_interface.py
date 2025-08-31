from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.engine.context import ContextToken

app = FastAPI(title="M.O.N.I.T.O.R. API")

@app.middleware("http")
async def validate_context_token(request: Request, call_next):
    if request.url.path in ["/docs", "/openapi.json", "/"]:
        return await call_next(request)

    token = request.headers.get("X-Context-Token")
    if not token:
        return JSONResponse(status_code=400, content={"error": "Missing X-Context-Token header"})
    try:
        ContextToken.model_validate_json(token)
    except Exception as e:
        return JSONResponse(status_code=422, content={"error": f"Invalid ContextToken: {str(e)}"})
    return await call_next(request)

@app.get("/")
def root():
    return {"message": "M.O.N.I.T.O.R. backend operativo"}
