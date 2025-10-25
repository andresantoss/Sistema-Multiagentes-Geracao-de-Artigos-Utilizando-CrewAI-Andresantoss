# Sistema Multiagente para Geração de Artigos com CrewAI

## 🎯 Descrição

Este projeto usa agentes de IA (CrewAI) para escrever artigos automaticamente. Você fornece um **tópico** através de uma interface web simples (Streamlit), o sistema pesquisa na **API da Wikipedia** para obter contexto e usa o **Google Gemini** para gerar um artigo de pelo menos 300 palavras, que é exibido diretamente na interface.

O fluxo é:
1.  Você digita um **tópico** na interface web.
2.  Um agente pesquisa o tópico na **API da Wikipedia**.
3.  Outro agente usa o **Google Gemini** para escrever um artigo (mínimo 300 palavras) baseado na pesquisa.
4.  O artigo gerado é exibido na interface web.

## 💻 Tecnologias Utilizadas

* **Python:** Linguagem principal.
* **CrewAI & CrewAI Tools:** Orquestração dos agentes de IA.
* **Google Gemini (API):** LLM para geração de texto.
* **Wikipedia (API):** Fonte de dados para pesquisa.
* **Streamlit:** Criação da interface web interativa.
* **Pydantic:** Definição da estrutura de dados do artigo.
* **Python-dotenv:** Gerenciamento das chaves de API.
* **Requests:** Requisições HTTP para a API da Wikipedia.
* *(FastAPI/Uvicorn ainda presentes no código base, mas não são a forma principal de interação)*

## ⚙️ Como Configurar

1.  **Baixe o Código:**
    ```bash
    git clone [https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss.git](https://github.com/andresantoss/Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss.git)
    cd Sistema-Multiagentes-Geracao-de-Artigos-Utilizando-CrewAI-Andresantoss
    ```

2.  **Crie um Ambiente Virtual:**
    ```bash
    python -m venv venv
    ```

3.  **Ative o Ambiente Virtual:**
    * **Windows:** `venv\Scripts\activate`
    * **Linux/macOS:** `source venv/bin/activate`
    *(Seu terminal mostrará `(venv)` na frente do prompt)*

4.  **Instale as Bibliotecas:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Isso inclui o Streamlit)*

5.  **Crie o Arquivo `.env`:**
    * Copie o arquivo de exemplo:
        * **Windows (cmd):** `copy .env.example .env`
        * **Windows (PowerShell):** `Copy-Item .env.example .env`
        * **Linux/macOS:** `cp .env.example .env`
    * Abra o arquivo `.env` e preencha as variáveis:
        * `GEMINI_API_KEY`: Cole sua chave da API do Google Gemini.
            * **Obtenha aqui:** [Google AI Studio](https://aistudio.google.com/app/apikey) (Clique em "Create API key").
        * `WIKIPEDIA_CONTACT_INFO`: Coloque seu email ou a URL do seu GitHub (usado para identificação na API da Wikipedia).

## ▶️ Como Rodar

Existem duas formas de executar a aplicação:

**Opção 1: Interface Web (Streamlit - Recomendado para Uso Direto)**

1.  **Ative o Ambiente Virtual** (se não estiver ativo):
    * Windows: `venv\Scripts\activate`
    * Linux/macOS: `source venv/bin/activate`

2.  **Inicie a Aplicação Streamlit:**
    ```bash
    streamlit run app.py
    ```
    * O Streamlit iniciará um servidor local e abrirá automaticamente uma nova aba no seu navegador (geralmente em `http://localhost:8501`).

3.  **Use a Interface:**
    * Digite o tópico desejado no campo de texto.
    * Clique no botão "Gerar Artigo".
    * Aguarde o resultado. O artigo gerado será exibido na página.

**Opção 2: API Backend (FastAPI/Uvicorn - Para Testes ou Integração)**

1.  **Ative o Ambiente Virtual** (se não estiver ativo):
    * Windows: `venv\Scripts\activate`
    * Linux/macOS: `source venv/bin/activate`

2.  **Inicie o Servidor da API:**
    Use o Uvicorn para rodar a aplicação FastAPI definida em `main.py`.
    ```bash
    python -m uvicorn main:app --reload
    ```
    * `main:app`: Indica ao Uvicorn para procurar o objeto `app` dentro do arquivo `main.py`.
    * `--reload`: Faz o servidor reiniciar automaticamente se você salvar alterações nos arquivos Python (ótimo para desenvolvimento).
    * O servidor estará rodando em `http://127.0.0.1:8000`.

3.  **Acesse a Documentação da API:**
    * Abra seu navegador em: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
    * Use a interface Swagger UI para enviar requisições `POST` para o endpoint `/generate-article/` com o tópico no corpo da requisição (JSON).

## ⏹️ Para Parar

1.  **Pare o Servidor (Streamlit ou Uvicorn):** Pressione `CTRL+C` no terminal onde o servidor está executando.
2.  **Desative o Ambiente Virtual:** Digite `deactivate` no terminal.
