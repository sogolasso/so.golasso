"""create articles table

Revision ID: 002
Revises: 001
Create Date: 2024-03-14 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create articles table
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('author_name', sa.String(), nullable=False),
        sa.Column('author_style', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('featured_image', sa.String(), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('meta_keywords', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('excerpt', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('team_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('player_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('is_trending', sa.Boolean(), nullable=False),
        sa.Column('likes_count', sa.Integer(), nullable=False),
        sa.Column('comments_count', sa.Integer(), nullable=False),
        sa.Column('shares_count', sa.Integer(), nullable=False),
        sa.Column('views_count', sa.Integer(), nullable=False),
        sa.Column('comments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_category'), 'articles', ['category'], unique=False)
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_slug'), 'articles', ['slug'], unique=True)
    op.create_index(op.f('ix_articles_title'), 'articles', ['title'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_articles_title'), table_name='articles')
    op.drop_index(op.f('ix_articles_slug'), table_name='articles')
    op.drop_index(op.f('ix_articles_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_category'), table_name='articles')
    op.drop_table('articles') 