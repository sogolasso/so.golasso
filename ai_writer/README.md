# Só Golasso AI Writer 📝⚽

Um serviço de geração automática de artigos sobre futebol com personalidade brasileira.

## Funcionalidades 🌟

- Geração automática de artigos a partir de notícias, tweets e posts do Instagram
- Três estilos de escrita diferentes:
  - 📢 Narração Esportiva
  - 📝 Análise Tática
  - 😂 Zoação
- Otimização automática para SEO
- Geração automática de posts para redes sociais
- API REST com FastAPI

## Configuração 🛠️

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
# Crie um arquivo .env com:
OPENAI_API_KEY=sua_chave_api_aqui
```

3. Inicie o servidor:
```bash
uvicorn main:app --reload
```

## Uso da API 🚀

### Gerar um Artigo

```bash
curl -X POST "http://localhost:8000/generate-article" \
     -H "Content-Type: application/json" \
     -d '{
       "news": "Flamengo vence o Palmeiras por 3 a 1",
       "tweets": ["🔥 Gabigol brilha com 2 gols"],
       "instagram_posts": ["Post do Instagram aqui"],
       "style": "narracao"
     }'
```

### Listar Estilos Disponíveis

```bash
curl "http://localhost:8000/styles"
```

## Exemplo de Resposta 📋

```json
{
  "titulo": "🔥 Gabigol Resolve! Flamengo Goleia Palmeiras e Assume a Liderança!",
  "subtitulo": "Artilheiro marca duas vezes em vitória convincente no Maracanã",
  "corpo": "Se tem decisão no Brasileirão, tem Gabigol brilhando!...",
  "hashtags": ["#Flamengo", "#Gabigol", "#Brasileirao"],
  "perguntas_interativas": ["E aí, torcedor, será que vem título por aí?"],
  "metadata": {
    "keywords": ["futebol", "gol", "brasileirao"],
    "generated_at": "2024-03-14T15:30:00"
  },
  "social_media": {
    "twitter": "🔥 Gabigol Resolve!...",
    "instagram": "📰 Gabigol Resolve!..."
  }
}
```

## Estilos de Escrita 📝

1. **Narração Esportiva (narracao)**
   - Estilo empolgante e dramático
   - Usa expressões típicas da narração brasileira
   - Ideal para resultados de jogos

2. **Análise Tática (tatica)**
   - Foco em aspectos técnicos e estratégicos
   - Linguagem mais formal e analítica
   - Ideal para análises pós-jogo

3. **Zoação (zoacao)**
   - Estilo bem-humorado com memes
   - Usa gírias e expressões populares
   - Ideal para conteúdo mais leve e divertido

## Contribuindo 🤝

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença 📄

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes. 