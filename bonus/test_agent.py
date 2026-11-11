"""Kiểm tra agent với tools bonus mà không gọi LLM API."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agent import run_agent
from bonus.tools import BonusTools


def call(call_id,name,args):
    raw=json.dumps(args)
    c={'id':call_id,'name':name,'arguments':raw}
    m={'role':'assistant','content':None,'tool_calls':[{'id':call_id,'type':'function','function':{'name':name,'arguments':raw}}]}
    return {'message':m,'calls':[c],'finish':'tool_calls','usage':{}}

def final(answer='Đã kiểm tra'):
    return {'message':{'role':'assistant','content':answer},'calls':[],'finish':'stop','usage':{}}


class ScriptedProvider:
    def __init__(self,responses): self.responses=iter(responses); self.histories=[]; self.schemas=[]
    def complete(self,messages,schemas):
        self.histories.append(list(messages));self.schemas.append(schemas)
        return next(self.responses)


class BonusAgentTests(unittest.TestCase):
    def test_bonus_schemas_and_system_prompt(self):
        t=BonusTools();p=ScriptedProvider([final()])
        self.assertEqual(run_agent('Kiểm tra',p,t)['status'],'completed')
        names={x['function']['name'] for x in p.schemas[0]}
        self.assertTrue({'get_github_status','get_cloudflare_status','get_vercel_status','get_npm_status','get_digitalocean_status'}.issubset(names))
        self.assertIn('DigitalOcean',p.histories[0][0]['content'])
    def test_429_observation_returns_to_model(self):
        t=BonusTools(scenario='rate_limit_once')
        p=ScriptedProvider([call('a','get_vercel_status',{}),call('b','get_vercel_status',{}),final()])
        result=run_agent('Kiểm tra',p,t,max_steps=5)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(json.loads(p.histories[1][-1]['content'])['error'],'RATE_LIMITED')
        self.assertEqual(json.loads(p.histories[2][-1]['content'])['provider'],'vercel')
    def test_invalid_arguments_observation_returns_to_model(self):
        t=BonusTools()
        bad={'provider':'npm','incident_id':'cc0t2r4403sy','offset':'zero'}
        good={'provider':'npm','incident_id':'cc0t2r4403sy','offset':0}
        details=t.execute('get_incident_details',good)
        p=ScriptedProvider([call('a','get_incident_details',bad),call('b','get_incident_details',good),final('Nguồn: '+details['url'])])
        result=run_agent('Kiểm tra',p,t,max_steps=5)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(json.loads(p.histories[1][-1]['content'])['error'],'INVALID_ARGUMENTS')
        self.assertTrue(json.loads(p.histories[2][-1]['content'])['ok'])

    def test_live_retry_after_waits_before_next_execution(self):
        t=BonusTools()
        p=ScriptedProvider([call('a','get_vercel_status',{}),call('b','get_vercel_status',{}),final()])
        limited={'ok':False,'error':'RATE_LIMITED','retry_after':'2','retriable':True}
        with patch.object(t,'execute',side_effect=[limited,{'provider':'vercel'}]) as execute, patch('agent.time.sleep') as sleep:
            result=run_agent('Kiểm tra',p,t,max_steps=4)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(execute.call_count,2)
        sleep.assert_called_once()
        self.assertGreater(sleep.call_args.args[0],0)
        self.assertLessEqual(sleep.call_args.args[0],2)

    def test_persistent_429_executes_at_most_three_times(self):
        t=BonusTools(scenario='rate_limit_always')
        p=ScriptedProvider([call(str(i),'get_vercel_status',{}) for i in range(4)]+[final()])
        with patch.object(t,'execute',wraps=t.execute) as execute:
            result=run_agent('Kiểm tra',p,t,max_steps=5)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(execute.call_count,3)
        self.assertEqual(json.loads(p.histories[4][-1]['content'])['error'],'RETRY_LIMIT_EXCEEDED')

    def test_long_retry_after_does_not_sleep_or_execute_again(self):
        t=BonusTools()
        p=ScriptedProvider([call('a','get_vercel_status',{}),call('b','get_vercel_status',{}),final()])
        limited={'ok':False,'error':'RATE_LIMITED','retry_after':'120','retriable':True}
        with patch.object(t,'execute',return_value=limited) as execute, patch('agent.time.sleep') as sleep:
            result=run_agent('Kiểm tra',p,t,max_steps=4)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(execute.call_count,1)
        sleep.assert_not_called()
        self.assertFalse(json.loads(p.histories[1][-1]['content'])['retriable'])

if __name__=='__main__': unittest.main()
