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

# --- Schema de Saída ATUALIZADO ---
class ArticleOutput(BaseModel):
    title: str = Field(..., description="O título principal do artigo gerado.")
    summary: str = Field(..., description="Resumo em português (máx 250 palavras).")
    keywords: List[str] = Field(..., min_length=3, max_length=5, description="3 a 5 palavras-chave em português.")
    introduction_subtitle: str = Field(..., description="Subtítulo da introdução.")
    introduction_content: str = Field(..., description="Texto da introdução.")
    development_subtitle: str = Field(..., description="Subtítulo do desenvolvimento.")
    development_content: str = Field(..., description="Texto do desenvolvimento.")
    conclusion_subtitle: str = Field(..., description="Subtítulo da conclusão.")
    conclusion_content: str = Field(..., description="Texto da conclusão.")
    source_title: Union[str, None] = Field(None, description="O título exato da fonte principal da Wikipedia.")
    source_url: Union[str, None] = Field(None, description="A URL completa da fonte principal.")
    access_date: Union[str, None] = Field(None, description="A data de acesso no formato 'DD de MÊS de AAAA'.")
    image_url: Union[str, None] = Field(None, description="URL da imagem principal encontrada na Wikipedia.")
    image_caption: str = Field(..., description="Legenda curta e descritiva gerada pela IA para a imagem.")
    word_count: int = Field(..., description="Contagem total de palavras (campos textuais).")

# Instancia a ferramenta
wikipedia_tool = WikipediaSearchTool()

def extract_json_from_text(text: str) -> str | None:
    """
    Extrai o primeiro objeto JSON encontrado no texto.
    Aceita blocos ```json { ... } ``` ou apenas {...}.
    Retorna a string JSON (com chaves) ou None se não encontrar.

    Args:
        text: A string de texto potencialmente contendo JSON.

    Returns:
        A string JSON extraída ou None se nenhum JSON válido for encontrado.
    """
    if not text:
        return None
        
    # 1. DEFINE a variável 'match_markdown' primeiro...
    match_markdown = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    
    # 2. ...DEPOIS verifica se ela encontrou algo.
    if match_markdown:
        return match_markdown.group(1).strip()
    
    # 3. DEFINE a variável 'match_bare'
    match_bare = re.search(r'(\{.*?\})', text, re.DOTALL)
    
    # 4. ...DEPOIS verifica se ela encontrou algo.
    if match_bare:
         return match_bare.group(1).strip()
         
    return None

# Função principal
def create_crew(topic: str) -> ArticleOutput:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Erro: Chave GEMINI_API_KEY não encontrada no .env!")

    llm_model_name = "google/gemini-2.0-flash"

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
        except locale.Error:
            print("AVISO: locale pt_BR não disponível, usando formatação padrão do sistema.")

    current_date_str = datetime.now().strftime("%d de %B de %Y").lower()

    # --- Definição dos Agentes ---
    researcher = Agent(
        role="Assistente de Pesquisa Multimídia",
        goal=f"Coletar da Wikipedia fatos chave, conceitos, E a imagem principal sobre '{topic}'.",
        backstory=(
            "Especialista em extrair informações essenciais da Wikipedia (texto e metadados de imagem), "
            "sintetizá-las e registrar as fontes."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[wikipedia_tool],
        llm=llm_model_name,
        max_iter=5,
    )

    writer = Agent(
        role="Redator Técnico Estruturado",
        goal=(
            f"Gerar conteúdo textual, subtítulos, legendas de imagem e metadados para um artigo sobre '{topic}', formatado como JSON." # Goal atualizado
        ),
        backstory=(
            "Você é um redator técnico que organiza informações (texto e links de imagem) "
            "em uma estrutura JSON pré-definida, seguindo um estilo formal e objetivo, usando chaves em INGLÊS. "
            "Você é perito em criar subtítulos relevantes e **legendas de imagem descritivas**." # Backstory atualizado
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm_model_name,
    )

    # --- Tarefas ---
    research_task = Task(
        description=(
            "1. Use a ferramenta Wikipedia para coletar informações sobre '{topic}'. A ferramenta retornará um JSON string.\n"
            "2. **Analise o JSON string retornado.** Ele conterá 'extract', 'source_title', 'image_url', e 'image_caption' (que é o nome do ficheiro).\n" # Explica o que a ferramenta retorna
            "3. **Sintetize** os fatos chave do 'extract' (máx 2-3 parágrafos).\n"
            "4. **Formate sua resposta final** incluindo o resumo E os dados da imagem, prefixando cada parte claramente:\n"
            "(Fonte Título: [título da fonte aqui])\n"
            "(Fonte URL Imagem: [url da imagem aqui, ou 'N/A' se não houver])\n"
            "(Nome Ficheiro Imagem: [nome do ficheiro da imagem aqui, ou 'N/A' se não houver])\n\n" # Ajustado para clareza
            "[Resumo factual conciso aqui...]"
        ),
        expected_output=(
             "Um resumo conciso (máx 2-3 parágrafos) sobre '{topic}', "
             "prefixado com (Fonte Título: ...), (Fonte URL Imagem: ...), e (Nome Ficheiro Imagem: ...)."
        ),
        agent=researcher,
    )

    write_task = Task(
        description=(
            f"Contexto: Você recebeu um resumo factual sobre '{topic}' e metadados (Fonte Título, Fonte URL Imagem, Nome Ficheiro Imagem).\n"
            f"Data de Acesso: {current_date_str}\n"
            "Tarefa: Gere APENAS um objeto JSON (delimitado por ```json ... ```) contendo as chaves em INGLÊS:\n"
            "- title: Crie um título formal para o artigo sobre '{topic}'.\n"
            "- summary: Elabore o resumo (máx 250 palavras).\n"
            "- keywords: Liste de 3 a 5 palavras-chave.\n"
            "- introduction_subtitle: Crie um subtítulo para a introdução.\n"
            "- introduction_content: Escreva a introdução.\n"
            "- development_subtitle: Crie um subtítulo para o desenvolvimento.\n"
            "- development_content: Elabore o corpo principal (mínimo 300 palavras no total com as outras seções).\n"
            "- conclusion_subtitle: Crie um subtítulo para a conclusão.\n"
            "- conclusion_content: Escreva a conclusão.\n"
            "- source_title: Extraia o 'Fonte Título' do contexto (DEVE ser uma **única string** ou `null`).\n"
            "- source_url: Crie a URL da Wikipedia para o 'Fonte Título' (https://pt.wikipedia.org/wiki/TÍTULO).\n"
            f"- access_date: Use **exatamente** a string de data: '{current_date_str}'.\n"
            "- image_url: Extraia a 'Fonte URL Imagem' do contexto (a URL http://... ou `null`).\n"
            "- image_caption: **Crie uma legenda curta e descritiva (máx 15 palavras)** para a imagem, baseando-se no 'Nome Ficheiro Imagem' (ex: 'Ficheiro:Brasil_ouro_olimpico.jpg' pode virar 'Brasil conquista ouro olímpico') e no contexto do artigo. Se não houver imagem, retorne 'Ilustração do tópico'.\n"
            "- word_count: **Calcule** a contagem total de palavras (title, summary, introduction_content, development_content, conclusion_content).\n"
            "**REQUISITO OBRIGATÓRIO:** A soma das palavras (summary, intro, dev, conclusion) **DEVE SER NO MÍNIMO 300 PALAVRAS**.\n"
            "Responda somente o JSON final."
        ),
        expected_output=(
            "Um *string* JSON válido, delimitado por ```json e ```, contendo todas as chaves em INGLÊS "
            "(incluindo image_url, **image_caption gerada**, source_url, access_date) preenchidas corretamente, "
            "e com o conteúdo textual principal somando no mínimo 300 palavras."
        ),
        agent=writer,
        context=[research_task],
    )

    # --- Montagem e Execução da Crew ---
    article_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True,
    )
    
    crew_result = article_crew.kickoff(inputs={'topic': topic})

    # --- Parsing e Validação Manual da Saída ---
    if not crew_result or not hasattr(crew_result, 'raw') or not crew_result.raw:
         raise ValueError("A CrewAI não retornou um resultado bruto válido da última tarefa.")
    raw_output = crew_result.raw

    json_string = extract_json_from_text(raw_output)
    if not json_string:
        raise ValueError(f"Não foi possível extrair um JSON válido da resposta do agente.\nResposta recebida:\n{raw_output}")

    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON extraído: {e}\nJSON extraído:\n{json_string}") from e

    # --- Normalizações Defensivas ---
    for k in ['introduction_subtitle', 'development_subtitle', 'conclusion_subtitle']:
        if k in data and isinstance(data[k], str): data[k] = data[k].strip()
    if 'keywords' in data and isinstance(data['keywords'], str):
        data['keywords'] = [k.strip() for k in data['keywords'].split(',') if k.strip()]
    for k in ['source_title', 'source_url', 'image_url', 'image_caption']:
        if k in data and data[k] == '': data[k] = None
    if 'word_count' in data and isinstance(data['word_count'], str):
        try: data['word_count'] = int(data['word_count'].strip())
        except ValueError: pass 

    try:
        parsed_output = ArticleOutput.model_validate(data)
        
        real_word_count = (
            len(parsed_output.summary.split()) +
            len(parsed_output.introduction_content.split()) +
            len(parsed_output.development_content.split()) +
            len(parsed_output.conclusion_content.split())
        )
        
        if real_word_count < 300: # 
            print(f"AVISO: O agente gerou apenas {real_word_count} palavras (mínimo 300).")
        
        return parsed_output
    
    except ValidationError as e:
        raise ValueError(
            "O JSON retornado pelo agente não está no formato esperado (ArticleOutput). "
            f"Detalhes: {e}\nJSON normalizado recebido:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        ) from e