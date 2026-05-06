import io
import importlib.util
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


MODULE_PATH = Path(__file__).with_name("git-commit-ai.py")
SPEC = importlib.util.spec_from_file_location("git_commit_ai_module", MODULE_PATH)
git_commit_ai = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(git_commit_ai)


class CallLlmFallbackTests(unittest.TestCase):
    def _config_side_effect(self, key):
        config = {
            "LLM_HOST": "https://api.example.com",
            "MODEL_NAME": "primary-model",
            "FALLBACK_MODEL": "fallback-model",
            "COMMIT_API_KEY": "test-key",
        }
        return config.get(key)

    @patch.object(git_commit_ai, "get_config_value")
    @patch.object(git_commit_ai.requests, "post")
    def test_primary_model_success_path(self, mock_post, mock_get_config_value):
        mock_get_config_value.side_effect = self._config_side_effect
        success_response = Mock()
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = {
            "choices": [{"message": {"content": 'feat: add fallback support'}}]
        }
        mock_post.return_value = success_response

        result = git_commit_ai.call_llm("diff content")

        self.assertEqual(result, "feat: add fallback support")
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args.kwargs["json"]["model"], "primary-model")

    @patch.object(git_commit_ai, "get_config_value")
    @patch.object(git_commit_ai.requests, "post")
    def test_primary_failure_then_fallback_success(self, mock_post, mock_get_config_value):
        mock_get_config_value.side_effect = self._config_side_effect

        primary_response = Mock()
        primary_response.raise_for_status.side_effect = RuntimeError("primary failed")
        fallback_response = Mock()
        fallback_response.raise_for_status.return_value = None
        fallback_response.json.return_value = {
            "choices": [{"message": {"content": "fix: use fallback model"}}]
        }
        mock_post.side_effect = [primary_response, fallback_response]

        result = git_commit_ai.call_llm("diff content")

        self.assertEqual(result, "fix: use fallback model")
        self.assertEqual(mock_post.call_count, 2)
        first_model = mock_post.call_args_list[0].kwargs["json"]["model"]
        second_model = mock_post.call_args_list[1].kwargs["json"]["model"]
        self.assertEqual(first_model, "primary-model")
        self.assertEqual(second_model, "fallback-model")

    @patch.object(git_commit_ai, "get_config_value")
    @patch.object(git_commit_ai.requests, "post")
    def test_primary_and_fallback_fail(self, mock_post, mock_get_config_value):
        mock_get_config_value.side_effect = self._config_side_effect

        primary_response = Mock()
        primary_response.raise_for_status.side_effect = RuntimeError("primary failed")
        fallback_response = Mock()
        fallback_response.raise_for_status.side_effect = RuntimeError("fallback failed")
        mock_post.side_effect = [primary_response, fallback_response]

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit):
                git_commit_ai.call_llm("diff content")

        output = stdout.getvalue()
        self.assertIn("Both primary and fallback model attempts failed", output)
        self.assertIn("primary failed", output)
        self.assertIn("fallback failed", output)


if __name__ == "__main__":
    unittest.main()
