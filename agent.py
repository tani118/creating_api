"""
LangChain Agent for Train Booking using Groq Llama 3.3 70B
Handles complete conversation flow from search to booking
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
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
    get_train_route,
    get_trains_summary,
    book_train_placeholder,
    get_trains_by_class,
    get_trains_by_type,
    get_train_booking_options,
    book_train_submit,
    close_browser
)

# Load environment variables
load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,  # Low temperature for consistent responses
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
    get_train_route,
    get_trains_summary,
    book_train_placeholder,
    get_trains_by_class,
    get_trains_by_type,
    get_train_booking_options,
    book_train_submit,
    close_browser
]

# Create the system prompt
system_prompt = """You are a helpful and friendly train booking assistant for Indian Railways (IRCTC). 
Your goal is to help users search for trains, find the best options, and guide them through the booking process.

IMPORTANT GUIDELINES:
1. Always be polite, clear, and concise
2. When searching trains, ask for source, destination, and date if not provided
3. Use standard station codes (e.g., NDLS for New Delhi, BCT for Mumbai Central)
4. After showing results, ask users how they want to filter (cheapest, fastest, specific class)
5. Proactively suggest relevant filters based on user needs
6. When user selects a train, confirm all details before booking
7. If booking is not available yet, inform them clearly and provide alternatives

STATION CODES - Common Examples:
- Delhi: NDLS (New Delhi), DLI (Old Delhi)
- Mumbai: BCT (Mumbai Central), CSTM (Mumbai CST), BVI (Borivali)
- Bangalore: SBC (Bangalore City), YPR (Yesvantpur)
- Chennai: MAS (Chennai Central)
- Kolkata: HWH (Howrah), SDAH (Sealdah)
- Ahmedabad: ADI
- Pune: PUNE
- Hyderabad: HYB

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
3. Show available options using get_available_trains
4. Apply filters if requested (cheapest, fastest, by class)
5. Show detailed train info when user selects
6. Attempt booking (currently placeholder)
7. Provide confirmation or next steps

Always use the provided tools to fetch real-time data. Never make up train numbers or availability.

CRITICAL INSTRUCTIONS:
- Always use proper station codes (NDLS, BCT, SBC, etc.)
- Date format must be DD-MM-YYYY
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
- If you need information from the user, use "Final Answer" to ask them directly
- For search_trains Action Input, provide a JSON string like: {{"source": "NDLS", "destination": "BCT", "date": "25-11-2025", "quota": "GN"}}

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
    max_iterations=15,
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
