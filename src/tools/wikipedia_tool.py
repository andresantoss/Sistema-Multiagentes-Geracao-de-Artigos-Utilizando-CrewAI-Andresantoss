import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
import os  # Importa a biblioteca OS

class WikipediaSearchTool(BaseTool):
    name: str = "Wikipedia Search Tool"
    description: str = "Busca por um tópico na Wikipedia e retorna o extrato do artigo."

    def _run(self, topic: str) -> str:
        # Carrega as variáveis do .env AQUI, no início do método
        load_dotenv()
        # Pega o email usando o nome CORRETO da variável no .env
        user_email = os.getenv("WIKIPEDIA_USER_EMAIL") 
        
        # Define um email padrão caso não encontre no .env
        if not user_email:
            user_email = "default_agent@example.com" # Ou pode lançar um erro
            print("AVISO: Variável 'WIKIPEDIA_USER_EMAIL' não encontrada no .env. Usando email padrão.")

        # Monta os cabeçalhos AGORA, usando o email carregado
        headers = {
            # Usa uma f-string para inserir o email na string do User-Agent
            'User-Agent': f'CrewAIAgent/1.0 ({user_email})' 
        }

        url = "https://pt.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts",
            "exlimit": 1,
            "explaintext": 1,
            "titles": topic,
            "format": "json",
            "utf8": 1,
            "redirects": 1
        }

        try:
            # Passa os cabeçalhos corretamente
            response = requests.get(url, params=params, headers=headers) 
            response.raise_for_status() 
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return f"Erro: Nenhum resultado encontrado para '{topic}'."

            page_id = next(iter(pages))
            if page_id == "-1":
                 return f"Erro: Nenhum artigo da Wikipedia encontrado para o tópico '{topic}'."

            extract = pages[page_id].get("extract")

            if extract:
                return extract
            else:
                return f"Erro: Artigo encontrado para '{topic}', mas sem conteúdo (extrato)."

        except requests.exceptions.RequestException as e:
            return f"Erro ao acessar a API da Wikipedia: {e}" 
        except Exception as e:
            return f"Erro inesperado na ferramenta Wikipedia: {e}"