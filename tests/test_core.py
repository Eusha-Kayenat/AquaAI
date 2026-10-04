import unittest
from backend.engine import score,next_question,FIELDS
from backend.validation import validate_ai_json,plausibility_flags
from backend.ai_provider import MockProvider,safe_extract
from backend.service import Store

class CoreTests(unittest.TestCase):
 def test_empty_score_and_rank(self):
  self.assertEqual(score({})[0],0.0); self.assertEqual(next_question({}).field,'banks')
 def test_stop_at_ready_and_keep_conflict_question_visible(self):
  complete={k:FIELDS[k]['options'][0] for k in FIELDS}; self.assertIsNone(next_question(complete).field)
  self.assertEqual(next_question({'banks':'Natural plants'},{'banks':'Concrete or stone'}).field,'banks')
 def test_reconfirmed_conflict_routes_to_researcher_without_silent_change(self):
  s=Store(); x=s.create({'text':'natural plant banks','photo_signals':{'banks':'Concrete or stone'},'ai_mode':'off'}); x['answers']['banks']='Natural plants'; s.recompute(x); self.assertEqual(x['question']['field'],'banks')
  s.answer(x['id'],x['question']['options'][0],confirm_conflict=True)
  self.assertEqual(x['status'],'Expert review'); self.assertEqual(x['answers']['banks'],'Natural plants'); self.assertEqual(x['breakdown']['banks']['state'],'confirmed_conflict'); self.assertNotEqual(x['question']['field'],'banks')
 def test_photo_conflict_and_human_confirmation(self):
  self.assertEqual(score({'banks':'Natural plants'},{'banks':'Concrete or stone'})[1]['banks']['state'],'conflict')
 def test_ai_output_allowlist(self):
  self.assertFalse(validate_ai_json('{"banks":"made up"}')['valid']); self.assertFalse(validate_ai_json('{"admin":true}')['valid'])
  self.assertEqual(validate_ai_json('{"waste":1.5}',{'waste'})['data']['waste'],1.0); self.assertFalse(validate_ai_json('{"waste":"often"}',{'waste'})['valid'])
 def test_mock_is_deterministic_and_vague_stays_empty(self):
  p=MockProvider(); self.assertEqual(p.extract('weird dirty')['data'],{}); self.assertEqual(p.extract('concrete banks'),p.extract('concrete banks'))
 def test_flags_do_not_mutate_observation(self):
  x={'location':{'lat':0,'lng':0},'text':'clear after rain','recent_rain':True}; original=dict(x); fs=plausibility_flags(x)
  self.assertTrue({'location_invalid','rain_clear_mismatch'} <= {f['code'] for f in fs}); self.assertEqual(x,original)
 def test_unconfirmed_suggestion_is_missing_until_confirmed(self):
  s=Store(); x=s.create({'text':'clear water','ai_mode':'simulated'}); before=x['score']; self.assertTrue(x['suggestions']); self.assertNotIn('water',x['answers']); self.assertEqual(before,0)
  key=next(iter(x['suggestions'])); s.confirm_suggestion(x['id'],key); self.assertIn(key,x['answers']); self.assertGreater(x['score'],before)
 def test_seed_has_three_cases_and_conflict(self):
  s=Store(); xs=s.seed(); self.assertEqual(len(xs),3); self.assertTrue(any(x['status']=='Expert review' for x in xs)); self.assertEqual(len({x['question']['field'] for x in xs}),3)

if __name__=='__main__': unittest.main()
