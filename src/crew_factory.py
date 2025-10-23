import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from src.tools.wikipedia_tool import WikipediaSearchTool
from dotenv import load_dotenv

load_dotenv()

# --- Requisito Extra: Output com Pydantic --- 
class ArticleOutput(BaseModel):
    title: str
    introduction: str
    body: str
    conclusion: str
    word_count: int

# 1. Configurar o LLM (Pode ficar aqui fora)
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# 2. Instanciar a Ferramenta (Pode ficar aqui fora)
wikipedia_tool = WikipediaSearchTool()


# 5. Montar a Crew (AGORA TUDO FICA AQUI DENTRO)
def create_crew(topic: str):

    # 3. Definir Agentes (MOVEMOS PARA CÁ)
    # Agente Pesquisador
    researcher = Agent(
        role="Pesquisador Sênior",
        goal="Buscar informações contextuais e relevantes sobre um tópico usando a Wikipedia.",
        backstory="Você é um especialista em pesquisa acadêmica, "
                  "focado em extrair informações precisas e úteis da Wikipedia.",
        verbose=True,
        allow_delegation=False,
        tools=[wikipedia_tool]
        # REMOVA llm=llm DAQUI
    )

    # Agente Redator
    writer = Agent(
        role="Redator de Artigos Tecnológicos",
        goal="Escrever um artigo envolvente e informativo, com no mínimo 300 palavras, "
             "baseado nas informações fornecidas pelo pesquisador.", # 
        backstory="Você é um redator de blog experiente, "
                  "capaz de transformar fatos brutos em uma narrativa coesa e interessante.",
        verbose=True,
        allow_delegation=False
        # REMOVA llm=llm DAQUI
    )

    # 4. Definir Tarefas (MOVEMOS PARA CÁ)
    research_task = Task(
        description="Pesquise sobre o tópico '{topic}' na Wikipedia. "
                    "Compile todas as informações relevantes encontradas.",
        expected_output="Um documento de texto contendo o extrato completo da Wikipedia sobre o tópico.",
        agent=researcher
    )

    write_task = Task(
        description=(
            "Usando as informações da pesquisa, escreva um artigo de blog completo sobre o tópico '{topic}'.\n"
            "O artigo DEVE ter no mínimo 300 palavras. \n"
            "Estruture o artigo com: \n"
            "1. Um título atraente.\n"
            "2. Uma introdução clara.\n"
            "3. Um corpo de texto (desenvolvimento) detalhado.\n"
            "4. Uma conclusão sólida.\n"
            "Formate a saída final usando o modelo Pydantic ArticleOutput. "
        ),
        expected_output="Um objeto Pydantic 'ArticleOutput' preenchido com o artigo finalizado.",
        agent=writer,
        context=[research_task],
        output_pydantic=ArticleOutput
    )

    # Montagem final da Crew
    article_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=2,
        llm=llm  # <-- ADICIONE O LLM AQUI, NA CREW
    )
    
    result = article_crew.kickoff(inputs={'topic': topic})
    return result