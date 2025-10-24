import os
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field
from src.tools.wikipedia_tool import WikipediaSearchTool
from dotenv import load_dotenv

# Define o schema de saída
class ArticleOutput(BaseModel):
    title: str = Field(..., description="Título principal do artigo gerado.")
    introduction: str = Field(..., description="Parágrafo introdutório do artigo.")
    body: str = Field(..., description="Corpo principal do artigo, com desenvolvimento do tema.")
    conclusion: str = Field(..., description="Parágrafo de conclusão do artigo.")
    word_count: int = Field(..., description="Contagem total de palavras no artigo gerado.")
    source_title: str | None = Field(None, description="Título(s) do(s) artigo(s) da Wikipedia utilizado(s) como fonte principal.") 

# Instancia a ferramenta
wikipedia_tool = WikipediaSearchTool()

# Função principal
def create_crew(topic: str):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key: raise ValueError("Erro: Chave GEMINI_API_KEY não encontrada no .env!")

    llm_model_name = "gemini/gemini-2.0-flash" 

    # --- Definição dos Agentes ---
    researcher = Agent(
        role="Especialista em Pesquisa Digital",
        goal=f"Coletar e sintetizar informações relevantes da Wikipedia sobre '{topic}', focando nos aspectos mais pertinentes ao tópico solicitado.", 
        backstory=(
            "Mestre em recuperação de informação via Wikipedia API, hábil em encontrar "
            "artigos pertinentes mesmo com termos de busca imprecisos, registrar a fonte, e resumir os achados chave." 
        ),
        verbose=True, 
        allow_delegation=False, 
        tools=[wikipedia_tool], 
        llm=llm_model_name,
        #Limita o número máximo de ciclos de pensamento/ação do agente
        max_iter=5  # Permite algumas tentativas de busca/refinamento, mas evita loops longos
    )

    writer = Agent(
        role="Redator de Conteúdo Web",
        goal=(
            f"Produzir um artigo de blog claro e informativo (mínimo 300 palavras) **focado estritamente no tópico original '{topic}'**, " 
            f"utilizando a pesquisa fornecida como base e adaptando-a conforme necessário, destinado a um público geral."
        ), 
        backstory=(
            "Escritor experiente na síntese de informações de pesquisa "
            "em artigos de blog bem estruturados e acessíveis. Foca em clareza, estrutura, aderência às instruções e, crucialmente, "
            "em manter a relevância ao tópico principal solicitado pelo usuário." 
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm_model_name 
    )

    # --- Definição das Tarefas ---

    # Tarefa de Pesquisa: Foco em relevância, resumo E LIMITE DE TAMANHO
    research_task = Task(
        description=(
            "1. Use a ferramenta de busca da Wikipedia UMA VEZ para encontrar informações sobre '{topic}'.\n"
            "2. Analise o resultado: O artigo encontrado é diretamente sobre '{topic}' ou sobre um tema relacionado?\n"
            "3. Se o resultado inicial não for diretamente relevante ou for muito amplo, considere usar a ferramenta NOVAMENTE (no máximo mais 1 ou 2 vezes) com termos mais específicos derivados de '{topic}' para obter mais contexto, se absolutamente necessário.\n" # Guia para limitar novas buscas
            "4. **Sintetize** as informações *mais importantes e relevantes* que você encontrou sobre '{topic}' em um resumo conciso.\n"
            "5. **Limite o resumo final a no máximo 3 parágrafos ou aproximadamente 250 palavras.**\n"
            "6. Inclua o(s) título(s) exato(s) da(s) fonte(s) consultada(s) (prefixo '(Fonte Wikipedia: ...)') no início do seu resumo."
        ),
        expected_output=(
             "Um resumo conciso e informativo (máximo 3 parágrafos/~250 palavras) contendo os pontos principais encontrados sobre '{topic}', "
             "iniciando com o(s) título(s) da(s) fonte(s) da Wikipedia utilizada(s) (prefixo '(Fonte Wikipedia: ...)' )."
             "O resumo deve ser útil e direto ao ponto para alguém escrever um artigo sobre '{topic}'."
        ),
        agent=researcher 
    )

    # Tarefa de Escrita:
    write_task = Task(
        description=( 
            "Contexto: Você recebeu um resumo de pesquisa sobre '{topic}', prefixado com '(Fonte Wikipedia: \'Título da Fonte\')'.\n"
            "Sua Tarefa:\n"
            "1. Escreva um artigo de blog original, claro e informativo (mínimo 300 palavras) **focado no tópico original '{topic}'**. Use o resumo da pesquisa como base principal, mas adapte e expanda as ideias para garantir que o artigo final seja sobre '{topic}'.\n" 
            "2. Estruture com: Título Principal (novo e sobre '{topic}'), Introdução, Desenvolvimento, Conclusão.\n"
            "3. Extraia o(s) 'Título(s) da(s) Fonte(s)' do texto de contexto e preencha o campo 'source_title'. Se houver mais de um, liste-os separados por vírgula.\n"
            "4. Calcule a contagem de palavras do seu artigo e preencha 'word_count'.\n"
            "5. Formate a resposta final completa como um JSON seguindo o modelo ArticleOutput.\n"
            "Restrições: Use *primariamente* a informação fornecida, mas **mantenha o foco em '{topic}'**. Não inclua o prefixo '(Fonte Wikipedia:...)' no artigo final."
        ),
        expected_output=( 
            "Um objeto JSON válido aderente ao schema ArticleOutput, com todos os campos "
            "(title, introduction, body, conclusion, word_count, source_title) corretamente preenchidos, "
            "e cujo conteúdo (title, introduction, body, conclusion) seja **claramente sobre o tópico original '{topic}'**." 
        ),
        agent=writer,
        context=[research_task], 
        output_pydantic=ArticleOutput 
    )

    # --- Montagem e Execução da Crew ---
    article_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential, 
        verbose=True, 
    )
    
    result = article_crew.kickoff(inputs={'topic': topic})
    return result