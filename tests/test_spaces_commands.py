import json

from typer.testing import CliRunner

from ax_cli.main import app

runner = CliRunner()


def test_spaces_use_accepts_slug_and_warns_when_bound_agent_not_attached(monkeypatch):
    saved = {}

    class FakeClient:
        def list_spaces(self):
            return {
                "spaces": [
                    {"id": "private-space", "slug": "madtank-workspace", "name": "madtank's Workspace"},
                    {"id": "team-space", "slug": "ax-cli-dev", "name": "aX CLI Dev"},
                ]
            }

        def whoami(self):
            return {
                "bound_agent": {
                    "agent_name": "orion",
                    "allowed_spaces": [{"space_id": "private-space", "name": "madtank's Workspace"}],
                }
            }

    def fake_save_space_id(space_id, *, local=True):
        saved["space_id"] = space_id
        saved["local"] = local

    monkeypatch.setattr("ax_cli.commands.spaces.get_client", lambda: FakeClient())
    monkeypatch.setattr("ax_cli.commands.spaces.save_space_id", fake_save_space_id)

    result = runner.invoke(app, ["spaces", "use", "ax-cli-dev", "--json"])

    assert result.exit_code == 0, result.output
    assert saved == {"space_id": "team-space", "local": True}
    payload = json.loads(result.output)
    assert payload["space_id"] == "team-space"
    assert payload["space_label"] == "ax-cli-dev"
    assert payload["scope"] == "local"
    assert payload["bound_agent"] == "orion"
    assert payload["bound_agent_allowed"] is False


def test_spaces_use_global_saves_global_config(monkeypatch):
    saved = {}

    class FakeClient:
        def list_spaces(self):
            return {"spaces": [{"id": "team-space", "slug": "ax-cli-dev", "name": "aX CLI Dev"}]}

        def whoami(self):
            return {}

    def fake_save_space_id(space_id, *, local=True):
        saved["space_id"] = space_id
        saved["local"] = local

    monkeypatch.setattr("ax_cli.commands.spaces.get_client", lambda: FakeClient())
    monkeypatch.setattr("ax_cli.commands.spaces.save_space_id", fake_save_space_id)

    result = runner.invoke(app, ["spaces", "use", "ax-cli-dev", "--global", "--json"])

    assert result.exit_code == 0, result.output
    assert saved == {"space_id": "team-space", "local": False}
    assert json.loads(result.output)["scope"] == "global"


def test_spaces_join_redeems_invite_json(monkeypatch):
    calls = {}

    class FakeClient:
        def join_space_with_invite(self, code):
            calls["code"] = code
            return {
                "space": {
                    "id": "space-invited",
                    "slug": "qa-lab",
                    "name": "QA Lab",
                    "visibility": "invite_only",
                }
            }

    monkeypatch.setattr("ax_cli.commands.spaces.get_client", lambda: FakeClient())

    result = runner.invoke(app, ["spaces", "join", " 9UZ8ZEPRTNHG ", "--json"])
    assert result.exit_code == 0, result.output
    assert calls["code"] == "9UZ8ZEPRTNHG"
    payload = json.loads(result.output)
    assert payload["space_id"] == "space-invited"
    assert payload["space_slug"] == "qa-lab"
    assert payload["space_name"] == "QA Lab"
    assert payload["invite_code"] == "9UZ8ZEPRTNHG"
    assert payload["used_as_current"] is False


def test_spaces_join_use_saves_local_space(monkeypatch):
    saved = {}

    class FakeClient:
        def join_space_with_invite(self, code):
            return {"space": {"id": "new-space", "slug": "joined", "name": "Joined"}}

        def whoami(self):
            return {}

    def fake_save_space_id(space_id, *, local=True):
        saved["space_id"] = space_id
        saved["local"] = local

    monkeypatch.setattr("ax_cli.commands.spaces.get_client", lambda: FakeClient())
    monkeypatch.setattr("ax_cli.commands.spaces.save_space_id", fake_save_space_id)

    result = runner.invoke(app, ["spaces", "join", "CODE", "--use", "--json"])
    assert result.exit_code == 0, result.output
    assert saved == {"space_id": "new-space", "local": True}
    assert json.loads(result.output)["used_as_current"] is True
    assert json.loads(result.output)["scope"] == "local"


def test_spaces_join_rejects_blank_invite():
    result = runner.invoke(app, ["spaces", "join", "   "])
    assert result.exit_code == 1
    assert "empty" in result.output.lower()
