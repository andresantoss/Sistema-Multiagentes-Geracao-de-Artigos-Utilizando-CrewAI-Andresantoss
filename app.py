import os
from datetime import datetime
from urllib.parse import quote

import streamlit as st
from src.crew_factory import create_crew, ArticleOutput
from google.genai.errors import ServerError

# ---------- Configuração da página e CSS ----------
st.set_page_config(page_title="Sistema Multiagente - CrewAI", layout="wide")

st.markdown(
    """
    <style>
        /* Espaçamento superior para evitar corte ao navegar por âncoras */
        div[id] { scroll-margin-top: 70px; }

        /* Infobox */
        .infobox-title { text-align: center; margin-bottom: 6px; }
        .infobox-image-container { display:flex; flex-direction:column; align-items:center; text-align:center; }
        .infobox-source { text-align:center; font-size:0.9em; color:#6c757d; margin-top:6px; }

        /* TOC */
        .toc-link { text-decoration:none; color:inherit !important; }
        .toc-item { margin-bottom:5px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Texto explicativo ----------
st.title("🤖 Sistema Multiagente para Geração de Artigos com CrewAI")
st.markdown(
    "Forneça um tópico e gere um artigo (mínimo 300 palavras). O sistema consulta a Wikipedia e gera o conteúdo."
)

# ---------- Configurações e paths ----------
topic = st.text_input("Qual o tópico do artigo?", placeholder="Ex: Inteligência Artificial")
remote_placeholder_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png"
placeholder_image_path = os.path.join("src", "No-Image-Placeholder.svg.png")  # relativo ao workspace

# ---------- Helpers reutilizáveis ----------
def _select_image(article: ArticleOutput) -> tuple[str | None, str]:
    """
    Retorna (image_path_or_url, caption) escolhendo entre:
      - article.image_url
      - placeholder local
      - fallback remoto
    """
    if getattr(article, "image_url", None):
        return article.image_url, (getattr(article, "image_caption", None) or "Imagem obtida da Wikipedia")
    if os.path.exists(placeholder_image_path):
        return placeholder_image_path, "Placeholder local"
    return remote_placeholder_image_url, "Placeholder remoto"

def _render_centered_image(path_or_url: str, width: int = 300):
    """
    Renderiza imagem centralizada. Usa st.image para arquivos locais/bytes; para URLs usa HTML.
    """
    if not path_or_url:
        return
    if os.path.exists(path_or_url):
        st.image(path_or_url, width=width)
    else:
        st.markdown(f'<div class="infobox-image-container"><img src="{path_or_url}" width="{width}" style="height:auto; max-width:100%;"></div>', unsafe_allow_html=True)

def _build_toc(anchors: dict, article: ArticleOutput) -> str:
    """
    Gera HTML simples do sumário (TOC). Anchors é dict com chaves lógicas -> id.
    """
    return f"""
    <div class="toc-item"><a class="toc-link" href="#{anchors['top']}">Início</a></div>
    <div class="toc-item"><a class="toc-link" href="#{anchors['summary']}">Resumo</a></div>
    <div class="toc-item"><a class="toc-link" href="#{anchors['intro']}">{article.introduction_subtitle}</a></div>
    <div class="toc-item"><a class="toc-link" href="#{anchors['dev']}">{article.development_subtitle}</a></div>
    <div class="toc-item"><a class="toc-link" href="#{anchors['conc']}">{article.conclusion_subtitle}</a></div>
    <div class="toc-item"><a class="toc-link" href="#{anchors['notes']}">Notas</a></div>
    <div class="toc-item"><a class="toc-link" href="#{anchors['refs']}">Referências</a></div>
    """

def _render_image_source_line(article: ArticleOutput):
    """
    Exibe a linha de Fonte abaixo da imagem no formato:
      Fonte: Wikipédia, <ANO_ATUAL>.
    O texto 'Wikipédia, ANO' é link para article.source_url (fallback image_url).
    """
    link_target = article.source_url or getattr(article, "image_url", None)
    if not link_target:
        return
    year = datetime.now().year
    link_text = f"Wikipédia, {year}"
    st.markdown(f'<div class="infobox-source">Fonte: <a href="{link_target}" target="_blank" rel="noopener noreferrer">{link_text}</a>.</div>', unsafe_allow_html=True)

def _render_abnt_reference(article: ArticleOutput):
    """
    Gera referência ABNT básica usando source_title/source_url/access_date quando disponíveis.
    """
    if article.source_title and article.source_url and article.access_date:
        title_abnt = article.source_title.upper()
        url = article.source_url
        access = article.access_date.lower()
        st.markdown(f"{title_abnt}. In: WIKIPÉDIA: a enciclopédia livre. Disponível em: <{url}>. Acesso em: {access}.")
    else:
        st.caption("Não foi possível gerar a referência ABNT (dados da fonte ausentes).")

# ---------- Ação principal ----------
if st.button("Gerar Artigo", type="primary"):
    if not topic:
        st.warning("Por favor, digite um tópico antes de gerar a estrutura.")
    else:
        with st.spinner(f"Pesquisando e gerando artigo sobre '{topic}'..."):
            try:
                # Geração via crew_factory (pode elevar ValueError / ServerError)
                article: ArticleOutput = create_crew(topic)

                # âncoras simples
                anchors = {
                    "top": "top",
                    "summary": "resumo",
                    "intro": "introducao",
                    "dev": "desenvolvimento",
                    "conc": "conclusao",
                    "notes": "notas",
                    "refs": "referencias",
                }

                # Layout: conteúdo principal + infobox lateral
                col_main, col_infobox = st.columns([2.5, 1])

                # ----- Conteúdo principal -----
                with col_main:
                    st.markdown(f'<div id="{anchors["top"]}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h1>{article.title}</h1>', unsafe_allow_html=True)
                    st.divider()

                    st.markdown(f'<div id="{anchors["summary"]}"></div>', unsafe_allow_html=True)
                    st.markdown("<h2>Resumo</h2>", unsafe_allow_html=True)
                    st.write(article.summary)

                    st.markdown(f'<div id="{anchors["intro"]}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>{article.introduction_subtitle}</h2>', unsafe_allow_html=True)
                    st.write(article.introduction_content)

                    st.markdown(f'<div id="{anchors["dev"]}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>{article.development_subtitle}</h2>', unsafe_allow_html=True)
                    st.write(article.development_content)

                    st.markdown(f'<div id="{anchors["conc"]}"></div>', unsafe_allow_html=True)
                    st.markdown(f'<h2>{article.conclusion_subtitle}</h2>', unsafe_allow_html=True)
                    st.write(article.conclusion_content)

                    st.divider()
                    st.markdown(f'<div id="{anchors["notes"]}"></div>', unsafe_allow_html=True)
                    st.markdown("<h2>Notas</h2>", unsafe_allow_html=True)
                    st.caption(f"**Palavras-chave:** {', '.join(article.keywords)}.")
                    st.markdown(f'<div id="{anchors["refs"]}"></div>', unsafe_allow_html=True)
                    st.markdown("<h2>Referências</h2>", unsafe_allow_html=True)
                    _render_abnt_reference(article)

                    st.success(f"Artigo gerado com sucesso! ({article.word_count} palavras)")

                # ----- Infobox lateral -----
                with col_infobox:
                    # título do infobox = legenda da imagem (ou tópico)
                    infobox_title = getattr(article, "image_caption", None) or topic.title()
                    st.markdown(f'<h3 class="infobox-title">{infobox_title}</h3>', unsafe_allow_html=True)

                    image_path, _caption = _select_image(article)
                    _render_centered_image(image_path, width=300)

                    # Fonte abaixo da imagem (centralizada)
                    _render_image_source_line(article)

                    st.divider()
                    st.markdown("**Informação geral**")
                    st.caption(f"Artigo principal da fonte: {article.source_title or 'Sem Fonte'}")
                    st.caption(f"Contagem de Palavras: {article.word_count}")

                # ----- Sumário na sidebar -----
                with st.sidebar.expander("Conteúdo"):
                    st.markdown(_build_toc(anchors, article), unsafe_allow_html=True)

            except ValueError as ve:
                st.error(f"Erro: {ve}")
                with st.expander("Detalhes (ValueError)"):
                    st.exception(ve)

            except ServerError as se:
                # Tratamento para erros 5xx do LLM
                err = str(se)
                if "503" in err and "overloaded" in err:
                    st.error("API do LLM sobrecarregada (503). Tente novamente mais tarde.")
                else:
                    st.error("Erro no serviço de geração. Veja detalhes.")
                with st.expander("Detalhes (ServerError)"):
                    st.exception(se)

            except Exception as e:
                st.error("Ocorreu um erro inesperado.")
                with st.expander("Detalhes (Exception)"):
                    st.exception(e)

# ---------- Rodapé ----------
st.sidebar.divider()
st.sidebar.info("Desenvolvido por Andresantoss")
st.sidebar.markdown(
    "GitHub: [Repositório do Projeto](https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss)"
)