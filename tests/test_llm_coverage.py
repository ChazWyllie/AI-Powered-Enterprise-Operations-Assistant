"""Targeted coverage tests for LLM module (WP6).

Covers OpenAILLM initialization, error fallback, and stub edge cases.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

from app.llm import LLMResponse, LLMStub, OpenAILLM


class TestOpenAILLMInit:
    """Tests for OpenAILLM initialization and client management."""

    def test_init_with_explicit_key(self):
        """OpenAILLM accepts explicit API key."""
        llm = OpenAILLM(api_key="test-key", model="gpt-4")
        assert llm.api_key == "test-key"
        assert llm.model == "gpt-4"
        assert llm._client is None

    def test_init_reads_env_key(self):
        """OpenAILLM falls back to env variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            llm = OpenAILLM()
            assert llm.api_key == "env-key"

    def test_init_no_key(self):
        """OpenAILLM handles missing API key gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("OPENAI_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                llm = OpenAILLM()
                assert llm.api_key is None

    def test_custom_model(self):
        """OpenAILLM accepts custom model name."""
        llm = OpenAILLM(api_key="test", model="gpt-3.5-turbo")
        assert llm.model == "gpt-3.5-turbo"

    def test_get_client_lazy_init(self):
        """Client is lazily initialized."""
        llm = OpenAILLM(api_key="test-key")
        assert llm._client is None
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = llm._get_client()
            assert client is not None
            mock_cls.assert_called_once_with(api_key="test-key")

    def test_get_client_reuses_existing(self):
        """Client is reused on subsequent calls."""
        llm = OpenAILLM(api_key="test-key")
        mock_client = MagicMock()
        llm._client = mock_client
        assert llm._get_client() is mock_client


class TestOpenAILLMGenerate:
    """Tests for OpenAILLM generate method."""

    async def test_generate_success_no_tools(self):
        """OpenAILLM returns answer without tool calls."""
        llm = OpenAILLM(api_key="test-key")

        mock_choice = MagicMock()
        mock_choice.message.content = "System looks healthy"
        mock_choice.message.tool_calls = None

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        llm._client = mock_client

        result = await llm.generate("Check status")
        assert isinstance(result, LLMResponse)
        assert result.answer == "System looks healthy"
        assert result.tool_calls == []

    async def test_generate_success_with_tools(self):
        """OpenAILLM parses tool calls from response."""
        llm = OpenAILLM(api_key="test-key")

        mock_tc = MagicMock()
        mock_tc.function.name = "get_system_status"
        mock_tc.function.arguments = '{"verbose": true}'

        mock_choice = MagicMock()
        mock_choice.message.content = "Let me check"
        mock_choice.message.tool_calls = [mock_tc]

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        llm._client = mock_client

        result = await llm.generate("Check status")
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool == "get_system_status"
        assert result.tool_calls[0].args == {"verbose": True}

    async def test_generate_empty_content(self):
        """OpenAILLM handles None content."""
        llm = OpenAILLM(api_key="test-key")

        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_choice.message.tool_calls = None

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        llm._client = mock_client

        result = await llm.generate("test")
        assert result.answer == ""

    async def test_generate_api_error_falls_back_to_stub(self):
        """OpenAILLM falls back to stub on API error."""
        llm = OpenAILLM(api_key="test-key")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API rate limit"))
        llm._client = mock_client

        result = await llm.generate("Check status")
        # Should fall back to stub and return a valid response
        assert isinstance(result, LLMResponse)
        assert len(result.answer) > 0
        assert len(result.tool_calls) > 0


class TestOpenAILLMHelpers:
    """Tests for OpenAILLM helper methods."""

    def test_build_system_prompt(self):
        """System prompt is well-formed."""
        llm = OpenAILLM(api_key="test")
        prompt = llm._build_system_prompt()
        assert "operations assistant" in prompt.lower()
        assert "get_logs" in prompt
        assert "get_system_status" in prompt
        assert "run_command" in prompt
        assert "update_config" in prompt

    def test_get_tool_definitions(self):
        """Tool definitions are well-formed."""
        llm = OpenAILLM(api_key="test")
        tools = llm._get_tool_definitions()
        assert len(tools) == 4
        tool_names = {t["function"]["name"] for t in tools}
        assert tool_names == {"get_logs", "get_system_status", "run_command", "update_config"}
        for tool in tools:
            assert tool["type"] == "function"
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


class TestLLMStubPatterns:
    """Tests for LLM stub pattern matching edge cases."""

    async def test_config_intent_debug(self):
        """Config debug detection."""
        stub = LLMStub()
        response = await stub.generate("Set the config to debug mode")
        tool_names = [tc.tool for tc in response.tool_calls]
        assert "update_config" in tool_names

    async def test_config_intent_warn(self):
        """Config warn detection."""
        stub = LLMStub()
        response = await stub.generate("Change the setting to warn level")
        tool_names = [tc.tool for tc in response.tool_calls]
        assert "update_config" in tool_names

    async def test_config_intent_error_level(self):
        """Config error-level detection."""
        stub = LLMStub()
        response = await stub.generate("Update the level to error")
        tool_names = [tc.tool for tc in response.tool_calls]
        assert "update_config" in tool_names

    async def test_log_source_joblog(self):
        """Joblog detection."""
        stub = LLMStub()
        response = await stub.generate("Show me the job logs")
        log_calls = [tc for tc in response.tool_calls if tc.tool == "get_logs"]
        assert len(log_calls) > 0
        assert log_calls[0].args["source"] == "joblog"

    async def test_log_source_audit(self):
        """Audit log detection."""
        stub = LLMStub()
        response = await stub.generate("Show audit log entries")
        log_calls = [tc for tc in response.tool_calls if tc.tool == "get_logs"]
        assert len(log_calls) > 0
        assert log_calls[0].args["source"] == "audit"

    async def test_command_grep(self):
        """Grep command detection."""
        stub = LLMStub()
        response = await stub.generate("grep for errors in the file")
        cmd_calls = [tc for tc in response.tool_calls if tc.tool == "run_command"]
        assert len(cmd_calls) > 0
        assert "grep" in cmd_calls[0].args["command"]

    async def test_command_head(self):
        """Head command detection."""
        stub = LLMStub()
        response = await stub.generate("Show me the head of the file")
        cmd_calls = [tc for tc in response.tool_calls if tc.tool == "run_command"]
        assert len(cmd_calls) > 0
        assert "head" in cmd_calls[0].args["command"]

    async def test_command_tail(self):
        """Tail command detection."""
        stub = LLMStub()
        response = await stub.generate("Show me the tail of the file")
        cmd_calls = [tc for tc in response.tool_calls if tc.tool == "run_command"]
        assert len(cmd_calls) > 0
        assert "tail" in cmd_calls[0].args["command"]

    async def test_command_cat(self):
        """Cat command detection."""
        stub = LLMStub()
        response = await stub.generate("Please cat this file")
        cmd_calls = [tc for tc in response.tool_calls if tc.tool == "run_command"]
        assert len(cmd_calls) > 0
        assert "cat" in cmd_calls[0].args["command"]

    async def test_no_intent_defaults_to_status(self):
        """No matching intent defaults to status check."""
        stub = LLMStub()
        response = await stub.generate("hello world foobar baz")
        assert len(response.tool_calls) > 0
        assert response.tool_calls[0].tool == "get_system_status"
