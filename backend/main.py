from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .service import store
from .engine import FIELDS
from pathlib import Path

app=FastAPI(title="AquaAI",version="1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:8000","http://localhost:8000"],allow_methods=["GET","POST"],allow_headers=["*"])
ROOT=Path(__file__).resolve().parent.parent
app.mount("/static",StaticFiles(directory=ROOT/"frontend"),name="static")
class Create(BaseModel):
    text:str=Field(default="",max_length=4000); site_id:str="unknown"; location:dict|None=None; recent_rain:bool=False; ai_mode:str="simulated"; photo_signals:dict|None=None; photos:list[dict]|list[str]|None=None
class Answer(BaseModel): answer:str; confirm_conflict:bool=False; field:str|None=None
class Confirm(BaseModel): action:str="confirm"; value:str|None=None
@app.get("/")
def home(): return FileResponse(ROOT/"frontend"/"index.html")
@app.get("/api/fields")
def fields(): return FIELDS
@app.post("/api/observations",status_code=201)
def create(body:Create): return store.create(body.model_dump())
def get_item(oid):
    if oid not in store.items: raise HTTPException(404,"Unknown observation")
    return store.items[oid]
@app.post("/api/observations/{oid}/answer")
def answer(oid:str,body:Answer):
    item=get_item(oid)
    try: return store.answer(oid,body.answer,body.confirm_conflict,body.field)
    except ValueError as e: raise HTTPException(422,str(e))
@app.post("/api/observations/{oid}/suggestions/{key}")
def confirm(oid:str,key:str,body:Confirm):
    get_item(oid)
    try: return store.confirm_suggestion(oid,key,body.value,body.action)
    except ValueError as e: raise HTTPException(422,str(e))
@app.get("/api/observations")
def listing(): return store.list()
@app.get("/api/observations/{oid}")
def observation(oid:str): return get_item(oid)
@app.post("/api/observations/{oid}/confirm-conflict")
def confirm_conflict(oid:str):
    item=get_item(oid); last=item.get("last_answer")
    if not last: raise HTTPException(422,"No answer to confirm")
    key=last["field"]
    if item["breakdown"][key]["state"]!="conflict": raise HTTPException(422,"There is no unresolved photo conflict")
    item["confirmed_conflicts"].append(key); store.recompute(item); item["status"]="Expert review"; item["last_answer"]["confirm_conflict"]=True
    item["audit"].append({"action":"citizen_reconfirmed_conflict","field":key})
    return store.save(item)
@app.get("/api/review-queue")
def queue(): return store.queue()
@app.get("/api/observations/{oid}/fhir")
def fhir(oid:str):
    get_item(oid); return store.fhir(oid)
@app.post("/api/seed")
def seed(): return store.seed()
@app.post("/api/observations/{oid}/review/{action}")
def review(oid:str,action:str):
    item=get_item(oid)
    if action not in {"verified","more-info"}: raise HTTPException(422,"Action must be verified or more-info")
    item["review"]="verified" if action=="verified" else "more_info"; item["audit"].append({"action":action,"who":"researcher demo","when":__import__('time').time()}); return store.save(item)
