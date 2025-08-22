"""
Example of a custom tool to demonstrate the generic routing system.
"""

from langchain.tools import tool


@tool
def joke_tool(topic: str) -> str:
    """Tell a joke about a specific topic.
    
    Args:
        topic: The topic for the joke
        
    Returns:
        A joke about the given topic
    """
    # This is a mock implementation with some predefined jokes
    jokes = {
        "programming": "Why do programmers prefer dark mode? Because light attracts bugs!",
        "ai": "Why did the AI go to therapy? It had too many deep learning issues!",
        "computer": "Why don't computers ever get cold? They have Windows!",
        "python": "Why do Python programmers prefer snakes? Because they're already used to dealing with bugs!",
        "cat": "Why don't cats make good quantum physicists? Because they always land on their feet!",
        "dog": "Why do dogs make terrible DJs? Because they have such ruff beats!"
    }
    
    topic_lower = topic.lower().strip()
    
    # Check for exact matches first
    if topic_lower in jokes:
        return jokes[topic_lower]
    
    # Check for partial matches
    for key, joke in jokes.items():
        if key in topic_lower or topic_lower in key:
            return joke
    
    # Default generic joke
    return f"Why did the {topic} cross the road? To get to the other side! (Sorry, I don't have a specific joke about {topic} yet!)"
