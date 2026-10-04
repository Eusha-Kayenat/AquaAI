# AquaAI — Find the Missing Piece

**Don't ask everything. Ask what matters.** AquaAI is a demo citizen assessment helper for stream observations. It asks one high-value question at a time, keeps scoring deterministic and rule-based, and routes photo conflicts for human review. It measures evidence completeness, not environmental truth.

## Run

Requires Python 3.10+. Install the listed packages, then start the app:

```powershell
python -m pip install -r requirements.txt
python run.py
```

The app opens at http://127.0.0.1:8000. For unattended start use `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`. No API key is required. In this version the default is an offline simulated provider. `live` mode is not a connected model integration yet and falls back to offline behavior.

## Test and synthetic evaluation

```powershell
python -m unittest discover -s tests -v
python eval.py
```

Evaluation examples are synthetic, hand-authored cases in `tests/eval_set.json`; they are not field data. Run `python eval.py` for the current question-selection agreement, conflict precision/recall, and vague-input null rate. **Measured on a small synthetic set; not evidence of real-world accuracy.**

Current output from `python eval.py`:

```text
Question-selection agreement: 60.0% (12/20)
Conflict-detection precision: 25.0% (2/8)
Conflict-detection recall: 50.0% (2/4)
Vague-word inputs left null: 100.0% (20/20)
Measured on a small synthetic set; not evidence of real-world accuracy.
```

## Track 3 alignment

| Requirement | Implementation |
|---|---|
| Versioned AI prompts | `backend/prompts/*_v1.txt` and `backend/prompts/README.md` |
| Validations | `backend/validation.py`; strict AI allow-list and observation flags |
| Explainability | `backend/engine.py` score breakdown; decision why, gain and runner-up in the citizen view |
| Human-in-the-loop | Unconfirmed suggestions are excluded from answers; confirmation endpoint; photo disagreement is marked Expert review |

The `MockProvider` is deterministic and explicitly simulated. It only matches explicit allow-listed phrases; vague words are left unparsed. Provider errors fail closed. No raw observation details are written to logs. The engine has no AI dependency.

## Responsible AI and limitations

- The score is weighted completeness and consistency of provided evidence. It is **not** a probability of truth, pollution indicator, or diagnosis. The same footnote is shown next to the citizen score.
- Photo disagreement is surfaced for human review and is never silently corrected.
- A real answer is not replaced with “I'm not sure”; every question provides an unsure option.
- The offline photo suggestion path and extraction mock are demonstrations, not model output. AI suggestions need explicit human confirmation before they affect score.
- Field weights and rules are demonstration defaults, not calibrated against citizen-versus-expert field data.
- Photo upload/vision inference, SQLite persistence, browser map, live Anthropic/OpenAI provider calls, full researcher correction/audit flow, mobile/desktop browser automation and end-to-end screenshots are not implemented in this starter build. The FHIR R4 output uses placeholder extension URLs and is not claimed to conform to the OneAquaHealth IG.
- The live-provider option currently sends no data: provider classes safely fall back to the mock. If live calls are connected in a future revision, text and photos may leave the device; disclose this and default the feature off.
- Seeded demo entries are labelled as demo data by the UI workflow; never treat them as real observations.

## Escalation

Any unresolved disagreement between a citizen answer and a photo signal is labelled **Expert review**. A citizen may re-confirm the answer, but this does not resolve the conflict automatically. Researchers retain the final say; marking verified or requesting more information is a demo action.

## Architecture

```text
frontend/index.html -> FastAPI backend/main.py -> service.py -> engine.py
                                          |-> validation.py
                                          |-> ai_provider.py -> versioned prompts/
                                          `-> FHIR R4 JSON (placeholder extensions)
```

## Demo script (3–5 minutes)

1. (0:00) Explain inconsistent citizen reports; state the score is evidence quality, not environmental truth.
2. (0:30) Submit a short observation and show the simulated suggestion review. Confirm or skip it.
3. (1:15) Show score and gentle validation notes. Open the breakdown and provenance.
4. (1:45) Answer one high-value question; explain the projected gain and before/after score.
5. (2:30) Demonstrate a photo conflict and show that it goes to expert review.
6. (3:15) Open Researcher demo access, queue, observation detail, and FHIR output with placeholder notice.
7. (4:15) Open About the AI and explain that the deterministic rules choose questions and score; simulated suggestions are not real AI.
8. (4:45) Close with calibration, persistence, real provider integrations and interoperability validation as next steps.

## API

`POST /api/observations`, `POST /api/observations/{id}/answer`, `POST /api/observations/{id}/suggestions/{field}`, `GET /api/observations`, `GET /api/review-queue`, `GET /api/observations/{id}/fhir`, and `POST /api/seed`.
