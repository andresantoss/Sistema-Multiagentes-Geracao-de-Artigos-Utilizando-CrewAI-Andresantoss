# Sistema Multiagente para Geração de Artigos com CrewAI

Este projeto utiliza CrewAI para criar um sistema multiagente que gera artigos para websites. Os agentes usam a API da Wikipedia para pesquisa e contextualização antes de gerar o conteúdo.

## 🎯 Descrição

Este projeto é um sistema de automação de conteúdo que usa agentes de IA (CrewAI) para escrever artigos. O fluxo funciona da seguinte forma:

1.  Você fornece um **tópico** via API.
2.  Um agente pesquisa o tópico na **API da Wikipedia** para obter contexto relevante.
3.  Outro agente usa o **Google Gemini** para escrever um artigo coeso com no mínimo 300 palavras, baseado na pesquisa.
4.  O resultado final é retornado em formato **JSON**.

## 💻 Tecnologias Utilizadas

* Python
* CrewAI & CrewAI Tools
* Google Gemini (API)
* Wikipedia (API)
* FastAPI
* Uvicorn
* Pydantic
* Python-dotenv
* Requests

## ⚙️ Como Configurar

1.  **Clone o Repositório:**
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

4.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Crie o Arquivo `.env`:**
    * Abra o arquivo `.env` e preencha as variáveis:
        * `GEMINI_API_KEY`: Cole sua chave da API do Google Gemini.
            * **Obtenha aqui:** [Google AI Studio](https://aistudio.google.com/app/apikey) (Clique em "Create API key").
<<<<<<< HEAD
        * `WIKIPEDIA_CONTACT_INFO`: Coloque seu email (usado para identificação na API da Wikipedia).
=======
        * `WIKIPEDIA_USER_EMAIL`: Coloque seu email (usado para identificação na API da Wikipedia).
>>>>>>> 7b0d62bc4fe9f714318a832afd5153a506221c57

## ▶️ Como Rodar

1.  **Ative o Ambiente Virtual** (se não estiver ativo):
    * Windows: `venv\Scripts\activate`
    * Linux/macOS: `source venv/bin/activate`

2.  **Inicie o Servidor:**
    ```bash
    python -m uvicorn main:app --reload
    ```
    *(Use `--reload` para desenvolvimento; ele reinicia o servidor automaticamente se você alterar o código)*

3.  **Acesse a Documentação da API:**
    * Abra seu navegador em: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
    * Clique no endpoint `POST /generate-article/`, depois em "Try it out".
    * No "Request body", mude o `"topic"` para o assunto desejado (ex: `"Inteligência Artificial"`).
    * Clique em "Execute".
    * Aguarde o resultado aparecer na seção "Response body".

## ⏹️ Para Parar

1.  **Pare o Servidor:** Pressione `CTRL+C` no terminal onde o `uvicorn` está rodando.
2.  **Desative o Ambiente Virtual:** Digite `deactivate` no terminal.
