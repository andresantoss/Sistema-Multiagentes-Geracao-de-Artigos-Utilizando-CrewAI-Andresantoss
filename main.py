from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel
# --- VOLTA A IMPORTAR ArticleOutput ---
from src.crew_factory import create_crew, ArticleOutput 

app = FastAPI(
    # --- Usa o Título e Descrição originais ---
    title="Sistema Multiagente para Geração de Artigos com CrewAI", 
    description="""Este projeto usa agentes de IA (CrewAI) para escrever artigos automaticamente. Você fornece um tópico através de uma interface web simples (Streamlit), o sistema pesquisa na API da Wikipedia para obter contexto e usa o Google Gemini para gerar um artigo de pelo menos 300 palavras, que é exibido diretamente na interface.

*(Esta API permite a interação programática com o sistema.)*

GitHub: [https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss](https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss)
""" 
)

# Modelo de Entrada (inalterado)
class TopicInput(BaseModel):
    topic: str

# Endpoint da API 
# --- Usa ArticleOutput como response_model ---
@app.post("/generate-article/", response_model=ArticleOutput) 
async def generate_article_endpoint(input: TopicInput):
    """
    Recebe um tópico e retorna um artigo de blog completo (estruturado como JSON) gerado pela CrewAI.
    """ # Docstring ajustado
    try:
        # create_crew agora retorna o objeto Pydantic ArticleOutput
        article_output = create_crew(input.topic) 
        return article_output
    except ValueError as ve: 
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e: 
        print(f"Erro inesperado no endpoint: {e}") 
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a requisição: {e}")

# Comandos de execução
# python -m uvicorn main:app --reload
# http://127.0.0.1:8000/docs