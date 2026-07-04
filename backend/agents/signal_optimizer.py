from crewai import Agent
from agents.tools import signal_timing_optimizer_tool, signal_config_writer_tool


def create_signal_optimizer_agent(llm) -> Agent:
    """Creates the Traffic Signal Optimization Agent - Agent 5."""
    return Agent(
        role="Smart Signal Control Engineer",
        goal="Calculate optimal traffic signal timing adjustments, recommend lane diversions, and configure emergency signal priority to reduce congestion and improve traffic flow around the incident.",
        backstory=(
            "You are a smart traffic signal control engineer specializing in adaptive signal systems. "
            "You calculate precise signal timing adjustments based on congestion data and write configuration files "
            "for the signal control system. You understand emergency vehicle preemption protocols and can configure "
            "priority green waves. You always save your signal configurations to files for the control system."
        ),
        tools=[signal_timing_optimizer_tool, signal_config_writer_tool],
        llm=llm,
        verbose=True,
        max_iter=10,
        max_execution_time=120,
    )
