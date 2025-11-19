"""
LangChain Agent for Train Booking
Supports Google Gemini and Groq (cloud) models
Handles complete conversation flow from search to booking
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from tools import (
    search_trains,
    get_available_trains,
    get_cheapest_trains,
    get_fastest_trains,
    get_train_details,
    filter_trains,
    book_train,
    get_train_booking_options,
    get_train_route,
    get_trains_summary,
    get_trains_by_class,
    get_trains_by_type,
    book_train_submit,
    submit_booking_otp,
    show_payment_page,
    hide_browser,
    signin_user,
    submit_signin_otp,
    reset_browser,
    close_browser,
    get_city_stations
)

# Load environment variables
load_dotenv()

# Initialize LLM - Choose one option below:

# Option 1: Google Gemini (Recommended - Fast, Smart, Free tier available)
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",  # Stable model with 15 RPM limit. Other options: "gemini-1.5-pro"
#     temperature=0.1,
#     google_api_key=os.getenv("GOOGLE_API_KEY"),
#     max_output_tokens=2048
#     # convert_system_message_to_human is deprecated and no longer needed
# )

# Option 2: Groq (Cloud-based, requires API key)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    max_tokens=2048
)

# Define all available tools
tools = [
    search_trains,
    get_available_trains,
    get_cheapest_trains,
    get_fastest_trains,
    get_train_details,
    filter_trains,
    book_train,
    get_train_booking_options,
    get_train_route,
    get_trains_summary,
    get_trains_by_class,
    get_trains_by_type,
    get_train_booking_options,
    book_train_submit,
    signin_user,
    submit_booking_otp,
    submit_signin_otp,
    show_payment_page,
    hide_browser,
    reset_browser,
    close_browser,
    get_city_stations
]

# Create the system prompt
system_prompt = """You are a helpful and friendly train booking assistant for Indian Railways (IRCTC). 
Your goal is to help users search for trains, find the best options, and guide them through the booking process.

IMPORTANT GUIDELINES:
1. Always be polite, complete and comprehensive
2. When searching trains, ask for source, destination, and date if not provided
3. Use standard station codes (e.g., NDLS for New Delhi, BCT for Mumbai Central)
4. **IMPORTANT**: When user mentions a city name (like "Delhi", "Mumbai", "Bangalore") instead of station code, ALWAYS use the get_city_stations tool to show them all available stations in that city
5. Always List out available trains after searching trains then ask users how they want to filter (cheapest, fastest, specific class)
6. When user selects a train, confirm all details before booking
7. If booking is not available yet, inform them clearly and provide alternatives
8. Only reply to queries relevant to train booking - politely decline unrelated questions
9. Always summarize the booking details at the end

STATION CODES - When user mentions a city, use get_city_stations tool to fetch all stations:
- Example: User says "Delhi" → Use get_city_stations("Delhi") to show NDLS, DLI, NZM, ANVT, etc.
- Example: User says "Mumbai" → Use get_city_stations("Mumbai") to show BCT, CSTM, LTT, BDTS, etc.
- Example: User says "Bangalore" → Use get_city_stations("Bangalore") to show SBC, YPR, BNC, etc.
- DO NOT manually list station codes - ALWAYS use the tool to get accurate, complete information

TRAIN CLASSES:
- 1A: First AC
- 2A: Second AC
- 3A: Third AC
- SL: Sleeper
- 2S: Second Sitting
- CC: Chair Car

CONVERSATION FLOW:
1. Greet and understand user's travel needs
2. Search trains using search_trains tool
3. Show and list available trains to user
4. Apply filters if requested (cheapest, fastest, by class)
5. Show detailed train info when user selects
6. Attempt booking (currently placeholder)
7. Provide confirmation or next steps

Always use the provided tools to fetch real-time data. Never make up train numbers or availability.

CRITICAL INSTRUCTIONS:
- Whenever chat begins ask the user to provide his/her phone number and sign them in using signin_user tool.
- Always use proper station codes (NDLS, BCT, SBC, etc.)
- If user doesn't provide source/destination/date, respond with Final Answer asking for the missing information
- You can respond directly to the user using Final Answer - you don't need a tool for everything

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (for search_trains, use JSON string format)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: 
- If you need information from the user (like passenger details, phone number, etc.), DO NOT use Action: None
- Instead, use "Final Answer" to ask them directly - this is how you communicate with users
- For search_trains Action Input, provide a JSON string like: {{"source": "NDLS", "destination": "BCT", "date": "25-11-2025", "quota": "GN"}}
- NEVER write "Action: None" - if you want to talk to the user, go directly to "Final Answer"

ERROR HANDLING:
- If any action fails or you encounter an error during train search or booking, use the reset_browser tool
- The reset_browser tool will clear cache, reset browser state, and prepare for a fresh attempt
- After using reset_browser, you can retry the failed operation
- Use reset_browser when: search fails, booking gets stuck, user says "try again", or browser is on wrong page

Begin!

Previous conversation:
{chat_history}

Question: {input}
{agent_scratchpad}"""

# Create prompt template
prompt = PromptTemplate.from_template(system_prompt)

# Create the agent
agent = create_react_agent(llm, tools, prompt)

# Create agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10,  # Reduced from 15 for better performance with smaller models
    max_execution_time=90,
    return_intermediate_steps=False,
    early_stopping_method="force"  # Force completion even if agent gets stuck
)

# Store for chat histories (in production, use Redis or DB)
chat_histories = {}

def get_chat_history(session_id: str) -> str:
    """Get or create chat history for a session"""
    if session_id not in chat_histories:
        chat_histories[session_id] = ChatMessageHistory()
    
    history = chat_histories[session_id]
    if not history.messages:
        return ""
    
    # Format history for the prompt
    formatted = []
    for msg in history.messages:
        role = "Human" if isinstance(msg, HumanMessage) else "AI"
        formatted.append(f"{role}: {msg.content}")
    return "\n".join(formatted)

def chat(message: str, session_id: str = "default") -> dict:
    """
    Main chat interface for the agent
    
    Args:
        message: User's message
        session_id: Unique session ID for maintaining conversation history
    
    Returns:
        dict with response and metadata
    """
    try:
        # Get chat history
        history = get_chat_history(session_id)
        
        # Run the agent
        response = agent_executor.invoke({
            "input": message,
            "chat_history": history
        })
        
        # Extract output
        output = response.get("output", "")
        
        # If no output, return error
        if not output or output.strip() == "":
            output = "I apologize, but I couldn't generate a proper response. Could you please rephrase your question?"
        
        # Save to history
        if session_id not in chat_histories:
            chat_histories[session_id] = ChatMessageHistory()
        chat_histories[session_id].add_user_message(message)
        chat_histories[session_id].add_ai_message(output)
        
        return {
            "success": True,
            "response": output,
            "session_id": session_id
        }
    except StopIteration as e:
        return {
            "success": False,
            "response": "An unexpected error occurred. Please try again.",
            "error": "StopIteration error - agent chain interrupted",
            "session_id": session_id
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Agent Error: {error_trace}")
        return {
            "success": False,
            "response": f"Sorry, I encountered an error: {str(e)}",
            "error": str(e),
            "session_id": session_id
        }

def clear_history(session_id: str = "default"):
    """Clear chat history for a session"""
    if session_id in chat_histories:
        del chat_histories[session_id]
        return {"success": True, "message": f"History cleared for session {session_id}"}
    return {"success": False, "message": "Session not found"}

if __name__ == "__main__":
    # Test the agent
    print("Train Booking Agent - Test Mode")
    print("=" * 50)
    
    session = "test_session"
    
    # Test conversation
    test_queries = [
        "Hi, I want to travel from Delhi to Mumbai tomorrow",
        "Show me the cheapest trains in 3AC class",
    ]
    
    for query in test_queries:
        print(f"\nUser: {query}")
        result = chat(query, session)
        print(f"Agent: {result['response']}")
        print("-" * 50)
