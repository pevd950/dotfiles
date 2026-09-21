import getpass
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

import pull_transcripts as puller
import read_transcripts as reader
from transcript_cache import read_json

AFTER = '2026-08-22T00:00:00Z'
THROUGH = '2026-09-21T00:00:00Z'


def record(kind, **payload):
    return {'timestamp': '2026-09-01T12:00:00Z', 'type': 'response_item',
            'payload': {'type': kind, **payload}}


class TranscriptReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/private/tmp' if Path('/private/tmp').exists() else None)
        self.base = Path(self.temp.name)
        self.cache = self.base / 'cache'
        self.codex = self.base / 'home' / '.codex'
        for area in ('sessions', 'archived_sessions'):
            (self.codex / area).mkdir(parents=True)
        self.spec = {'label': 'source-a', 'ssh': None, 'hostnames': [socket.gethostname()],
                     'user': getpass.getuser(), 'roots': {a: str(self.codex / a) for a in ('sessions', 'archived_sessions')}}
        self.config = {'sources': [self.spec]}
        self.relative = 'source-a/sessions/old-name.jsonl'

    def tearDown(self):
        self.temp.cleanup()

    def write(self, records, area='sessions', name='old-name.jsonl'):
        path = self.codex / area / name
        path.write_text(''.join(json.dumps(r) + '\n' for r in records))
        return path

    def pull(self):
        return puller.pull(self.cache, self.config)

    def scan(self, **kwargs):
        for _ in range(100):
            result = reader.scan_batch(self.cache, **kwargs)
            if not result['remaining_files']:
                return
        self.fail('Reader did not finish')

    def report(self):
        return reader.report(self.cache, AFTER, THROUGH)

    def test_nonstring_source_labels_are_controlled_errors(self):
        for value in (42,None,[],{}):
            self.spec['label']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.pull()
        self.assertFalse(self.cache.exists())

    def test_same_metadata_cache_edit_invalidates_all_read_paths(self):
        self.write([{'type':'session_meta','payload':{'id':'old'}},record('user_message',message='hello')])
        self.pull();self.scan();self.assertTrue(self.report()['all_sources_covered'])
        path=self.cache/self.relative;old=path.stat()
        path.write_text(path.read_text().replace('old','new'));os.utime(path,ns=(old.st_atime_ns,old.st_mtime_ns))
        with self.assertRaises(ValueError):reader.context(self.cache,self.relative,2)
        self.assertEqual(reader.candidates(self.cache,AFTER,THROUGH),[])
        self.assertFalse(self.report()['all_sources_covered'])
        self.assertEqual(self.report()['sources']['source-a']['changed_files'],1)

    def test_record_limit_decrease_is_rejected(self):
        self.write([{'type':'session_meta','payload':{'id':'keep'}},record('user_message',message='x'*2000)])
        self.pull();self.scan(max_record_bytes=4096)
        with self.assertRaisesRegex(ValueError,'cannot decrease'):
            reader.scan_batch(self.cache,max_record_bytes=1024)
        self.scan(max_record_bytes=4096)
        self.assertEqual(len(reader.candidates(self.cache,AFTER,THROUGH)),1)

    def test_case_colliding_source_labels_rejected(self):
        self.config['sources'].append({**self.spec,'label':'SOURCE-A'})
        with self.assertRaises(ValueError):self.pull()
        self.assertFalse(self.cache.exists())
        self.config['sources'].pop();self.pull();self.spec['label']='SOURCE-A'
        with self.assertRaises(ValueError):self.pull()

    def test_oversized_session_identity_is_gap_without_index_amplification(self):
        self.write([{'type':'session_meta','payload':{'id':'x'*(1024*1024)}}]+[record('user_message',message='small') for _ in range(100)])
        self.pull();self.scan(max_records=2)
        self.assertFalse(self.report()['all_sources_covered'])
        self.assertTrue(all(r['session'] is None for r in reader.candidates(self.cache,AFTER,THROUGH)))
        self.assertLess((self.cache/'index.sqlite3').stat().st_size,1024*1024)

    def test_undated_report_does_not_query_header_per_activity(self):
        activity=record('user_message',message='undated');activity.pop('timestamp')
        self.write([{'type':'session_meta','payload':{'id':'keep'}}]+[activity]*5000)
        self.pull();self.scan()
        with patch.object(reader,'scope_at_record',side_effect=AssertionError('per-record scope lookup')):
            self.assertEqual(self.report()['sources']['source-a']['undated_files_with_session_time'],0)

    def test_cache_cannot_overlap_local_source(self):
        for cache in (self.codex/'sessions', self.codex/'sessions'/'cache', self.codex):
            with self.subTest(cache=cache), self.assertRaises(ValueError):
                puller.pull(cache,self.config)
        self.assertFalse((self.codex/'sessions'/'cache').exists())

    def test_reserved_source_labels_rejected_before_cache_creation(self):
        for label in ('index.sqlite3','snapshot.json','INDEX.SQLITE3','index.sqlite3-wal'):
            self.spec['label']=label
            with self.subTest(label=label),self.assertRaises(ValueError):self.pull()
        self.assertFalse(self.cache.exists())

    def test_interrupted_pull_invalidates_old_candidates(self):
        path=self.write([{'type':'session_meta','payload':{'id':'keep'}},record('user_message',message='old')])
        self.pull();self.scan();self.assertEqual(len(reader.candidates(self.cache,AFTER,THROUGH)),1)
        path.write_text(path.read_text().replace('old','new'))
        original=puller.subprocess.run
        def interrupt(command,**kwargs):
            result=original(command,**kwargs)
            if command[0]=='rsync':raise KeyboardInterrupt()
            return result
        with patch.object(puller.subprocess,'run',side_effect=interrupt), self.assertRaises(KeyboardInterrupt):self.pull()
        self.assertEqual(reader.candidates(self.cache,AFTER,THROUGH),[])
        self.assertFalse(self.report()['all_sources_covered'])
        self.pull();self.scan();self.assertIn('new',reader.context(self.cache,self.relative,2)['records'][-1]['text'])

    def test_undated_time_count_uses_current_header(self):
        for parent_time,child_time,expected in ((True,False,0),(False,True,1)):
            parent={'type':'session_meta','payload':{'id':'parent'}}
            child={'type':'session_meta','payload':{'id':'child'}}
            if parent_time:parent['timestamp']='2026-09-01T00:00:00Z'
            if child_time:child['timestamp']='2026-09-02T00:00:00Z'
            activity=record('user_message',message='undated');activity.pop('timestamp')
            self.write([parent,child,activity]);self.pull();self.scan()
            self.assertEqual(self.report()['sources']['source-a']['undated_files_with_session_time'],expected)

    def test_excluded_filename_keeps_included_fork(self):
        self.config['exclude_sessions'] = ['excluded']
        self.write([{'type':'session_meta','payload':{'id':'excluded'}}, record('user_message',message='hide'),
                    {'type':'session_meta','payload':{'id':'keep'}},record('user_message',message='keep')],name='rollout-excluded.jsonl')
        self.pull(); self.scan(max_records=1)
        self.assertEqual([r['session'] for r in reader.candidates(self.cache,AFTER,THROUGH)],['keep'])

    def test_parse_failure_quarantines_excluded_segment_across_batches(self):
        self.config['exclude_sessions']=['excluded']
        path=self.write([{'type':'session_meta','payload':{'id':'excluded'}}])
        with path.open('a') as f:
            f.write('not json\n'+json.dumps(record('user_message',message='hide'))+'\n')
            f.write(json.dumps({'type':'session_meta','payload':{'id':'keep'}})+'\n'+json.dumps(record('user_message',message='keep'))+'\n')
        self.pull();self.scan(max_records=1)
        self.assertEqual([r['line'] for r in reader.candidates(self.cache,AFTER,THROUGH)],[5])
        with self.assertRaises(ValueError):reader.context(self.cache,self.relative,3)

    def test_supported_bad_envelopes_are_gaps(self):
        self.write([{'type':'session_meta','payload':{'id':'keep'}},
                    {'type':'response_item','payload':None},{'type':'event_msg'},
                    {'type':'event_msg','payload':{}},record('user_message',message='later')])
        self.pull();self.scan()
        self.assertGreaterEqual(self.report()['sources']['source-a']['malformed_records'],3)
        self.assertFalse(self.report()['all_sources_covered'])
        self.assertEqual(len(reader.candidates(self.cache,AFTER,THROUGH)),1)

    def test_headerless_activity_is_identity_gap(self):
        self.write([record('user_message',message='unknown')]);self.pull();self.scan()
        self.assertFalse(self.report()['all_sources_covered'])
        self.assertEqual(self.report()['sources']['source-a']['malformed_records'],1)
        self.assertIsNone(reader.candidates(self.cache,AFTER,THROUGH)[0]['session'])

    def test_partial_inventory_cannot_attribute_uncopied_bytes(self):
        self.pull()
        self.write([record('user_message',message='source')])
        cached=self.cache/self.relative;cached.write_text(json.dumps(record('user_message',message='unverified'))+'\n');cached.chmod(0o600)
        original=puller.probe
        def partial(spec,exclude):
            result=original(spec,exclude);result['roots']['sessions']['status']='partial';return result
        with patch.object(puller,'probe',side_effect=partial):
            result=self.pull()['source-a']
        self.assertEqual(result['cached_files'],0)
        self.scan();self.assertEqual(reader.candidates(self.cache,AFTER,THROUGH),[])

    def test_signal_filter_matches_only_exact_array_values(self):
        self.write([{'type':'session_meta','payload':{'id':'keep'}},
                    record('function_call',name='friction_candidate',call_id='a'),
                    record('function_call_output',call_id='a',output='error: failed')])
        self.pull();self.scan()
        rows=reader.candidates(self.cache,AFTER,THROUGH,signal='friction_candidate')
        self.assertEqual([r['kind'] for r in rows],['tool_result'])
        self.assertEqual(reader.candidates(self.cache,AFTER,THROUGH,signal='%'),[])

    def test_real_rsync_scope_privacy_and_no_deletion_propagation(self):
        path = self.write([record('user_message', message='hello')])
        (self.codex / 'config.toml').write_text('not a transcript')
        (self.codex / 'sessions' / 'credentials.txt').write_text('not a transcript')
        self.assertEqual(self.pull()['source-a']['status'], 'ok')
        self.assertEqual([p.name for p in self.cache.rglob('*.jsonl')], ['old-name.jsonl'])
        self.assertFalse(list(self.cache.rglob('*.toml')))
        self.assertFalse(list(self.cache.rglob('*.txt')))
        for p in self.cache.rglob('*'):
            self.assertEqual(p.stat().st_mode & 0o777, 0o700 if p.is_dir() else 0o600)
        path.unlink()
        self.pull()
        self.assertTrue((self.cache / self.relative).exists())
        self.scan()
        self.assertEqual(self.report()['sources']['source-a']['retained_files_absent_at_source'], 1)

    def test_resumes_whole_records_and_uses_activity_not_filename(self):
        self.write([{'type':'session_meta','payload':{'id':'keep'}}] + [record('user_message', message=str(i)) for i in range(8)])
        self.pull()
        first = reader.scan_batch(self.cache, max_records=1, max_bytes=1)
        self.assertEqual(first['batch_records'], 1)
        self.assertEqual(first['remaining_files'], 1)
        self.scan(max_records=1, max_bytes=1)
        self.assertEqual(self.report()['sources']['source-a']['selected_records'], 8)
        page1 = reader.candidates(self.cache, AFTER, THROUGH, limit=3)
        page2 = reader.candidates(self.cache, AFTER, THROUGH, limit=3, offset=3)
        self.assertEqual([r['line'] for r in page1 + page2], list(range(2, 8)))
        self.assertTrue(self.report()['all_sources_covered'])

    def test_large_record_and_fork_headers_do_not_hide_later_activity(self):
        self.write([{'type': 'session_meta', 'payload': {'id': 'parent'}},
                    record('message', role='assistant', content=[{'text': 'x' * (2*1024*1024)}]),
                    {'type': 'session_meta', 'payload': {'id': 'child'}},
                    record('user_message', message='Actually fix the later failure')])
        self.pull(); self.scan(max_bytes=1024)
        rows = reader.candidates(self.cache, AFTER, THROUGH)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]['session'], 'child')
        self.assertEqual(rows[-1]['owner'], 'parent')
        self.assertEqual(self.report()['sources']['source-a']['oversized_unparsed'], 0)

    def test_oversize_gap_continues_and_larger_limit_retries(self):
        self.write([{'type':'session_meta','payload':{'id':'keep'}}, record('user_message', message='x'*1000), record('user_message', message='later')])
        self.pull(); self.scan(max_record_bytes=300)
        self.assertFalse(self.report()['all_sources_covered'])
        self.assertEqual(self.report()['sources']['source-a']['selected_records'], 1)
        self.scan(max_record_bytes=2000)
        self.assertTrue(self.report()['all_sources_covered'])
        self.assertEqual(self.report()['sources']['source-a']['selected_records'], 2)

    def test_checksum_change_invalidates_candidates_and_context_before_rescan(self):
        source = self.write([record('user_message', message='first')])
        self.pull(); self.scan()
        old = source.stat()
        source.write_text(source.read_text().replace('first', 'other'))
        os.utime(source, ns=(old.st_atime_ns, old.st_mtime_ns))
        self.pull()
        self.assertEqual(reader.candidates(self.cache, AFTER, THROUGH), [])
        with self.assertRaises(ValueError):
            reader.context(self.cache, self.relative, 1)
        self.scan()
        self.assertIn('other', reader.context(self.cache, self.relative, 1)['records'][0]['text'])

    def test_context_retrieves_user_call_result_and_response(self):
        self.write([record('user_message', message='Please run the build'),
                    record('function_call', name='exec', call_id='c1', arguments='build'),
                    record('function_call_output', call_id='c1', output='Error: build failed, exit code: 1'),
                    record('agent_message', message='I corrected the path and retried')])
        self.pull(); self.scan()
        context = reader.context(self.cache, self.relative, 3, radius=1)
        self.assertEqual([r['line'] for r in context['records']], [1, 2, 3, 4])
        self.assertIn('build failed', context['records'][2]['text'])

    def test_unavailable_sources_and_interrupted_pull_remain_explicit(self):
        self.write([record('user_message', message='local')])
        other = {**self.spec, 'label': 'source-b', 'hostnames': ['wrong-identity']}
        self.config['sources'].append(other)
        self.pull(); self.scan()
        self.assertEqual(self.report()['sources']['source-b']['pull_status'], 'unavailable')
        self.assertFalse(self.report()['all_sources_covered'])
        real_probe = puller.probe
        def interrupt(spec, excluded):
            if spec['label'] == 'source-b':
                raise KeyboardInterrupt()
            return real_probe(spec, excluded)
        with patch.object(puller, 'probe', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt): self.pull()
        snapshot = read_json(self.cache / 'snapshot.json')
        self.assertEqual(set(snapshot['sources']), {'source-a', 'source-b'})
        self.assertEqual(snapshot['sources']['source-b']['status'], 'not_attempted')

    def test_archive_baseline_and_later_observation(self):
        self.write([record('user_message', message='already archived')], area='archived_sessions', name='baseline.jsonl')
        active = self.write([record('user_message', message='active')])
        self.pull()
        active.rename(self.codex / 'archived_sessions' / active.name)
        self.pull(); self.scan()
        report = self.report()
        self.assertEqual(report['sources']['source-a']['new_archive_observations'], 1)
        self.assertIn('unknown', report['archive_history'])
        self.assertEqual(report['sources']['source-a']['retained_files_absent_at_source'], 1)

    def test_exclusions_change_reindexes_prior_excluded_file(self):
        self.write([{'type': 'session_meta', 'payload': {'id': 'excluded-id'}}, record('user_message', message='test')])
        self.config['exclude_sessions'] = ['excluded-id']
        self.pull(); self.scan()
        self.assertEqual(self.report()['sources']['source-a']['excluded_files'], 1)
        self.config['exclude_sessions'] = []
        self.pull(); self.scan()
        self.assertEqual(self.report()['sources']['source-a']['selected_records'], 1)

    def test_legacy_scope_retains_session_time_and_verified_source_host(self):
        self.write([{'id': 'legacy-session', 'timestamp': '2025-08-28T08:15:51Z', 'instructions': ''},
                    {'type': 'message', 'role': 'user', 'content': [{'text': 'legacy request'}]}])
        self.pull(); self.scan()
        rows = reader.candidates(self.cache, AFTER, THROUGH)
        self.assertEqual(len(rows), 1)
        scope = rows[0]['scope']
        self.assertEqual(scope['source_host'], socket.gethostname())
        self.assertEqual(scope['session_id'], 'legacy-session')
        self.assertEqual(scope['timestamp'], '2025-08-28T08:15:51.000000+00:00')
        self.assertEqual(scope['timestamp_basis'], 'session_start')
        self.assertIsNone(scope['activity_timestamp'])
        self.assertEqual(scope['window_membership'], 'unknown')
        self.assertEqual(reader.candidates(self.cache, AFTER, THROUGH, time_scope='dated'), [])
        self.assertEqual(len(reader.candidates(self.cache, AFTER, THROUGH, time_scope='undated')), 1)
        state = self.report()['sources']['source-a']
        self.assertEqual(state['undated_files_with_session_time'], 1)
        self.assertFalse(state['timestamp_selection_complete'])
        detail = reader.context(self.cache, self.relative, 2)
        self.assertEqual(detail['source_host'], socket.gethostname())
        self.assertEqual(detail['records'][-1]['scope']['timestamp_basis'], 'session_start')

    def test_undated_fork_context_uses_its_current_session_header(self):
        self.write([{'type': 'session_meta', 'timestamp': '2025-01-01T00:00:00Z', 'payload': {'id': 'parent'}},
                    {'type': 'session_meta', 'timestamp': '2026-09-01T00:00:00Z', 'payload': {'id': 'child'}},
                    {'type': 'message', 'role': 'user', 'content': [{'text': 'undated child'}]}])
        self.pull(); self.scan()
        scope = reader.candidates(self.cache, AFTER, THROUGH)[0]['scope']
        self.assertEqual(scope['file_session_id'], 'parent')
        self.assertEqual(scope['session_id'], 'child')
        self.assertEqual(scope['timestamp'], '2026-09-01T00:00:00.000000+00:00')
        self.assertEqual(scope['window_membership'], 'unknown')

    def test_timestamp_scope_never_uses_filename_or_mtime(self):
        self.write([{'type': 'message', 'role': 'user', 'content': [{'text': 'no header'}]},
                    record('user_message', message='dated')])
        self.pull(); self.scan()
        rows = reader.candidates(self.cache, AFTER, THROUGH)
        unknown = next(r for r in rows if r['stamp'] is None)
        self.assertIsNone(unknown['scope']['timestamp'])
        self.assertEqual(unknown['scope']['timestamp_basis'], 'unknown')
        dated = next(r for r in rows if r['stamp'])
        self.assertEqual(dated['scope']['timestamp_basis'], 'activity')
        self.assertEqual(dated['scope']['window_membership'], 'confirmed')
        self.assertEqual(dated['scope']['source_host'], socket.gethostname())

    def test_scope_migration_reindexes_legacy_header_without_recopy(self):
        self.write([{'id': 'legacy-session', 'timestamp': '2025-08-28T08:15:51Z'},
                    {'type': 'message', 'role': 'user', 'content': [{'text': 'legacy'}]}])
        self.pull(); self.scan()
        db = reader.connect(self.cache)
        with db:
            db.execute("DELETE FROM settings WHERE key='reader_version'")
            db.execute("UPDATE records SET kind='unknown' WHERE line=1")
            db.execute('UPDATE files SET owner=NULL,session=NULL')
        db.close()
        self.assertEqual(reader.candidates(self.cache, AFTER, THROUGH), [])
        self.scan()
        self.assertEqual(reader.candidates(self.cache, AFTER, THROUGH)[0]['scope']['session_id'], 'legacy-session')

    def test_context_neighbors_skip_trace_metadata(self):
        self.write([record('user_message', message='request'),
                    record('function_call', name='exec', call_id='x', arguments='build'),
                    *[{'type': 'token_usage_record'} for _ in range(30)],
                    record('function_call_output', call_id='x', output='failed'),
                    *[{'type': 'token_usage_record'} for _ in range(30)],
                    record('agent_message', message='corrected')])
        self.pull(); self.scan()
        rows = reader.context(self.cache, self.relative, 33, radius=1)['records']
        self.assertEqual([r['kind'] for r in rows], ['user_message', 'tool_call', 'tool_result', 'assistant_message'])
        self.assertIn('corrected', rows[-1]['text'])

    def test_unknown_cache_file_cannot_acquire_verified_host_attribution(self):
        self.write([record('user_message', message='source record')])
        self.pull()
        unknown = self.cache / 'source-a' / 'sessions' / 'unknown.jsonl'
        unknown.write_text(json.dumps(record('user_message', message='unknown origin')) + '\n')
        unknown.chmod(0o600)
        result = self.pull()['source-a']
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['cached_files'], 1)
        self.scan()
        self.assertEqual(len(reader.candidates(self.cache, AFTER, THROUGH)), 1)

    def test_requested_window_cannot_extend_beyond_inventory(self):
        self.write([{'type':'session_meta','payload':{'id':'keep'}}, record('user_message', message='dated')]); self.pull(); self.scan()
        from transcript_cache import write_json
        snapshot = read_json(self.cache / 'snapshot.json')
        snapshot['sources']['source-a']['coverage_through'] = '2026-09-10T00:00:00Z'
        write_json(self.cache / 'snapshot.json', snapshot)
        state = self.report()['sources']['source-a']
        self.assertFalse(state['timestamp_selection_complete'])
        self.assertFalse(state['inventory_reaches_window_end'])
        self.assertTrue(reader.report(self.cache, AFTER, '2026-09-09T00:00:00Z')['all_sources_covered'])

    def test_excluded_child_is_hidden_without_losing_parent_or_later_child(self):
        self.write([{'type':'session_meta','payload':{'id':'parent'}}, record('user_message',message='keep parent'),
                    {'type':'session_meta','payload':{'id':'excluded-child'}}, record('user_message',message='hide child'),
                    {'type':'session_meta','payload':{'id':'kept-child'}}, record('user_message',message='keep child')])
        self.config['exclude_sessions']=['excluded-child']; self.pull(); self.scan(max_records=1)
        rows=reader.candidates(self.cache,AFTER,THROUGH)
        self.assertEqual([r['line'] for r in rows],[2,6])
        self.assertEqual(self.report()['sources']['source-a']['excluded_records'],2)
        with self.assertRaises(ValueError): reader.context(self.cache,self.relative,4)
        self.assertNotIn(4,[r['line'] for r in reader.context(self.cache,self.relative,6,radius=20)['records']])

    def test_excluded_parent_does_not_hide_later_included_child(self):
        self.write([{'type':'session_meta','payload':{'id':'excluded-parent'}},record('user_message',message='hide'),
                    {'type':'session_meta','payload':{'id':'included-child'}},record('user_message',message='keep')])
        self.config['exclude_sessions']=['excluded-parent'];self.pull();self.scan(max_records=1)
        self.assertEqual([r['line'] for r in reader.candidates(self.cache,AFTER,THROUGH)],[4])

    def test_invalid_first_header_is_gap_and_not_reassigned_to_child(self):
        for payload in (None, {}, {'id':2}, {'id':''}):
            with self.subTest(payload=payload):
                self.write([{'type':'session_meta','payload':payload},record('user_message',message='unknown owner'),
                            {'type':'session_meta','payload':{'id':'child'}},record('user_message',message='child')])
                self.pull();self.scan(max_records=1)
                state=self.report()['sources']['source-a']
                self.assertEqual(state['malformed_records'],2)
                self.assertFalse(state['timestamp_selection_complete'])
                rows=reader.candidates(self.cache,AFTER,THROUGH)
                self.assertTrue(all(r['owner'] is None for r in rows))
                self.assertIsNone(rows[0]['scope']['session_id'])

    def test_abandoned_rsync_staging_is_not_transcript_evidence(self):
        self.write([record('user_message', message='source record')])
        self.pull()
        staging = self.cache / 'source-a' / 'sessions' / '.~tmp~'
        staging.mkdir(mode=0o700)
        abandoned = staging / 'abandoned.jsonl'
        abandoned.write_text(json.dumps(record('user_message', message='unfinished transfer')) + '\n')
        abandoned.chmod(0o600)
        result = self.pull()
        self.assertEqual(result['source-a']['cached_files'], 1)
        self.scan()
        self.assertEqual(self.report()['sources']['source-a']['selected_records'], 1)

    def test_source_label_cannot_mix_different_roots(self):
        self.write([record('user_message', message='source one')])
        self.pull()
        other = self.base / 'other' / '.codex'
        for area in ('sessions', 'archived_sessions'):
            (other / area).mkdir(parents=True)
        self.spec['roots'] = {area: str(other / area) for area in ('sessions', 'archived_sessions')}
        self.assertEqual(self.pull()['source-a']['status'], 'unavailable')
        self.assertTrue((self.cache / self.relative).exists())

    def test_mutation_during_resumed_scan_cannot_be_reported_complete(self):
        self.write([{'type':'session_meta','payload':{'id':'keep'}}, record('user_message', message='first'), record('user_message', message='later')])
        self.pull()
        reader.scan_batch(self.cache, max_records=1)
        cached = self.cache / self.relative
        cached.write_text(cached.read_text() + 'changed')
        self.scan()
        state = self.report()['sources']['source-a']
        self.assertEqual(state['changed_files'], 1)
        self.assertFalse(state['timestamp_selection_complete'])
        self.assertEqual(reader.candidates(self.cache, AFTER, THROUGH), [])
        self.pull(); self.scan()
        self.assertTrue(self.report()['all_sources_covered'])

    def test_malformed_and_untimestamped_events_are_visible_gaps(self):
        source = self.write([{'type':'session_meta','payload':{'id':'keep'}}, record('user_message', message='valid'),
                             {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'missing timestamp'}}])
        with source.open('a') as handle: handle.write('malformed\n')
        self.pull(); self.scan()
        state = self.report()['sources']['source-a']
        self.assertEqual(state['malformed_records'], 1)
        self.assertEqual(state['untimestamped_events'], 1)
        self.assertEqual(state['selected_records'], 1)
        self.assertFalse(state['timestamp_selection_complete'])

    def test_symlinks_are_not_copied_and_cache_redirection_is_rejected(self):
        self.write([record('user_message', message='safe')])
        (self.codex / 'sessions' / 'linked.jsonl').symlink_to(self.codex / 'sessions' / 'old-name.jsonl')
        self.assertEqual(self.pull()['source-a']['status'], 'partial')
        self.assertFalse((self.cache / 'source-a/sessions/linked.jsonl').exists())
        (self.codex / 'sessions' / 'linked.jsonl').unlink()
        self.pull()
        target = self.cache / self.relative
        target.unlink(); target.symlink_to(self.codex / 'sessions' / 'old-name.jsonl')
        self.assertEqual(self.pull()['source-a']['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
