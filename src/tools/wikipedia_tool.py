import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
import os 
import re 
import json 

class WikipediaSearchTool(BaseTool):
    """
    Ferramenta para buscar na API da Wikipedia.
    Tenta busca exata; se falhar, faz busca ampla (full-text).
    Retorna um JSON string contendo o extrato, título da fonte, URL da imagem e legenda.
    """
    name: str = "Wikipedia Search Tool"
    description: str = ("Busca por um tópico na Wikipedia. Retorna um JSON string com o extrato do artigo, "
                      "o título da fonte, a URL da imagem principal e uma legenda para a imagem.")

    def _fetch_wikipedia_data(self, search_title: str, headers: dict) -> tuple[dict | None, str | None]:
        """
        Tenta buscar o extrato E a imagem principal (thumbnail) de um título específico.
        Retorna um dicionário com os dados ou None, e uma mensagem de erro (se houver).
        """
        url = "https://pt.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts|pageimages", # PEDE EXTRATO E IMAGEM
            "piprop": "thumbnail",        # Pede um thumbnail (web-friendly, ex: .jpg, .png)
            "pithumbsize": 600,           # Pede um thumbnail com 600px de largura
            "exlimit": 1,
            "explaintext": 1,
            "titles": search_title,
            "format": "json",
            "utf8": 1,
            "redirects": 1
        }
        try:
            response = requests.get(url, params=params, headers=headers) 
            response.raise_for_status() 
            data = response.json()
            pages = data.get("query", {}).get("pages", {})

            if not pages: 
                return None, f"Erro interno da API: Nenhuma 'page' retornada para '{search_title}'."

            page_id = next(iter(pages))
            if page_id == "-1": 
                return None, None # Título exato não encontrado

            page_data = pages[page_id]
            extract = page_data.get("extract") 
            
            if not extract: 
                return None, f"Erro: Artigo exato '{search_title}' encontrado, mas sem conteúdo (extrato)."

            # --- CORREÇÃO DE IMAGEM ---
            # Extrai informações da imagem (agora do 'thumbnail')
            image_url = page_data.get("thumbnail", {}).get("source")
            # --- FIM DA CORREÇÃO ---
            
            # Usa o nome do 'pageimage' (ex: Ficheiro:...) como legenda
            image_caption = page_data.get("pageimage") 

            return {
                "source_title": search_title,
                "extract": extract,
                "image_url": image_url,
                "image_caption": image_caption
            }, None # Sucesso

        except requests.exceptions.RequestException as e: 
            return None, f"Erro de rede ao buscar extrato/imagem: {e}"
        except Exception as e: 
            return None, f"Erro inesperado ao buscar extrato/imagem: {e}"

    def _perform_full_text_search(self, search_term: str, headers: dict) -> tuple[str | None, str | None, str | None]:
        """Realiza uma busca ampla e retorna o título e snippet do resultado mais relevante."""
        url = "https://pt.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_term,
            "srlimit": 1,         
            "srprop": "snippet",  
            "format": "json",
            "utf8": 1
        }
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            search_results = data.get("query", {}).get("search")
            if search_results:
                top_result = search_results[0]
                title = top_result.get("title")
                snippet = top_result.get("snippet")
                return title, snippet, None 
            else:
                return None, None, None # Nenhum resultado
        except requests.exceptions.RequestException as e:
             return None, None, f"Erro de rede ao realizar busca ampla na Wikipedia: {e}"
        except Exception as e:
            return None, None, f"Erro inesperado na busca ampla: {e}"

    # --- MÉTODO PRINCIPAL _run ---
    def _run(self, topic: str) -> str:
        load_dotenv()
        contact_info = os.getenv("WIKIPEDIA_CONTACT_INFO") 
        if not contact_info:
            contact_info = "https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss" 
        headers = {'User-Agent': f'CrewAIAgent/1.0 ({contact_info})'}
        
        output_data = {} 

        # 1. Tenta busca exata
        data_dict, error = self._fetch_wikipedia_data(topic, headers)
        
        if data_dict:
            output_data = data_dict
        elif error and "sem conteúdo" not in error: 
              return json.dumps({"error": error}) 
              
        # 2. Se a busca exata falhou, faz busca ampla
        else:
            found_title, found_snippet, search_error = self._perform_full_text_search(topic, headers)
            
            if search_error: return json.dumps({"error": search_error})             
            if not found_title: 
                return json.dumps({"error": f"A pesquisa ampla na Wikipedia não encontrou artigos relevantes para '{topic}'."})

            # 3. Tenta buscar extrato E IMAGEM do título encontrado
            data_dict_found, final_error = self._fetch_wikipedia_data(found_title, headers) 

            if data_dict_found:
                output_data = data_dict_found
            else:
                # Fallback: Usa o snippet (sem imagem)
                clean_snippet = re.sub('<[^<]+?>', '', found_snippet or "") 
                output_data = {
                    "source_title": found_title,
                    "extract": f"...{clean_snippet}...",
                    "image_url": None,
                    "image_caption": "Snippet da Busca (sem imagem)"
                }
                if final_error:
                    # Log silencioso no console do servidor, não retorna ao agente
                    print(f"AVISO: Falha ao buscar extrato/imagem de '{found_title}': {final_error}. Usando snippet.")
        
        return json.dumps(output_data, ensure_ascii=False)