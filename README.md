# Parent Co-Pilot

A therapeutic AI assistant designed to support divorced parents by providing emotional guidance and support while referencing their divorce agreements.

## Overview

Parent Co-Pilot AI Assistant is an API-based service that combines emotional intelligence with legal context awareness. The application helps divorced individuals navigate their emotions, understand their divorce agreements, and make informed decisions about co-parenting issues.

## Features

- **Emotional Support**: Provides warm, empathetic responses to users' emotional concerns
- **Contract-Aware Responses**: References relevant sections of divorce agreements when answering questions
- **Conversation Memory**: Maintains context across conversations with persistent chat history
- **Vector Search**: Uses semantic search to find relevant clauses in divorce agreements
- **API-First Design**: Easy integration with mobile apps, web interfaces, or other platforms

## Technology Stack

- **Backend**: FastAPI
- **Language Models**: OpenAI GPT models (configurable)
- **Vector Database**: Supabase Vector Store
- **Embedding Models**: OpenAI text-embedding-3-large
- **Containerization**: Docker
- **Text Processing**: LangChain for document chunking and processing

## Installation

### Prerequisites

- Python 3.10+
- Docker (optional)
- Supabase account
- OpenAI API key

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/parent-co-pilot.git
cd parent-co-pilot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Running Locally

```bash
uvicorn src.v1.main:app --reload
```

### Docker Deployment

```bash
docker build -t parent-co-pilot .
docker run -p 8000:8000 --env-file .env parent-co-pilot
```

## API Endpoints

### Health Check
```
GET /api/health
```
Simple endpoint to verify API is running.

### Conversation
```
POST /api/conversation
```
Process a user message and return an AI response with relevant context.

**Request Body:**
```json
{
  "user_input": "What does my divorce agreement say about summer vacations?",
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "response": "Based on your divorce agreement, each parent is entitled to two weeks of summer vacation time with the children...",
  "relevant_contract_statements": "Summer Vacation: Each parent shall be entitled to two consecutive weeks of vacation time with the children during the summer break...",
  "total_tokens": 450
}
```

### Vector Store Creation
```
POST /api/vector-store
```
Store divorce agreement document in vector database for retrieval.

**Request Body:**
```json
{
  "text": "Full text of divorce agreement...",
  "user_id": "user_123"
}
```

## System Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  FastAPI    │──────►  Response   │──────►  OpenAI     │
│  Endpoints  │      │  Handler    │      │  Models     │
└─────────────┘      └─────────────┘      └─────────────┘
                           │
                           ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Supabase   │◄─────┤  Memory     │◄─────┤  Document   │
│  Vector DB  │      │  Engine     │      │  Chunking   │
└─────────────┘      └─────────────┘      └─────────────┘
```

## Evaluation and Monitoring

The system currently has basic logging but would benefit from:

- Response quality metrics
- User feedback collection
- Performance monitoring
- A/B testing platform for prompt optimization

## Future Improvements

- Enhanced evaluation framework
- User feedback mechanism
- Multi-model support
- Multi-language support
- Voice interface integration
- Advanced analytics dashboard for user satisfaction
- Compliance and ethical use monitoring

## License

This project is licensed under the MIT License - see the LICENSE file for details.
