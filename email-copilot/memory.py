import json
import os
from models import WritingStyle
from typing import Optional

STYLE_FILE = os.path.join(os.path.dirname(__file__), "style_profile.json")

def load_style() -> WritingStyle:
    if os.path.exists(STYLE_FILE):
        with open(STYLE_FILE, "r") as f:
            data = json.load(f)
            return WritingStyle.model_validate(data)
    return WritingStyle()

def save_style(style: WritingStyle):
    with open(STYLE_FILE, "w") as f:
        f.write(style.model_dump_json(indent=2))

def update_style_profile(feedback_type: str, value: str):
    style = load_style()
    
    if feedback_type == "tone":
        style.tone_markers.append(value)
    elif feedback_type == "greeting":
        if value not in style.preferred_greetings:
            style.preferred_greetings.append(value)
    elif feedback_type == "closing":
        if value not in style.preferred_closings:
            style.preferred_closings.append(value)
            
    save_style(style)
