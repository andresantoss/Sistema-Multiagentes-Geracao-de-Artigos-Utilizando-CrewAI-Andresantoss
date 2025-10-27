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

# --- Schema de Saída (Pydantic) ATUALIZADO ---
class ArticleOutput(BaseModel):
    """
    Define a estrutura de dados esperada para o artigo gerado,
    utilizando Pydantic para validação e documentação automática dos campos.
    As chaves estão em inglês para consistência com a instrução ao LLM.
    """
    title: str = Field(..., description="The main title of the generated article.")
    summary: str = Field(..., description="Abstract in Portuguese (max 250 words), presenting objective, method, and main conclusions.")
    keywords: List[str] = Field(..., min_length=3, max_length=5, description="List of 3 to 5 relevant keywords in Portuguese.")
    introduction_subtitle: str = Field(..., description="Subtítulo da introdução.")
    introduction_content: str = Field(..., description="Texto da introdução.")
    development_subtitle: str = Field(..., description="Subtítulo do desenvolvimento.")
    development_content: str = Field(..., description="Texto do desenvolvimento.")
    conclusion_subtitle: str = Field(..., description="Subtítulo da conclusão.")
    conclusion_content: str = Field(..., description="Texto da conclusão.")
    source_title: Union[str, None] = Field(None, description="O título exato da fonte principal da Wikipedia.")
    source_url: Union[str, None] = Field(None, description="A URL completa da fonte principal.")
    access_date: Union[str, None] = Field(None, description="Data de acesso no formato 'DD de MÊS de AAAA'.")
    # --- CORREÇÃO: ADICIONADOS CAMPOS DE IMAGEM ---
    image_url: Union[str, None] = Field(None, description="URL da imagem principal encontrada na Wikipedia.")
    image_caption: Union[str, None] = Field(None, description="Legenda (gerada pela IA) da imagem principal.")
    # --- FIM DA CORREÇÃO ---
    word_count: int = Field(..., description="Contagem total de palavras (campos textuais).")

# Instancia a ferramenta Wikipedia (wrapper local)
wikipedia_tool = WikipediaSearchTool()

# --- CORREÇÃO DO NameError ---
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
# --- FIM DA CORREÇÃO ---

# Função principal que configura e executa a Crew de geração de artigos.
def create_crew(topic: str) -> ArticleOutput:
    """
    Monta e executa uma CrewAI para pesquisar um tópico na Wikipedia, 
    gerar o conteúdo textual estruturado de um artigo e validá-lo.
    """
    load_dotenv() 
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key: 
        raise ValueError("Erro: Chave GEMINI_API_KEY não encontrada no .env!")

    llm_model_name = "google/gemini-2.0-flash" 

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252') # Windows fallback
        except locale.Error:
            pass # Silenciosamente usa o locale padrão se pt_BR falhar

    current_date_str = datetime.now().strftime("%d de %B de %Y").lower()

    # --- Definição dos Agentes ---
    researcher = Agent(
        role="Assistente de Pesquisa Multimídia", # Role atualizado
        goal=f"Coletar da Wikipedia fatos chave, conceitos, E a imagem principal sobre '{topic}'.", # Goal atualizado
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
            f"Gerar conteúdo textual (em Português-BR) e subtítulos relevantes para um artigo sobre '{topic}', formatado como JSON."
        ), 
        
        system_prompt=( # Força o idioma PT-BR
            "Você é um redator técnico que escreve **exclusivamente em Português do Brasil (pt-br)**. "
            "Sua regra mais importante é que todo o conteúdo textual que você gerar (títulos, resumos, etc.) "
            "DEVE estar em Português-BR. "
            "Você organiza as informações em uma estrutura JSON com chaves em INGLÊS, conforme solicitado."
        ),

        backstory=(
            "Você é um redator técnico que organiza informações em JSON com chaves em INGLÊS. "
            "Foco em precisão, estilo formal, e cumprimento rigoroso de regras de formato, idioma e contagem de palavras."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm_model_name,
    )

    # --- Tarefas ---
    research_task = Task(
        description=( 
            "1. Use a ferramenta Wikipedia para encontrar informações sobre '{topic}'. A ferramenta retornará um JSON string.\n"
            "2. **Analise o JSON string retornado.** Ele conterá 'extract', 'source_title', 'image_url', e 'image_caption' (nome do ficheiro).\n"
            "3. Resuma os principais fatos/conceitos encontrados (máx 2-3 parágrafos) **em Português**.\n" 
            "4. **Formate sua resposta final** incluindo o resumo E os dados da imagem, prefixando cada parte claramente:\n"
            "(Fonte Título: [título da fonte aqui])\n"
            "(Fonte URL Imagem: [url da imagem aqui, ou 'N/A' se não houver])\n"
            "(Nome Ficheiro Imagem: [nome do ficheiro da imagem aqui, ou 'N/A' se não houver])\n\n"
            "[Resumo factual conciso aqui...]"
        ),
        expected_output=( 
             "Um resumo factual conciso (máx 2-3 parágrafos) sobre '{topic}', **em Português**, " 
             "prefixado com (Fonte Título: ...), (Fonte URL Imagem: ...), e (Nome Ficheiro Imagem: ...)."
        ),
        agent=researcher 
    )

    write_task = Task(
        description=( 
            f"Contexto: você recebeu o resumo (em português) prefixado com '(Fonte Título: \"Título da Fonte\")' e outros metadados.\n"
            f"Data de Acesso: {current_date_str}\n"
            "Sua Tarefa:\n"
            "**REQUISITO DE IDIOMA OBRIGATÓRIO: Todo o conteúdo textual gerado (title, summary, etc.) DEVE ser escrito em Português do Brasil (pt-br).**\n\n"
            "Com base nesse contexto, gere o conteúdo textual para CADA UMA das seguintes chaves (em INGLÊS):\n"
            "- title: Crie um título formal para o artigo sobre '{topic}'.\n"
            "- summary: Elabore o resumo (máx 250 palavras).\n"
            "- keywords: Liste de 3 a 5 palavras-chave em português.\n"
            "- introduction_subtitle: Crie um subtítulo para a introdução.\n"
            "- introduction_content: Escreva a introdução.\n"
            "- development_subtitle: Crie um subtítulo para o desenvolvimento.\n"
            "- development_content: Elabore o corpo principal.\n"
            "- conclusion_subtitle: Crie um subtítulo para a conclusão.\n"
            "- conclusion_content: Escreva a conclusão.\n"
            "- source_title: Extraia o 'Fonte Título' (DEVE ser uma **única string** ou `null`).\n"
            "- source_url: Crie a URL da Wikipedia para o 'Fonte Título' (https://pt.wikipedia.org/wiki/TÍTULO, substituindo espaços por underscores).\n"
            f"- access_date: Use **exatamente** a string de data: '{current_date_str}'.\n"
            # --- CORREÇÃO: Instruções para os campos de imagem ---
            "- image_url: Extraia a 'Fonte URL Imagem' do contexto (ou `null`).\n"
            "- image_caption: **Crie uma legenda curta e descritiva (máx 15 palavras)** para a imagem. Se não houver imagem, retorne 'Ilustração do tópico'.\n"
            # --- FIM DA CORREÇÃO ---
            "- word_count: **Calcule** a contagem total de palavras (title, summary, introduction_content, development_content, conclusion_content).\n" 
            "**REQUISITO OBRIGATÓRIO (PALAVRAS):** A soma das palavras (summary, intro, dev, conclusion) **DEVE SER NO MÍNIMO 300 PALAVRAS**.\n"
            "Responda somente o JSON final, delimitado por ```json e ```."
        ),
        expected_output=( 
            "Um *string* JSON válido... com **todo o conteúdo textual (valores) em Português do Brasil (pt-br)**... "
            "e com o conteúdo textual principal somando no mínimo 300 palavras."
        ),
        agent=writer,
        context=[research_task], 
    )

    # --- Montagem da Crew e execução ---
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
    if 'keywords' in data and isinstance(data['keywords'], str):
        data['keywords'] = [k.strip() for k in data['keywords'].split(',') if k.strip()]
    for k in ['introduction_subtitle', 'development_subtitle', 'conclusion_subtitle']:
        if k in data and isinstance(data[k], str): data[k] = data[k].strip()
    # CORREÇÃO: Normaliza os novos campos de imagem
    for k in ['source_title', 'source_url', 'image_url', 'image_caption']:
        if k in data and data[k] == '': data[k] = None
    if 'word_count' in data and isinstance(data['word_count'], str):
        try: data['word_count'] = int(data['word_count'].strip())
        except ValueError: pass

    # --- Validação final com Pydantic ---
    try:
        parsed_output = ArticleOutput.model_validate(data)
        
        real_word_count = (
            (len(parsed_output.summary.split()) if parsed_output.summary else 0) +
            (len(parsed_output.introduction_content.split()) if parsed_output.introduction_content else 0) +
            (len(parsed_output.development_content.split()) if parsed_output.development_content else 0) +
            (len(parsed_output.conclusion_content.split()) if parsed_output.conclusion_content else 0)
        )
        
        if real_word_count < 300: # 
            print(f"AVISO: O agente gerou apenas {real_word_count} palavras (mínimo 300).")
        
        return parsed_output
    
    except ValidationError as e:
        raise ValueError(
            "O JSON retornado pelo agente não está no formato esperado (ArticleOutput). "
            f"Detalhes: {e}\nJSON normalizado recebido:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        ) from e