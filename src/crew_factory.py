# Importações necessárias
import os
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel
from src.tools.wikipedia_tool import WikipediaSearchTool
from dotenv import load_dotenv

# Define a estrutura da resposta final usando Pydantic 
class ArticleOutput(BaseModel):
    title: str
    introduction: str
    body: str
    conclusion: str
    word_count: int

# Instancia a ferramenta de busca na Wikipedia 
wikipedia_tool = WikipediaSearchTool()

# Função principal que monta e executa a Crew
def create_crew(topic: str):
    
    # Carrega a chave da API do arquivo .env 
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key:
        raise ValueError("Erro: Chave GEMINI_API_KEY não encontrada no .env!")

    # Define qual modelo LLM usar (formato provedor/modelo) 
    llm_model_name = "gemini/gemini-2.0-flash" 

    # --- Cria os Agentes --- 
    researcher = Agent(
        role="Pesquisador Sênior", 
        goal="Achar informações importantes sobre o tópico na Wikipedia.", 
        backstory="Você é bom em achar fatos corretos na Wikipedia.",
        verbose=True, 
        allow_delegation=False, 
        tools=[wikipedia_tool], 
        llm=llm_model_name 
    )

    writer = Agent(
        role="Escritor de Artigos",
        goal="Escrever um artigo claro e interessante, com pelo menos 300 palavras, usando a pesquisa.", # 
        backstory="Você escreve bem, transformando informações em textos fáceis de ler.",
        verbose=True,
        allow_delegation=False,
        llm=llm_model_name 
    )

    # --- Cria as Tarefas ---
    research_task = Task(
        description="Encontre informações sobre '{topic}' na Wikipedia.",
        expected_output="O texto completo encontrado na Wikipedia sobre '{topic}'.",
        agent=researcher 
    )

    write_task = Task(
        description=(
            "Use a pesquisa sobre '{topic}' para escrever um artigo de blog (mínimo 300 palavras).\n" # 
            "Organize com: Título, Introdução, Desenvolvimento e Conclusão.\n"
            "Formate a resposta final como pedido (usando ArticleOutput)." # 
        ),
        expected_output="O artigo final formatado como um objeto ArticleOutput (JSON).", # 
        agent=writer,
        context=[research_task], # Define que esta tarefa usa o resultado da 'research_task'
        output_pydantic=ArticleOutput # Garante que a saída final siga o modelo Pydantic 
    )

    # --- Monta e Roda a Crew --- 
    article_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential, # Tarefas executadas em ordem
        verbose=True, 
    )
    
    # Inicia a execução da Crew com o tópico fornecido
    result = article_crew.kickoff(inputs={'topic': topic})
    
    # Retorna o resultado final (o artigo formatado)
    return result