import json
import os
from crewai import Agent, Task, Crew, Process

from agents.traffic_monitor import create_traffic_monitor_agent
from agents.congestion_analyst import create_congestion_analyst_agent
from agents.rag_knowledge import create_rag_knowledge_agent
from agents.emergency_router import create_emergency_router_agent
from agents.signal_optimizer import create_signal_optimizer_agent
from agents.public_notifier import create_public_notifier_agent


class TrafficCommanderCrew:
    """AI City Traffic Commander - CrewAI Orchestrator with 6 Agents."""

    def __init__(self):
        self.llm = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")

    def run(self, incident_description: str, location: str = "Unknown", incident_type: str = "General") -> dict:
        """Run the full 6-agent pipeline for a traffic incident."""
        
        # Create all 6 agents
        monitor_agent = create_traffic_monitor_agent(self.llm)
        congestion_agent = create_congestion_analyst_agent(self.llm)
        rag_agent = create_rag_knowledge_agent(self.llm)
        route_agent = create_emergency_router_agent(self.llm)
        signal_agent = create_signal_optimizer_agent(self.llm)
        notifier_agent = create_public_notifier_agent(self.llm)

        # Define tasks in sequential pipeline
        task1_monitor = Task(
            description=(
                f"Analyze this traffic incident report and extract all critical details:\n\n"
                f"INCIDENT REPORT: {incident_description}\n"
                f"REPORTED LOCATION: {location}\n"
                f"INCIDENT TYPE: {incident_type}\n\n"
                f"You MUST:\n"
                f"1. Use the Weather Lookup Tool to get current weather for the location\n"
                f"2. Use the Geocode Location Tool to validate and get coordinates for the location\n"
                f"3. Extract: location details, weather conditions, accident type, estimated traffic density, "
                f"number of blocked lanes, total lanes, severity level, time of day\n\n"
                f"Return a structured report with all extracted data."
            ),
            expected_output=(
                "A comprehensive structured report containing: exact location with coordinates, "
                "current weather conditions from the API, accident type and description, "
                "traffic density estimate, number of blocked and total lanes, "
                "severity level (minor/moderate/major/critical/fatal), and time of day. "
                "All data should be clearly organized for the next agent to use."
            ),
            agent=monitor_agent,
        )

        task2_congestion = Task(
            description=(
                f"Using the structured incident data from the Traffic Monitor, analyze congestion:\n\n"
                f"You MUST:\n"
                f"1. Use the Traffic Density Calculator Tool with the extracted parameters "
                f"(blocked_lanes, total_lanes, accident_severity, time_of_day, is_highway)\n"
                f"2. Use the Historical Incidents Database Tool to check for past incidents in the area\n"
                f"3. Identify all affected roads and potential traffic hotspots\n"
                f"4. Predict cascading congestion effects on nearby intersections\n\n"
                f"Provide a detailed congestion analysis with quantitative data."
            ),
            expected_output=(
                "A detailed congestion analysis report containing: congestion severity score (1-10), "
                "estimated delay in minutes, list of affected roads, identified traffic hotspots, "
                "historical incident patterns, cascading effects on nearby areas, "
                "and recommendations for traffic management priorities."
            ),
            agent=congestion_agent,
            context=[task1_monitor],
        )

        task3_rag = Task(
            description=(
                f"Based on the incident details and congestion analysis, search the traffic knowledge base:\n\n"
                f"You MUST perform MULTIPLE searches using the RAG Knowledge Search Tool:\n"
                f"1. Search for traffic rules relevant to the incident type\n"
                f"2. Search for emergency response SOPs applicable to this situation\n"
                f"3. Search for road diversion policies for the affected area type\n"
                f"4. Search for signal control guidelines for emergency situations\n\n"
                f"Compile all retrieved knowledge into a comprehensive guideline document."
            ),
            expected_output=(
                "A comprehensive knowledge retrieval report containing: relevant traffic rules and regulations, "
                "applicable emergency response standard operating procedures, recommended diversion policies, "
                "signal control guidelines, with source citations for each piece of retrieved knowledge. "
                "This should directly inform the emergency route planning and signal optimization."
            ),
            agent=rag_agent,
            context=[task1_monitor, task2_congestion],
        )

        task4_routes = Task(
            description=(
                f"Using the congestion data and traffic guidelines, plan emergency routes:\n\n"
                f"You MUST:\n"
                f"1. Use the Route Calculator Tool to calculate routes for an AMBULANCE from the nearest hospital to the incident\n"
                f"2. Use the Route Calculator Tool to calculate routes for POLICE from the nearest station to the incident\n"
                f"3. Use the Route Calculator Tool to calculate routes for a FIRE TRUCK from the nearest fire station to the incident\n"
                f"4. Consider the congestion score from the analysis when calculating routes\n"
                f"5. Use Geocode Location Tool to verify any location names\n\n"
                f"Provide detailed route recommendations for all three emergency services."
            ),
            expected_output=(
                "Emergency route recommendations for ambulance, police, and fire services. "
                "Each should include: primary route with ETA, alternate route with ETA, "
                "emergency bypass option, current road conditions, and specific instructions. "
                "Include the congestion score used and justify route choices."
            ),
            agent=route_agent,
            context=[task1_monitor, task2_congestion, task3_rag],
        )

        task5_signals = Task(
            description=(
                f"Based on the congestion data and emergency routes, optimize traffic signals:\n\n"
                f"You MUST:\n"
                f"1. Use the Signal Timing Optimizer Tool for the main incident intersection\n"
                f"2. Use the Signal Timing Optimizer Tool for at least one adjacent intersection\n"
                f"3. Use the Signal Config File Writer Tool to save the configurations\n"
                f"4. Consider emergency vehicle preemption based on the route plan\n\n"
                f"Provide optimized signal configurations and lane diversion plans."
            ),
            expected_output=(
                "Signal optimization report containing: optimized timing for incident intersection, "
                "optimized timing for adjacent intersections, emergency vehicle preemption configuration, "
                "lane diversion plans, contraflow recommendations if needed, "
                "and confirmation that configurations have been saved to files."
            ),
            agent=signal_agent,
            context=[task2_congestion, task3_rag, task4_routes],
        )

        task6_notify = Task(
            description=(
                f"Generate comprehensive public notifications based on all analysis:\n\n"
                f"You MUST:\n"
                f"1. Use the Public Alert Generator Tool to create alerts for SMS, email, dashboard, and social media\n"
                f"2. Use the Alert File Writer Tool to save the alerts for distribution\n"
                f"3. Include alternate route recommendations for commuters\n"
                f"4. Create clear, actionable messages appropriate for each channel\n\n"
                f"Generate complete public notification package."
            ),
            expected_output=(
                "A complete public notification package containing: SMS alert (under 160 characters), "
                "email advisory with full details, dashboard notification with severity color coding, "
                "social media post, alternate route recommendations for commuters, "
                "and confirmation that all alerts have been saved to files."
            ),
            agent=notifier_agent,
            context=[task1_monitor, task2_congestion, task4_routes, task5_signals],
        )

        # Create and run the crew
        crew = Crew(
            agents=[monitor_agent, congestion_agent, rag_agent, route_agent, signal_agent, notifier_agent],
            tasks=[task1_monitor, task2_congestion, task3_rag, task4_routes, task5_signals, task6_notify],
            process=Process.sequential,
            verbose=True,
            max_rpm=10,
        )

        result = crew.kickoff()

        # Parse results from each task
        results = {
            "traffic_monitor": {
                "agent": "Traffic Monitoring Officer",
                "tools_used": ["Weather Lookup API", "Geocode Location API"],
                "output": str(task1_monitor.output) if task1_monitor.output else "Processing...",
            },
            "congestion_analysis": {
                "agent": "Traffic Data Analyst",
                "tools_used": ["Traffic Density Calculator", "Historical Incidents Database"],
                "output": str(task2_congestion.output) if task2_congestion.output else "Processing...",
            },
            "rag_knowledge": {
                "agent": "Traffic Knowledge Expert (RAG)",
                "tools_used": ["RAG Knowledge Search (Gemini Embeddings)"],
                "output": str(task3_rag.output) if task3_rag.output else "Processing...",
            },
            "emergency_routes": {
                "agent": "Emergency Navigation Specialist",
                "tools_used": ["Route Calculator", "Geocode Location API"],
                "output": str(task4_routes.output) if task4_routes.output else "Processing...",
            },
            "signal_optimization": {
                "agent": "Smart Signal Control Engineer",
                "tools_used": ["Signal Timing Optimizer", "Signal Config File Writer"],
                "output": str(task5_signals.output) if task5_signals.output else "Processing...",
            },
            "public_notification": {
                "agent": "Public Information Officer",
                "tools_used": ["Public Alert Generator", "Alert File Writer"],
                "output": str(task6_notify.output) if task6_notify.output else "Processing...",
            },
            "crew_output": str(result) if result else "No output",
        }

        return results
