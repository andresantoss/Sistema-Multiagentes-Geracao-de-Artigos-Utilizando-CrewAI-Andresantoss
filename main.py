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
    crew_result = create_crew(input.topic) 
    # Extrai o objeto Pydantic de dentro do resultado da Crew
    article_output = crew_result.pydantic 
    return article_output

# Comando para rodar a API (execute no terminal):

# Ative o Ambiente Virtual Este é o passo mais importante. Para "ligar" o ambiente, execute o seguinte comando. (Note que a barra é invertida \ no Windows):
# venv\Scripts\activate

# Para Desativar: Quando terminar de trabalhar, basta digitar
# deactivate

# python -m uvicorn main:app --reload
# http://127.0.0.1:8000/docs