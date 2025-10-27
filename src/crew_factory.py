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

# --- Schema de Saída (Pydantic) ---
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
    source_title: Union[str, None] = Field(None, description="Título da fonte principal (Wikipedia).")
    source_url: Union[str, None] = Field(None, description="URL completa da fonte principal.")
    access_date: Union[str, None] = Field(None, description="Data de acesso no formato 'DD de MÊS de AAAA'.")
    word_count: int = Field(..., description="Contagem total de palavras (campos textuais).")

# Instancia a ferramenta Wikipedia (wrapper local)
wikipedia_tool = WikipediaSearchTool()

def extract_json_from_text(text: str) -> str | None:
    """
    Extrai o primeiro objeto JSON encontrado no texto.
    Aceita blocos ```json { ... } ``` ou apenas {...}.
    Retorna a string JSON (com chaves) ou None se não encontrar.
    """
    if not text:
        return None
    match_md = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match_md:
        return match_md.group(1).strip()
    match_raw = re.search(r'(\{.*?\})', text, re.DOTALL)
    if match_raw:
        return match_raw.group(1).strip()
    return None

# Função principal que configura e executa a Crew de geração de artigos.
def create_crew(topic: str) -> ArticleOutput:
    """
    Monta e executa uma CrewAI para pesquisar um tópico na Wikipedia, 
    gerar o conteúdo textual estruturado de um artigo e validá-lo.

    Args:
        topic: O tópico/assunto para o artigo.

    Returns:
        Um objeto ArticleOutput (validado pelo Pydantic) contendo o artigo gerado.
        
    Raises:
        ValueError: Se a chave GEMINI_API_KEY não for encontrada no .env,
                    se a Crew não retornar um resultado bruto,
                    se nenhum JSON puder ser extraído da resposta do agente,
                    se o JSON extraído for inválido, ou
                    se o JSON não puder ser validado pelo modelo Pydantic,
                    ou se o artigo gerado não atingir 300 palavras.
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
            print("AVISO: locale pt_BR não disponível, usando formatação padrão do sistema.")

    current_date_str = datetime.now().strftime("%d de %B de %Y").lower()

    # --- Definição dos Agentes ---
    researcher = Agent(
        role="Assistente de Pesquisa Acadêmica", 
        goal=f"Coletar da Wikipedia e sintetizar fatos/conceitos chave sobre '{topic}'.", 
        backstory="Especialista em extrair e resumir informações essenciais da Wikipedia, registrando a fonte.",
        verbose=True, 
        allow_delegation=False, 
        tools=[wikipedia_tool], 
        llm=llm_model_name,
        max_iter=5,
    )

    writer = Agent(
        role="Redator Técnico Estruturado", 
        goal=(
            f"Gerar o conteúdo textual para um artigo sobre '{topic}', "
            f"garantindo que o conteúdo principal (summary, introduction, development, conclusions) **some no mínimo 300 palavras**." # REQUISITO ADICIONADO 
        ), 
        backstory=(
            "Redator técnico que organiza informações em JSON com chaves em INGLÊS. "
            "Foco em precisão, estilo objetivo, formato validável e **cumprimento rigoroso de contagem mínima de palavras**." # BACKSTORY ATUALIZADO
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm_model_name,
    )

    # --- Tarefas ---
    research_task = Task(
        description=(
            "1) Use a ferramenta Wikipedia para coletar informações sobre '{topic}'.\n"
            "2) Resuma os principais fatos (máx 2-3 parágrafos).\n"
            "3) Prefixe o resumo com '(Fonte Wikipedia: <Título da Fonte>)'."
        ),
        expected_output=(
            "Resumo factual conciso (máx 2-3 parágrafos) sobre '{topic}', iniciando com '(Fonte Wikipedia: <Título>)'."
        ),
        agent=researcher,
    )

    write_task = Task(
        description=(
            "Contexto: você recebeu o resumo prefixado com '(Fonte Wikipedia: \"Título da Fonte\")'.\n"
            f"Data de Acesso: {current_date_str}\n"
            "Tarefa: Gere APENAS um objeto JSON (delimitado por ```json ... ``` se possível) contendo as chaves em INGLÊS:\n"
            "title, summary, keywords (3-5), introduction_subtitle, introduction_content,\n"
            "development_subtitle, development_content, conclusion_subtitle, conclusion_content,\n"
            "source_title, source_url, access_date (use a data fornecida), word_count.\n"
            "**REQUISITO OBRIGATÓRIO:** A soma das palavras dos campos 'summary', 'introduction_content', 'development_content' e 'conclusion_content' **DEVE SER NO MÍNIMO 300 PALAVRAS**. Elabore o 'development_content' o suficiente para atingir essa meta.\n"
            "Calcule word_count como soma das palavras nos campos textuais mencionados.\n"
            "Responda somente o JSON final."
        ),
        expected_output=(
             "JSON válido com as chaves listadas preenchidas. "
             "O conteúdo textual principal (summary, introduction_content, development_content, conclusions) **DEVE SOMAR no mínimo 300 palavras**." 
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

    # Valida existência de saída bruta
    if not crew_result or not hasattr(crew_result, 'raw') or not crew_result.raw:
         raise ValueError("A CrewAI não retornou um resultado bruto válido.")

    raw_output = crew_result.raw

    # Extrai bloco JSON do texto bruto
    json_string = extract_json_from_text(raw_output)
    if not json_string:
        raise ValueError(f"Não foi possível extrair um JSON válido da resposta do agente.\nResposta recebida:\n{raw_output}")

    # Decodifica JSON e aplica normalizações defensivas
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON extraído: {e}\nJSON extraído:\n{json_string}") from e

    # Normalizações (código original mantido)
    if 'keywords' in data and isinstance(data['keywords'], str):
        data['keywords'] = [k.strip() for k in data['keywords'].split(',') if k.strip()]
    for k in ['introduction_subtitle', 'development_subtitle', 'conclusion_subtitle']:
        if k in data and isinstance(data[k], str):
            data[k] = data[k].strip()
    if 'source_title' in data and data['source_title'] == '':
        data['source_title'] = None
    if 'word_count' in data and isinstance(data['word_count'], str):
        try:
            data['word_count'] = int(data['word_count'].strip())
        except ValueError:
            pass

    # Validação final com Pydantic
    try:
        parsed_output = ArticleOutput.model_validate(data)
        
        # Verificação manual da contagem de palavras pós-validação Pydantic
        real_word_count = (
            len(parsed_output.summary.split()) +
            len(parsed_output.introduction_content.split()) +
            len(parsed_output.development_content.split()) +
            len(parsed_output.conclusion_content.split())
        )
        
        if real_word_count < 300:
            # Lança um erro se o agente não cumpriu o requisito mínimo 
            raise ValueError(
                f"Erro de Validação Pós-Geração: O agente falhou em atender o requisito de 300 palavras. "
                f"Gerado apenas {real_word_count} palavras."
            )
        
        # Se a contagem estiver ok, retorna o objeto validado
        return parsed_output
    
    except ValidationError as e:
        raise ValueError(
            "O JSON retornado pelo agente não está no formato esperado (ArticleOutput). "
            f"Detalhes: {e}\nJSON normalizado recebido:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        ) from e