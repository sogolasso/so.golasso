from typing import Dict, List, Optional
from datetime import datetime
import re
from app.schemas.article import Article
from app.core.config import settings

class MonetizationService:
    def __init__(self):
        self.team_affiliate_links = {
            "Flamengo": {
                "jersey": "https://amzn.to/flamengo-jersey",
                "tickets": "https://tickets.flamengo.com.br"
            },
            "Palmeiras": {
                "jersey": "https://amzn.to/palmeiras-jersey",
                "tickets": "https://tickets.palmeiras.com.br"
            },
            # Add more teams here
        }
        
        self.ad_templates = {
            "in_content": """
                <div class="ad-container my-4">
                    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
                    <ins class="adsbygoogle"
                        style="display:block"
                        data-ad-client="{}"
                        data-ad-slot="{}"
                        data-ad-format="auto"
                        data-full-width-responsive="true"></ins>
                    <script>
                        (adsbygoogle = window.adsbygoogle || []).push({});
                    </script>
                </div>
            """,
            "sidebar": """
                <div class="sidebar-ad">
                    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
                    <ins class="adsbygoogle"
                        style="display:block"
                        data-ad-client="{}"
                        data-ad-slot="{}"
                        data-ad-format="vertical"
                        data-full-width-responsive="false"></ins>
                    <script>
                        (adsbygoogle = window.adsbygoogle || []).push({});
                    </script>
                </div>
            """
        }

    async def process_content(self, article: Article) -> Dict[str, str]:
        """Process article content for monetization."""
        # Add affiliate links
        content_with_links = await self._add_affiliate_links(article)
        
        # Inject ads
        content_with_ads = await self._inject_ads(content_with_links)
        
        return {
            "processed_content": content_with_ads,
            "has_affiliate_links": bool(article.team_tags),
            "ad_positions": self._get_ad_positions(content_with_ads)
        }

    async def _add_affiliate_links(self, article: Article) -> str:
        """Add affiliate links for team merchandise and tickets."""
        content = article.content
        
        for team in article.team_tags:
            if team in self.team_affiliate_links:
                links = self.team_affiliate_links[team]
                
                # Add jersey affiliate link
                jersey_pattern = f"camisa d[eo] {team}"
                content = re.sub(
                    jersey_pattern,
                    f'<a href="{links["jersey"]}" target="_blank" rel="nofollow">\\g<0></a>',
                    content,
                    flags=re.IGNORECASE
                )
                
                # Add ticket affiliate link
                ticket_pattern = f"(ingresso|bilhete|entrada).{{0,30}}(?:{team})"
                content = re.sub(
                    ticket_pattern,
                    f'<a href="{links["tickets"]}" target="_blank" rel="nofollow">\\g<0></a>',
                    content,
                    flags=re.IGNORECASE
                )
        
        return content

    async def _inject_ads(self, content: str) -> str:
        """Inject ads into article content at appropriate positions."""
        paragraphs = content.split('\n\n')
        processed_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            processed_paragraphs.append(paragraph)
            
            # Add in-content ad after every 3rd paragraph
            if (i + 1) % 3 == 0 and i < len(paragraphs) - 1:
                ad = self.ad_templates["in_content"].format(
                    settings.ADSENSE_CLIENT_ID,
                    settings.ADSENSE_IN_ARTICLE_SLOT
                )
                processed_paragraphs.append(ad)
        
        return '\n\n'.join(processed_paragraphs)

    def _get_ad_positions(self, content: str) -> List[Dict[str, int]]:
        """Get positions of injected ads for frontend rendering."""
        positions = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if 'adsbygoogle' in line:
                positions.append({
                    "line": i,
                    "type": "in_content" if "data-ad-format=\"auto\"" in line else "sidebar"
                })
        
        return positions

    def get_sidebar_ad(self) -> str:
        """Get sidebar ad HTML."""
        return self.ad_templates["sidebar"].format(
            settings.ADSENSE_CLIENT_ID,
            settings.ADSENSE_SIDEBAR_SLOT
        )

    async def track_revenue(
        self,
        article_id: str,
        revenue_type: str,
        amount: float
    ) -> None:
        """Track revenue from different sources."""
        # TODO: Implement revenue tracking
        pass 