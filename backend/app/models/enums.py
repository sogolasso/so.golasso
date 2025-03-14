from enum import Enum

class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

class AuthorStyle(str, Enum):
    NARRACAO = "narracao"  # Narration style
    TATICO = "tatico"      # Tactical analysis style
    ZOACAO = "zoacao"      # Humorous style 