import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
import os 
import re 

class WikipediaSearchTool(BaseTool):
    """
    Uma ferramenta CrewAI para buscar extratos de artigos na API da Wikipedia em português.
    Implementa uma lógica de fallback: tenta buscar pelo título exato, 
    se falhar, realiza uma busca textual ampla e tenta obter o extrato do resultado mais relevante.
    Retorna o extrato prefixado com o título da fonte encontrada ou uma mensagem de erro/status.
    """
    name: str = "Wikipedia Search Tool"
    description: str = ("Busca por um tópico na Wikipedia. Se o tópico exato não for encontrado, "
                      "realiza uma busca mais ampla por termos relacionados e retorna o extrato do artigo mais relevante encontrado, "
                      "prefixado com o título da fonte encontrada.")

    def _run(self, topic: str) -> str:
        """
        Executa a lógica de busca na Wikipedia.

        Args:
            topic: O tópico a ser pesquisado.

        Returns:
            Uma string contendo o extrato do artigo encontrado (prefixado com a fonte) 
            ou uma mensagem indicando falha na busca.
        """
        # Carrega informações de contato do .env para o User-Agent
        load_dotenv()
        contact_info = os.getenv("WIKIPEDIA_CONTACT_INFO") 
        if not contact_info:
            # Fallback para URL do repositório se variável não definida
            contact_info = "https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss" 
        headers = {'User-Agent': f'CrewAIAgent/1.0 ({contact_info})'} # Conforme política da Wikimedia
        
        base_url = "https://pt.wikipedia.org/w/api.php"
        
        # --- 1. Tentativa de Busca Exata (action=query, prop=extracts) ---
        print(f"INFO: Tentando busca exata por '{topic}'...")
        params_extract = {
            "action": "query",          # Tipo de ação: consulta
            "prop": "extracts",       # Propriedade a obter: extrato do conteúdo
            "exlimit": 1,             # Limitar a 1 extrato
            "explaintext": 1,         # Obter como texto puro
            "titles": topic,          # Título exato a buscar
            "format": "json",         # Formato da resposta
            "utf8": 1,                # Usar UTF-8
            "redirects": 1            # Seguir redirecionamentos automaticamente
        }
        try:
            response_extract = requests.get(base_url, params=params_extract, headers=headers) 
            response_extract.raise_for_status() # Lança exceção para erros HTTP (4xx, 5xx)
            data_extract = response_extract.json()
            pages_extract = data_extract.get("query", {}).get("pages", {})

            if pages_extract: 
                page_id_extract = next(iter(pages_extract)) # Pega o ID da primeira (e única) página retornada
                if page_id_extract != "-1": # ID "-1" significa que a página não foi encontrada
                    extract = pages_extract[page_id_extract].get("extract") 
                    if extract: 
                        print(f"INFO: Busca exata por '{topic}' bem-sucedida.")
                        # Retorna formatado com a fonte
                        return f"(Fonte Wikipedia: '{topic}')\n\n{extract}"
                    else:
                        # Artigo encontrado mas vazio, prossegue para busca ampla
                        print(f"INFO: Artigo exato '{topic}' encontrado, mas sem conteúdo. Prosseguindo para busca ampla...")
                # else: Título exato não encontrado, prossegue para busca ampla
            # else: Estrutura 'pages' inesperadamente ausente, prossegue para busca ampla (como falha)

        except requests.exceptions.RequestException as e: 
            # Erro de rede na primeira tentativa, retorna erro
            return f"Erro de rede ao tentar busca exata: {e}"
        except Exception as e: 
             # Outro erro na primeira tentativa, retorna erro
            return f"Erro inesperado na busca exata: {e}"

        # --- 2. Busca Ampla (action=query, list=search) ---
        # Executada como fallback se a busca exata falhou
        print(f"INFO: Tópico exato '{topic}' não encontrado ou vazio. Realizando busca ampla...")
        params_search = {
            "action": "query",          # Tipo de ação: consulta
            "list": "search",         # Sub-ação: realizar busca textual
            "srsearch": topic,        # Termo para a busca ampla
            "srlimit": 1,             # Limitar a 1 resultado (o mais relevante)
            "srprop": "snippet",      # Incluir um snippet do resultado
            "format": "json",         # Formato da resposta
            "utf8": 1                 # Usar UTF-8
        }
        found_title = None
        found_snippet = None
        try:
            response_search = requests.get(base_url, params=params_search, headers=headers)
            response_search.raise_for_status()
            data_search = response_search.json()
            search_results = data_search.get("query", {}).get("search")
            if search_results:
                top_result = search_results[0]
                found_title = top_result.get("title")
                found_snippet = top_result.get("snippet")
            else:
                # Busca ampla não retornou resultados
                return f"A pesquisa ampla na Wikipedia não encontrou artigos relevantes para '{topic}'."
        except requests.exceptions.RequestException as e:
             return f"Erro de rede ao realizar busca ampla na Wikipedia: {e}"
        except Exception as e:
            return f"Erro inesperado na busca ampla: {e}"

        # --- 3. Busca do Extrato do Resultado da Busca Ampla ---
        if found_title:
            print(f"INFO: Busca ampla encontrou '{found_title}'. Tentando buscar extrato completo...")
            # Reutiliza params_extract, alterando apenas 'titles'
            params_extract_found = params_extract.copy()
            params_extract_found["titles"] = found_title
            
            try: 
                response_extract_found = requests.get(base_url, params=params_extract_found, headers=headers) 
                response_extract_found.raise_for_status() 
                data_extract_found = response_extract_found.json()
                pages_extract_found = data_extract_found.get("query", {}).get("pages", {})

                if pages_extract_found: 
                    page_id_extract_found = next(iter(pages_extract_found))
                    if page_id_extract_found != "-1":
                        extract_found = pages_extract_found[page_id_extract_found].get("extract") 
                        if extract_found: 
                            print(f"INFO: Extrato completo para '{found_title}' obtido com sucesso.")
                            # Retorna extrato formatado com a fonte encontrada na busca
                            return f"(Fonte Wikipedia: '{found_title}')\n\n{extract_found}"
                
                # Se chegou aqui, a busca pelo extrato do título encontrado falhou ou retornou vazio. Usa o snippet.

            except requests.exceptions.RequestException as e:
                 print(f"AVISO: Erro de rede ao buscar extrato de '{found_title}': {e}. Retornando snippet.")
            except Exception as e:
                 print(f"AVISO: Erro inesperado ao buscar extrato de '{found_title}': {e}. Retornando snippet.")

            # --- Fallback: Retorna o snippet da busca ampla ---
            print(f"AVISO: Não foi possível obter extrato completo de '{found_title}'. Retornando snippet da busca.")
            if found_snippet:
                # Limpeza básica de tags HTML do snippet
                clean_snippet = re.sub('<[^<]+?>', '', found_snippet) 
                # Retorna snippet formatado com a fonte encontrada na busca
                return f"(Fonte Wikipedia (Snippet da Busca): '{found_title}')\n\n...{clean_snippet}..."
            else:
                 # Caso raro: Título encontrado, mas sem snippet e sem extrato.
                 return f"A pesquisa ampla na Wikipedia encontrou o artigo '{found_title}', mas não foi possível obter seu conteúdo (extrato ou snippet)."

        # Se a busca ampla não retornou erro, mas não encontrou 'found_title'.
        return f"Erro inesperado: A busca ampla por '{topic}' não produziu resultados nem erros claros."