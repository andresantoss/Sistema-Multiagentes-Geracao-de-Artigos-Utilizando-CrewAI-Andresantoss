# Sistema Multiagentes para Geração de Artigos Utilizando CrewAI Andresantoss
Este projeto usa CrewAI para criar um sistema multiagente que gera artigos para websites, utilizando a API da Wikipedia para pesquisa e contextualização.

# Geração de Artigos com CrewAI

## Descrição

Este projeto usa agentes de IA (CrewAI) para escrever artigos automaticamente. [cite_start]Você dá um **tópico**, o sistema pesquisa na **Wikipedia** [cite: 7] [cite_start]e usa o **Google Gemini** [cite: 8] [cite_start]para gerar um artigo de pelo menos 300 palavras [cite: 3][cite_start], formatado em JSON[cite: 18].

## Tecnologias

* [cite_start]Python [cite: 11]
* [cite_start]CrewAI [cite: 12] [cite_start]& CrewAI Tools [cite: 13]
* [cite_start]Google Gemini (API) [cite: 8]
* [cite_start]Wikipedia API [cite: 14]
* [cite_start]FastAPI [cite: 20]
* Uvicorn
* [cite_start]Pydantic [cite: 18]
* Python-dotenv
* Requests

## Como Configurar

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
    *(Seu terminal mostrará `(venv)` na frente)*

4.  **Instale as Bibliotecas:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Crie o Arquivo `.env`:**
    * Copie o arquivo de exemplo:
        * **Windows (cmd):** `copy .env.example .env`
        * **Windows (PowerShell):** `Copy-Item .env.example .env`
        * **Linux/macOS:** `cp .env.example .env`
    * Abra o arquivo `.env` e preencha:
        * `GEMINI_API_KEY`: Cole sua chave da API do Google Gemini.
            * **Obtenha aqui:** [Google AI Studio](https://aistudio.google.com/app/apikey) (Clique em "Create API key").
        * `WIKIPEDIA_USER_EMAIL`: Coloque seu email (usado para acessar a Wikipedia de forma educada).

## Como Rodar

1.  **Ative o Ambiente Virtual** (se não estiver ativo):
    * Windows: `venv\Scripts\activate`
    * Linux/macOS: `source venv/bin/activate`

2.  **Inicie o Servidor:**
    ```bash
    python -m uvicorn main:app --reload 
    ```
    *(Use `--reload` para desenvolvimento; ele reinicia o servidor se você mudar o código)*

3.  **Acesse a API:**
    * Abra seu navegador em: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
    * Clique em `POST /generate-article/`, depois em "Try it out".
    * Mude o `"topic"` para o assunto desejado (ex: `"Inteligência Artificial"`).
    * Clique em "Execute".
    * Aguarde o resultado aparecer na seção "Response body".

## Para Parar

1.  **Pare o Servidor:** Pressione `CTRL+C` no terminal onde o `uvicorn` está rodando.
2.  **Desative o Ambiente Virtual:** Digite `deactivate` no terminal.
