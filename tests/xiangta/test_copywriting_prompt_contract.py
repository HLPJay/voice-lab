"""
P18-XIANGTA-LLM-PROMPT-CONTRACT-C10C — Prompt contract tests.

Covers:
1. PromptContractInput / PromptContract / PromptMessage dataclasses
2. build_copywriting_prompt_contract returns PromptContract
3. messages contain system + user
4. prompt includes recipient / scene / raw_text
5. prompt includes restrained / gentle / sincere
6. expected schema has exactly 3 suggestions
7. output schema excludes forbidden fields
8. 10 offline eval cases are present and complete
9. validate_prompt_contract_static returns [] for valid contract
10. static validator catches missing JSON requirement
"""
import pytest

from src.xiangta.services.copywriting_prompt_contract import (
    CONTRACT_VERSION,
    EXPECTED_JSON_SCHEMA,
    GLOBAL_SAFETY_RULES,
    OFFLINE_EVAL_CASES,
    RECIPIENT_BOUNDARIES,
    SCENE_EMOTION_RULES,
    STYLE_OUTPUT_RULES,
    TTS_FRIENDLY_RULES,
    PromptContract,
    PromptContractInput,
    PromptMessage,
    build_copywriting_prompt_contract,
    build_offline_eval_cases,
    validate_prompt_contract_static,
)


class TestPromptContractDataclasses:

    def test_contract_version_exists(self):
        assert CONTRACT_VERSION == "1.0"

    def test_prompt_contract_input_fields(self):
        inp = PromptContractInput(recipient="lover", scene="miss", raw_text="很想你")
        assert inp.recipient == "lover"
        assert inp.scene == "miss"
        assert inp.raw_text == "很想你"
        assert inp.max_suggestions == 3

    def test_prompt_contract_input_custom_max(self):
        inp = PromptContractInput(recipient="friend", scene="thanks", raw_text="谢谢", max_suggestions=5)
        assert inp.max_suggestions == 5

    def test_prompt_message_fields(self):
        msg = PromptMessage(role="system", content="hello")
        assert msg.role == "system"
        assert msg.content == "hello"

    def test_prompt_contract_fields(self):
        contract = PromptContract(
            version="1.0",
            messages=[PromptMessage(role="user", content="test")],
            expected_json_schema={},
            evaluation_notes={},
        )
        assert contract.version == "1.0"
        assert len(contract.messages) == 1
        assert contract.expected_json_schema == {}
        assert contract.evaluation_notes == {}


class TestRecipientAndSceneRules:

    def test_recipient_boundaries_has_all_four(self):
        assert set(RECIPIENT_BOUNDARIES.keys()) == {"lover", "family", "friend", "self"}

    def test_scene_emotion_rules_has_all_five(self):
        assert set(SCENE_EMOTION_RULES.keys()) == {"miss", "sorry", "thanks", "comfort", "night"}

    def test_each_scene_has_goal_and_avoid(self):
        for scene, rule in SCENE_EMOTION_RULES.items():
            assert "goal" in rule
            assert "should_include" in rule
            assert "should_avoid" in rule
            assert "suitable_tones" in rule
            assert rule["goal"]
            assert rule["should_avoid"]

    def test_style_rules_has_all_three(self):
        assert set(STYLE_OUTPUT_RULES.keys()) == {"restrained", "gentle", "sincere"}

    def test_each_style_has_goal_and_avoid(self):
        for style, rule in STYLE_OUTPUT_RULES.items():
            assert "goal" in rule
            assert "language" in rule
            assert "avoid" in rule
            assert "scenes" in rule

    def test_safety_rules_not_empty(self):
        assert len(GLOBAL_SAFETY_RULES) > 100
        assert "禁止" in GLOBAL_SAFETY_RULES

    def test_tts_rules_not_empty(self):
        assert len(TTS_FRIENDLY_RULES) > 50
        assert "TTS" in TTS_FRIENDLY_RULES


class TestBuildPromptContract:

    def _make_input(self, **kwargs):
        defaults = dict(recipient="lover", scene="miss", raw_text="很想你")
        defaults.update(kwargs)
        return PromptContractInput(**defaults)

    def test_returns_prompt_contract(self):
        inp = self._make_input()
        result = build_copywriting_prompt_contract(inp)
        assert isinstance(result, PromptContract)
        assert result.version == CONTRACT_VERSION

    def test_messages_contains_system_and_user(self):
        inp = self._make_input()
        result = build_copywriting_prompt_contract(inp)
        roles = {m.role for m in result.messages}
        assert "system" in roles
        assert "user" in roles

    def test_system_message_contains_product_context(self):
        inp = self._make_input()
        result = build_copywriting_prompt_contract(inp)
        system = next(m.content for m in result.messages if m.role == "system")
        assert "想Ta了" in system or "情绪表达" in system

    def test_system_message_contains_safety_rules(self):
        inp = self._make_input()
        result = build_copywriting_prompt_contract(inp)
        system = next(m.content for m in result.messages if m.role == "system")
        assert "安全禁止项" in system or "禁止" in system

    def test_system_message_contains_tts_rules(self):
        inp = self._make_input()
        result = build_copywriting_prompt_contract(inp)
        system = next(m.content for m in result.messages if m.role == "system")
        assert "TTS" in system or "朗读" in system

    def test_user_message_contains_recipient(self):
        inp = self._make_input(recipient="family")
        result = build_copywriting_prompt_contract(inp)
        user = next(m.content for m in result.messages if m.role == "user")
        assert "family" in user.lower()

    def test_user_message_contains_scene(self):
        inp = self._make_input(scene="sorry")
        result = build_copywriting_prompt_contract(inp)
        user = next(m.content for m in result.messages if m.role == "user")
        assert "sorry" in user.lower()

    def test_user_message_contains_raw_text(self):
        inp = self._make_input(raw_text="我很后悔")
        result = build_copywriting_prompt_contract(inp)
        user = next(m.content for m in result.messages if m.role == "user")
        assert "我很后悔" in user

    def test_prompt_includes_all_three_styles(self):
        inp = self._make_input()
        result = build_copywriting_prompt_contract(inp)
        content = " ".join(m.content for m in result.messages)
        assert "restrained" in content
        assert "gentle" in content
        assert "sincere" in content

    def test_contract_has_expected_json_schema(self):
        inp = self._make_input()
        result = build_copywriting_prompt_contract(inp)
        assert result.expected_json_schema is EXPECTED_JSON_SCHEMA

    def test_schema_has_three_suggestions(self):
        suggestions_schema = EXPECTED_JSON_SCHEMA["properties"]["suggestions"]
        assert suggestions_schema["minItems"] == 3
        assert suggestions_schema["maxItems"] == 3

    def test_schema_excludes_forbidden_fields(self):
        schema_str = str(EXPECTED_JSON_SCHEMA)
        forbidden = ["apiKey", "coreProfileId", "providerRawResponse", "rawResponse"]
        for f in forbidden:
            assert f not in schema_str


class TestOfflineEvalCases:

    def test_offline_eval_cases_returns_list(self):
        cases = build_offline_eval_cases()
        assert isinstance(cases, list)

    def test_exactly_10_cases(self):
        cases = build_offline_eval_cases()
        assert len(cases) == 10

    def test_all_cases_have_required_fields(self):
        required = {"case_id", "recipient", "scene", "raw_text", "expected_effect",
                    "must_avoid", "expected_styles", "suggested_tone", "manual_eval_notes"}
        cases = build_offline_eval_cases()
        for case in cases:
            assert required.issubset(case.keys()), f"case {case.get('case_id')} missing fields"

    def test_all_c10b_cases_present(self):
        cases = build_offline_eval_cases()
        case_ids = {c["case_id"] for c in cases}
        assert case_ids == {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

    def test_all_recipients_present(self):
        cases = build_offline_eval_cases()
        recipients = {c["recipient"] for c in cases}
        assert recipients == {"lover", "family", "friend", "self"}

    def test_all_scenes_present(self):
        cases = build_offline_eval_cases()
        scenes = {c["scene"] for c in cases}
        assert scenes == {"miss", "sorry", "thanks", "comfort", "night"}

    def test_key_cases_have_expected_styles(self):
        cases = {c["case_id"]: c for c in build_offline_eval_cases()}
        # lover + miss should have gentle/sincere
        assert "gentle" in cases[1]["expected_styles"]
        # lover + sorry should have sincere/restrained
        assert "sincere" in cases[2]["expected_styles"]
        # family + sorry should have restrained/sincere
        assert "restrained" in cases[5]["expected_styles"]


class TestStaticValidator:

    def test_valid_contract_returns_empty_list(self):
        from src.xiangta.services.copywriting_prompt_contract import build_copywriting_prompt_contract
        inp = PromptContractInput(recipient="lover", scene="miss", raw_text="很想你")
        contract = build_copywriting_prompt_contract(inp)
        errors = validate_prompt_contract_static(contract)
        assert errors == []

    def test_empty_messages_returns_error(self):
        contract = PromptContract(
            version="1.0",
            messages=[],
            expected_json_schema={},
            evaluation_notes={},
        )
        errors = validate_prompt_contract_static(contract)
        assert any("empty" in e.lower() for e in errors)

    def test_missing_system_message_returns_error(self):
        contract = PromptContract(
            version="1.0",
            messages=[PromptMessage(role="user", content="hello")],
            expected_json_schema={},
            evaluation_notes={},
        )
        errors = validate_prompt_contract_static(contract)
        assert any("system" in e.lower() for e in errors)

    def test_missing_user_message_returns_error(self):
        contract = PromptContract(
            version="1.0",
            messages=[PromptMessage(role="system", content="hello")],
            expected_json_schema={},
            evaluation_notes={},
        )
        errors = validate_prompt_contract_static(contract)
        assert any("user" in e.lower() for e in errors)

    def test_forbidden_field_in_output_schema_returns_error(self):
        # Forbidden fields should not appear in the expected output schema
        contract = PromptContract(
            version="1.0",
            messages=[
                PromptMessage(role="system", content="helpful assistant"),
                PromptMessage(role="user", content="say hello"),
            ],
            expected_json_schema={"properties": {"apiKey": {"type": "string"}}},
            evaluation_notes={},
        )
        errors = validate_prompt_contract_static(contract)
        assert any("forbidden" in e.lower() or "apikey" in e.lower() for e in errors)

    def test_no_recipient_returns_error(self):
        # Build a contract with a user message that lacks "recipient"
        contract = PromptContract(
            version="1.0",
            messages=[
                PromptMessage(role="system", content="you are helpful"),
                PromptMessage(role="user", content="scene: miss, raw_text: hello"),
            ],
            expected_json_schema={},
            evaluation_notes={},
        )
        errors = validate_prompt_contract_static(contract)
        assert any("recipient" in e.lower() for e in errors)
