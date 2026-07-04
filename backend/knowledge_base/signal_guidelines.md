# Traffic Signal Timing & Control Guidelines

## 1. Standard Signal Phase Design
- **Green Phase Definition**:
  - The green interval must be calculated based on intersection lane capacity and saturation flow rate.
  - **Minimum Green Interval**: 7 seconds for major approaches, 5 seconds for minor approaches, to allow queued vehicles to react and enter the intersection.
  - **Maximum Green Interval**: Typically capped at 60 seconds in urban networks to prevent excessive delay on waiting approaches.
- **Yellow Change Interval**:
  - Purpose: To warn drivers that the green phase is ending and the red phase is imminent.
  - Formula: Calculated using the ITE (Institute of Transportation Engineers) formula:
    \[t_y = t_{reaction} + \frac{V}{2a + 2gG}\]
    Where:
    - \(t_{reaction}\) = driver reaction time (default: 1.0 second).
    - \(V\) = approach speed in m/s.
    - \(a\) = deceleration rate (standard: 3.0 m/s²).
    - \(g\) = acceleration due to gravity (9.81 m/s²).
    - \(G\) = road grade (decimal).
  - Standard Value: 3.0 to 5.0 seconds based on approach speed.
- **Red Clearance (All-Red) Interval**:
  - Purpose: To allow vehicles that entered the intersection during the yellow phase to clear the conflict zone before cross-traffic receives a green light.
  - Standard Value: 1.0 to 3.0 seconds, depending on intersection width and design speed.

## 2. Adaptive Signal Control Principles
- **Dynamic Phase Extension**:
  - Loop detectors or video sensors detect vehicle presence. If a vehicle passes over the detector before the green time expires, the green phase is extended by a pre-set unit extension (typically 2.0 to 4.0 seconds), up to the Maximum Green limit.
- **Queue Clearance Adjustments**:
  - Signal controllers calculate queue lengths using camera feed metrics. The green phase is dynamically extended if queue discharge rates indicate that the queue has not cleared.
- **Green Wave Coordination (Progression)**:
  - Coordinate adjacent signals along an arterial road to allow a platoon of vehicles to pass through multiple intersections without stopping.
  - Calculated using the speed of the platoon and the distance between intersections (offset design).

## 3. Emergency Vehicle Preemption Protocols
- **Triggering Mechanisms**:
  - Emergency vehicle preemption is activated using GPS-based coordinates, optical sensors detecting flashing strobe lights, or acoustic sirens.
- **Phase Sequence Manipulation**:
  - **Immediate Termination**: If a conflicting phase is green, it must immediately transition to yellow (standard duration) and then all-red, before transitioning to green for the emergency vehicle's approach.
  - **Hold Phase**: If the emergency vehicle's approach is already green, the green phase is held indefinitely until the vehicle clears the intersection.
  - **Pedestrian Safety**: Pedestrian walk phases must be immediately truncated if preemption is triggered, transitioning to flashing "Don't Walk" at an accelerated rate.

## 4. Signal Control during Incidents & Blockages
- **Manual Control Override**:
  - Authorized traffic officers can override automatic signal controllers via physical control boxes or remote commands from the Traffic Control Center.
- **Phase Adjustments for Lane Blockages**:
  - If a lane is blocked on an approach, reduce the green time for that approach (as throughput is restricted) and increase green time for diversionary routes.
- **Late-Night Flashing Modes**:
  - During low-traffic hours (typically 23:00 to 05:00), signals may be set to flashing mode:
    - Major Road: Flashing yellow (proceed with caution).
    - Minor Road: Flashing red (treat as a stop sign).
