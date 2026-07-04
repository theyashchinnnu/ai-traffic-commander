from crewai import Agent
from agents.tools import route_calculator_tool, geocode_location_tool


def create_emergency_router_agent(llm) -> Agent:
    """Creates the Emergency Route Planner Agent - Agent 4."""
    return Agent(
        role="Emergency Navigation Specialist",
        goal="Using congestion analysis and traffic guidelines, calculate and recommend the fastest and safest routes for ambulances, police vehicles, and fire services responding to the incident.",
        backstory=(
            "You are a specialized emergency navigation expert who has coordinated thousands of emergency responses. "
            "You calculate optimal routes considering real-time congestion, road blockages, and vehicle capabilities. "
            "You always provide primary, alternate, and emergency bypass routes for each emergency vehicle type. "
            "Your route recommendations save lives by minimizing response times."
        ),
        tools=[route_calculator_tool, geocode_location_tool],
        llm=llm,
        verbose=True,
        max_iter=3,
        max_execution_time=120,
    )
