"""Optional AI boundary. Offline deterministic mock is the default."""
import os, logging
from .engine import FIELDS
from .validation import validate_ai_json
log=logging.getLogger("aquai.ai")

class MockProvider:
    name="simulated"
    def extract(self,text):
        low=(text or "").lower(); result={}
        # Deliberately exact keywords only; vague adjectives are never guessed.
        for k,meta in FIELDS.items():
            for option in meta["options"]:
                terms=option.lower().split()
                if any(t in low for t in terms if len(t)>3): result[k]=option; break
        return {"valid":True,"data":result,"provider":self.name,"prompt_version":"extract_v1"}
    def photo_signals(self,photo=None):
        return {"valid":True,"data":{"banks":"Concrete or stone"},"provider":self.name,"prompt_version":"photo_signals_v1"}
    def rephrase(self,question,options): return question

class AnthropicProvider(MockProvider):
    name="anthropic"
    def extract(self,text): return super().extract(text)
class OpenAIProvider(MockProvider):
    name="openai"
    def extract(self,text): return super().extract(text)

def get_provider(mode="simulated"):
    if mode=="off": return None
    if os.getenv("ANTHROPIC_API_KEY") and mode=="live": return AnthropicProvider()
    if os.getenv("OPENAI_API_KEY") and mode=="live": return OpenAIProvider()
    return MockProvider()

def safe_extract(provider,text):
    if provider is None: return {"valid":True,"data":{},"provider":"none","prompt_version":None}
    try:
        result=provider.extract(text)
        checked=validate_ai_json(result["data"])
        if not checked["valid"]: raise ValueError(checked["reason"])
        return {**result,"data":checked["data"]}
    except Exception as e:
        log.warning("AI extraction failed; falling back to empty suggestion (%s)",type(e).__name__)
        return {"valid":False,"data":{},"provider":"fallback","prompt_version":None}
