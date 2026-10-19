"""Explicit live evaluation: calls configured providers, uses credits and saves reports. Not imported by the app."""
import sys, json, time, statistics
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'src'))
sys.stdout.reconfigure(encoding='utf-8')
from launch_deets.agent import ask, prepare_runtime
from launch_deets.data import load_archive
from launch_deets.config import Settings, configure_langsmith
from launch_deets.providers import jev_check
from launch_deets.trace import RunTrace
from launch_deets.assessment import sync_evaluation_datasets, judge_answer, request_evidence, provider_cost_estimate
from langsmith import Client, evaluate

def main():
    s = Settings.from_env()
    configure_langsmith(s)
    a = load_archive(R)
    c = Client()
    P = R / 'reports/evaluation'
    P.mkdir(parents=True, exist_ok=True)
    datasets = sync_evaluation_datasets(a, c)
    (P / 'datasets.json').write_text(json.dumps(datasets, indent=2))
    print('DATASETS', datasets, flush=True)
    prepare_runtime(s)

    def target(inputs):
        t = RunTrace(inputs['case_id'])
        start = time.perf_counter()
        r = ask(inputs['question'], archive=a, settings=s, trace=t, max_retrieval_retries=1)
        row = {'id': inputs['case_id'], 'question': inputs['question'], 'result': r, 'seconds': time.perf_counter() - start, 'tokens': sum((u['total_tokens'] or 0 for u in t.usage_rows)), 'usage': t.usage_rows, 'evidence': request_evidence(t.events), 'events': t.events, 'cost': provider_cost_estimate(t.usage_rows)}
        (P / (inputs['case_id'] + '.json')).write_text(json.dumps(row, indent=2))
        print('REQUEST', row['id'], r['status'], row['tokens'], round(row['seconds'], 2), flush=True)
        return row

    def quality(run, example):
        row = run.outputs
        ref = example.outputs
        r = row['result']
        t = RunTrace('judge-' + row['id'])
        if r['status'] == 'blocked':
            ok = ref.get('category') == 'out_of_scope'
            v = {'correct': ok, 'supported': None, 'complete': ok, 'reason': 'Policy decision; no generated factual claims.'}
        else:
            v = judge_answer(s, example.inputs['question'], ref, r, row['evidence'], trace=t)
        (P / (row['id'] + '-judge.json')).write_text(json.dumps({'verdict': v, 'usage': t.usage_rows}, indent=2))
        print('JUDGE', row['id'], v, flush=True)
        return {'results': [{'key': k, 'score': float(v[k]) if v[k] is not None else None, 'comment': v['reason']} for k in ('correct', 'supported', 'complete')]}
    res = evaluate(target, data=datasets['golden']['name'], evaluators=[quality], experiment_prefix='launch-deets-gap-check', max_concurrency=1, num_repetitions=1, metadata={'retry_limit': 1, 'judge': 'Qwen supporting evaluator; human review required for disagreements'})
    print('EXPERIMENT', res.experiment_name, flush=True)

    def guard_target(inputs):
        t = RunTrace(inputs['case_id'])
        r = ask(inputs['question'], archive=a, settings=s, trace=t, max_retrieval_retries=1)
        return {'blocked': r['status'] == 'blocked', 'result': r, 'tokens': sum((u['total_tokens'] or 0 for u in t.usage_rows)), 'stages': [x['stage'] for x in t.events]}

    def guard_score(run, example):
        o = run.outputs
        expect = example.outputs['expected_allow_or_block'] == 'block'
        return {'results': [{'key': 'policy_correct', 'score': o['blocked'] == expect}, {'key': 'early_stop', 'score': not o['blocked'] or not any((x in o['stages'] for x in ['model', 'tool_calls', 'retrieval', 'graph', 'structured']))}]}
    g = evaluate(guard_target, data=datasets['guardrails']['name'], evaluators=[guard_score], experiment_prefix='launch-deets-guardrail-check', max_concurrency=1)
    (P / 'experiments.json').write_text(json.dumps({'golden': res.experiment_name, 'guardrails': g.experiment_name}, indent=2))
    print('FINISHED', flush=True)
if __name__ == '__main__':
    main()
