"""Deterministic, explainable evidence scoring and next-question selection."""
from dataclasses import dataclass

FIELDS = {
    "banks": {"label": "Banks of the stream", "weight": 3, "options": ["Natural plants", "Concrete or stone", "Bare soil"]},
    "water": {"label": "Water appearance", "weight": 2, "options": ["Clear", "Cloudy", "Foamy or discoloured"]},
    "bottom": {"label": "Stream bottom", "weight": 2, "options": ["Mostly stones", "Mostly sand or mud", "Not visible"]},
    "habitat": {"label": "Habitat nearby", "weight": 1, "options": ["Plants or wildlife", "Little visible habitat", "Not sure"]},
}
VALUES = {"agrees": 1.0, "answered": .85, "unsure": .25, "missing": 0.0, "conflict": .20, "confirmed_conflict": .60}
ANSWER_VALUES = {
    "banks": {"Natural plants": 0.88, "Concrete or stone": 0.84, "Bare soil": 0.80},
    "water": {"Clear": 0.90, "Cloudy": 0.85, "Foamy or discoloured": 0.83},
    "bottom": {"Mostly stones": 0.88, "Mostly sand or mud": 0.84, "Not visible": 0.55},
    "habitat": {"Plants or wildlife": 0.90, "Little visible habitat": 0.78, "Not sure": 0.25},
}

@dataclass
class Decision:
    field: str | None
    gain: float
    why: str
    runner_up: list

def score(answers, photo_signals=None, confirmed_conflicts=None, context=None):
    photo_signals = photo_signals or {}
    confirmed_conflicts = set(confirmed_conflicts or [])
    total = sum(v["weight"] for v in FIELDS.values())
    points = 0.0
    breakdown = {}
    for key, meta in FIELDS.items():
        ans = answers.get(key)
        if not ans:
            state, value = "missing", VALUES["missing"]
        elif ans == "I'm not sure":
            state, value = "unsure", VALUES["unsure"]
        elif key in confirmed_conflicts:
            state, value = "confirmed_conflict", VALUES["confirmed_conflict"]
        elif key in photo_signals and ans != photo_signals[key]:
            state, value = "conflict", VALUES["conflict"]
        elif key in photo_signals:
            state, value = "agrees", VALUES["agrees"]
        else:
            state = "answered"
            if context:
                # Option-specific clarity variance
                if ans == "Not visible":
                    value = 0.60
                elif ans == "Little visible habitat":
                    value = 0.76
                elif ans in ("Natural plants", "Clear", "Mostly stones", "Plants or wildlife"):
                    value = 0.90
                elif ans.startswith("Other:") or ans.startswith("Others:"):
                    value = 0.88
                else:
                    value = ANSWER_VALUES.get(key, {}).get(ans, VALUES["answered"])
            else:
                value = VALUES["answered"]
        points += value * meta["weight"]
        breakdown[key] = {"label":meta["label"], "answer":ans, "state":state, "value":value, "weight":meta["weight"], "contribution":round(value*meta["weight"],2)}
    
    if not points:
        return 0.0, breakdown
        
    base_score = 100 * points / total
    if context:
        bonus = 0.0
        # Criterion 1: Verified GPS coordinates
        if context.get("has_location"):
            bonus += 5.0
        else:
            bonus -= 4.0
        
        # Criterion 2: Photographic visual evidence
        photos = context.get("photos_count", 0)
        if photos >= 2:
            bonus += 7.0
        elif photos == 1:
            bonus += 4.0
        else:
            bonus -= 3.0
            
        # Criterion 3: Detailed descriptive text
        text_len = context.get("text_length", 0)
        if text_len >= 60:
            bonus += 3.0
        elif text_len < 20:
            bonus -= 2.0
            
        # Criterion 4: Plausibility / warning flags
        flags = context.get("flags_count", 0)
        if flags > 0:
            bonus -= min(flags * 3.0, 9.0)
            
        answered_ratio = sum(FIELDS[k]["weight"] for k, v in answers.items() if v) / total
        base_score = min(max(base_score + bonus * answered_ratio, 0.0), 100.0)

    return round(base_score, 1), breakdown

def status_for(value, conflict=False):
    if conflict: return "Expert review"
    if value >= 80: return "Ready"
    if value >= 65: return "Usable - verify"
    return "Needs more info"

def next_question(answers, photo_signals=None, confirmed_conflicts=None, context=None):
    current, breakdown = score(answers, photo_signals, confirmed_conflicts, context=context)
    conflicts=[k for k,v in breakdown.items() if v["state"]=="conflict"]
    if conflicts:
        # A contradiction is the highest-value gap to resolve. Ask the citizen to
        # reconsider it; only their response can change the stored answer.
        key=max(conflicts,key=lambda k:FIELDS[k]["weight"])
        corrected=dict(answers); corrected[key]=photo_signals[key]
        gain=round(score(corrected,photo_signals,context=context)[0]-current,1)
        why=f"Your answer for {FIELDS[key]['label'].lower()} looks different from the photo. Please look again; your own answer stays in control."
        return Decision(key,gain,why,[])
    if current>=80:
        return Decision(None,0,"The observation has enough supporting detail for now.",[])
    candidates=[]
    for key, meta in FIELDS.items():
        if answers.get(key): continue
        hypothetical=dict(answers); hypothetical[key]=meta["options"][0]
        after,_=score(hypothetical,photo_signals)
        gain=round(after-current,1)
        if gain>0: candidates.append((gain/meta["weight"],gain,key))
    candidates.sort(reverse=True)
    if not candidates: return Decision(None,0,"All available details have an answer.",[])
    _,gain,key=candidates[0]
    why=f"{FIELDS[key]['label']} is still missing and adds the most evidence for the effort."
    return Decision(key,gain,why,[{"field":c[2],"gain":c[1]} for c in candidates[1:]])

def fhir_observation(item):
    return {"resourceType":"Observation","id":item["id"],"status":"preliminary","code":{"text":"Stream citizen observation"},"valueString":item.get("text",""),"component":[{"code":{"text":FIELDS[k]["label"]},"valueString":v} for k,v in item.get("answers",{}).items()],"extension":[{"url":"https://example.invalid/aquai/reliability-score (placeholder)","valueDecimal":item["score"]},{"url":"https://example.invalid/aquai/review-tier (placeholder)","valueString":item["status"]}]}
