"""ax spaces — list, create, join via invite, and manage spaces."""

from typing import Optional

import httpx
import typer

from ..config import get_client, resolve_gateway_config, resolve_space_id, save_space_id
from ..output import JSON_OPTION, console, handle_error, print_json, print_kv, print_table

app = typer.Typer(name="spaces", help="Space management", no_args_is_help=True)


def _space_items(result: object) -> list[dict]:
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if not isinstance(result, dict):
        return []
    for key in ("spaces", "items", "results"):
        items = result.get(key)
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _space_label(space: dict, fallback: str) -> str:
    return str(space.get("slug") or space.get("name") or space.get("space_name") or fallback)


def _find_space(client, space_id: str) -> dict | None:
    try:
        for space in _space_items(client.list_spaces()):
            sid = str(space.get("id") or space.get("space_id") or "")
            if sid == space_id:
                return space
    except Exception:
        return None
    return None


def _bound_agent_allows_space(client, space_id: str) -> tuple[bool | None, str | None]:
    try:
        me = client.whoami()
    except Exception:
        return None, None
    bound = me.get("bound_agent") if isinstance(me, dict) else None
    if not isinstance(bound, dict) or not bound:
        return None, None
    agent_name = str(bound.get("agent_name") or bound.get("name") or "bound agent")
    allowed_spaces = bound.get("allowed_spaces")
    if not isinstance(allowed_spaces, list):
        return None, agent_name
    allowed_ids = {
        str(item.get("space_id") or item.get("id") or "")
        for item in allowed_spaces
        if isinstance(item, dict) and str(item.get("space_id") or item.get("id") or "")
    }
    return space_id in allowed_ids, agent_name


@app.command("list")
def list_spaces(
    as_json: bool = JSON_OPTION,
):
    """List all spaces you belong to."""
    gateway_cfg = resolve_gateway_config()
    if gateway_cfg:
        from .messages import _gateway_local_call

        spaces = _gateway_local_call(gateway_cfg=gateway_cfg, method="list_spaces")
    else:
        client = get_client()
        try:
            spaces = client.list_spaces()
        except httpx.HTTPStatusError as e:
            handle_error(e)
    if not isinstance(spaces, list):
        spaces = spaces.get("spaces", spaces.get("items", []))
    if as_json:
        print_json(spaces)
    else:
        print_table(
            ["ID", "Name", "Visibility", "Members"],
            spaces,
            keys=["id", "name", "visibility", "member_count"],
        )


@app.command("create")
def create(
    name: str = typer.Argument(..., help="Space name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Space description"),
    visibility: str = typer.Option("private", "--visibility", "-v", help="private, invite_only, or public"),
    as_json: bool = JSON_OPTION,
):
    """Create a new space."""
    client = get_client()
    try:
        result = client.create_space(name, description=description, visibility=visibility)
    except httpx.HTTPStatusError as e:
        handle_error(e)
    space = result.get("space", result) if isinstance(result, dict) else result
    if as_json:
        print_json(space)
    else:
        console.print(
            f"[green]Created:[/green] {space.get('name')} (id={str(space.get('id', ''))[:8]}…, visibility={space.get('visibility')})"
        )


@app.command("join")
def join_space(
    invite_code: str = typer.Argument(..., help="Space invite code from the inviter"),
    use: bool = typer.Option(False, "--use", help="Set joined space as the CLI current space"),
    global_config: bool = typer.Option(
        False, "--global", help="With --use: save default space to global config instead of local .ax/config.toml"
    ),
    as_json: bool = JSON_OPTION,
):
    """Redeem a space invite and join that space."""
    code = invite_code.strip()
    if not code:
        console.print("[red]Invite code cannot be empty.[/red]")
        raise typer.Exit(1)

    client = get_client()
    try:
        result = client.join_space_with_invite(code)
    except httpx.HTTPStatusError as e:
        handle_error(e)

    raw_space = result.get("space") if isinstance(result.get("space"), dict) else None
    space = raw_space if raw_space is not None else (result if isinstance(result, dict) else {})
    sid = str(space.get("id") or space.get("space_id") or result.get("space_id") or "")
    label = _space_label(space, sid) if space else sid

    if use and not sid:
        msg = (
            "Join succeeded but the response had no space id; cannot apply --use. "
            "Run `ax spaces list`, then `ax spaces use` with the new space when it appears."
        )
        if as_json:
            print_json(
                {
                    "error": "join_missing_space_id",
                    "message": msg,
                    "used_as_current": False,
                }
            )
        else:
            console.print(f"[red]{msg}[/red]")
        raise typer.Exit(1)

    allowed: bool | None = None
    agent_name: str | None = None
    if use and sid:
        save_space_id(sid, local=not global_config)
        allowed, agent_name = _bound_agent_allows_space(client, sid)

    payload = {
        "space_id": sid or None,
        "space_slug": space.get("slug") if space else None,
        "space_name": space.get("name") if space else None,
        "visibility": space.get("visibility") if space else None,
        "used_as_current": use,
        "scope": ("global" if global_config else "local") if use else None,
        "bound_agent": agent_name,
        "bound_agent_allowed": allowed,
    }
    if as_json:
        print_json(payload)
        return

    if sid:
        console.print(f"[green]Joined space:[/green] {label} (id={sid})")
    else:
        console.print("[green]Invite redeemed.[/green]")
    if use and sid:
        console.print(
            f"[dim]Saved current space to {'global config' if global_config else 'local .ax/config.toml'}.[/dim]"
        )
        if allowed is False and agent_name:
            console.print(
                f"[yellow]Warning:[/yellow] @{agent_name} is not attached to this space; agent-authored writes may be rejected."
            )
    console.print(
        "[dim]If `ax spaces list` does not show the new space yet, cached JWT claims may be stale — try again shortly or re-exchange your PAT.[/dim]"
    )


@app.command("use")
def use_space(
    space: str = typer.Argument(..., help="Space id, slug, or name to make current"),
    global_config: bool = typer.Option(
        False, "--global", help="Save to global config instead of local .ax/config.toml"
    ),
    as_json: bool = JSON_OPTION,
):
    """Set the current CLI space by id, slug, or name."""
    client = get_client()
    sid = resolve_space_id(client, explicit=space)
    space_row = _find_space(client, sid) or {}
    label = _space_label(space_row, sid)
    save_space_id(sid, local=not global_config)
    allowed, agent_name = _bound_agent_allows_space(client, sid)
    result = {
        "space_id": sid,
        "space_label": label,
        "scope": "global" if global_config else "local",
        "bound_agent": agent_name,
        "bound_agent_allowed": allowed,
    }
    if as_json:
        print_json(result)
        return
    console.print(f"[green]Current space:[/green] {label}")
    console.print(f"[dim]Saved to {'global config' if global_config else 'local .ax/config.toml'}.[/dim]")
    if allowed is False and agent_name:
        console.print(
            f"[yellow]Warning:[/yellow] @{agent_name} is not attached to this space; agent-authored writes may be rejected."
        )


@app.command("get")
def get_space(
    space_id: str = typer.Argument(..., help="Space ID"),
    as_json: bool = JSON_OPTION,
):
    """Get space details."""
    client = get_client()
    try:
        data = client.get_space(space_id)
    except httpx.HTTPStatusError as e:
        handle_error(e)
    if as_json:
        print_json(data)
    else:
        print_kv(data)


@app.command("members")
def members(
    space_id: Optional[str] = typer.Argument(None, help="Space ID (default: current space)"),
    as_json: bool = JSON_OPTION,
):
    """List members of a space."""
    client = get_client()
    sid = space_id or resolve_space_id(client)
    try:
        data = client.list_space_members(sid)
    except httpx.HTTPStatusError as e:
        handle_error(e)
    members_list = data if isinstance(data, list) else data.get("members", [])
    if as_json:
        print_json(members_list)
    else:
        print_table(
            ["User", "Role"],
            members_list,
            keys=["username", "role"],
        )
