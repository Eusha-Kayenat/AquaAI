import json
from pathlib import Path
from backend.engine import FIELDS, next_question, score
from backend.ai_provider import MockProvider
data=json.loads((Path(__file__).parent/'tests'/'eval_set.json').read_text())
agree=tp=fp=fn=vague_ok=0; n=len(data['cases'])
for c in data['cases']:
    d=next_question(c['answers'],{"banks":"Concrete or stone"} if c['conflict'] else {})
    agree+=int(d.field==c['question'])
    predicted=any(v['state']=='conflict' for v in score(c['answers'],{"banks":"Concrete or stone"})[1].values())
    tp+=int(predicted and c['conflict']); fp+=int(predicted and not c['conflict']); fn+=int(not predicted and c['conflict'])
    vague_ok+=int(MockProvider().extract(c['vague'])['data']=={})
precision=tp/(tp+fp) if tp+fp else 0; recall=tp/(tp+fn) if tp+fn else 0
print(f"Question-selection agreement: {agree/n*100:.1f}% ({agree}/{n})")
print(f"Conflict-detection precision: {precision*100:.1f}% ({tp}/{tp+fp})")
print(f"Conflict-detection recall: {recall*100:.1f}% ({tp}/{tp+fn})")
print(f"Vague-word inputs left null: {vague_ok/n*100:.1f}% ({vague_ok}/{n})")
print("Measured on a small synthetic set; not evidence of real-world accuracy.")
