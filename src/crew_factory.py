import os
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field, ValidationError
from src.tools.wikipedia_tool import WikipediaSearchTool
from dotenv import load_dotenv
from typing import Union, List 
import json 
import re 

# Define o schema de saída do artigo utilizando Pydantic para validação e clareza.
class ArticleOutput(BaseModel):
    """
    Define a estrutura de dados esperada para o artigo gerado, 
    utilizando Pydantic para validação e documentação automática dos campos.
    As chaves estão em inglês para consistência com a instrução ao LLM.
    """
    title: str = Field(..., description="The main title of the generated article.")
    summary: str = Field(..., description="Abstract in Portuguese (max 250 words), presenting objective, method, and main conclusions.") 
    keywords: List[str] = Field(..., min_length=3, max_length=5, description="List of 3 to 5 relevant keywords in Portuguese.") 
    introduction: str = Field(..., description="Introduction: Presents the topic ('{topic}'), its relevance, objectives, and structure.") 
    development: str = Field(..., description="Development: Main body, logically presenting the Wikipedia research with formal language.") 
    conclusions: str = Field(..., description="Conclusions: Brief final section, summarizing main points and objectives.") 
    source_title: Union[str, None] = Field(None, description="Exact title(s) of the Wikipedia article(s) used as the main source.")
    word_count: int = Field(..., description="Total word count of the generated text fields (title, summary, introduction, development, conclusions).")

# Instancia a ferramenta Wikipedia para ser utilizada pelos agentes.
wikipedia_tool = WikipediaSearchTool()

def extract_json_from_text(text: str) -> str | None:
    """
    Tenta extrair um bloco de código JSON de uma string de texto.
    Procura por blocos delimitados por ```json ... ``` ou, como fallback,
    o primeiro JSON válido encontrado.

    Args:
        text: A string de texto potencialmente contendo JSON.

    Returns:
        A string JSON extraída ou None se nenhum JSON válido for encontrado.
    """
    # Prioriza a busca por blocos JSON explicitamente marcados
    match_markdown = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match_markdown:
        return match_markdown.group(1).strip() # .strip() para remover espaços extras
    
    # Fallback: Tenta encontrar o primeiro objeto JSON válido na string
    # Cuidado: Isso pode capturar JSONs parciais ou incorretos se houver múltiplos na string.
    match_bare = re.search(r'(\{.*?\})', text, re.DOTALL)
    if match_bare:
         return match_bare.group(1).strip()
         
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
                    se o JSON não puder ser validado pelo modelo Pydantic.
    """
    load_dotenv() 
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key: 
        raise ValueError("Erro: Chave GEMINI_API_KEY não encontrada no .env!")

    # Modelo LLM a ser usado
    llm_model_name = "google/gemini-2.0-flash" 

    # --- Definição dos Agentes ---
    researcher = Agent(
        role="Assistente de Pesquisa Acadêmica", 
        goal=f"Coletar da Wikipedia e sintetizar os fatos/conceitos chave sobre '{topic}' para a redação de um artigo estruturado.", 
        backstory=(
            "Especialista em extrair e resumir informações essenciais da Wikipedia, "
            "focando na precisão factual e registrando a fonte." 
        ),
        verbose=True, 
        allow_delegation=False, 
        tools=[wikipedia_tool], 
        llm=llm_model_name,
        max_iter=5 # Limita iterações para evitar loops excessivos
    )

    writer = Agent(
        role="Redator Técnico Estruturado", 
        goal=(
            f"Gerar o conteúdo textual para as seções de um artigo sobre '{topic}' (title, summary, keywords, introduction, development, conclusions, source_title), "
            f"baseado no resumo da pesquisa e formatado como um objeto JSON." 
        ), 
        backstory=(
            "Você é um redator técnico que organiza informações de pesquisa em uma estrutura JSON pré-definida, "
            "seguindo um estilo formal e objetivo similar ao acadêmico, usando chaves em INGLÊS." 
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm_model_name 
    )

    # --- Definição das Tarefas ---
    research_task = Task(
        description=( 
            "1. Use a ferramenta Wikipedia para encontrar informações sobre '{topic}'.\n"
            "2. Resuma os principais fatos/conceitos encontrados.\n" 
            "3. Inclua o(s) título(s) da(s) fonte(s) (prefixo '(Fonte Wikipedia: ...)') no início."
        ),
        expected_output=( 
             "Um resumo conciso sobre '{topic}', baseado na Wikipedia, "
             "iniciando com o(s) título(s) da(s) fonte(s) (prefixo '(Fonte Wikipedia: ...)' )."
        ),
        agent=researcher 
    )

    # Tarefa de Escrita: Pede JSON com chaves em inglês E word_count
    write_task = Task(
        description=( 
            "Contexto: Você recebeu um resumo factual sobre '{topic}' vindo da Wikipedia, prefixado com '(Fonte Wikipedia: \'Título da Fonte\')'.\n"
            "Sua Tarefa:\n"
            "Com base nesse contexto, gere o conteúdo textual para CADA UMA das seguintes chaves (em INGLÊS):\n"
            "- title: Crie um título formal para o artigo sobre '{topic}'.\n"
            "- summary: Elabore o resumo (máx 250 palavras) - objetivo, método (revisão), conclusões.\n"
            "- keywords: Liste de 3 a 5 palavras-chave relevantes em português.\n"
            "- introduction: Escreva a introdução - apresente '{topic}', relevância, objetivos, estrutura.\n"
            "- development: Elabore o corpo principal, expandindo os fatos do contexto com linguagem formal.\n"
            "- conclusions: Escreva a conclusão breve, recapitulando os pontos.\n"
            "- source_title: Extraia o 'Título da Fonte' principal do texto de contexto. O valor DEVE ser uma **única string** (não uma lista), ou `null` se nenhum título for encontrado.\n"
            "- word_count: **Calcule** a contagem total de palavras dos campos **title, summary, introduction, development, e conclusions** combinados e insira o número aqui.\n" 
            "**Formato Final OBRIGATÓRIO:** Sua resposta DEVE ser APENAS o objeto JSON, delimitado por ```json e ```, usando EXATAMENTE as chaves em INGLÊS listadas acima (incluindo word_count)."
        ),
        expected_output=(
            "Um *string* JSON válido, delimitado por ```json e ```, contendo as chaves em INGLÊS "
            "(title, summary, keywords, introduction, development, conclusions, source_title, **word_count**) " # Adicionado word_count
            "preenchidas com o conteúdo apropriado sobre '{topic}'. O campo 'source_title' deve ser uma string ou null, e 'word_count' deve ser um número inteiro."
        ),
        agent=writer,
        context=[research_task], 
    )

    # --- Montagem e Execução da Crew ---
    article_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential, 
        verbose=True, # Mantém logs detalhados da execução da Crew
    )
    
    crew_result = article_crew.kickoff(inputs={'topic': topic})

    # --- Parsing e Validação Manual da Saída ---
    if not crew_result or not hasattr(crew_result, 'raw') or not crew_result.raw:
         raise ValueError("A CrewAI não retornou um resultado bruto válido da última tarefa.")
    raw_output = crew_result.raw

    json_string = extract_json_from_text(raw_output)
    if not json_string:
        raise ValueError(f"Não foi possível extrair um bloco JSON válido da resposta do agente. Resposta recebida:\n{raw_output}")

    try:
        # Primeiro, decodifica o JSON em dict para normalizações necessárias
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"--- ERRO DE DECODIFICAÇÃO JSON ---\nTexto após extração:\n{json_string}\nErro: {e}")
        raise ValueError(f"O texto extraído não é um JSON válido: {e}\nTexto recebido:\n{json_string}") from e

    # Normalizações defensivas para lidar com saídas do agente
    # Se keywords vier como string separada por vírgulas, converte para lista de strings
    if 'keywords' in data and isinstance(data['keywords'], str):
        data['keywords'] = [k.strip() for k in data['keywords'].split(',') if k.strip()]

    # Garante que source_title vazio vire null
    if 'source_title' in data and data['source_title'] == '':
        data['source_title'] = None

    # Converte word_count para int se o agente retornou como string numérica
    if 'word_count' in data and isinstance(data['word_count'], str):
        try:
            data['word_count'] = int(data['word_count'].strip())
        except ValueError:
            pass  # deixa o Pydantic reportar o erro caso não seja um inteiro válido

    try:
        # Valida o dict normalizado contra o modelo Pydantic ArticleOutput
        parsed_output = ArticleOutput.model_validate(data)
        return parsed_output
    except ValidationError as e:
        print(f"--- ERRO DE VALIDAÇÃO PYDANTIC ---\nJSON normalizado:\n{json.dumps(data, ensure_ascii=False, indent=2)}\nErro: {e}")
        raise ValueError(f"O JSON retornado pelo agente não está no formato esperado (ArticleOutput): {e}\nJSON recebido (normalizado):\n{json.dumps(data, ensure_ascii=False, indent=2)}") from e