"""
Weather tool for getting weather information.
"""

from langchain.tools import tool
from typing import Dict, Any


@tool
def weather_tool(location: str) -> str:
    """Get current weather information for a given location.
    
    Args:
        location: The city or location to get weather for
        
    Returns:
        Weather information as a string
    """
    # This is a mock implementation - in real use, you'd call a weather API
    weather_data = {
        "New York": "Sunny, 22°C",
        "London": "Cloudy, 15°C", 
        "Tokyo": "Rainy, 18°C",
        "Paris": "Partly cloudy, 20°C",
        "Sydney": "Sunny, 25°C"
    }
    
    location_clean = location.strip().title()
    
    if location_clean in weather_data:
        return f"Weather in {location_clean}: {weather_data[location_clean]}"
    else:
        return f"Weather data not available for {location_clean}. Available cities: {', '.join(weather_data.keys())}"
