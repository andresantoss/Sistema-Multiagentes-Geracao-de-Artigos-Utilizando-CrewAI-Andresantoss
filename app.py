import os
import streamlit as st
from src.crew_factory import create_crew, ArticleOutput

# --- Configuração da Página ---
st.set_page_config(page_title="Sistema Multiagente para Geração de Artigos com CrewAI", layout="wide") 

# --- CSS Customizado (CORREÇÃO ÂNCORA + CENTRALIZAÇÃO INFOBOX) ---
st.markdown("""
    <style>
        /* ÂNCORA  */
        div[id] {
            scroll-margin-top: 100px; 
        }
        
        /* Centraliza o título do infobox */
        .infobox-title {
            text-align: center;
        }

        /* Container para centralizar a imagem e a legenda */
        .infobox-image-container {
            display: flex;
            flex-direction: column;
            align-items: center; 
            text-align: center;   
            margin-bottom: 10px; 
        }
            
        .infobox-image-container figcaption {
            font-size: 0.9em;
            color: #6c757d; 
            padding: 2px 0;
        }

        /* Estilos do Sumário (TOC) */
        .toc-link { 
            text-decoration: none; 
            color: inherit !important; 
        }
        .toc-item { 
            margin-bottom: 5px; 
        }
    </style>
""", unsafe_allow_html=True)

# --- Título e Descrição ---
st.title("🤖 Sistema Multiagente para Geração de Artigos com CrewAI") 
st.markdown("""
    Este projeto usa agentes de IA (CrewAI) para escrever artigos automaticamente. Você fornece um tópico através de uma interface web simples (Streamlit), o sistema pesquisa na API da Wikipedia para obter contexto e usa o Google Gemini para gerar um artigo de pelo menos 300 palavras, que é exibido diretamente na interface.
""") 

# --- Input do Usuário ---
topic = st.text_input("Qual o tópico do artigo?", placeholder="Ex: Inteligência Artificial no Brasil") 

# URL da imagem placeholder REMOTO (fallback)
remote_placeholder_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png"

# Caminho local do placeholder solicitado (Windows). Use r-string para evitar escape de \
placeholder_image_path = r"src\No-Image-Placeholder.svg.png"

# --- Botão de Ação ---
if st.button("Gerar Artigo", type="primary"): 
    if topic:
        with st.spinner(f"Pesquisando e gerando artigo sobre '{topic}'... Por favor, aguarde."): 
            try:
                article: ArticleOutput = create_crew(topic) 
                
                # Define âncoras para o sumário (TOC)
                anchor_top = "top"
                anchor_summary = "resumo"
                anchor_intro = "introducao"
                anchor_dev = "desenvolvimento"
                anchor_conc = "conclusao"
                anchor_notes = "notas"
                anchor_refs = "referencias"

                # --- 1. LAYOUT PRINCIPAL (Conteúdo e Infobox) ---
                col_main, col_infobox = st.columns([2.5, 1]) 

                with col_main:
                    # --- CONTEÚDO PRINCIPAL (Esquerda) ---
                    
                    # Usa a estrutura de âncora DIV + Título
                    st.markdown(f'<div id="{anchor_top}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h1>{article.title}</h1>', unsafe_allow_html=True)
                    st.divider()
                    
                    st.markdown(f'<div id="{anchor_summary}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>Resumo</h2>', unsafe_allow_html=True)
                    st.write(article.summary)
                    
                    st.markdown(f'<div id="{anchor_intro}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>{article.introduction_subtitle}</h2>', unsafe_allow_html=True) 
                    st.write(article.introduction_content)
                    
                    st.markdown(f'<div id="{anchor_dev}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>{article.development_subtitle}</h2>', unsafe_allow_html=True) 
                    st.write(article.development_content) 
                        
                    st.markdown(f'<div id="{anchor_conc}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>{article.conclusion_subtitle}</h2>', unsafe_allow_html=True)
                    st.write(article.conclusion_content) 
                        
                    st.divider()

                    # --- Seções Finais (Notas e Referências) ---
                    
                    st.markdown(f'<div id="{anchor_notes}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>Notas</h2>', unsafe_allow_html=True)
                    keywords_str = ", ".join(article.keywords)
                    st.caption(f"**Palavras-chave:** {keywords_str}.")

                    st.markdown(f'<div id="{anchor_refs}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>Referências</h2>', unsafe_allow_html=True)
                    
                    if article.source_title and article.source_url and article.access_date:
                        abnt_title = article.source_title.upper()
                        abnt_url = article.source_url
                        abnt_access = article.access_date.lower()
                        
                        abnt_reference = (
                            f"{abnt_title}. In: WIKIPÉDIA: a enciclopédia livre. "
                            f"Disponível em: <{abnt_url}>. "
                            f"Acesso em: {abnt_access}."
                        )
                        st.markdown(abnt_reference)
                    else:
                        st.caption("Não foi possível gerar a referência ABNT (dados da fonte ausentes).")
                    
                    st.success(f"Artigo gerado com sucesso! ({article.word_count} palavras)")

                with col_infobox:
                    # Infobox simples (Streamlit container sem border param)
                    st.markdown(f'<h3 class="infobox-title">{topic.title()}</h3>', unsafe_allow_html=True)

                    # Escolhe imagem: primeiro tenta image retornada pelo ArticleOutput,
                    # depois arquivo local placeholder, por fim URL remota fallback.
                    image_to_display = None
                    caption_to_display = "Imagem ilustrativa"

                    if getattr(article, "image_url", None):
                        image_to_display = article.image_url
                        caption_to_display = getattr(article, "image_caption", "Imagem obtida da Wikipedia")
                    elif os.path.exists(placeholder_image_path):
                        image_to_display = placeholder_image_path
                        caption_to_display = "Placeholder local"
                    else:
                        image_to_display = remote_placeholder_image_url
                        caption_to_display = "Placeholder remoto"

                    # Exibe imagem usando st.image (funciona com caminho local ou URL)
                    st.image(image_to_display, width=300, caption=caption_to_display)

                    st.markdown("**Informação geral**")
                    st.caption(f"Artigo principal da fonte: {article.source_title or 'Sem Fonte'}")
                    st.caption(f"Contagem de Palavras: {article.word_count}")

                # --- 2. SUMÁRIO (Sidebar Esquerda - Pós Geração) ---
                st.sidebar.divider()
                
                with st.sidebar.expander("Conteúdo"):
                    # Links HTML (Sumário)
                    toc_html = f"""
                    <div class="toc-item"><a class="toc-link" href="#{anchor_top}">Início</a></div>
                    <div class="toc-item"><a class="toc-link" href="#{anchor_summary}">Resumo</a></div>
                    <div class="toc-item"><a class="toc-link" href="#{anchor_intro}">{article.introduction_subtitle}</a></div>
                    <div class="toc-item"><a class="toc-link" href="#{anchor_dev}">{article.development_subtitle}</a></div>
                    <div class="toc-item"><a class="toc-link" href="#{anchor_conc}">{article.conclusion_subtitle}</a></div>
                    <div class="toc-item"><a class="toc-link" href="#{anchor_notes}">Notas</a></div>
                    <div class="toc-item"><a class="toc-link" href="#{anchor_refs}">Referências</a></div>
                    """
                    st.markdown(toc_html, unsafe_allow_html=True)
                
            except ValueError as ve: 
                 st.error(f"Erro: {ve}") 
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado durante a geração:") 
                st.exception(e) 

    else:
        st.warning("Por favor, digite um tópico antes de gerar a estrutura.")

# --- Rodapé (SEMPRE VISÍVEL) ---
st.sidebar.info("Desenvolvido por Andresantoss")
st.sidebar.markdown("GitHub: [Repositório do Projeto](https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss)")