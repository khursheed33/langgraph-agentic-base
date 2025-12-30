"""Utility functions for JSON parsing and extraction."""

import re
from typing import Any

from app.utils.logger import logger


def extract_json_from_text(text: str) -> str:
    """Extract JSON from text, handling markdown code blocks.
    
    Args:
        text: Text that may contain JSON in markdown code blocks or directly.
        
    Returns:
        Extracted JSON string, or original text if no JSON found.
    """
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # Return original text if no JSON found
    return text

