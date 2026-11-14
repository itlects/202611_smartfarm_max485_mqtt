import unittest
from unittest.mock import Mock
import app
class WebTest(unittest.TestCase):
 def setUp(self):
  self.c=app.app.test_client(); app.nodes.clear();app.pending.clear();app.client=None
 def login(self):
  return self.c.post('/api/login',json={'username':'smartfarm2026','password':'smartfarm1234'}).json['csrf']
 def test_auth(self):
  self.assertEqual(self.c.get('/api/state').status_code,401)
  self.assertEqual(self.c.post('/api/login',json={'username':'x','password':'x'}).status_code,401)
 def test_csrf_and_validation(self):
  token=self.login()
  self.assertEqual(self.c.post('/api/command',json={}).status_code,403)
  self.assertEqual(self.c.post('/api/command',json={'node':3,'pump':1,'led':0},headers={'X-CSRF-Token':token}).status_code,400)
 def test_offline(self):
  token=self.login()
  self.assertEqual(self.c.post('/api/command',json={'node':1,'pump':1,'led':0},headers={'X-CSRF-Token':token}).status_code,409)
 def test_command_confirm(self):
  import time
  token=self.login(); app.nodes[1]={'received':time.time()};app.client=Mock();app.client.is_connected.return_value=True;app.client.publish.return_value.rc=0
  r=self.c.post('/api/command',json={'node':1,'pump':1,'led':3},headers={'X-CSRF-Token':token})
  self.assertEqual(r.status_code,202);self.assertFalse(app.client.publish.call_args.kwargs['retain'])
  import json
  app.db=Mock(side_effect=RuntimeError('test DB offline'))
  app.on_message(None,None,Mock(topic='smartfarm/v1/1/telemetry',payload=json.dumps({'id':r.json['id'],'raw':500,'pump':1,'led':3}).encode()))
  self.assertEqual(self.c.get('/api/state').json['commands']['1']['status'],'confirmed')
if __name__=='__main__':unittest.main()
