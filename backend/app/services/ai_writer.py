import logging
from typing import Dict, Any
from openai import AsyncOpenAI
import hashlib
import json
from .ai_usage_tracker import AIUsageTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIWriter:
    def __init__(self, api_key: str, max_daily_articles: int = 10, max_monthly_cost: float = 100.0):
        self.client = AsyncOpenAI(api_key=api_key)
        self.usage_tracker = AIUsageTracker(max_daily_articles, max_monthly_cost)
        
    def _calculate_content_hash(self, title: str, source_text: str, source_type: str) -> str:
        """Calculate a hash for the content to use as cache key"""
        content = f"{title}|{source_text}|{source_type}"
        return hashlib.md5(content.encode()).hexdigest()
        
    async def generate_article(
        self,
        title: str,
        source_text: str,
        source_type: str
    ) -> Dict[str, Any]:
        """Generate an article using OpenAI's GPT model with usage tracking and caching"""
        try:
            # Log the attempt
            logger.info(f"Tentando gerar artigo: {title}")
            logger.info(f"Tipo de fonte: {source_type}")
            logger.info(f"Tamanho do texto fonte: {len(source_text)} caracteres")
            
            # Check if we can generate more articles today
            if not self.usage_tracker.can_generate_article():
                logger.warning("Limite diário de artigos atingido")
                return None
                
            # Check monthly cost limit
            if not self.usage_tracker.check_monthly_cost_limit():
                logger.warning("Limite mensal de custo se aproximando")
                return None
                
            # Check cache first
            content_hash = self._calculate_content_hash(title, source_text, source_type)
            cached_article = self.usage_tracker.get_cached_article(content_hash)
            if cached_article:
                logger.info("Usando artigo em cache")
                return cached_article
            
            # Create a prompt based on the source type and content
            prompt = self._create_prompt(title, source_text, source_type)
            logger.info("Prompt criado para geração do artigo")
            
            # Generate content using OpenAI
            logger.info("Enviando requisição para OpenAI...")
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo-16k",  # Using 16k model for longer content
                    messages=[
                        {"role": "system", "content": "Você é um jornalista esportivo profissional especializado em futebol. Escreva artigos envolventes, precisos e bem estruturados em português brasileiro."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000  # Increased token limit
                )
                logger.info("Resposta recebida com sucesso da OpenAI")
            except Exception as e:
                logger.error(f"Erro na API OpenAI: {str(e)}")
                return None
            
            # Calculate cost (approximate)
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * 0.003  # $0.003 per 1K tokens for GPT-3.5-16k
            logger.info(f"Usados {tokens_used} tokens (custo: ${cost:.4f})")
            
            # Track usage
            self.usage_tracker.track_usage(tokens_used, cost)
            
            # Parse the response
            content = response.choices[0].message.content
            if not content or len(content.strip()) < 100:
                logger.error("Conteúdo gerado muito curto ou vazio")
                return None
                
            logger.info("Conteúdo do artigo gerado com sucesso")
            logger.info(f"Tamanho do conteúdo gerado: {len(content)} caracteres")
            
            # Generate a summary
            logger.info("Gerando resumo...")
            summary = await self._generate_summary(content)
            
            # Determine category and author details
            logger.info("Determinando categoria e detalhes do autor...")
            category = await self._determine_category(content)
            author_details = await self._generate_author_details(content)
            
            # Generate slug from title
            from slugify import slugify
            slug = slugify(title)
            
            # Create article data
            article_data = {
                "title": title,
                "content": content,
                "summary": summary,
                "category": category,
                "author_style": author_details["style"],
                "author_name": author_details["name"],
                "meta_description": summary[:160] if summary else content[:160],
                "meta_keywords": self._extract_keywords(content),
                "slug": slug
            }
            
            # Cache the article
            self.usage_tracker.cache_article(content_hash, article_data)
            logger.info(f"Artigo gerado com sucesso: {title}")
            logger.info(f"Categoria: {category}")
            logger.info(f"Autor: {author_details['name']}")
            
            return article_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar artigo '{title}': {str(e)}", exc_info=True)
            return None
            
    def _create_prompt(self, title: str, source_text: str, source_type: str) -> str:
        """Create a prompt for the AI based on source type"""
        return f"""Escreva um artigo de futebol baseado nas seguintes informações:

Título: {title}

Conteúdo Fonte: {source_text}

Tipo: {source_type}

Diretrizes:
1. Escreva em português brasileiro
2. Use linguagem envolvente e dinâmica
3. Inclua contexto e histórico relevantes
4. Mantenha conciso (500-700 palavras)
5. Foque nos fatos principais e análise
6. Mantenha integridade jornalística
7. Se a fonte estiver em inglês, traduza as informações principais para português

Por favor, estruture o artigo com:
- Introdução envolvente
- Conteúdo principal com parágrafos claros
- Conclusão ou implicações futuras"""

    async def _generate_summary(self, content: str) -> str:
        """Generate a brief summary of the article"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Crie um breve resumo deste artigo de futebol em 2-3 frases em português brasileiro."},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return content[:200] + "..."
            
    async def _determine_category(self, content: str) -> str:
        """Determine the article category"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Categorize este artigo de futebol em uma destas categorias: Transferências, Partida, Jogador, Time, Análise, Opinião"},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=20
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Erro ao determinar categoria: {e}")
            return "Geral"
    
    async def _generate_author_details(self, content: str) -> Dict[str, str]:
        """Generate author details based on content"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Com base no conteúdo e estilo deste artigo, sugira um nome de autor e estilo de escrita (ex: Analítico, Narrativo, Técnico, etc.)"},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=50
            )
            result = response.choices[0].message.content.strip().split("\n")
            return {
                "name": result[0] if len(result) > 0 else "Redação Esportiva",
                "style": result[1] if len(result) > 1 else "Jornalístico"
            }
        except Exception as e:
            logger.error(f"Erro ao gerar detalhes do autor: {e}")
            return {"name": "Redação Esportiva", "style": "Jornalístico"}
    
    def _extract_keywords(self, content: str) -> str:
        """Extract relevant keywords from the content"""
        # Enhanced keyword extraction for Brazilian Portuguese
        common_keywords = [
            "futebol", "gol", "campeonato", "brasileiro", "copa",
            "time", "jogador", "técnico", "partida", "vitória",
            "derrota", "empate", "clássico", "torneio", "liga",
            "atacante", "zagueiro", "goleiro", "meio-campo", "lateral",
            "artilheiro", "placar", "jogo", "bola", "campo",
            "torcida", "estádio", "árbitro", "cartão", "falta",
            "pênalti", "escanteio", "chute", "defesa", "goleada"
        ]
        keywords = []
        
        content_words = content.lower().split()
        for word in content_words:
            if len(word) > 3 and (word in common_keywords or any(kw in word for kw in common_keywords)):
                keywords.append(word)
                
        return ",".join(set(keywords[:10]))  # Limit to top 10 keywords
        
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from the title"""
        from slugify import slugify
        return slugify(title)  # Using python-slugify for better slug generation
        
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from the title"""
        return "-".join(title.lower().split()[:8]) 