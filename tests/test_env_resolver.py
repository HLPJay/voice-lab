"""Tests for app.config.env_resolver module.

P16-XIAOMI-MIMO-TTS-B1-CHECK: Tests for VOICE_LAB_ENV_FILE support and resolution order.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestResolveEnvValuePriority:
    """Tests for resolve_env_value priority order."""

    def setup_method(self):
        """Clear cache before each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

        # Ensure test keys are not in os.environ
        os.environ.pop("TEST_OS_PRIORITY_KEY", None)
        os.environ.pop("TEST_VOICE_LAB_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)

    def teardown_method(self):
        """Clean up after each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

        os.environ.pop("TEST_OS_PRIORITY_KEY", None)
        os.environ.pop("TEST_VOICE_LAB_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)

    def test_os_environ_highest_priority(self):
        """os.environ values take priority over VOICE_LAB_ENV_FILE and project .env."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        # Create a temp env file with a key
        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("TEST_OS_PRIORITY_KEY=from_temp_env\n")
            temp_env_path = f.name

        try:
            # Set VOICE_LAB_ENV_FILE to temp env
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            # Also set os.environ (should win)
            os.environ["TEST_OS_PRIORITY_KEY"] = "from_os_environ"

            clear_env_cache()
            value = resolve_env_value("TEST_OS_PRIORITY_KEY")

            assert value == "from_os_environ", f"Expected 'from_os_environ' but got {value!r}"
        finally:
            os.unlink(temp_env_path)

    def test_voice_lab_env_file_over_project_dot_env(self):
        """VOICE_LAB_ENV_FILE takes priority over project .env."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        # Create a temp env file
        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("TEST_VOICE_LAB_KEY=from_temp_env_file\n")
            temp_env_path = f.name

        try:
            # Set VOICE_LAB_ENV_FILE to temp env
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()

            value = resolve_env_value("TEST_VOICE_LAB_KEY")

            assert value == "from_temp_env_file", f"Expected 'from_temp_env_file' but got {value!r}"
        finally:
            os.unlink(temp_env_path)

    def test_missing_key_returns_none(self):
        """resolve_env_value returns None for non-existent keys."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        clear_env_cache()
        os.environ.pop("NONEXISTENT_KEY_12345", None)

        value = resolve_env_value("NONEXISTENT_KEY_12345")

        assert value is None

    def test_empty_string_from_environ(self):
        """Empty string from os.environ is returned (not treated as missing)."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        os.environ["TEST_EMPTY_STRING_KEY"] = ""
        clear_env_cache()

        value = resolve_env_value("TEST_EMPTY_STRING_KEY")

        assert value == ""
        os.environ.pop("TEST_EMPTY_STRING_KEY", None)


class TestVoiceLabEnvFile:
    """Tests for VOICE_LAB_ENV_FILE support."""

    def setup_method(self):
        """Clear cache before each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        os.environ.pop("TEST_VLF_KEY", None)

    def teardown_method(self):
        """Clean up after each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        os.environ.pop("TEST_VLF_KEY", None)

    def test_voice_lab_env_file_loads_key(self):
        """VOICE_LAB_ENV_FILE env file can be read for keys."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        # Create temp env file
        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("TEST_VLF_KEY=temp_env_value\n")
            temp_env_path = f.name

        try:
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()

            value = resolve_env_value("TEST_VLF_KEY")

            assert value == "temp_env_value"
        finally:
            os.unlink(temp_env_path)

    def test_voice_lab_env_file_nonexistent_does_not_crash(self):
        """VOICE_LAB_ENV_FILE pointing to non-existent file does not crash."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        os.environ["VOICE_LAB_ENV_FILE"] = "/nonexistent/path/to/env.file"
        clear_env_cache()

        # Should not raise, just return None
        value = resolve_env_value("ANY_KEY")
        assert value is None

    def test_voice_lab_env_file_caches_per_path(self):
        """Different VOICE_LAB_ENV_FILE paths are cached separately."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        # Create two temp env files with different values
        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f1:
            f1.write("TEST_CACHE_KEY=first_value\n")
            temp_env_path1 = f1.name

        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f2:
            f2.write("TEST_CACHE_KEY=second_value\n")
            temp_env_path2 = f2.name

        try:
            # First file
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path1
            clear_env_cache()
            value1 = resolve_env_value("TEST_CACHE_KEY")
            assert value1 == "first_value"

            # Second file
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path2
            clear_env_cache()
            value2 = resolve_env_value("TEST_CACHE_KEY")
            assert value2 == "second_value"
        finally:
            os.unlink(temp_env_path1)
            os.unlink(temp_env_path2)


class TestClearEnvCache:
    """Tests for clear_env_cache functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()
        os.environ.pop("TEST_CACHE_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)

    def teardown_method(self):
        """Clean up after each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()
        os.environ.pop("TEST_CACHE_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)

    def test_clear_cache_allows_reload_of_changed_file(self):
        """clear_env_cache allows reloading changed env files."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("TEST_CACHE_KEY=original_value\n")
            temp_env_path = f.name

        try:
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()

            value1 = resolve_env_value("TEST_CACHE_KEY")
            assert value1 == "original_value"

            # Modify the file
            with open(temp_env_path, "w", encoding="utf-8") as f:
                f.write("TEST_CACHE_KEY=modified_value\n")

            # Without clearing cache, should still see old value (cached)
            value2 = resolve_env_value("TEST_CACHE_KEY")
            assert value2 == "original_value", "Should still return cached value"

            # After clearing cache, should see new value
            clear_env_cache()
            value3 = resolve_env_value("TEST_CACHE_KEY")
            assert value3 == "modified_value"
        finally:
            os.unlink(temp_env_path)


class TestEnvFileFormats:
    """Tests for various .env file formats."""

    def setup_method(self):
        """Clear cache before each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()
        os.environ.pop("SIMPLE_KEY", None)
        os.environ.pop("QUOTED_KEY", None)
        os.environ.pop("SINGLE_QUOTED_KEY", None)
        os.environ.pop("COMMENT_KEY", None)
        os.environ.pop("EMPTY_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)

    def teardown_method(self):
        """Clean up after each test."""
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()
        os.environ.pop("SIMPLE_KEY", None)
        os.environ.pop("QUOTED_KEY", None)
        os.environ.pop("SINGLE_QUOTED_KEY", None)
        os.environ.pop("COMMENT_KEY", None)
        os.environ.pop("EMPTY_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)

    def test_simple_key_value(self):
        """Simple KEY=value format."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("SIMPLE_KEY=simple_value\n")
            temp_env_path = f.name

        try:
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()
            assert resolve_env_value("SIMPLE_KEY") == "simple_value"
        finally:
            os.unlink(temp_env_path)

    def test_double_quoted_value(self):
        """KEY="value" format."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write('QUOTED_KEY="quoted_value"\n')
            temp_env_path = f.name

        try:
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()
            assert resolve_env_value("QUOTED_KEY") == "quoted_value"
        finally:
            os.unlink(temp_env_path)

    def test_single_quoted_value(self):
        """KEY='value' format."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("SINGLE_QUOTED_KEY='single_quoted'\n")
            temp_env_path = f.name

        try:
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()
            assert resolve_env_value("SINGLE_QUOTED_KEY") == "single_quoted"
        finally:
            os.unlink(temp_env_path)

    def test_comment_lines_ignored(self):
        """Comment lines (#) are ignored."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("# This is a comment\n")
            f.write("COMMENT_KEY=comment_value\n")
            f.write("# Another comment\n")
            temp_env_path = f.name

        try:
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()
            assert resolve_env_value("COMMENT_KEY") == "comment_value"
        finally:
            os.unlink(temp_env_path)

    def test_empty_lines_ignored(self):
        """Empty lines are ignored."""
        from app.config.env_resolver import resolve_env_value, clear_env_cache

        with NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("\n")
            f.write("EMPTY_KEY=empty_value\n")
            f.write("\n")
            temp_env_path = f.name

        try:
            os.environ["VOICE_LAB_ENV_FILE"] = temp_env_path
            clear_env_cache()
            assert resolve_env_value("EMPTY_KEY") == "empty_value"
        finally:
            os.unlink(temp_env_path)
