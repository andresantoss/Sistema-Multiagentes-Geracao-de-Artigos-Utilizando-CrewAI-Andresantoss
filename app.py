import streamlit as st
from src.crew_factory import create_crew, ArticleOutput
from typing import List

# --- Configuração da Página ---
st.set_page_config(
    page_title="Sistema Multiagente para Geração de Artigos com CrewAI",
    layout="wide",
)

# --- Cabeçalho / Descrição ---
st.title("Sistema Multiagente para Geração de Artigos com CrewAI")
st.markdown(
    """
    Ferramenta que usa agentes (CrewAI) para pesquisar na Wikipedia e gerar um artigo
    com o Google Gemini. Informe um tópico e clique em "Gerar Artigo".
    """
)

# --- Entrada do Usuário ---
topic = st.text_input(
    "Qual o tópico do artigo?",
    placeholder="Ex: História do futebol do Brasil",
)

# URL da imagem placeholder usada no infobox direito
placeholder_image_url = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png"
)

# --- Botão de Ação: gera o artigo quando clicado ---
if st.button("Gerar Artigo", type="primary"):
    if not topic:
        st.warning("Por favor, digite um tópico antes de gerar a estrutura.")
    else:
        with st.spinner(f"Pesquisando e gerando artigo sobre '{topic}'... Por favor, aguarde."):
            try:
                # Executa a rotina principal que retorna um ArticleOutput (Pydantic)
                article: ArticleOutput = create_crew(topic)

                # --- Ancoras para Sumário / Navegação interna ---
                anchor_top = "top"
                anchor_summary = "resumo"
                anchor_intro = "introducao"
                anchor_dev = "desenvolvimento"
                anchor_conc = "conclusao"
                anchor_notes = "notas"
                anchor_refs = "referencias"

                # --- Layout principal: conteúdo + infobox lateral ---
                col_main, col_infobox = st.columns([2.5, 1])

                # Conteúdo principal (col_main)
                with col_main:
                    st.markdown(f'<a name="{anchor_top}"></a>', unsafe_allow_html=True)
                    st.title(article.title)
                    st.divider()

                    # Resumo
                    st.markdown(f'<a name="{anchor_summary}"></a>', unsafe_allow_html=True)
                    st.subheader("Resumo")
                    st.write(article.summary)

                    # Introdução (subtítulo dinâmico + conteúdo)
                    st.markdown(f'<a name="{anchor_intro}"></a>', unsafe_allow_html=True)
                    st.header(article.introduction_subtitle)
                    st.write(article.introduction_content)

                    # Desenvolvimento (subtítulo dinâmico + conteúdo)
                    st.markdown(f'<a name="{anchor_dev}"></a>', unsafe_allow_html=True)
                    st.header(article.development_subtitle)
                    st.write(article.development_content)

                    # Conclusão (subtítulo dinâmico + conteúdo)
                    st.markdown(f'<a name="{anchor_conc}"></a>', unsafe_allow_html=True)
                    st.header(article.conclusion_subtitle)
                    st.write(article.conclusion_content)

                    st.divider()

                    # Notas (palavras-chave)
                    st.markdown(f'<a name="{anchor_notes}"></a>', unsafe_allow_html=True)
                    st.subheader("Notas")
                    keywords: List[str] = article.keywords or []
                    keywords_str = ", ".join(keywords) if keywords else "Nenhuma palavra-chave"
                    st.caption(f"**Palavras-chave:** {keywords_str}.")

                    # Referências (formatação ABNT simples)
                    st.markdown(f'<a name="{anchor_refs}"></a>', unsafe_allow_html=True)
                    st.subheader("Referências")
                    if article.source_title and article.source_url and article.access_date:
                        abnt_title = article.source_title.upper()
                        abnt_url = article.source_url
                        abnt_access = article.access_date
                        abnt_reference = (
                            f"{abnt_title}. In: WIKIPÉDIA: a enciclopédia livre. "
                            f"Disponível em: <{abnt_url}>. "
                            f"Acesso em: {abnt_access}."
                        )
                        st.markdown(abnt_reference)
                    else:
                        st.caption("Não foi possível gerar a referência ABNT (dados da fonte ausentes).")

                    st.success(f"Artigo gerado com sucesso! ({article.word_count} palavras)")

                # Infobox lateral (col_infobox)
                with col_infobox:
                    with st.container():
                        st.subheader(f"{topic.title()}")
                        st.image(placeholder_image_url, width=300, caption="Imagem ilustrativa (placeholder)")
                        st.markdown("**Informação geral**")
                        st_name = article.source_title if article.source_title else "Sem Fonte"
                        st.caption(f"Artigo principal da fonte: {st_name}")
                        st.caption(f"Contagem de Palavras: {article.word_count}")

                # --- Sumário na sidebar (expansível) ---
                with st.sidebar.expander("Conteúdo"):
                    # Pequeno CSS para estilo das âncoras do TOC
                    st.markdown(
                        """
                        <style>
                            .toc-link { text-decoration: none; color: inherit !important; }
                            .toc-item { margin-bottom: 5px; }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

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
                # Erros esperados (validação, entrada do agente, etc.)
                st.error(f"Erro: {ve}")
            except Exception as e:
                # Erro inesperado: mostrar exceção para debug
                st.error("Ocorreu um erro inesperado durante a geração:")
                st.exception(e)

# --- Rodapé e informações na sidebar ---
st.sidebar.divider()
st.sidebar.info("Desenvolvido por Andresantoss")
st.sidebar.markdown(
    "GitHub: [Repositório do Projeto](https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss)"
)