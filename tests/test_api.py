import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.service import store

class ApiTests(unittest.TestCase):
 def setUp(self): store.items.clear(); self.c=TestClient(app)
 def test_fields_and_full_read_paths(self):
  self.assertIn('AquaAI',self.c.get('/').text)
  self.assertEqual(set(self.c.get('/api/fields').json()),{'banks','water','bottom','habitat'})
  created=self.c.post('/api/observations',json={'text':'clear water','ai_mode':'off'}); self.assertEqual(created.status_code,201); oid=created.json()['id']
  self.assertEqual(self.c.get(f'/api/observations/{oid}').status_code,200)
  self.assertEqual(self.c.get('/api/observations').json()[0]['id'],oid)
  self.assertEqual(self.c.get('/api/review-queue').status_code,200)
  self.assertEqual(self.c.get(f'/api/observations/{oid}/fhir').json()['resourceType'],'Observation')
 def test_answer_unknown_id_is_404(self): self.assertEqual(self.c.post('/api/observations/missing/answer',json={'answer':'Clear'}).status_code,404)
 def test_create_answer_list_queue_fhir_seed(self):
  r=self.c.post('/api/observations',json={'text':'clear water','ai_mode':'off'}); self.assertEqual(r.status_code,201); x=r.json(); oid=x['id']
  self.assertEqual(self.c.get('/api/observations').status_code,200)
  q=x['question']; bad=self.c.post(f'/api/observations/{oid}/answer',json={'answer':'nope'}); self.assertEqual(bad.status_code,422)
  good=self.c.post(f'/api/observations/{oid}/answer',json={'answer':q['options'][0]}); self.assertEqual(good.status_code,200)
  self.assertEqual(self.c.get('/api/review-queue').status_code,200); self.assertEqual(self.c.get(f'/api/observations/{oid}/fhir').json()['resourceType'],'Observation')
  self.assertEqual(self.c.post('/api/seed').status_code,200)
 def test_unknown_id_404(self): self.assertEqual(self.c.get('/api/observations/missing/fhir').status_code,404)
 def test_suggestion_confirmation_validation_and_researcher_actions(self):
  x=self.c.post('/api/observations',json={'text':'clear water','ai_mode':'simulated'}).json(); oid=x['id']; self.assertIn('water',x['suggestions']); self.assertEqual(x['score'],0)
  invalid=self.c.post(f'/api/observations/{oid}/suggestions/water',json={'action':'edit','value':'polluted'}); self.assertEqual(invalid.status_code,422); self.assertEqual(self.c.get(f'/api/observations/{oid}').json()['score'],0)
  confirmed=self.c.post(f'/api/observations/{oid}/suggestions/water',json={'action':'confirm'}); self.assertGreater(confirmed.json()['score'],0)
  self.assertEqual(self.c.post(f'/api/observations/{oid}/review/verified').status_code,200)
  self.assertNotIn(oid,[item['id'] for item in self.c.get('/api/review-queue').json()])
  self.assertEqual(self.c.post(f'/api/observations/{oid}/review/more-info').status_code,200)
  self.assertIn(oid,[item['id'] for item in self.c.get('/api/review-queue').json()])
  self.assertEqual(self.c.post(f'/api/observations/{oid}/review/nope').status_code,422)
 def test_reconfirmed_photo_conflict_enters_expert_review(self):
  x=self.c.post('/api/observations',json={'text':'banks are natural','photo_signals':{'banks':'Concrete or stone'},'ai_mode':'off'}).json(); oid=x['id']
  response=self.c.post(f'/api/observations/{oid}/answer',json={'answer':'Clear'}); self.assertEqual(response.status_code,200)
  for _ in range(2):
   q=response.json()['question']; response=self.c.post(f'/api/observations/{oid}/answer',json={'answer':q['options'][0]}); self.assertEqual(response.status_code,200)
  self.assertEqual(response.json()['question']['field'],'banks')
  response=self.c.post(f'/api/observations/{oid}/answer',json={'answer':'Natural plants'}); self.assertEqual(response.status_code,200); self.assertEqual(response.json()['question']['field'],'banks')
  reviewed=self.c.post(f'/api/observations/{oid}/confirm-conflict'); self.assertEqual(reviewed.status_code,200); self.assertEqual(reviewed.json()['status'],'Expert review'); self.assertEqual(reviewed.json()['answers']['banks'],'Natural plants'); self.assertEqual(reviewed.json()['breakdown']['banks']['state'],'confirmed_conflict')

if __name__=='__main__': unittest.main()
