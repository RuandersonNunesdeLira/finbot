# FinBot — Seu Assistente Financeiro Inteligente

Seja bem-vindo ao repositório do **FinBot**! Este projeto foi criado para ser um chatbot financeiro completo e inteligente. Ele tira dúvidas sobre educação financeira, acompanha o mercado de ações (B3) e de criptomoedas em tempo real e — o mais legal — **aprende com os seus feedbacks** ajustando o próprio comportamento sozinho.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![React](https://img.shields.io/badge/React-Vite-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## O Que Ele Faz?

- **Bate-Papo Inteligente:** Converse naturalmente! Ele utiliza o contexto de uma base de conhecimento privada (ChromaDB) e o poder do LangChain + OpenAI.
- **Cotações em Tempo Real:** Pergunte o preço atual do Bitcoin ou a cotação da Petrobras. Ele vai lá e busca a informação fresquinha pra você usando integrações (CoinGecko e Brapi).
- **Aprende com Você:** Achou a resposta ruim ou muito longa? Avalie o bot na aba de feedback! Mais tarde, o sistema processa esses dados e a **própria IA reescreve dinamicamente seu prompt base** para não errar na próxima vez.
- **WhatsApp Sync:** Além do chat web, você pode escanear um QR Code e conversar com o mesmo bot direto do seu celular através da API do WAHA.

---

## Tecnologias Utilizadas

Para garantir um código limpo, moderno e separado por responsabilidades, usamos:

- **Frontend:** React + Vite, rápido e focado em uma experiência direta (separando as áreas de Chat e Gestão).
- **Backend:** FastAPI (Python), organizando e orquestrando as chamadas de API do LangChain e endpoints via REST.
- **Inteligência:** LangChain + modelo GPT-4o-mini da OpenAI, gerenciando agentes e uso de *Tools*.
- **Memória:** ChromaDB, um banco vetorial que guarda conteúdos financeiros pré-indexados (RAG).
- **Infra e Deploy:** Totalmente "Dockerizado", fácil e prático de subir na máquina (basta um comando).

---

## Como Rodar o Projeto

É muito simples rodar a aplicação através do Docker.

**O que você vai precisar ter instalado:**
- Docker Desktop e Docker Compose atualizados
- Chave de API da OpenAI (paga ou com créditos - para o LLM)
- Chave de API da Brapi (gratuita e pode ser gerada em brapi.dev - para ações B3)

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/RuandersonNunesdeLira/finbot.git
   cd finbot
   ```

2. **Configure suas chaves (Variáveis de Ambiente):**
   Pegamos um atalho e deixamos um arquivo modelo preparado, basta copiá-lo:
   ```bash
   cp .env.example .env
   ```
   Agora, abra o seu recém-criado arquivo `.env` e preencha suas chaves principais:
   `OPENAI_API_KEY` = Sua chave da OpenAI
   `BRAPI_API_KEY` = Sua chave da Brapi

3. **Subindo o FinBot no Docker:**
   Execute o seguinte comando no terminal do seu computador. Vai demorar um pouquinho até ele baixar as imagens e construir nossos 4 serviços (Frontend, Backend, ChromaDB e WAHA).
   ```bash
   docker-compose up --build -d
   ```

4. **Tudo pronto! Pode acessar:**
   - **Aplicativo (React):** [http://localhost:5173](http://localhost:5173)
   - **API Backend (FastAPI Swagger):** [http://localhost:8080/docs](http://localhost:8080/docs)

---

## Como Testar as Funcionalidades

Assim que você acessar a tela da nossa Aplicação em `http://localhost:5173`, notará **três abas principais**:

1. **Aba Chat:** Vá em frente! Peça cotações e recomendações. (Ex: *"Como está o Ethereum?"* ou *"Qual o valor de VALE3 hoje?"*). O bot já vai identificar as ferramentas corretas para te responder.
2. **Aba Prompt & Feedback:** Deixe notas para a IA sobre as interações passadas. Quando quiser otimizar o projeto baseado nas suas críticas, aperte em "Process Feedback & Optimize". O LLM analisará os erros e vai redigir uma versão 2.0 do seu coração (System Prompt).
3. **Aba WhatsApp:** Escaneie o QR Code lá disponível pelo seu WhatsApp ("Aparelhos Conectados") e comece a enviar mensagens pelo número.

> ** Dica Bônus | Testes Unitários:** Para a galera que ama ver os bastidores, foram implementados testes automatizados cobrindo os serviços do bot. Basta entrar no diretório raiz do projeto com o interpretador Python ligado nas dependências (`pip install -r requirements.txt`) e rodar um `pytest tests/ -v`.

Qualquer dúvida ou problema na hora de executar, o código fonte foi divido em camadas visando boas práticas do mercado (rotas HTTP isoladas dos serviços principais e injeções de ferramentas de IA). Muito sucesso e espero que gostem do resultado!
