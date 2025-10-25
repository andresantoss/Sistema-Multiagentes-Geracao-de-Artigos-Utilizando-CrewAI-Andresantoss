import streamlit as st
# Importa o ArticleOutput (que agora inclui word_count)
from src.crew_factory import create_crew, ArticleOutput 

# --- Configuração da Página ---
st.set_page_config(page_title="Sistema Multiagente para Geração de Artigos com CrewAI", layout="wide") 

# --- Título e Descrição ---
st.title("🤖 Sistema Multiagente para Geração de Artigos com CrewAI") 
st.markdown("""
    Este projeto usa agentes de IA (CrewAI) para escrever artigos automaticamente. 
    Você fornece um tópico através de uma interface web simples (Streamlit), 
    o sistema pesquisa na API da Wikipedia para obter contexto e usa o Google Gemini 
    para gerar um artigo de pelo menos 300 palavras, que é exibido diretamente na interface.
""") 

# --- Input do Usuário ---
topic = st.text_input("Qual o tópico do artigo?", placeholder="Ex: Inteligência Artificial no Brasil") 

# --- Botão de Ação ---
if st.button("Gerar Artigo", type="primary"): 
    if topic:
        with st.spinner(f"Pesquisando e escrevendo sobre '{topic}'... Por favor, aguarde, isso pode levar um minuto ou mais."): 
            try:
                # create_crew retorna o objeto Pydantic ArticleOutput
                article: ArticleOutput = create_crew(topic) 
                    
                # --- Exibe os campos (incluindo os nomes em inglês) ---
                st.divider() 
                st.subheader(f"📄 Artigo Gerado: {article.title}")
                    
                if article.source_title:
                     st.caption(f"Fonte principal da Wikipedia: {article.source_title}") 
                
                st.markdown("### Resumo") 
                st.write(article.summary) 

                st.markdown("### Palavras-Chave")
                st.write(", ".join(article.keywords)) 
                
                st.markdown("### Introdução")
                st.write(article.introduction) 
                    
                st.markdown("### Desenvolvimento")
                st.write(article.development) 
                    
                st.markdown("### Conclusões")
                st.write(article.conclusions) 
                    
                st.divider() 
                
                # --- CORREÇÃO APLICADA AQUI ---
                # Exibe a mensagem de sucesso COM a contagem de palavras
                st.success(f"Artigo gerado com sucesso! ({article.word_count} palavras)")
                # st.success("Artigo gerado com sucesso!") # Linha antiga comentada/removida

            except ValueError as ve: 
                 st.error(f"Erro: {ve}") 
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado durante a geração:") 
                st.exception(e) 

    else:
        st.warning("Por favor, digite um tópico antes de gerar o artigo.")

# --- Rodapé ---
st.sidebar.info("Desenvolvido por Andresantoss")
st.sidebar.markdown("GitHub: [Repositório do Projeto](https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss)")