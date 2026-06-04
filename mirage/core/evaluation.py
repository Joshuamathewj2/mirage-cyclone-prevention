import re
from typing import Dict, Any, List
from mirage.models.state import MirageState
from mirage.models.bulletin import CommunicationBulletin

def calculate_completeness(bulletin: CommunicationBulletin, state: MirageState) -> float:
    """M13: Measures whether critical information appears in the bulletin."""
    checks = 0
    met = 0
    
    # 1. Cyclone status mentioned?
    checks += 1
    if state.cyclone and str(state.cyclone.category) in bulletin.executive_summary:
        met += 1
    elif not state.cyclone:
        # If no cyclone, it shouldn't be mentioned? Or just pass.
        met += 1 
    
    # 2. Critical resources mentioned?
    checks += 1
    crit_res = [r.type for r in state.resources if r.quantity < 5000]
    if not crit_res: 
        met += 1
    else:
        if any(str(r) in bulletin.executive_summary.upper() for r in crit_res):
            met += 1
            
    # 3. Affected shelters mentioned?
    checks += 1
    state_shelter_ids = [s.id for s in state.shelters]
    if any(s in bulletin.affected_shelters for s in state_shelter_ids):
        met += 1
        
    return met / checks

def calculate_consistency(bulletin: CommunicationBulletin, state: MirageState) -> float:
    """M14: Checks whether bulletin statements match MirageState."""
    # Simple heuristic: find numbers in bulletin and check if they exist in state
    numbers = re.findall(r'\d+', bulletin.executive_summary)
    if not numbers:
        return 1.0
        
    state_data_str = str(state.model_dump())
    matches = sum(1 for n in numbers if n in state_data_str)
    
    return matches / len(numbers)

def calculate_readability(text: str) -> Dict[str, float]:
    """M17: Flesch Reading Ease and Grade Level."""
    # Simple implementation based on syllable/word/sentence counts to avoid deps
    sentences = len(re.split(r'[.!?]+', text))
    words = len(text.split())
    if words == 0: return {"ease": 0, "grade": 0}
    
    # Syllable approximation (simple)
    syllables = sum(len(re.findall(r'[aeiouy]+', w.lower())) for w in text.split())
    
    # Flesch Reading Ease
    ease = 206.835 - 1.015 * (words / max(1, sentences)) - 84.6 * (syllables / words)
    
    # Flesch-Kincaid Grade Level
    grade = 0.39 * (words / max(1, sentences)) + 11.8 * (syllables / words) - 15.59
    
    return {"ease": round(ease, 2), "grade": round(grade, 2)}
