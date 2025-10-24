from fastapi import FastAPI
from pydantic import BaseModel
from src.crew_factory import create_crew, ArticleOutput # Importe o Pydantic model

app = FastAPI(
    title="API Sistema Multiagente para Geração de Artigos com CrewAI",
    description="""Este projeto utiliza CrewAI para criar um sistema multiagente que gera artigos para websites. Os agentes usam a API da Wikipedia para pesquisa e contextualização antes de gerar o conteúdo.

## 🎯 Descrição

Este projeto é um sistema de automação de conteúdo que usa agentes de IA (CrewAI) para escrever artigos. O fluxo funciona da seguinte forma:

1.  Você fornece um **tópico** via API.
2.  Um agente pesquisa o tópico na **API da Wikipedia** para obter contexto relevante.
3.  Outro agente usa o **Google Gemini** para escrever um artigo coeso com no mínimo 300 palavras, baseado na pesquisa.
4.  O resultado final é retornado em formato **JSON**.

GitHub: https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss
"""
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