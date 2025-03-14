from typing import Dict, List, Optional
import openai
from enum import Enum
import re
import json
import os
from datetime import datetime

class ArticleStyle(Enum):
    NARRACAO = "narracao"  # Sports commentator style
    TATICA = "tatica"      # Tactical analysis style
    ZOACAO = "zoacao"      # Memes and jokes style

class ArticleGenerator:
    def __init__(self, api_key: str):
        """Initialize the ArticleGenerator with OpenAI API key."""
        self.api_key = api_key
        openai.api_key = api_key
        
    def _create_prompt(self, news: str, tweets: List[str], instagram_posts: List[str], 
                      style: ArticleStyle) -> str:
        """Create a prompt for the AI based on input content and style."""
        style_instructions = {
            ArticleStyle.NARRACAO: (
                "Escreva como um narrador de futebol empolgado, usando expressões típicas "
                "da narração esportiva brasileira. Seja energético e dramático."
            ),
            ArticleStyle.TATICA: (
                "Analise taticamente o jogo como um comentarista profissional, focando em "
                "aspectos técnicos e estratégicos, mas mantendo uma linguagem acessível."
            ),
            ArticleStyle.ZOACAO: (
                "Escreva de forma bem-humorada e descontraída, usando memes do futebol "
                "brasileiro e gírias populares. Seja engraçado mas não ofensivo."
            )
        }

        base_prompt = f"""
        Você é um escritor esportivo brasileiro especializado em futebol.
        
        ESTILO DE ESCRITA:
        {style_instructions[style]}
        
        CONTEÚDO BASE:
        Notícia Principal: {news}
        
        Tweets Relacionados: {json.dumps(tweets, ensure_ascii=False)}
        
        Posts do Instagram: {json.dumps(instagram_posts, ensure_ascii=False)}
        
        INSTRUÇÕES:
        1. Escreva um artigo em português brasileiro natural e fluido
        2. Use gírias e expressões comuns do futebol brasileiro
        3. Mantenha um tom casual e envolvente
        4. Inclua elementos interativos (perguntas para os leitores)
        5. Gere um título chamativo e hashtags relevantes
        6. Divida o texto em parágrafos curtos e use emojis apropriados
        
        FORMATO DE SAÍDA:
        {
            "titulo": "Título do artigo",
            "subtitulo": "Subtítulo chamativo",
            "corpo": "Corpo do artigo",
            "hashtags": ["#Tag1", "#Tag2"],
            "perguntas_interativas": ["Pergunta 1?", "Pergunta 2?"]
        }
        """
        return base_prompt

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from the text for SEO."""
        # Add your keyword extraction logic here
        # For now, we'll use a simple approach
        common_football_terms = [
            "futebol", "gol", "brasileirão", "campeonato", "time",
            "jogador", "técnico", "partida", "jogo", "clássico"
        ]
        
        words = re.findall(r'\w+', text.lower())
        keywords = [word for word in words if word in common_football_terms]
        return list(set(keywords))

    def generate_article(self, 
                        news: str, 
                        tweets: List[str] = None, 
                        instagram_posts: List[str] = None,
                        style: ArticleStyle = ArticleStyle.NARRACAO) -> Dict:
        """Generate an article based on input content."""
        tweets = tweets or []
        instagram_posts = instagram_posts or []
        
        # Create the prompt
        prompt = self._create_prompt(news, tweets, instagram_posts, style)
        
        try:
            # Generate content using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um escritor esportivo brasileiro especializado."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            # Parse the response
            content = json.loads(response.choices[0].message.content)
            
            # Extract keywords for SEO
            keywords = self._extract_keywords(content["corpo"])
            
            # Add metadata
            content["metadata"] = {
                "keywords": keywords,
                "generated_at": datetime.now().isoformat(),
                "style": style.value
            }
            
            return content
            
        except Exception as e:
            print(f"Error generating article: {str(e)}")
            return None

    def optimize_seo(self, content: Dict) -> Dict:
        """Optimize the article content for SEO."""
        # Add SEO-specific metadata
        if "metadata" not in content:
            content["metadata"] = {}
            
        content["metadata"].update({
            "description": content["subtitulo"],
            "keywords": self._extract_keywords(content["corpo"]),
            "og_title": content["titulo"],
            "og_description": content["subtitulo"]
        })
        
        # Add more hashtags based on content
        additional_hashtags = [f"#{keyword}" for keyword in content["metadata"]["keywords"]]
        content["hashtags"].extend(additional_hashtags)
        content["hashtags"] = list(set(content["hashtags"]))  # Remove duplicates
        
        return content

    def create_social_media_posts(self, article_content: Dict) -> Dict:
        """Create social media posts from the article content."""
        # Extract key information
        title = article_content["titulo"]
        hashtags = " ".join(article_content["hashtags"])
        
        # Create Twitter post (max 280 chars)
        twitter_text = f"{title[:200]}... {hashtags}"
        
        # Create Instagram caption (more detailed)
        instagram_caption = f"""📰 {title}

{article_content['subtitulo']}

Leia a matéria completa no link da bio! 👆

.
.
.
{hashtags}"""
        
        return {
            "twitter": twitter_text,
            "instagram": instagram_caption
        } 