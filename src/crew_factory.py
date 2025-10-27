import os
import re
import json
import locale
from datetime import datetime
from typing import Union, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from crewai import Agent, Task, Crew, Process
from src.tools.wikipedia_tool import WikipediaSearchTool

# --- Modelo de saída ---
class ArticleOutput(BaseModel):
    title: str
    summary: str
    keywords: List[str] = Field(..., min_length=3, max_length=5)
    introduction_subtitle: str
    introduction_content: str
    development_subtitle: str
    development_content: str
    conclusion_subtitle: str
    conclusion_content: str
    source_title: Union[str, None] = None
    source_url: Union[str, None] = None
    access_date: Union[str, None] = None
    image_url: Union[str, None] = None
    image_caption: Union[str, None] = None
    word_count: int

wikipedia_tool = WikipediaSearchTool()

def extract_json_from_text(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL) or re.search(r'(\{.*\})', text, re.DOTALL)
    return m.group(1).strip() if m else None

def _count_words_in_fields(d: dict, fields: List[str]) -> int:
    return sum(len((d.get(f) or "").split()) for f in fields)

def create_crew(topic: str) -> ArticleOutput:
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("Erro: GEMINI_API_KEY ausente no .env")

    llm_model = "google/gemini-2.0-flash"
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
        except locale.Error:
            pass

    current_date_str = datetime.now().strftime("%d de %B de %Y").lower()

    researcher = Agent(
        role="Assistente de Pesquisa Multimídia",
        goal=f"Coletar da Wikipedia fatos chave, conceitos e a imagem principal sobre '{topic}'.",
        backstory="Especialista em extrair informações essenciais da Wikipedia (texto e metadados de imagem).",
        verbose=True, allow_delegation=False, tools=[wikipedia_tool], llm=llm_model, max_iter=5
    )

    writer = Agent(
        role="Redator Técnico Estruturado",
        goal=f"Gerar conteúdo textual em Português-BR sobre '{topic}' estruturado como JSON.",
        system_prompt=(
            "Você é um redator que escreve exclusivamente em Português do Brasil (pt-br). "
            "Produza apenas um objeto JSON com chaves em INGLÊS conforme instruído."
        ),
        backstory="Redator técnico: manter coerência, formalidade e cumprimento estrito do formato.",
        verbose=True, allow_delegation=False, llm=llm_model
    )

    research_task = Task(
        description=(
            "Use a ferramenta Wikipedia para obter dados sobre '{topic}'. Analise o JSON retornado "
            "e gere um breve resumo factual em Português. Prefixe metadados: (Fonte Título: ...), "
            "(Fonte URL: ...), (Fonte URL Imagem: ...), (Nome Ficheiro Imagem: ...)."
        ),
        expected_output="Resumo factual conciso em Português com metadados quando disponíveis.",
        agent=researcher
    )

    write_task = Task(
        description=(
            f"Contexto: resumo (pt-BR) e metadados. Data de Acesso: {current_date_str}.\n"
            "Produza SOMENTE um objeto JSON com as chaves (em INGLÊS): "
            "title, summary, keywords (3-5), introduction_subtitle, introduction_content, "
            "development_subtitle, development_content, conclusion_subtitle, conclusion_content, "
            "source_title, source_url, access_date, image_url (ou null), image_caption (ou null), word_count.\n"
            "O ARTIGO DEVE TER NO MÍNIMO 300 PALAVRAS somando summary + introduction_content + development_content + conclusion_content. "
            "Calcule word_count exatamente. Texto em Português do Brasil (pt-BR). Use null para campos não disponíveis."
        ),
        expected_output="JSON válido com word_count >= 300 e textos em pt-BR.",
        agent=writer,
        context=[research_task],
    )

    crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task], process=Process.sequential, verbose=True)
    result = crew.kickoff(inputs={'topic': topic})

    if not result or not getattr(result, "raw", None):
        raise ValueError("A CrewAI não retornou resultado bruto válido.")

    raw = result.raw
    json_str = extract_json_from_text(raw)
    if not json_str:
        raise ValueError(f"Não foi possível extrair JSON da resposta do agente.\nResposta:\n{raw}")

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON: {e}\nJSON extraído:\n{json_str}") from e

    # Normalizações agrupadas
    if isinstance(data.get('keywords'), str):
        data['keywords'] = [k.strip() for k in data['keywords'].split(',') if k.strip()]
    for k in ['introduction_subtitle', 'development_subtitle', 'conclusion_subtitle']:
        if isinstance(data.get(k), str):
            data[k] = data[k].strip()
    # campos opcionais garantidos como chaves presentes
    for k in ['source_title', 'source_url', 'access_date', 'image_url', 'image_caption']:
        v = data.get(k)
        if v == '':
            data[k] = None
        data.setdefault(k, None)
    if isinstance(data.get('word_count'), str):
        try:
            data['word_count'] = int(data['word_count'].strip())
        except Exception:
            pass

    try:
        parsed = ArticleOutput.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Formato JSON inválido: {e}\nJSON:\n{json.dumps(data, ensure_ascii=False, indent=2)}") from e

    # Valida contagem mínima
    fields = ['summary', 'introduction_content', 'development_content', 'conclusion_content']
    real_count = _count_words_in_fields(parsed.model_dump(), fields)
    if real_count < 300:
        raise ValueError(f"Artigo insuficiente: {real_count} palavras (mínimo 300).")

    return parsed