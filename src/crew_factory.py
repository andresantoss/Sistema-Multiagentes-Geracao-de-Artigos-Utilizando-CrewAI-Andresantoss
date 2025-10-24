import os
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field
from src.tools.wikipedia_tool import WikipediaSearchTool
from dotenv import load_dotenv

# Define o schema de saída do artigo utilizando Pydantic para validação e clareza.
class ArticleOutput(BaseModel):
    title: str = Field(..., description="Título principal do artigo gerado.")
    introduction: str = Field(..., description="Parágrafo introdutório do artigo.")
    body: str = Field(..., description="Corpo principal do artigo, com desenvolvimento do tema.")
    conclusion: str = Field(..., description="Parágrafo de conclusão do artigo.")
    word_count: int = Field(..., description="Contagem total de palavras no artigo gerado.")
    source_title: str | None = Field(None, description="Título exato do artigo da Wikipedia utilizado como fonte principal.")

# Instancia a ferramenta Wikipedia para ser utilizada pelos agentes.
wikipedia_tool = WikipediaSearchTool()

# Função que configura e executa a Crew de geração de artigos.
def create_crew(topic: str):
    """
    Monta e executa uma CrewAI para pesquisar um tópico na Wikipedia e escrever um artigo.

    Args:
        topic: O tópico/assunto para o artigo.

    Returns:
        Um objeto ArticleOutput (validado pelo Pydantic) contendo o artigo gerado.
        
    Raises:
        ValueError: Se a chave GEMINI_API_KEY não for encontrada no .env.
    """
    load_dotenv() # Carrega variáveis de ambiente do arquivo .env
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key: 
        # Garante que a chave da API esteja configurada antes de prosseguir.
        raise ValueError("Erro: Chave GEMINI_API_KEY não encontrada no .env!")

    # Define o modelo LLM a ser usado (formato 'provedor/nome_modelo' para LiteLLM/CrewAI).
    llm_model_name = "gemini/gemini-2.0-flash" # Confirmado como funcional neste ambiente

    # --- Definição dos Agentes ---
    researcher = Agent(
        role="Especialista em Pesquisa Digital",
        goal=f"Localizar e extrair o conteúdo do artigo mais relevante na Wikipedia sobre '{topic}', incluindo o título exato da fonte.",
        backstory=(
            "Mestre em recuperação de informação via Wikipedia API, hábil em encontrar "
            "artigos pertinentes mesmo com termos de busca imprecisos e em registrar a fonte."
        ),
        verbose=True, # Loga as ações e pensamentos do agente.
        allow_delegation=False, # Mantém o fluxo simples, sem delegação.
        tools=[wikipedia_tool], # Ferramenta disponível para este agente.
        llm=llm_model_name # LLM que o agente utilizará.
    )

    writer = Agent(
        role="Redator de Conteúdo Web",
        goal=(
            f"Produzir um artigo de blog claro e informativo (mínimo 300 palavras) sobre '{topic}', "
            f"baseado estritamente na pesquisa fornecida, para um público geral."
        ), 
        backstory=(
            "Escritor experiente na síntese de informações de pesquisa (como extratos da Wikipedia) "
            "em artigos de blog bem estruturados e acessíveis. Foca em clareza, estrutura e aderência às instruções."
        ),
        verbose=True,
        allow_delegation=False, # Focado na tarefa de escrita.
        llm=llm_model_name 
    )

    # --- Definição das Tarefas ---
    research_task = Task(
        description=(
            "Utilize a ferramenta de busca na Wikipedia para obter o conteúdo mais relevante sobre '{topic}'. "
            "A ferramenta tratará buscas exatas e amplas."
        ),
        expected_output=( 
             "O resultado textual da ferramenta, iniciando com o título da fonte encontrada "
             "(e.g., '(Fonte Wikipedia: \'Título\')\\n\\n...') seguido pelo extrato ou snippet."
        ),
        agent=researcher # Agente designado para esta tarefa.
    )

    write_task = Task(
        description=( 
            "Contexto: Você recebeu um texto prefixado com '(Fonte Wikipedia: \'Título\')' contendo informações sobre '{topic}'.\n"
            "Sua Tarefa:\n"
            "1. Escreva um artigo de blog original e informativo sobre '{topic} (mínimo 300 palavras).\n"
            "2. Estruture com: Título Principal (novo), Introdução, Desenvolvimento, Conclusão.\n"
            "3. Extraia o 'Título da Fonte' do texto de contexto e preencha o campo 'source_title'.\n"
            "4. Calcule a contagem de palavras do seu artigo e preencha 'word_count'.\n"
            "5. Formate a resposta final completa como um JSON seguindo o modelo ArticleOutput.\n"
            "Restrições: Use apenas a informação fornecida. Não inclua o prefixo '(Fonte Wikipedia:...)' no artigo final."
        ),
        expected_output=( 
            "Um objeto JSON válido aderente ao schema ArticleOutput, com todos os campos "
            "(title, introduction, body, conclusion, word_count, source_title) corretamente preenchidos."
        ),
        agent=writer,
        context=[research_task], # Depende do output da tarefa anterior.
        output_pydantic=ArticleOutput # Força a validação e formatação da saída final.
    )
    
    # --- Montagem e Execução da Crew ---
    article_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential, # Garante a execução ordenada das tarefas.
        verbose=True, # Habilita logging do fluxo da Crew.
    )
    
    # Inicia o processo da Crew.
    result = article_crew.kickoff(inputs={'topic': topic})
    
    # Retorna o resultado final, que deve ser uma instância de ArticleOutput.
    return result