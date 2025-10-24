import streamlit as st
# Importa a função principal da sua lógica CrewAI e o modelo de saída
from src.crew_factory import create_crew, ArticleOutput 

# --- Configuração da Página ---
st.set_page_config(page_title="Gerador de Artigos CrewAI", layout="wide")

# --- Título e Descrição ---
st.title("🤖 Gerador de Artigos com CrewAI e Wikipedia")
st.markdown("""
    Digite um tópico abaixo e clique em 'Gerar Artigo'. 
    A inteligência artificial irá pesquisar na Wikipedia e escrever um artigo sobre o tema.
""")

# --- Input do Usuário ---
topic = st.text_input("Qual o tópico do artigo?", placeholder="Ex: Inteligência Artificial no Brasil")

# --- Botão de Ação ---
if st.button("Gerar Artigo", type="primary"):
    # Verifica se o usuário digitou um tópico
    if topic:
        # Mostra uma mensagem de "carregando" enquanto a Crew trabalha
        with st.spinner(f"Pesquisando e escrevendo sobre '{topic}'... Por favor, aguarde, isso pode levar um minuto ou mais."):
            try:
                # Chama a função principal da sua CrewAI
                # Especificamos o tipo de retorno esperado
                crew_result = create_crew(topic) 
                
                # Extrai o resultado Pydantic (se existir)
                if crew_result and hasattr(crew_result, 'pydantic') and crew_result.pydantic:
                    article: ArticleOutput = crew_result.pydantic
                    
                    # --- Exibe o Resultado ---
                    st.divider() # Linha divisória
                    st.subheader(f"📄 Artigo Gerado: {article.title}")
                    
                    if article.source_title:
                         st.caption(f"Fonte principal da Wikipedia: {article.source_title}") # Mostra o título da fonte
                    
                    st.markdown("### Introdução")
                    st.write(article.introduction)
                    
                    st.markdown("### Desenvolvimento")
                    st.write(article.body) # st.write lida bem com quebras de linha (\n)
                    
                    st.markdown("### Conclusão")
                    st.write(article.conclusion)
                    
                    st.divider() 
                    st.success(f"Artigo gerado com sucesso! ({article.word_count} palavras)")

                else:
                    # Se o resultado não tiver o .pydantic esperado (caso raro)
                    st.error("A CrewAI finalizou, mas não retornou o artigo no formato esperado.")
                    st.write("Resultado bruto recebido:")
                    st.write(crew_result) # Mostra o resultado bruto para debug

            # Captura erros específicos ou gerais durante a execução da Crew
            except ValueError as ve: # Captura o erro da API Key não encontrada
                 st.error(f"Erro de Configuração: {ve}")
            except Exception as e:
                # Captura outros erros (como 503 da API, erros na ferramenta, etc.)
                st.error(f"Ocorreu um erro durante a geração do artigo:")
                st.exception(e) # Mostra o traceback do erro de forma formatada

    else:
        # Se o usuário clicar no botão sem digitar um tópico
        st.warning("Por favor, digite um tópico antes de gerar o artigo.")

# --- Rodapé (Opcional) ---
st.sidebar.info("Desenvolvido por Andresantoss")
st.sidebar.markdown("GitHub: [Repositório do Projeto](https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss)")