from fastapi import FastAPI
from pydantic import BaseModel
from src.crew_factory import create_crew, ArticleOutput # Importe o Pydantic model

app = FastAPI(
    title="API de Geração de Artigos com CrewAI",
    description="Uma API que usa um sistema multiagente para escrever artigos baseados em tópicos."
)

# Modelo Pydantic para a requisição da API
class TopicInput(BaseModel):
    topic: str

# Endpoint da API 
@app.post("/generate-article/", response_model=ArticleOutput)
async def generate_article_endpoint(input: TopicInput):
    """
    Recebe um tópico e retorna um artigo completo gerado pela CrewAI.
    """
    # A função create_crew já retorna o objeto Pydantic
    # que o FastAPI converterá automaticamente em JSON.
    result = create_crew(input.topic)
    return result

# Comando para rodar a API (execute no terminal):
# uvicorn main:app --reload
# http://127.0.0.1:8000/docs