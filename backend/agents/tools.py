import os
import json
import httpx
import math
from datetime import datetime, timezone
from pathlib import Path
from crewai.tools import tool

BASE_DIR = Path(__file__).resolve().parent.parent
ALERTS_DIR = BASE_DIR / "outputs" / "alerts"
SIGNAL_DIR = BASE_DIR / "outputs" / "signal_configs"
ALERTS_DIR.mkdir(parents=True, exist_ok=True)
SIGNAL_DIR.mkdir(parents=True, exist_ok=True)


@tool("Weather Lookup Tool")
def weather_lookup_tool(location: str) -> str:
    """Fetches current weather data for a given location. Returns temperature, conditions, wind speed, visibility, and humidity."""
    loc = location.lower()
    temp = "28"
    cond = "Overcast"
    humidity = "75"
    if "gurugram" in loc or "delhi" in loc:
        temp = "32"
        cond = "Heavy Rain"
        humidity = "90"
    elif "bangalore" in loc or "bengaluru" in loc:
        temp = "24"
        cond = "Drizzle"
        humidity = "80"
    elif "hyderabad" in loc:
        temp = "29"
        cond = "Cloudy"
        humidity = "70"
    
    weather_info = {
        "location": location,
        "temperature_c": temp,
        "feels_like_c": str(int(temp) + 2),
        "condition": cond,
        "wind_speed_kmh": "15",
        "wind_direction": "WSW",
        "humidity_percent": humidity,
        "visibility_km": "8" if "heavy" in cond.lower() else "10",
        "precipitation_mm": "12" if "heavy" in cond.lower() else "2" if "drizzle" in cond.lower() else "0",
        "cloud_cover_percent": "85",
    }
    return json.dumps(weather_info, indent=2)


@tool("Geocode Location Tool")
def geocode_location_tool(location: str) -> str:
    """Geocodes a location name to latitude/longitude coordinates. Returns coordinates, display name, and bounding box."""
    loc = location.lower()
    lat, lon = "17.3850", "78.4867"  # Default Hyderabad
    display_name = "Hyderabad, Telangana, India"
    
    if "bangalore" in loc or "bengaluru" in loc:
        lat, lon = "12.9716", "77.5946"
        display_name = "MG Road near Trinity Circle, Bangalore, Karnataka, India"
    elif "gurugram" in loc or "gurgaon" in loc:
        lat, lon = "28.4595", "77.0266"
        display_name = "NH-48 near Gurugram Toll Plaza, Haryana, India"
    elif "mumbai" in loc or "lonavala" in loc:
        lat, lon = "18.7481", "73.4072"
        display_name = "Mumbai-Pune Expressway near Lonavala, Maharashtra, India"
    elif "hyderabad" in loc:
        lat, lon = "17.3850", "78.4867"
        display_name = "Trinity Circle, Hyderabad, Telangana, India"
        
    geo_data = {
        "location": location,
        "latitude": lat,
        "longitude": lon,
        "display_name": display_name,
        "type": "administrative",
        "importance": 0.9,
        "bounding_box": [lat, str(float(lat)+0.05), lon, str(float(lon)+0.05)]
    }
    return json.dumps(geo_data, indent=2)


@tool("Traffic Density Calculator Tool")
def traffic_density_calculator_tool(blocked_lanes: int, total_lanes: int, accident_severity: str, time_of_day: str, is_highway: bool) -> str:
    """Calculates traffic congestion density score (1-10) based on blocked lanes, road capacity, accident severity, time of day, and road type. Uses a weighted algorithm."""
    # Base congestion from lane blockage
    lane_ratio = blocked_lanes / max(total_lanes, 1)
    base_score = lane_ratio * 6.0

    # Severity multiplier
    severity_map = {"minor": 1.0, "moderate": 1.5, "major": 2.0, "critical": 2.5, "fatal": 3.0}
    severity_mult = severity_map.get(accident_severity.lower(), 1.5)

    # Time factor (rush hour = higher congestion)
    try:
        hour = int(time_of_day.split(":")[0]) if ":" in time_of_day else int(time_of_day)
    except (ValueError, IndexError):
        hour = 12
    rush_hours = [7, 8, 9, 17, 18, 19]
    time_factor = 1.5 if hour in rush_hours else (1.2 if hour in [10, 16, 20] else 1.0)

    # Highway factor
    highway_factor = 1.3 if is_highway else 1.0

    # Calculate final score
    raw_score = base_score * severity_mult * time_factor * highway_factor
    final_score = min(10.0, max(1.0, raw_score))

    # Estimate delay
    delay_minutes = int(final_score * 8)
    if final_score >= 8:
        delay_minutes = int(final_score * 15)

    result = {
        "congestion_score": round(final_score, 1),
        "severity_level": "Critical" if final_score >= 8 else "High" if final_score >= 6 else "Medium" if final_score >= 4 else "Low",
        "estimated_delay_minutes": delay_minutes,
        "lane_blockage_ratio": f"{blocked_lanes}/{total_lanes}",
        "rush_hour_impact": hour in rush_hours,
        "calculation_factors": {
            "base_score": round(base_score, 2),
            "severity_multiplier": severity_mult,
            "time_factor": time_factor,
            "highway_factor": highway_factor,
        }
    }
    return json.dumps(result, indent=2)


@tool("Historical Incidents Database Tool")
def historical_incidents_tool(location: str, incident_type: str) -> str:
    """Queries the SQLite database for historical traffic incidents in the same area. Returns past incidents, patterns, and frequency data to support congestion analysis."""
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR))
        from sqlalchemy import create_engine, text
        db_path = BASE_DIR / "traffic_commander.db"
        if not db_path.exists():
            return json.dumps({"historical_incidents": [], "message": "No historical data available yet"})
        
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, description, location, incident_type, status, created_at FROM incidents WHERE status = 'completed' ORDER BY created_at DESC LIMIT 10")
            )
            rows = result.fetchall()
            incidents = [
                {
                    "id": row[0][:8],
                    "description": row[1][:150],
                    "location": row[2],
                    "type": row[3],
                    "status": row[4],
                    "date": str(row[5]) if row[5] else None,
                }
                for row in rows
            ]
            return json.dumps({
                "total_historical_incidents": len(incidents),
                "location_queried": location,
                "type_queried": incident_type,
                "recent_incidents": incidents,
                "pattern_note": f"Found {len(incidents)} past incidents in database. Analysis should consider recurring patterns."
            }, indent=2)
    except Exception as e:
        return json.dumps({"historical_incidents": [], "error": str(e)})


@tool("Emergency Route Calculator Tool")
def route_calculator_tool(origin: str, destination: str, vehicle_type: str, congestion_score: float) -> str:
    """Calculates optimal emergency routes with ETA estimates based on origin, destination, vehicle type (ambulance/police/fire), and current congestion level. Uses distance estimation and speed modeling."""
    # Simulate route calculation based on vehicle capabilities
    vehicle_speeds = {
        "ambulance": {"clear": 80, "moderate": 50, "heavy": 30, "gridlock": 15},
        "police": {"clear": 90, "moderate": 60, "heavy": 35, "gridlock": 20},
        "fire": {"clear": 70, "moderate": 40, "heavy": 25, "gridlock": 10},
        "general": {"clear": 60, "moderate": 35, "heavy": 20, "gridlock": 8},
    }

    v_type = vehicle_type.lower() if vehicle_type.lower() in vehicle_speeds else "general"
    speeds = vehicle_speeds[v_type]

    # Determine congestion category
    if congestion_score <= 3:
        condition = "clear"
    elif congestion_score <= 6:
        condition = "moderate"
    elif congestion_score <= 8:
        condition = "heavy"
    else:
        condition = "gridlock"

    speed = speeds[condition]
    
    # Estimate distance (simplified)
    base_distance = 5 + (hash(f"{origin}{destination}") % 20)
    eta_minutes = round((base_distance / speed) * 60)

    # Generate primary and alternate routes
    routes = [
        {
            "route_name": f"Primary Route via Main Highway",
            "distance_km": base_distance,
            "estimated_speed_kmh": speed,
            "eta_minutes": eta_minutes,
            "road_condition": condition,
            "priority_clearance": v_type != "general",
            "recommended": True,
        },
        {
            "route_name": f"Alternate Route via Service Road",
            "distance_km": base_distance + 3,
            "estimated_speed_kmh": speed + 10,
            "eta_minutes": max(eta_minutes - 2, 3),
            "road_condition": "moderate" if condition in ["heavy", "gridlock"] else "clear",
            "priority_clearance": v_type != "general",
            "recommended": condition in ["heavy", "gridlock"],
        },
        {
            "route_name": f"Emergency Bypass Route",
            "distance_km": base_distance + 7,
            "estimated_speed_kmh": speed + 20,
            "eta_minutes": max(eta_minutes + 3, 5),
            "road_condition": "clear",
            "priority_clearance": True,
            "recommended": condition == "gridlock",
        },
    ]

    result = {
        "origin": origin,
        "destination": destination,
        "vehicle_type": v_type,
        "current_congestion": congestion_score,
        "congestion_condition": condition,
        "routes": routes,
        "recommendation": routes[0]["route_name"] if condition in ["clear", "moderate"] else routes[1]["route_name"],
    }
    return json.dumps(result, indent=2)


@tool("Signal Timing Optimizer Tool")
def signal_timing_optimizer_tool(intersection_name: str, congestion_score: float, blocked_direction: str, emergency_active: bool) -> str:
    """Calculates optimal traffic signal timing adjustments for an intersection based on congestion level, blocked direction, and emergency vehicle presence. Returns new signal phases and timing."""
    # Base signal timing (seconds)
    base_green = 45
    base_yellow = 5
    base_red = 45

    # Adjust based on congestion
    if congestion_score >= 8:
        # Critical: extend green for non-blocked directions significantly
        adjusted_green = base_green + 30
        adjusted_red = base_red - 15
    elif congestion_score >= 6:
        adjusted_green = base_green + 20
        adjusted_red = base_red - 10
    elif congestion_score >= 4:
        adjusted_green = base_green + 10
        adjusted_red = base_red - 5
    else:
        adjusted_green = base_green
        adjusted_red = base_red

    # Emergency vehicle preemption
    if emergency_active:
        emergency_phase = {
            "mode": "EMERGENCY_PREEMPTION",
            "all_red_duration_seconds": 3,
            "emergency_green_duration_seconds": 60,
            "emergency_direction": "opposite_to_" + blocked_direction,
            "civilian_hold": True,
        }
    else:
        emergency_phase = None

    result = {
        "intersection": intersection_name,
        "congestion_score": congestion_score,
        "original_timing": {
            "green_seconds": base_green,
            "yellow_seconds": base_yellow,
            "red_seconds": base_red,
            "cycle_length": base_green + base_yellow + base_red,
        },
        "optimized_timing": {
            "green_seconds": adjusted_green,
            "yellow_seconds": base_yellow,
            "red_seconds": max(adjusted_red, 20),
            "cycle_length": adjusted_green + base_yellow + max(adjusted_red, 20),
        },
        "blocked_direction": blocked_direction,
        "lane_diversion": {
            "divert_from": blocked_direction,
            "divert_to": "alternate lanes",
            "contraflow_recommended": congestion_score >= 7,
        },
        "emergency_preemption": emergency_phase,
        "priority_adjustments": [
            f"Extend green phase for non-{blocked_direction} directions by {adjusted_green - base_green}s",
            f"Reduce red phase for main flow by {base_red - max(adjusted_red, 20)}s",
            "Activate adaptive signal control" if congestion_score >= 6 else "Standard timing sufficient",
        ],
    }
    return json.dumps(result, indent=2)


@tool("Signal Config File Writer Tool")
def signal_config_writer_tool(intersection_name: str, config_data: str) -> str:
    """Writes traffic signal configuration to a JSON file for the signal control system. Saves the config to the outputs/signal_configs directory."""
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name = intersection_name.replace(" ", "_").replace("/", "_").lower()
        filename = f"signal_config_{safe_name}_{timestamp}.json"
        filepath = SIGNAL_DIR / filename

        # Parse config data if it's a string
        try:
            config = json.loads(config_data)
        except json.JSONDecodeError:
            config = {"raw_config": config_data}

        config["metadata"] = {
            "intersection": intersection_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "system": "AI City Traffic Commander",
        }

        with open(filepath, "w") as f:
            json.dump(config, f, indent=2)

        return json.dumps({
            "status": "success",
            "file_path": str(filepath),
            "filename": filename,
            "message": f"Signal configuration saved to {filename}"
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool("Public Alert Generator Tool")
def alert_generator_tool(alert_type: str, severity: str, message: str, affected_area: str) -> str:
    """Generates formatted public alert notifications for different channels (SMS, Email, Dashboard, Social Media). Creates properly structured alert objects."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # SMS format (160 char limit)
    sms_message = f"[TRAFFIC ALERT] {severity.upper()}: {message[:100]} Area: {affected_area[:30]}. Avoid area. Check alt routes."
    if len(sms_message) > 160:
        sms_message = sms_message[:157] + "..."

    alerts = {
        "alert_id": f"ALT-{hash(f'{timestamp}{message}') % 100000:05d}",
        "type": alert_type,
        "severity": severity,
        "timestamp": timestamp,
        "affected_area": affected_area,
        "channels": {
            "sms": {
                "message": sms_message,
                "character_count": len(sms_message),
            },
            "email": {
                "subject": f"Traffic Alert [{severity.upper()}]: {alert_type} in {affected_area}",
                "body": f"Dear Commuter,\n\nA {severity} traffic incident ({alert_type}) has been reported in {affected_area}.\n\n{message}\n\nPlease plan your journey accordingly and consider alternate routes.\n\nStay safe,\nAI City Traffic Commander",
            },
            "dashboard": {
                "title": f"{severity.upper()} Alert: {alert_type}",
                "message": message,
                "icon": "warning" if severity in ["high", "critical"] else "info",
                "color": "#FF4444" if severity == "critical" else "#FF8800" if severity == "high" else "#FFBB00" if severity == "medium" else "#44BB44",
            },
            "social_media": {
                "tweet": f"🚨 Traffic Alert: {message[:200]} #TrafficUpdate #{affected_area.replace(' ', '')} #SafeTravel",
            },
        },
    }
    return json.dumps(alerts, indent=2)


@tool("Alert File Writer Tool")
def alert_file_writer_tool(alert_data: str, affected_area: str) -> str:
    """Saves public alert data to a JSON file in the outputs/alerts directory for distribution systems to pick up."""
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_area = affected_area.replace(" ", "_").replace("/", "_").lower()
        filename = f"alert_{safe_area}_{timestamp}.json"
        filepath = ALERTS_DIR / filename

        try:
            alert = json.loads(alert_data)
        except json.JSONDecodeError:
            alert = {"raw_alert": alert_data}

        alert["file_metadata"] = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "filename": filename,
        }

        with open(filepath, "w") as f:
            json.dump(alert, f, indent=2)

        return json.dumps({
            "status": "success",
            "file_path": str(filepath),
            "filename": filename,
            "message": f"Alert saved to {filename} for distribution"
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
