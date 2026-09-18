"""Provider boundary tests with synthetic responses, not model benchmarks."""

import json
import unittest
from unittest.mock import patch

from thread_agent.domain.records import AgentError
from thread_agent.providers.ollama.client import Ollama


class OllamaTests(unittest.TestCase):
    def invoke(self, content='{"pointer":"/database/default"}', **changes):
        response = {"done": True, "done_reason": "stop", "message": {"content": content}, **changes}
        client = Ollama("test:local")
        records = []
        replies = [
            ({"models": [{"name": "test:local", "digest": "fixture-digest"}]}, "{}"),
            ({"capabilities": ["completion"], "template": "fixture"}, "{}"),
            ({"version": "fixture-version"}, "{}"),
            (response, json.dumps(response)),
        ]
        with patch.object(client, "request", side_effect=replies) as request:
            result = client.suggest("Which database?", ["/database/default"], records.append)
        return result, records, request

    def test_success_records_exact_input_and_raw_output(self):
        result, records, request = self.invoke()
        self.assertEqual("/database/default", result)
        self.assertEqual(["model_request", "model_response"], [r["type"] for r in records])
        self.assertEqual(records[0]["request"], json.loads(records[0]["serialized_input"]))
        self.assertIn('"pointer"', records[1]["raw_output"].replace('\\"', '"'))
        self.assertIsNone(records[1]["usage"]["eval_count"])
        payload = request.call_args.args[1]
        self.assertNotIn("tools", payload)
        self.assertFalse(payload["stream"])

    def test_none_is_not_forced_to_a_field(self):
        result, _, _ = self.invoke('{"pointer":null}')
        self.assertIsNone(result)

    def test_invalid_output_rejected(self):
        for content in ["not json", '{"pointer":"/invented"}', '{"pointer":null,"extra":1}', "[]"]:
            with self.subTest(content=content), self.assertRaises(AgentError):
                self.invoke(content)
        for changes in [
            {"done": False},
            {"done_reason": "length"},
            {"message": {"content": "{}", "tool_calls": [{"name": "write"}]}},
        ]:
            with self.subTest(changes=changes), self.assertRaises(AgentError):
                self.invoke(**changes)

    def test_nonlocal_endpoints_and_credentials_rejected(self):
        for endpoint in [
            "https://api.example.com",
            "http://localhost:11434",
            "http://127.0.0.1@evil.test",
            "http://127.0.0.1/path",
            "http://user:secret@127.0.0.1",
            "http://127.0.0.1?x=1",
        ]:
            with self.subTest(endpoint=endpoint), self.assertRaises(AgentError):
                Ollama("test", endpoint)

    def test_cloud_model_and_embedding_model_rejected_before_inference(self):
        client = Ollama("test-cloud")
        with patch.object(client, "inventory", return_value=[{"name": "test-cloud"}]):
            with self.assertRaises(AgentError):
                client.suggest("question", ["/x"], lambda _: None)
        client = Ollama("test")
        with patch.object(client, "inventory", return_value=[{"name": "test"}]):
            for metadata in [{"remote_host": "external"}, {"capabilities": ["embedding"]}]:
                with patch.object(client, "request", return_value=(metadata, "{}")):
                    with self.assertRaises(AgentError):
                        client.suggest("question", ["/x"], lambda _: None)

    def test_http_redirect_never_followed(self):
        client = Ollama("test")
        with patch("thread_agent.providers.ollama.client.http.client.HTTPConnection") as connection:
            connection.return_value.getresponse.return_value.status = 302
            with self.assertRaises(AgentError):
                client.inventory()
            self.assertEqual(1, connection.call_count)
