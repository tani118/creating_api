# Train Booking AI Agent

An intelligent train booking assistant powered by Groq's Llama 3.3 70B and LangChain, with a Flask backend.

## Features

- 🤖 **AI-Powered Conversational Agent** using Groq Llama 3.3 70B
- 🚂 **Complete Train Search** - Search trains between any stations
- 💰 **Smart Filtering** - Find cheapest, fastest, or filter by class/time
- 🔍 **Detailed Information** - Get complete train schedules and routes
- 💬 **Context-Aware Chat** - Maintains conversation history
- 🎯 **Multi-Step Booking Flow** - Guides users through the entire process

## Architecture

```
Frontend (Next.js) → Flask API → LangChain Agent → Groq LLM
                                      ↓
                                  Train APIs
```

## Setup Instructions

### 1. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up/Login
3. Create a new API key (FREE tier available)
4. Copy your API key

### 2. Configure Environment

Edit `.env` file:
```bash
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Backend

```bash
python main.py
```

Server will start on `http://localhost:5000`

## API Endpoints

### Train Search & Query Endpoints

- `POST /getTrainDetailsWithRefresh` - Search trains (opens browser)
- `GET /trains/available` - Get available trains
- `GET /trains/cheapest?class=3A` - Get cheapest trains
- `GET /trains/fastest` - Get fastest trains
- `POST /trains/filter` - Filter trains by criteria
- `GET /trains/<train_number>` - Get train details
- `GET /trains/<train_number>/route` - Get train route
- `GET /trains/summary` - Get search summary

### AI Agent Endpoints (NEW)

#### Chat with Agent
```bash
POST /chat
Content-Type: application/json

{
  "message": "Find trains from Delhi to Mumbai tomorrow",
  "session_id": "user123"  # Optional, maintains conversation history
}
```

Response:
```json
{
  "success": true,
  "response": "I'll help you search for trains...",
  "session_id": "user123"
}
```

#### Clear Chat History
```bash
POST /chat/clear
Content-Type: application/json

{
  "session_id": "user123"
}
```

## Usage Examples

### Example 1: Search Trains
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to travel from NDLS to BCT on 16-11-2025",
    "session_id": "user1"
  }'
```

### Example 2: Find Cheapest
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me the cheapest trains in 3AC class",
    "session_id": "user1"
  }'
```

### Example 3: Get Train Details
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about train 12301",
    "session_id": "user1"
  }'
```

## Agent Capabilities

The AI agent can:

1. **Search Trains** - Between any source and destination
2. **Filter Options** - By price, speed, class, departure time
3. **Show Details** - Complete train information
4. **Compare Trains** - Help choose best option
5. **Multi-turn Conversations** - Remember context
6. **Guide Booking** - Step-by-step assistance

## Station Codes Reference

Common station codes:
- **Delhi**: NDLS (New Delhi), DLI (Old Delhi)
- **Mumbai**: BCT (Mumbai Central), CSTM (Mumbai CST)
- **Bangalore**: SBC (Bangalore City), YPR (Yesvantpur)
- **Chennai**: MAS (Chennai Central)
- **Kolkata**: HWH (Howrah), SDAH (Sealdah)
- **Ahmedabad**: ADI
- **Pune**: PUNE
- **Hyderabad**: HYB

## Train Classes

- **1A**: First AC
- **2A**: Second AC
- **3A**: Third AC
- **SL**: Sleeper
- **2S**: Second Sitting
- **CC**: Chair Car

## Project Structure

```
creating_api/
├── main.py              # Flask backend with all endpoints
├── agent.py             # LangChain agent with Groq LLM
├── tools.py             # LangChain tools for train APIs
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (API keys)
├── .env.example         # Example environment file
└── README.md           # This file
```

## Technologies Used

- **Backend**: Flask, Flask-CORS
- **LLM**: Groq (Llama 3.3 70B)
- **Agent Framework**: LangChain
- **Web Scraping**: Selenium Wire
- **API**: RESTful endpoints

## Rate Limits (Groq Free Tier)

- 30 requests per minute
- 14,400 requests per day
- 500+ tokens/second (blazing fast!)

## Next Steps

1. **Get Groq API Key** and add to `.env`
2. **Test the agent** using curl or Postman
3. **Build Frontend** - Next.js chat interface
4. **Add Booking** - Complete the booking endpoint
5. **Deploy** - Host on cloud platform

## Troubleshooting

### Agent not responding?
- Check if GROQ_API_KEY is set in `.env`
- Verify backend is running on port 5000
- Check Groq API rate limits

### Search not working?
- Ensure browser automation works (ChromeDriver)
- Check IRCTC website availability
- Try with valid station codes

### Import errors?
- Run `pip install -r requirements.txt`
- Check Python version (3.8+)

## Contributing

Feel free to contribute by:
- Adding more tools/features
- Improving prompts
- Building the frontend
- Completing booking functionality

## License

MIT License

---

Built with ❤️ using Groq, LangChain, and Flask
