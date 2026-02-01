# Strands Agent Application 🤖

A conversational AI application powered by Strands Agents and Claude AI. When you run this application, it automatically hits an API, opens a web page, and provides an intelligent agent that can answer your questions.

## Features ✨

- **One-Command Launch**: Run the app and it automatically opens in your browser
- **Intelligent Agent**: Powered by Claude 3.5 Sonnet via Strands Agents
- **Beautiful UI**: Modern, responsive chat interface
- **Conversation Memory**: Maintains context across multiple questions
- **Real-time Interaction**: Instant responses to your queries
- **Multiple Capabilities**: 
  - General knowledge and information
  - Code help and technical assistance
  - Problem-solving and analysis
  - Creative writing
  - Math and calculations

## Prerequisites 📋

- Python 3.8 or higher
- An OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation & Setup 🚀

### 1. Clone or Download the Project

```bash
cd c:\Users\Hp\Desktop\apistrandsagentproject
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure API Key

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Open `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

## Running the Application 🎯

Simply run:

```bash
python app.py
```

**What happens:**
1. The Flask API server starts on `http://127.0.0.1:5000`
2. After 2 seconds, your default browser automatically opens
3. You'll see a beautiful chat interface with the Strands Agent
4. Start asking questions!

## How to Use 💬

1. **Ask Questions**: Type your question in the input box and press Enter or click "Send"
2. **Get Answers**: The Strands Agent will process your question and respond
3. **Continue Conversation**: The agent remembers context from previous messages
4. **Reset Chat**: Click "Reset" to start a fresh conversation

### Example Questions

Try asking:
- "What is artificial intelligence?"
- "Can you help me write Python code to sort a list?"
- "Explain quantum computing in simple terms"
- "What are best practices for REST API design?"
- "Write a short poem about coding"

## Project Structure 📁

```
apistrandsagentproject/
│
├── app.py                 # Main Flask application with Strands Agent
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API key)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore rules
├── README.md             # This file
│
└── templates/
    └── index.html        # Chat interface UI
```

## API Endpoints 🔌

### `GET /`
Serves the main chat interface

### `POST /api/chat`
Sends a question to the agent
```json
Request: {"question": "Your question here"}
Response: {"answer": "Agent's response", "status": "success"}
```

### `POST /api/reset`
Resets the conversation history
```json
Response: {"status": "success", "message": "Conversation reset"}
```

### `GET /api/health`
Health check endpoint
```json
Response: {"status": "healthy", "agent": "ready"}
```

## Technology Stack 🛠️

- **Backend**: Flask (Python web framework)
- **AI Model**: GPT-4 Turbo (via OpenAI API)
- **Agent Framework**: Strands Agents pattern
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with gradient design

## How It Works 🔍

1. **Application Launch**: When you run `app.py`, Flask starts a web server
2. **Auto-Open**: A timer triggers your browser to open the application
3. **User Interaction**: You type a question in the web interface
4. **API Request**: JavaScript sends your question to `/api/chat`
5. **Agent Processing**: The Strands Agent (powered by GPT-4 Turbo) processes your question with conversation context
6. **Response**: The answer is sent back and displayed in the chat
7. **Context Maintenance**: Conversation history is maintained for contextual responses

## Strands Agent Implementation 🧠

The application uses a custom Strands Agent implementation that:
- Maintains conversation history for context
- Uses GPT-4 Turbo for intelligent responses
- Provides a system prompt defining agent capabilities
- Handles errors gracefully
- Supports conversation reset

## Customization 🎨

### Change the AI Model

Edit `app.py` and modify the model parameter:
```python
agent = StrandsAgent(model="gpt-4")  # or "gpt-3.5-turbo"
```

### Customize Agent Behavior

Edit the `AGENT_SYSTEM_PROMPT` in `app.py` to change how the agent responds.

### Modify the UI

Edit `templates/index.html` to change colors, layout, or add features.

## Troubleshooting 🔧

### "OPENAI_API_KEY not set" Error
- Make sure you created a `.env` file (not `.env.example`)
- Verify your API key is correctly copied into the `.env` file

### Browser Doesn't Open Automatically
- Manually navigate to `http://127.0.0.1:5000` in your browser

### Agent Responses are Slow
- This is normal; AI processing can take a few seconds
- Check your internet connection

### Port 5000 Already in Use
Edit `app.py` and change the port:
```python
app.run(debug=True, use_reloader=False, port=5001)
```

## Security Notes 🔒

- Never commit your `.env` file to version control
- Keep your API key confidential
- The `.gitignore` file is configured to exclude `.env`

## License 📄

This project is open source and available for educational and commercial use.

## Support & Contribution 🤝

Feel free to:
- Report issues
- Suggest features
- Submit pull requests
- Share your improvements

---

**Enjoy using your Strands Agent! 🚀**

For questions about OpenAI's API, visit: https://platform.openai.com/docs
