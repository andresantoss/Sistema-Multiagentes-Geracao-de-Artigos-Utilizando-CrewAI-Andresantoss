import requests
from crewai.tools import BaseTool

class WikipediaSearchTool(BaseTool):
    name: str = "Wikipedia Search Tool"
    description: str = "Busca por um tópico na Wikipedia e retorna o extrato do artigo."

    def _run(self, topic: str) -> str:
        # URL da API da Wikipedia em português 
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
            response = requests.get(url, params=params)
            response.raise_for_status()  # Verifica se houve erros HTTP
            data = response.json()
            
            # Navega pela estrutura JSON para encontrar o extrato
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return f"Erro: Nenhum resultado encontrado para '{topic}'."
                
            # Pega o ID da primeira página (já que pedimos exlimit=1)
            page_id = next(iter(pages))
            extract = pages[page_id].get("extract")
            
            if extract:
                return extract
            else:
                return f"Erro: Artigo encontrado para '{topic}', mas sem conteúdo (extrato)."

        except requests.exceptions.RequestException as e:
            return f"Erro ao acessar a API da Wikipedia: {e}"