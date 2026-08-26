from fastapi import FastAPI


app = FastAPI(
    title="OWASP LLM Top 10 RAG API",
    description="API local para consultar el OWASP Top 10 para aplicaciones con LLM.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Report whether the HTTP service is running."""
    return {"status": "ok"}
