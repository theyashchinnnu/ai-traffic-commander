from crewai import Agent
from agents.tools import traffic_density_calculator_tool, historical_incidents_tool


def create_congestion_analyst_agent(llm) -> Agent:
    """Creates the Congestion Analysis Agent - Agent 2."""
    return Agent(
        role="Traffic Data Analyst",
        goal="Analyze traffic incidents to predict congestion severity, estimate delays, identify affected roads, and pinpoint traffic hotspots using quantitative data analysis.",
        backstory=(
            "You are a senior traffic data analyst specializing in congestion modeling and predictive analytics. "
            "You use mathematical models to calculate congestion density scores and cross-reference historical incident data. "
            "Your analyses are data-driven — you always use the traffic density calculator and check historical patterns. "
            "You provide precise severity scores, delay estimates, and identify cascading congestion effects on nearby roads."
        ),
        tools=[traffic_density_calculator_tool, historical_incidents_tool],
        llm=llm,
        verbose=True,
        max_iter=10,
        max_execution_time=120,
    )
