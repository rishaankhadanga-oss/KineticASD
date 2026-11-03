import tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
import main

class KineticASDTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_path=main.DB_PATH
        main.DB_PATH=Path(self.tmp.name)/'test.db'
        main.initialize_database()
        self.client=TestClient(main.app)
    def tearDown(self):
        self.client.close(); main.DB_PATH=self.old_path; self.tmp.cleanup()
    def test_health(self):
        r=self.client.get('/api/health'); self.assertEqual(r.status_code,200); self.assertEqual(r.json()['status'],'ok')
    def test_seed_data_is_demo(self):
        data=self.client.get('/api/observations').json(); self.assertGreaterEqual(len(data),6); self.assertTrue(all(x['is_demo']==1 for x in data))
    def test_create_and_persist_observation(self):
        p={'setting':'Home','discipline':'Caregiver','antecedent':'Sample transition','behavior':'Asked for help','consequence':'Support offered','context_notes':'Synthetic test','created_by':'Test user'}
        r=self.client.post('/api/observations',json=p); self.assertEqual(r.status_code,201); oid=r.json()['id']
        self.assertTrue(any(x['id']==oid for x in self.client.get('/api/observations').json()))
    def test_summary_shape(self):
        s=self.client.get('/api/summary').json(); self.assertIn('total_observations',s); self.assertIn('by_setting',s); self.assertIn('by_discipline',s); self.assertIn('by_day',s)
    def test_filter(self):
        data=self.client.get('/api/observations',params={'setting':'School'}).json(); self.assertTrue(data); self.assertTrue(all(x['setting']=='School' for x in data))
    def test_decision_is_simulation(self):
        r=self.client.post('/api/therapist-applications/DEMO-001/decision',params={'decision':'approve'}); self.assertEqual(r.status_code,200); self.assertTrue(r.json()['simulation_only'])

if __name__=='__main__': unittest.main()
