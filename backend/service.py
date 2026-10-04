"""Small service layer with explicit human confirmation and a demo seed."""
import hashlib, time, uuid
from .engine import FIELDS, score, next_question, status_for, fhir_observation
from .validation import plausibility_flags
from .ai_provider import get_provider, safe_extract

class Store:
    def __init__(self): self.items={}
    def create(self,payload):
        item={"id":uuid.uuid4().hex[:10],"text":payload.get("text",""),"site_id":payload.get("site_id","unknown"),"timestamp":payload.get("timestamp",time.time()),"location":payload.get("location"),"recent_rain":payload.get("recent_rain",False),"answers":{},"suggestions":{},"provenance":{},"audit":[],"decision_log":[],"flags":[],"review":"open","confirmed_conflicts":[],"photos":payload.get("photos",[])}
        item["text_hash"]=hashlib.sha256(item["text"].encode()).hexdigest()
        extracted=safe_extract(get_provider(payload.get("ai_mode","simulated")),item["text"])
        item["suggestions"]={k:{"value":v,"source":"Demo: simulated AI suggestion","model":extracted.get("provider","simulated"),"prompt_version":extracted.get("prompt_version"),"confirmed":False} for k,v in extracted["data"].items() if v}
        for k,suggestion in item["suggestions"].items(): item["provenance"][k]={"source":"ai_suggestion_unconfirmed","model":suggestion["model"],"prompt_version":suggestion["prompt_version"]}
        item["photo_signals"]=payload.get("photo_signals",{})
        item["flags"]=plausibility_flags(item,self.items.values())
        self.recompute(item); self.items[item["id"]]=item; return item
    def recompute(self,item):
        item["score"],item["breakdown"]=score(item["answers"],item.get("photo_signals"),item.get("confirmed_conflicts"))
        decision=next_question(item["answers"],item.get("photo_signals"),item.get("confirmed_conflicts"))
        item["question"]={"field":decision.field,"text":FIELDS[decision.field]["label"]+"?" if decision.field else None,"options":FIELDS[decision.field]["options"] if decision.field else [],"gain":decision.gain,"why":decision.why,"runner_up":decision.runner_up} if decision.field else None
        item["decision_log"].append({"field":decision.field,"gain":decision.gain,"runner_up":decision.runner_up})
        has_conflict=any(v["state"]=="conflict" for v in item["breakdown"].values())
        item["status"]=status_for(item["score"],has_conflict)
    def answer(self,oid,answer,confirm_conflict=False,field=None):
        item=self.items[oid]; key=field or (item.get("question") and item["question"]["field"])
        if not key: return item
        if key not in FIELDS: raise ValueError(f"Unknown field {key}")
        valid=FIELDS[key]["options"]+["I'm not sure"]
        is_other=answer.startswith("Other:") or answer.startswith("Others:") or answer.strip()=="Other" or answer.strip()=="Others"
        if answer not in valid and not is_other: raise ValueError("Invalid answer option")
        item["answers"][key]=answer; item["provenance"][key]={"source":"citizen_answer"}
        item["last_answer"]={"field":key,"answer":answer,"confirm_conflict":confirm_conflict}
        if key in item["confirmed_conflicts"] and key in item.get("photo_signals",{}) and answer==item["photo_signals"][key]:
            item["confirmed_conflicts"]=[k for k in item["confirmed_conflicts"] if k!=key]
        self.recompute(item)
        if confirm_conflict and item["breakdown"][key]["state"]=="conflict":
            if key not in item["confirmed_conflicts"]: item["confirmed_conflicts"].append(key)
            self.recompute(item); item["status"]="Expert review"
        return item
    def confirm_suggestion(self,oid,key,value=None,action="confirm"):
        item=self.items[oid]; s=item["suggestions"].get(key)
        if not s: raise ValueError("No suggestion for this field")
        if action=="confirm": val=value or s["value"]
        elif action=="remove": item["suggestions"].pop(key); return item
        else: val=value
        if val not in FIELDS[key]["options"]: raise ValueError("Invalid value")
        item["answers"][key]=val; item["provenance"][key]={"source":"ai_suggestion_confirmed","model":"simulated","prompt_version":"extract_v1"}; s["confirmed"]=True
        return self.recompute(item) or item
    def seed(self):
        samples=[("Banks are concrete beside clear water.",{"banks":"Natural plants"}, {"banks":"Concrete or stone"}),("The water is cloudy after rain; banks are natural plants.",{"banks":"Natural plants"},{}),("Mostly stones on the bottom and plants nearby.",{"banks":"Natural plants","water":"Clear"}, {})]
        result=[]
        for text,answers,signals in samples:
            x=self.create({"text":text,"site_id":"greenway","location":{"lat":23.78,"lng":90.41},"photo_signals":signals,"ai_mode":"off"}); x["answers"].update(answers); self.recompute(x); x["demo_data"]=True; result.append(x)
        return result
    def list(self): return list(self.items.values())
    def queue(self): return sorted([x for x in self.items.values() if x["review"]!="verified" and (x["status"]=="Expert review" or x["review"]=="more_info")],key=lambda x:(x["status"]!="Expert review",x["score"]))
    def fhir(self,oid): return fhir_observation(self.items[oid])

store=Store()
