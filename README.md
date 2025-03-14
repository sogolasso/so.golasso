# Só Golasso

A modern football news aggregator and content generation platform.

## Features

- Automated news scraping from multiple sources
- AI-powered article generation
- RESTful API with FastAPI
- PostgreSQL database
- Automated content scheduling and publishing

## Tech Stack

- **Backend**: Python, FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **AI**: OpenAI GPT
- **Deployment**: Render

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sogolasso.git
cd sogolasso
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/sogolasso
OPENAI_API_KEY=your_openai_api_key
```

5. Run migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Deployment

The application is configured for deployment on Render. Simply connect your GitHub repository to Render and it will automatically deploy using the `render.yaml` configuration.

## License

MIT License 