"""
test_history_play_static.py

P13-HISTORY-PLAY-UX1: Static contract tests for history.js play UX fix.
Verifies toggleHistoryAudio calls audioEl.play() after expanding the player.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'history.js')


class TestHistoryPlayStatic:
    """Static contract — read history.js as text and assert facts."""

    def test_toggleHistoryAudio_exists(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        assert 'window.toggleHistoryAudio' in content, \
            'history.js must define window.toggleHistoryAudio'

    def test_audioEl_play_called_after_insert(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.toggleHistoryAudio')
        func_end = content.find('\n  };', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'audioEl.play()' in func_body or '.play()' in func_body, \
            'toggleHistoryAudio must call audioEl.play()'

    def test_audioEl_play_after_attachHistoryAudioEvents(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.toggleHistoryAudio')
        func_end = content.find('\n  };', func_start) + 4
        func_body = content[func_start:func_end]
        # play() should come after attachHistoryAudioEvents
        attach_pos = func_body.find('attachHistoryAudioEvents')
        play_pos = func_body.find('.play()')
        assert attach_pos >= 0 and play_pos > attach_pos, \
            'audioEl.play() must be called after attachHistoryAudioEvents'

    def test_playPromise_catch_exists(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.toggleHistoryAudio')
        func_end = content.find('\n  };', func_start) + 4
        func_body = content[func_start:func_end]
        assert '.catch' in func_body, \
            'toggleHistoryAudio must handle play() promise rejection with .catch'

    def test_autoplay_failure_user_message(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.toggleHistoryAudio')
        func_end = content.find('\n  };', func_start) + 4
        func_body = content[func_start:func_end]
        # Must show user-friendly message when autoplay is blocked
        assert ('浏览器阻止' in func_body or '自动播放' in func_body), \
            'autoplay failure must show user-friendly message'

    def test_no_real_api_calls_in_toggleHistoryAudio(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('window.toggleHistoryAudio')
        func_end = content.find('\n  };', func_start) + 4
        func_body = content[func_start:func_end]
        # No fetch or guardedJsonFetch in toggleHistoryAudio
        assert 'fetch(' not in func_body, \
            'toggleHistoryAudio must not make fetch calls'
        assert 'guardedJsonFetch' not in func_body, \
            'toggleHistoryAudio must not call guardedJsonFetch'

    def test_no_sample_store_in_history_js(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        assert 'SampleStore' not in content, \
            'history.js must not reference SampleStore'

    def test_no_safePushWorkspaceSample_in_history_js(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        assert 'safePushWorkspaceSample' not in content, \
            'history.js must not reference safePushWorkspaceSample'

    def test_no_safePushAuditionSample_in_history_js(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        assert 'safePushAuditionSample' not in content, \
            'history.js must not reference safePushAuditionSample'

    def test_no_sample_sidebar_js_in_history_js(self):
        content = open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()
        assert 'sample_sidebar' not in content.lower(), \
            'history.js must not reference sample_sidebar'
