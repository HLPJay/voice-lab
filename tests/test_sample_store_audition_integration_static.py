"""
test_sample_store_audition_integration_static.py

B3: Static contract tests for audition_records -> sample_store integration.
Verifies audition_records.js and index.html contain correct
safePushAuditionSample helper and call-site facts without
executing browser-side code.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDITION_RECORDS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'audition_records.js')
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')


class TestAuditionSampleIntegrationStatic:
    """Static contract — read JS/HTML files as text and assert facts."""

    def test_safePushAuditionSample_exists_in_audition_records(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        assert 'window.safePushAuditionSample' in content, \
            'audition_records.js must define window.safePushAuditionSample'

    def test_safePushAuditionSample_calls_sample_store_pushSample(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        assert 'window.SampleStore.pushSample' in content, \
            'safePushAuditionSample must call window.SampleStore.pushSample'

    def test_safePushAuditionSample_has_try_catch(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert 'try {' in func_body and '} catch' in func_body, \
            'safePushAuditionSample must be wrapped in try/catch'

    def test_safePushAuditionSample_guards_sample_store_exists(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert re.search(r"if\s*\(\s*!\s*window\.SampleStore", func_body) or \
               re.search(r"if\s*\(\s*typeof\s+window\.SampleStore", func_body), \
            'safePushAuditionSample must guard against missing SampleStore'

    def test_safePushAuditionSample_rejects_blob_url(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert "startsWith('blob:')" in func_body or 'indexOf' in func_body, \
            'safePushAuditionSample must reject blob: URLs'

    def test_sample_source_is_audition(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert re.search(r"source\s*:\s*'audition'", func_body), \
            'sample source must be "audition"'

    def test_sample_tags_include_audition(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert re.search(r"tags\s*:\s*\[\s*'audition'\s*\]", func_body), \
            "sample tags must include 'audition'"

    def test_sample_has_voice_id_field(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert 'voice_id:' in func_body or 'voice_id ' in func_body, \
            'sample must have voice_id field'

    def test_sample_has_voice_name_field(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert 'voice_name:' in func_body or 'voice_name ' in func_body, \
            'sample must have voice_name field'

    def test_sample_has_text_preview_field(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert 'text_preview:' in func_body or 'text_preview ' in func_body, \
            'sample must have text_preview field'

    def test_sample_has_duration_ms_field(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert 'duration_ms:' in func_body or 'duration_ms ' in func_body, \
            'sample must have duration_ms field'

    def test_sample_has_audio_format_field(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        assert 'audio_format:' in func_body or 'audio_format ' in func_body, \
            'sample must have audio_format field'

    def test_safePushAuditionSample_no_direct_localStorage(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.safePushAuditionSample')
        func_end = content.find('};', func_start) + 2
        func_body = content[func_start:func_end]
        forbidden = ['localStorage.getItem', 'localStorage.setItem', 'localStorage.removeItem']
        found = [kw for kw in forbidden if kw in func_body]
        assert not found, \
            f'safePushAuditionSample must not use localStorage directly: {found}'

    def test_safePushAuditionSample_no_recentJobs_access(self):
        content = open(AUDITION_RECORDS_PATH, 'r', encoding='utf-8').read()
        lower = content.lower()
        forbidden = [
            r"localstorage\s*\.\s*getitem\s*\(\s*['\"]recentjobs['\"]",
            r"localstorage\s*\.\s*setitem\s*\(\s*['\"]recentjobs['\"]",
            r"safegetitem\s*\(\s*['\"]recentjobs['\"]",
            r"safesetitem\s*\(\s*['\"]recentjobs['\"]",
            r"window\s*\.\s*recentjobs",
            r"\[\s*['\"]recentjobs['\"]\s*\]",
            r"recentjobs\s*[.\[]",
        ]
        for pattern in forbidden:
            assert not re.search(pattern, lower), \
                f'safePushAuditionSample must not access recentJobs: {pattern}'

    def test_handleGenerateAudition_constructs_auditionRecord(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # Must construct auditionRecord object before pushing
        assert re.search(r"const\s+auditionRecord\s*=\s*\{", content), \
            'handleGenerateAudition must construct auditionRecord object'

    def test_auditionRecord_contains_provider(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # Find auditionRecord block
        block = re.search(
            r"const\s+auditionRecord\s*=\s*\{[\s\S]*?\};",
            content
        )
        assert block, 'auditionRecord object not found'
        body = block.group(0)
        assert 'provider' in body, \
            'auditionRecord must contain provider'

    def test_auditionRecord_contains_model(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        block = re.search(
            r"const\s+auditionRecord\s*=\s*\{[\s\S]*?\};",
            content
        )
        assert block, 'auditionRecord object not found'
        body = block.group(0)
        assert 'model' in body, \
            'auditionRecord must contain model'

    def test_auditionRecord_contains_assetId(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        block = re.search(
            r"const\s+auditionRecord\s*=\s*\{[\s\S]*?\};",
            content
        )
        assert block, 'auditionRecord object not found'
        body = block.group(0)
        assert 'assetId' in body, \
            'auditionRecord must contain assetId'

    def test_auditionRecord_contains_audioFormat(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        block = re.search(
            r"const\s+auditionRecord\s*=\s*\{[\s\S]*?\};",
            content
        )
        assert block, 'auditionRecord object not found'
        body = block.group(0)
        assert 'audioFormat' in body, \
            'auditionRecord must contain audioFormat'

    def test_handleGenerateAudition_calls_safePushAuditionSample(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # Must call safePushAuditionSample after pushing to _auditionRecords
        assert 'safePushAuditionSample' in content, \
            'handleGenerateAudition must call safePushAuditionSample'

    def test_safePushAuditionSample_called_in_success_branch(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # safePushAuditionSample must be called in the audition success branch
        # We verify by finding handleGenerateAudition, then the success condition,
        # then safePushAuditionSample in order within that function
        hga_pos = content.find('async function handleGenerateAudition')
        assert hga_pos >= 0, 'handleGenerateAudition not found'
        success_pos = content.find('data.audio_asset && data.audio_asset.url', hga_pos)
        assert success_pos >= 0, 'audition success condition not found'
        safe_push_pos = content.find('safePushAuditionSample', success_pos)
        assert safe_push_pos >= 0, 'safePushAuditionSample not found after success condition'
        # Also verify it's within the handleGenerateAudition function (next function starts)
        next_func = content.find('\n  async function ', hga_pos + 1)
        if next_func < 0:
            next_func = content.find('\n  function ', hga_pos + 1)
        if next_func < 0:
            next_func = len(content)
        assert safe_push_pos < next_func, \
            'safePushAuditionSample call must be within handleGenerateAudition'

    def test_no_workspace_calls_in_audition_context(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # After B3 changes, workspace calls must not appear in audition success branch
        hga_pos = content.find('async function handleGenerateAudition')
        assert hga_pos >= 0, 'handleGenerateAudition not found'
        success_pos = content.find('data.audio_asset && data.audio_asset.url', hga_pos)
        assert success_pos >= 0, 'audition success condition not found'
        next_func = content.find('\n  async function ', hga_pos + 1)
        if next_func < 0:
            next_func = content.find('\n  function ', hga_pos + 1)
        if next_func < 0:
            next_func = len(content)
        audition_body = content[hga_pos:next_func]
        assert 'safePushWorkspaceSample' not in audition_body, \
            'safePushWorkspaceSample must not appear in audition function'

    def test_no_batch_longtext接入(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # batch_longtext.js is already referenced in script tags (pre-existing)
        # Verify it is NOT called/invoked within handleGenerateAudition
        hga_pos = content.find('async function handleGenerateAudition')
        assert hga_pos >= 0, 'handleGenerateAudition not found'
        next_func = content.find('\n  async function ', hga_pos + 1)
        if next_func < 0:
            next_func = content.find('\n  function ', hga_pos + 1)
        if next_func < 0:
            next_func = len(content)
        audition_body = content[hga_pos:next_func]
        assert 'batch_longtext' not in audition_body, \
            'batch_longtext must not be called within handleGenerateAudition'

    def test_no_batch_script接入(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # batch_script.js is already referenced in script tags (pre-existing)
        # Verify it is NOT called/invoked within handleGenerateAudition
        hga_pos = content.find('async function handleGenerateAudition')
        assert hga_pos >= 0, 'handleGenerateAudition not found'
        next_func = content.find('\n  async function ', hga_pos + 1)
        if next_func < 0:
            next_func = content.find('\n  function ', hga_pos + 1)
        if next_func < 0:
            next_func = len(content)
        audition_body = content[hga_pos:next_func]
        assert 'batch_script' not in audition_body, \
            'batch_script must not be called within handleGenerateAudition'

    def test_sample_sidebar_js_loaded(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'sample_sidebar.js' in content, \
            'sample_sidebar.js must be referenced in index.html (added in B4)'
