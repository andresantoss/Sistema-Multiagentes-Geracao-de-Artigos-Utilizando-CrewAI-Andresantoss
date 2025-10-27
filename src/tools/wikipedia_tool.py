import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
import os
import re
import json
from urllib.parse import quote

class WikipediaSearchTool(BaseTool):
    """
    Ferramenta simplificada para buscar extrato e imagem (quando possível) na Wikipédia (pt).
    Retorna JSON com: title, extract, source_url, image_url, image_caption.
    """

    name: str = "Wikipedia Search Tool"
    description: str = (
        "Busca por um tópico na Wikipedia (pt). Tenta título exato; se não, faz busca textual."
    )

    def _normalize_url(self, url: str) -> str | None:
        if not url:
            return None
        url = url.strip()
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return "https://pt.wikipedia.org" + url
        return url

    def _url_accessible(self, url: str, headers: dict, timeout: int = 6) -> bool:
        try:
            r = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            return 200 <= r.status_code < 400
        except requests.RequestException:
            return False

    def _get_imageinfo_for_file(self, file_title: str, headers: dict, base_url: str) -> tuple[str | None, str | None]:
        """
        Retorna (image_url, caption) a partir de um "File:..." via imageinfo (iiprop=url).
        """
        params = {
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
            "utf8": 1,
        }
        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=8)
            r.raise_for_status()
            j = r.json()
            pages = j.get("query", {}).get("pages", {})
            if not pages:
                return None, None
            page = pages[next(iter(pages))]
            info = (page.get("imageinfo") or [])
            if info:
                url = info[0].get("url")
                url = self._normalize_url(url)
                return url, file_title.replace("File:", "")
        except Exception:
            pass
        return None, None

    def _fetch_wikipedia_data(self, search_title: str, headers: dict) -> tuple[dict | None, str | None]:
        """
        Tenta extrato + imagem usando (em ordem):
         1) pageimages (thumbnail)
         2) pageimages original
         3) lista de images -> imageinfo (primeiro válido)
         4) parse HTML (og:image / infobox)
        Retorna dicionário ou (None, erro).
        """
        base_url = "https://pt.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts|pageimages",
            "piprop": "thumbnail",
            "pithumbsize": 600,
            "explaintext": 1,
            "titles": search_title,
            "format": "json",
            "utf8": 1,
            "redirects": 1,
        }

        try:
            resp = requests.get(base_url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            j = resp.json()
            pages = j.get("query", {}).get("pages", {})
            if not pages:
                return None, "Nenhuma página retornada pela API."
            page = pages[next(iter(pages))]
            if str(next(iter(pages))) == "-1":
                return None, "Página não encontrada."

            title = page.get("title")
            extract = page.get("extract")
            source_url = f"https://pt.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"

            # tentativa 1: thumbnail via pageimages
            image_url = None
            image_caption = None
            thumb = page.get("thumbnail", {})
            candidate = self._normalize_url(thumb.get("source") if isinstance(thumb, dict) else None)
            if candidate and self._url_accessible(candidate, headers):
                image_url = candidate
                image_caption = title

            # tentativa 2: pageimages original (se não houve thumbnail)
            if not image_url:
                try:
                    params_orig = {
                        "action": "query",
                        "prop": "pageimages",
                        "piprop": "original",
                        "titles": title,
                        "format": "json",
                        "utf8": 1,
                    }
                    r2 = requests.get(base_url, params=params_orig, headers=headers, timeout=8)
                    r2.raise_for_status()
                    j2 = r2.json()
                    pages2 = j2.get("query", {}).get("pages", {})
                    if pages2:
                        orig = pages2[next(iter(pages2))].get("original", {})
                        candidate2 = self._normalize_url(orig.get("source"))
                        if candidate2 and self._url_accessible(candidate2, headers):
                            image_url = candidate2
                            image_caption = title
                except Exception:
                    pass

            # tentativa 3: listar imagens e pedir imageinfo para o primeiro válido
            if not image_url:
                try:
                    params_imgs = {"action": "query", "titles": title, "prop": "images", "imlimit": "max", "format": "json", "utf8": 1}
                    r3 = requests.get(base_url, params=params_imgs, headers=headers, timeout=8)
                    r3.raise_for_status()
                    j3 = r3.json()
                    pages3 = j3.get("query", {}).get("pages", {})
                    if pages3:
                        imgs = pages3[next(iter(pages3))].get("images") or []
                        for img in imgs:
                            ft = img.get("title")
                            if not ft or not ft.lower().startswith("file:"):
                                continue
                            cand, cap = self._get_imageinfo_for_file(ft, headers, base_url)
                            if cand and self._url_accessible(cand, headers):
                                image_url = cand
                                image_caption = cap
                                break
                except Exception:
                    pass

            # tentativa 4: parse HTML (og:image / infobox)
            if not image_url:
                try:
                    rhtml = requests.get(source_url, headers=headers, timeout=8)
                    rhtml.raise_for_status()
                    html = rhtml.text
                    m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                    if not m:
                        m = re.search(r'<(?:td|div)[^>]*class=["\'][^"\']*(?:sidebar-image|infobox)[^"\']*["\'][\s\S]*?<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
                    if m:
                        cand = self._normalize_url(m.group(1))
                        if cand and self._url_accessible(cand, headers):
                            image_url = cand
                            image_caption = title
                except Exception:
                    pass

            data = {
                "title": title,
                "extract": extract,
                "source_url": source_url,
                "image_url": image_url,
                "image_caption": image_caption,
            }
            return data, None

        except requests.exceptions.RequestException as e:
            return None, f"Erro de rede: {e}"
        except Exception as e:
            return None, f"Erro inesperado: {e}"

    def _perform_full_text_search(self, search_term: str, headers: dict) -> tuple[str | None, str | None, str | None]:
        base_url = "https://pt.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": search_term, "srlimit": 1, "srprop": "snippet", "format": "json", "utf8": 1}
        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=10)
            r.raise_for_status()
            j = r.json()
            results = j.get("query", {}).get("search") or []
            if not results:
                return None, None, "Nenhum resultado."
            top = results[0]
            return top.get("title"), top.get("snippet"), None
        except requests.exceptions.RequestException as e:
            return None, None, f"Erro de rede: {e}"
        except Exception as e:
            return None, None, f"Erro inesperado: {e}"

    def _run(self, topic: str) -> str:
        load_dotenv()
        contact_info = os.getenv("WIKIPEDIA_CONTACT_INFO") or "https://github.com/andresantoss"
        headers = {"User-Agent": f"CrewAIAgent/1.0 ({contact_info})"}

        data, err = self._fetch_wikipedia_data(topic, headers)
        if data and data.get("extract"):
            payload = {
                "title": data["title"],
                "extract": f"(Fonte Wikipedia: '{data['title']}')\n\n{data['extract']}",
                "source_url": data.get("source_url"),
                "image_url": data.get("image_url"),
                "image_caption": data.get("image_caption"),
            }
            return json.dumps(payload, ensure_ascii=False)

        found_title, snippet, search_err = self._perform_full_text_search(topic, headers)
        if found_title:
            data2, err2 = self._fetch_wikipedia_data(found_title, headers)
            if data2 and data2.get("extract"):
                payload = {
                    "title": data2["title"],
                    "extract": f"(Fonte Wikipedia: '{data2['title']}')\n\n{data2['extract']}",
                    "source_url": data2.get("source_url"),
                    "image_url": data2.get("image_url"),
                    "image_caption": data2.get("image_caption"),
                }
                return json.dumps(payload, ensure_ascii=False)
            if snippet:
                clean_snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                payload = {
                    "title": found_title,
                    "extract": f"(Fonte Wikipedia (Snippet da Busca): '{found_title}')\n\n{clean_snippet}",
                    "source_url": f"https://pt.wikipedia.org/wiki/{quote(found_title.replace(' ', '_'))}",
                    "image_url": None,
                    "image_caption": None,
                }
                return json.dumps(payload, ensure_ascii=False)

        fallback = {
            "title": topic,
            "extract": f"A pesquisa na Wikipedia não encontrou conteúdo para '{topic}'.",
            "source_url": None,
            "image_url": None,
            "image_caption": None,
        }
        return json.dumps(fallback, ensure_ascii=False)