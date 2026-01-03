"""
Task line parser.

Extracts task title and duration from a single line of text.
Moved from app.core.parser to consolidate business logic in services.
"""

import re
from typing import Tuple


def parse_task_line(line: str) -> Tuple[str, int, float, str]:
    """
    Parse a single task line to extract title and duration.

    Args:
        line: Raw task line from user input

    Returns:
        Tuple of (title, duration_minutes, confidence, parse_method)
        - title: The task description/name
        - duration_minutes: Parsed or default duration in minutes
        - confidence: How confident we are in the parse (0.0 to 1.0)
        - parse_method: Which parsing strategy was used

    Examples:
        >>> parse_task_line("Buy groceries 30m")
        ("Buy groceries", 30, 1.0, "regex_v1")
        >>> parse_task_line("Team meeting")
        ("Team meeting", 60, 0.5, "default")
    """
    line = line.strip()

    if not line:
        return ("", 60, 0.0, "empty")

    # Pattern: matches duration at end of line
    # Supports: 30m, 1h, 2.5h, 90min, 1.5hr, 2 hours
    duration_pattern = r'\s+(\d+\.?\d*)\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\s*$'

    match = re.search(duration_pattern, line, re.IGNORECASE)

    if match:
        # Extract title (everything before the duration)
        title = line[:match.start()].strip()

        # Extract duration value and unit
        value = float(match.group(1))
        unit = match.group(2).lower()

        # Convert to minutes
        if unit in ('m', 'min', 'mins', 'minute', 'minutes'):
            duration_minutes = int(value)
        elif unit in ('h', 'hr', 'hrs', 'hour', 'hours'):
            duration_minutes = int(value * 60)
        else:
            duration_minutes = 60  # fallback

        return (title, duration_minutes, 1.0, "regex_v1")

    # No duration found - use default
    return (line, 60, 0.5, "default")
