"""Offline regression cases from the saved full-flow failures."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from launch_deets import agent, retrieval
from launch_deets.data import load_archive
from launch_deets.trace import RunTrace
from langchain_core.messages import AIMessage


class ToolContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = load_archive(ROOT)

    def test_complete_count_not_top_k(self):
        result = retrieval.structured_query(self.archive, operation='count_launches', event_type='incident', severity='major')
        self.assertEqual(result['value'], 3)
        self.assertEqual(set(result['launch_ids']), {'L7-ALPHA', 'L7-CHARLIE', 'L7-ECHO'})

    def test_numeric_max_and_ties_use_all_eligible_rows(self):
        result = retrieval.structured_query(self.archive, operation='max_value', event_type='component', unit='percent')
        self.assertEqual(result['value'], 99.1)
        self.assertEqual(result['records'][0]['record_id'], 'REC-L7-018')
        self.assertEqual(result['matched_records'], 2)
        frame = self.archive.records.copy()
        frame.loc[frame.record_id == 'REC-L7-002', 'value'] = '99.1'
        copy = Mock(records=frame)
        self.assertEqual(len(retrieval.structured_query(copy, operation='max_value', event_type='component', unit='percent')['records']), 2)

    def test_explicit_scope_does_not_fill_with_other_launches(self):
        result = retrieval.structured_query(self.archive, query='packet loss confirmed', launch_id='L7-ALPHA')
        self.assertTrue(result['records'])
        self.assertTrue(all(r['launch_id'] == 'L7-ALPHA' for r in result['records']))
        self.assertIn('REC-L7-021', [r['record_id'] for r in result['records']])

    def test_invalid_filters_and_sql_fail_explicitly(self):
        with self.assertRaises(ValueError):
            retrieval.structured_query(self.archive, operation='max_value')
        with self.assertRaises(ValueError):
            retrieval.structured_query(self.archive, query='SELECT MAX(value) FROM records')
        with self.assertRaises(ValueError):
            retrieval.structured_query(self.archive, severity='majoor')

    def test_zero_is_computed_only_by_aggregate(self):
        lookup = retrieval.structured_query(self.archive, query='zznonexistent')
        self.assertEqual(lookup['status'], 'no_match')
        result = retrieval.structured_query(self.archive, operation='count_launches', launch_id='L7-BRAVO', severity='major', event_type='incident')
        self.assertEqual(result['value'], 0)
        self.assertEqual(result['status'], 'ok')

    def test_launch_scope_respects_cross_launch_questions(self):
        self.assertEqual(retrieval.resolve_launch_scope(self.archive, 'Alpha incident', ''), 'L7-ALPHA')
        self.assertEqual(retrieval.resolve_launch_scope(self.archive, 'Compare Alpha and Echo', ''), '')
        self.assertEqual(retrieval.resolve_launch_scope(self.archive, 'Compare Alpha and Echo', 'L7-ECHO'), 'L7-ECHO')
        with self.assertRaises(ValueError):
            retrieval.resolve_launch_scope(self.archive, 'Alpha incident', 'L7-ECHO')

    def run_mock(self, question, responses):
        model, bound = Mock(), Mock()
        model.bind_tools.return_value = bound
        responses = iter(responses)
        bound.invoke.side_effect = lambda *args, **kwargs: next(responses)
        model.invoke.side_effect = lambda *args, **kwargs: next(responses)
        trace = RunTrace()
        with patch.object(agent, 'configure_langsmith'), patch.object(agent, 'make_nebius_chat', return_value=model):
            workflow = agent.build_workflow(self.archive, Mock(nebius_model='mock'), trace=trace, request_question=question, max_retrieval_retries=0)
            result = workflow.invoke({'question': question, 'iterations': 0})
        return result, trace

    def test_no_tool_hallucination_is_rejected_without_extra_call(self):
        result, trace = self.run_mock('What was the yaw bias?', [AIMessage(content='0.8 degrees for seven days [fake-2023].')])
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assertNotIn('0.8', result['answer'])
        self.assertEqual(len([e for e in trace.events if e['stage'] == 'model']), 1)

    def test_empty_lookup_cannot_be_reported_as_zero(self):
        result, _ = self.run_mock('How many launches?', [
            AIMessage(content='', tool_calls=[{'name':'lookup_records','args':{'query':'zznonexistent'},'id':'t1','type':'tool_call'}]),
            AIMessage(content='There were 0 launches.')])
        self.assertEqual(result['status'], 'insufficient_evidence')

    def test_aggregate_answer_has_supported_citation(self):
        result, _ = self.run_mock('How many launches had major incidents?', [
            AIMessage(content='', tool_calls=[{'name':'lookup_records','args':{'operation':'count_launches','event_type':'incident','severity':'major'},'id':'t1','type':'tool_call'}]),
            AIMessage(content='3 launches [REC-L7-003, REC-L7-011, REC-L7-019].')])
        self.assertEqual(result['status'], 'answered')

    def test_unknown_citation_is_rejected(self):
        result, _ = self.run_mock('Alpha packet loss?', [
            AIMessage(content='', tool_calls=[{'name':'lookup_records','args':{'query':'packet loss','launch_id':'L7-ALPHA'},'id':'t1','type':'tool_call'}]),
            AIMessage(content='41 seconds [REC-L7-999].')])
        self.assertEqual(result['status'], 'insufficient_evidence')

    def test_document_payload_preserves_meaning_without_duplicate_fields(self):
        chunk={'text':'C8 followed launch [REC-L7-012].', 'metadata':{'document_id':'DOC-L7-009','source_id':'DOC-L7-009','related_ids':'REC-L7-012','occurred_at':'2026-06-25','revised_at':'2026-06-26','start_index':0,'revision':'2','summary_scope':'retrospective'},'jev_score':3.5}
        item=agent._document_evidence(chunk)
        self.assertEqual(item['source_id'],'DOC-L7-009')
        self.assertEqual(item['record_ids'],'REC-L7-012')
        self.assertNotIn('source_id',item['metadata'])
        self.assertNotIn('related_ids',item['metadata'])
        self.assertEqual(item['metadata']['revised_at'],'2026-06-26')
        self.assertEqual(item['text'],chunk['text'])

    def test_document_request_preserves_fix_and_scope(self):
        q='Which component was tied to the Charlie yaw incident, and what fixed it?'
        candidate={'text':'IM-03 was fixed with C8.', 'metadata':{'document_id':'DOC-L7-009','launch_id':'L7-CHARLIE','related_ids':'REC-L7-012'}}
        with patch.object(agent,'pinecone_upsert_and_query',return_value=[candidate]) as dense, patch.object(agent,'jev_score',return_value=[candidate]):
            result, _ = self.run_mock(q,[
                AIMessage(content='',tool_calls=[{'name':'search_incident_documents','args':{'query':'Charlie yaw incident','launch_id':''},'id':'t1','type':'tool_call'}]),
                AIMessage(content='IM-03, firmware C8 [DOC-L7-009].')])
        self.assertIn('what fixed it', dense.call_args.args[2])
        self.assertEqual(dense.call_args.kwargs['filters'], {'launch_id':'L7-CHARLIE'})
        self.assertEqual(result['status'],'answered')


if __name__=='__main__':
    unittest.main()
