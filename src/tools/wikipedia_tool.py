import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
import os
import re

class WikipediaSearchTool(BaseTool):
    """
    Ferramenta CrewAI para buscar conteúdo na Wikipédia em português.

    Comportamento:
    1. Tenta obter o extrato (extracts) do artigo com título exato.
    2. Se não encontrar, realiza busca textual (search) e pega o título mais relevante.
    3. Tenta obter o extrato do título encontrado; se falhar, retorna o snippet (limpo de HTML).
    4. Em todos os retornos bem-sucedidos, prefixa com "(Fonte Wikipedia: 'Título')".

    Observações:
    - Usa variável de ambiente WIKIPEDIA_CONTACT_INFO para o User-Agent (recomendado pela API).
    - Retorna mensagens de erro legíveis quando há falha de rede ou resultado vazio.
    """

    name: str = "Wikipedia Search Tool"
    description: str = (
        "Busca por um tópico na Wikipedia (pt). Primeiro tenta título exato; "
        "se não, faz busca textual e retorna o extrato/snippet do resultado top."
    )

    def _run(self, topic: str) -> str:
        """
        Executa a busca na API da Wikipédia (pt).

        Args:
            topic (str): termo ou título a ser pesquisado. Ex.: "Inteligência Artificial"

        Returns:
            str: texto com o extrato encontrado prefixado com a fonte, ou mensagem de erro/estado.
        """
        load_dotenv()
        contact_info = os.getenv("WIKIPEDIA_CONTACT_INFO")
        if not contact_info:
            # Fallback para identificar o agente nas requisições (recomendado pela Wikipédia)
            contact_info = "https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss"
        headers = {'User-Agent': f'CrewAIAgent/1.0 ({contact_info})'}

        base_url = "https://pt.wikipedia.org/w/api.php"

        # --- 1) Tentativa de obter extrato por título exato ---
        # params_extract: parâmetros para a chamada action=query&prop=extracts
        params_extract = {
            "action": "query",  # Ação: consulta de páginas.
            "prop": "extracts", # Propriedade: extrato do conteúdo da página.
            "exlimit": 1,       # Limita número de extratos retornados.
            "explaintext": 1,   # retorna texto limpo (sem HTML)
            "titles": topic,    # título exato a procurar
            "format": "json",   # formato de resposta
            "utf8": 1,          # garante codificação UTF-8
            "redirects": 1,     # segue redirecionamentos automaticamente
        }
        try:
            response_extract = requests.get(base_url, params=params_extract, headers=headers, timeout=10)
            response_extract.raise_for_status()
            data_extract = response_extract.json()
            pages_extract = data_extract.get("query", {}).get("pages", {})

            # pages é um dict onde a chave é o pageid; se pageid == "-1" => não encontrado
            if pages_extract:
                page_id_extract = next(iter(pages_extract))
                if page_id_extract != "-1":
                    extract = pages_extract[page_id_extract].get("extract")
                    # Se há extrato, devolve com prefixo de fonte (título usado: topic)
                    if extract:
                        return f"(Fonte Wikipedia: '{topic}')\n\n{extract}"
                    # Se não há extract (página sem conteúdo), continua para busca ampla
        except requests.exceptions.RequestException as e:
            # Erro de rede; devolve mensagem clara para o agente/usuário
            return f"Erro de rede ao tentar busca exata: {e}"
        except Exception as e:
            return f"Erro inesperado na busca exata: {e}"

        # --- 2) Busca ampla via lista de busca (search) ---
        params_search = {
            "action": "query",
            "list": "search",
            "srsearch": topic,
            "srlimit": 1,
            "srprop": "snippet",
            "format": "json",
            "utf8": 1,
        }

        found_title = None
        found_snippet = None
        try:
            response_search = requests.get(base_url, params=params_search, headers=headers, timeout=10)
            response_search.raise_for_status()
            data_search = response_search.json()
            search_results = data_search.get("query", {}).get("search")
            if search_results:
                top_result = search_results[0]
                found_title = top_result.get("title")
                found_snippet = top_result.get("snippet")  # contém HTML (<span> etc.)
            else:
                # Nenhum resultado relevante encontrado
                return f"A pesquisa ampla na Wikipedia não encontrou artigos relevantes para '{topic}'."
        except requests.exceptions.RequestException as e:
            return f"Erro de rede ao realizar busca ampla na Wikipedia: {e}"
        except Exception as e:
            return f"Erro inesperado na busca ampla: {e}"

        # --- 3) Tenta extrair o conteúdo do título encontrado na busca ampla ---
        if found_title:
            params_extract_found = params_extract.copy()
            params_extract_found["titles"] = found_title

            try:
                response_extract_found = requests.get(base_url, params=params_extract_found, headers=headers, timeout=10)
                response_extract_found.raise_for_status()
                data_extract_found = response_extract_found.json()
                pages_extract_found = data_extract_found.get("query", {}).get("pages", {})

                if pages_extract_found:
                    page_id_extract_found = next(iter(pages_extract_found))
                    if page_id_extract_found != "-1":
                        extract_found = pages_extract_found[page_id_extract_found].get("extract")
                        if extract_found:
                            return f"(Fonte Wikipedia: '{found_title}')\n\n{extract_found}"
                # Se não obteve extract, seguirá para fallback de snippet abaixo
            except (requests.exceptions.RequestException, Exception):
                # Não interrompe o fluxo; usaremos o snippet como fallback
                pass

            # --- Fallback: usar snippet da busca ampla se disponível ---
            if found_snippet:
                # Remove tags HTML do snippet e torna legível
                clean_snippet = re.sub(r'<[^>]+>', '', found_snippet).strip()
                # Indica que é um snippet e não o extrato completo
                return f"(Fonte Wikipedia (Snippet da Busca): '{found_title}')\n\n...{clean_snippet}..."
            else:
                return f"A pesquisa ampla na Wikipedia encontrou o artigo '{found_title}', mas não foi possível obter seu conteúdo (extrato ou snippet)."

        # Caso extremo: não encontrou título e não houve exceção clara
        return f"Erro inesperado: A busca ampla por '{topic}' não produziu resultados nem erros explícitos."