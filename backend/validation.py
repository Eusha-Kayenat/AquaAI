"""Framework-free validation: reject unknown AI fields and flag implausible inputs."""
import json
from .engine import FIELDS

def validate_ai_json(raw, allowed=None):
    allowed=set(allowed or FIELDS)
    try:
        data=json.loads(raw) if isinstance(raw,str) else raw
        if not isinstance(data,dict): raise ValueError("Expected a JSON object")
        if set(data)-allowed: raise ValueError("Unexpected field keys")
        clean={}
        for k,v in data.items():
            if v is None: clean[k]=None
            elif k in FIELDS and v not in FIELDS[k]["options"]: raise ValueError(f"Value is not allowed for {k}")
            elif k in {"cloudy_water","waste","concrete_banks"}:
                if isinstance(v,bool) or not isinstance(v,(int,float)): raise ValueError(f"Expected a number for {k}")
                clean[k]=max(0.0,min(1.0,float(v)))
            elif isinstance(v,str) and len(v)>120: raise ValueError(f"Value too long for {k}")
            else: clean[k]=v
        return {"valid":True,"data":clean,"reason":None}
    except Exception as e: return {"valid":False,"data":{},"reason":str(e)}

def plausibility_flags(observation, existing=None):
    flags=[]; loc=observation.get("location") or {}
    lat,lng=loc.get("lat"),loc.get("lng")
    if lat is None or lng is None: flags.append(flag("location_missing","Location was not added; you can still submit without it.","note"))
    else:
        try:
            lat,lng=float(lat),float(lng)
            if not (-90<=lat<=90 and -180<=lng<=180) or (lat==0 and lng==0): raise ValueError()
        except (TypeError,ValueError): flags.append(flag("location_invalid","Please check the location coordinates.","attention"))
    ts=observation.get("timestamp")
    if ts:
        try:
            if float(ts)>__import__('time').time(): flags.append(flag("future_timestamp","The observation time appears to be in the future.","attention"))
            elif float(ts)<__import__('time').time()-365*24*3600: flags.append(flag("old_timestamp","This observation is more than a year old; please check its date.","note"))
        except (TypeError,ValueError): flags.append(flag("timestamp_invalid","The observation time could not be checked.","attention"))
    text=(observation.get("text") or "").lower()
    if observation.get("recent_rain") and "clear" in text: flags.append(flag("rain_clear_mismatch","Recent rain and a clear-water description may be worth a second look.","attention"))
    photo=observation.get("photo") or {}
    if photo.get("width",999)<80 or photo.get("height",999)<80: flags.append(flag("photo_small","The photo may be too small to review clearly.","note"))
    for old in existing or []:
        if old.get("site_id")==observation.get("site_id") and old.get("text_hash")==observation.get("text_hash"):
            flags.append(flag("possible_duplicate","A similar report for this site was recently submitted.","attention")); break
    return flags

def flag(code,message,severity): return {"code":code,"message":message,"severity":severity}
