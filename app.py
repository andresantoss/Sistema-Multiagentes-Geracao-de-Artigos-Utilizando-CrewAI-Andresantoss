import streamlit as st
from src.crew_factory import create_crew, ArticleOutput 

# --- Configuração da Página ---
st.set_page_config(page_title="Sistema Multiagente para Geração de Artigos com CrewAI", layout="wide") 

# --- CSS Customizado para Centralizar Imagem e Legenda ---
st.markdown("""
    <style>
        /* Container para centralizar a imagem e a legenda dentro do infobox */
        .infobox-image-container {
            display: flex;
            flex-direction: column;
            align-items: center; /* Centraliza horizontalmente */
            text-align: center;   /* Centraliza texto da legenda */
            margin-bottom: 10px; /* Espaçamento abaixo da imagem/legenda */
        }
        /* Estilo da legenda (similar ao <figcaption>) */
        .infobox-image-container figcaption {
            font-size: 0.9em;
            color: #6c757d; /* Cor padrão de legenda do Streamlit */
            padding: 2px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- Título e Descrição ---
st.title("🤖 Sistema Multiagente para Geração de Artigos com CrewAI") 
st.markdown("""
    Este projeto usa agentes de IA (CrewAI) para escrever artigos automaticamente. 
    Você fornece um tópico através de uma interface web simples (Streamlit), 
    o sistema pesquisa na API da Wikipedia para obter contexto e usa o Google Gemini 
    para gerar um artigo (no estilo NBR 6022), que é exibido diretamente na interface.
""") 

# --- Input do Usuário ---
topic = st.text_input("Qual o tópico do artigo?", placeholder="Ex: Inteligência Artificial no Brasil") 

# URL da imagem placeholder
placeholder_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png"

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
                    
                    st.markdown(f'<a name="{anchor_top}"></a>', unsafe_allow_html=True) 
                    st.title(article.title)
                    st.divider()
                    
                    st.markdown(f'<a name="{anchor_summary}"></a>', unsafe_allow_html=True)
                    st.subheader("Resumo")
                    st.write(article.summary)
                    
                    st.markdown(f'<a name="{anchor_intro}"></a>', unsafe_allow_html=True)
                    st.header(article.introduction_subtitle) 
                    st.write(article.introduction_content)
                    
                    st.markdown(f'<a name="{anchor_dev}"></a>', unsafe_allow_html=True) 
                    st.header(article.development_subtitle) 
                    st.write(article.development_content) 
                        
                    st.markdown(f'<a name="{anchor_conc}"></a>', unsafe_allow_html=True)
                    st.header(article.conclusion_subtitle) 
                    st.write(article.conclusion_content) 
                        
                    st.divider() 

                    # --- Seções Finais (Notas e Referências) ---
                    
                    st.markdown(f'<a name="{anchor_notes}"></a>', unsafe_allow_html=True)
                    st.subheader("Notas")
                    keywords_str = ", ".join(article.keywords)
                    st.caption(f"**Palavras-chave:** {keywords_str}.")

                    st.markdown(f'<a name="{anchor_refs}"></a>', unsafe_allow_html=True)
                    st.subheader("Referências")
                    
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
                    # --- INFOBOX (Direita) ---
                    with st.container(border=True):
                        st.subheader(f"{topic.title()}")
                        
                        # Usa a imagem da Wikipedia se encontrada, senão usa o placeholder
                        image_to_display = article.image_url if article.image_url else placeholder_image_url
                        # Usa a legenda gerada pela IA, ou um fallback
                        caption_to_display = article.image_caption if article.image_caption else "Imagem ilustrativa"
                        
                        # Usa HTML/CSS para centralizar a imagem e a legenda
                        st.markdown(
                            f"""
                            <div class="infobox-image-container">
                                <img src="{image_to_display}" width="300" style="aspect-ratio: auto 300 / 250; height: auto;">
                                <figcaption>{caption_to_display}</figcaption>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        st.markdown(f"**Informação geral**")
                        st_name = "Sem Fonte"
                        if article.source_title:
                            st_name = article.source_title
                        st.caption(f"Artigo principal da fonte: {st_name}")
                        st.caption(f"Contagem de Palavras: {article.word_count}")

                # --- 2. SUMÁRIO (Sidebar Esquerda - Pós Geração) ---
                st.sidebar.divider()
                
                with st.sidebar.expander("Conteúdo"):
                    # CSS Customizado (movido para o topo do script)
                    st.markdown(
                        """
                        <style>
                            .toc-link { text-decoration: none; color: inherit !important; }
                            .toc-item { margin-bottom: 5px; }
                        </style>
                        """, 
                        unsafe_allow_html=True
                    )
                    
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