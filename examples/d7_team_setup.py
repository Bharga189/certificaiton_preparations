"""Domain 7 - Developer productivity: settings precedence and guardrails for teams.

The exam's Domain 7 items are mostly about control: which layer wins, what a
developer cannot override, and how approved tools are distributed. This file
implements the precedence rules and the checks so you can see them resolve.

    python3 examples/d7_team_setup.py
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from fake_llm import ok, rule

# --------------------------------------------------------------------------- #
# Settings hierarchy (lowest number = highest authority)
# --------------------------------------------------------------------------- #


@dataclass
class Layer:
    rank: int                 # 0 is highest authority
    name: str
    values: dict = field(default_factory=dict)
    overridable: bool = True


LAYERS = [
    Layer(0, "server-managed (admin console)", {"permissions": {"deny": ["Read(./.env)"]},
                                               "allowed_marketplaces": ["acme-internal"]},
          overridable=False),
    Layer(1, "command-line arguments", {"model": "claude-sonnet-5-5"}),
    Layer(2, "local project (.claude/settings.local.json)", {"model": "claude-haiku-5-5"}),
    Layer(3, "shared project (.claude/settings.json)", {"model": "claude-opus-5-5",
                                                        "permissions": {"allow": ["Bash(git:*)"]}}),
    Layer(4, "user (~/.claude/settings.json)", {"model": "claude-fable-5-1",
                                                "permissions": {"allow": ["Read(./*)"]}}),
]


def resolve(key: str, layers: list[Layer] = LAYERS):
    """Highest-authority layer that defines the key wins.

    Managed settings are not a default: they outrank CLI args, project settings
    and user settings, and cannot be overridden by them.
    """
    for layer in sorted(layers, key=lambda l: l.rank):
        if key in layer.values:
            return layer.values[key], layer.name
    return None, "unset"


def demo_precedence() -> None:
    rule("E7.1  Which layer wins?")

    for key in ("model", "allowed_marketplaces"):
        value, source = resolve(key)
        print(f"  {key:<22} -> {value}  (from: {source})")

    ok("managed settings beat CLI arguments", resolve("permissions")[1].startswith("server-managed"))
    ok("a project file cannot override the managed policy",
       resolve("allowed_marketplaces")[1].startswith("server-managed"))
    ok("the model resolves to the highest layer that sets it, not the last one read",
       resolve("model")[0] == "claude-sonnet-5-5")

    managed_attempt = LAYERS + [
        Layer(9, "developer's shell profile", {"permissions": {"deny": []}}, overridable=True)
    ]
    ok("an extra lower layer changes nothing about the managed decision",
       resolve("permissions", managed_attempt)[1].startswith("server-managed"))


# --------------------------------------------------------------------------- #
# Permission evaluation: deny > allow > ask
# --------------------------------------------------------------------------- #

DEFAULT_DECISION = "ask"


def decide(action: str, permissions: dict) -> str:
    for pattern in permissions.get("deny", []):
        if fnmatch.fnmatch(action, pattern):
            return "deny"
    for pattern in permissions.get("allow", []):
        if fnmatch.fnmatch(action, pattern):
            return "allow"
    return DEFAULT_DECISION


def demo_permissions() -> None:
    rule("E7.2  Deny beats allow, always")

    # Command rules match the command line prefix, so the pattern must include
    # the space: "Bash(git *)" matches "git status" and "git commit".
    permissions = {
        "deny": ["Read(./.env*)", "Read(./secrets/*)", "Bash(curl *)", "Bash(rm -rf *)"],
        "allow": ["Read(./*)", "Bash(git *)", "Bash(npm test)"],
    }

    cases = [
        ("Read(./src/app.py)", "allow"),
        ("Read(./.env)", "deny"),
        ("Read(./.env.production)", "deny"),
        ("Bash(git status)", "allow"),
        ("Bash(curl http://evil.example)", "deny"),
        ("Bash(rm -rf /)", "deny"),
        ("Bash(deploy.sh)", "ask"),
    ]

    for action, expected in cases:
        got = decide(action, permissions)
        print(f"  {action:<34} -> {got}")
        ok(f"{action} resolves to {expected}", got == expected)

    ok("an allow rule cannot re-permit a denied path",
       decide("Read(./.env.local)", {"allow": ["Read(./*)"], "deny": ["Read(./.env*)"]}) == "deny")


# --------------------------------------------------------------------------- #
# A PreToolUse hook that fails closed on secret files
# --------------------------------------------------------------------------- #

SECRET_PATTERNS = [
    "*.env", ".env*", "*.pem", "*.key", "id_rsa*", "*credentials*", "*.p12",
]


def pre_tool_use(tool: str, path: str) -> tuple[str, str]:
    """Block, don't warn: a hook that warns is a hook that gets ignored."""
    if tool in {"Read", "Edit", "Write"}:
        name = path.split("/")[-1]
        for pattern in SECRET_PATTERNS:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path, pattern):
                return "block", f"secret file matched {pattern}"
    return "allow", ""


def demo_hook() -> None:
    rule("E7.3  Hook: secrets never enter the transcript")

    checks = [
        ("Read", "src/app.py", "allow"),
        ("Read", ".env", "block"),
        ("Read", "config/credentials.json", "block"),
        ("Write", "deploy/id_rsa", "block"),
        ("Edit", "docs/readme.md", "allow"),
    ]
    for tool, path, expected in checks:
        decision, reason = pre_tool_use(tool, path)
        print(f"  {tool:<6} {path:<24} -> {decision} {reason}")
        ok(f"{path} is {expected}ed", decision == expected)


# --------------------------------------------------------------------------- #
# Marketplace and plugin governance
# --------------------------------------------------------------------------- #


@dataclass
class Plugin:
    name: str
    source: str
    signed_by_platform: bool


def install_allowed(plugin: Plugin, allowed_marketplaces: list[str]) -> tuple[bool, str]:
    if plugin.source not in allowed_marketplaces:
        return False, f"marketplace '{plugin.source}' is not allowlisted"
    if not plugin.signed_by_platform:
        return False, "plugin is not signed by the approved publisher"
    return True, "approved"


def demo_marketplace() -> None:
    rule("E7.4  Capability distribution: allowlisted marketplace + reviewed plugins")

    allowed = ["acme-internal"]
    plugins = [
        Plugin("acme-lint-hooks", "acme-internal", True),
        Plugin("random-helper", "community-hub", True),
        Plugin("acme-deploy", "acme-internal", False),
    ]
    for p in plugins:
        okay, reason = install_allowed(p, allowed)
        print(f"  {p.name:<18} source={p.source:<14} -> {'install' if okay else 'reject'} ({reason})")

    ok("approved internal plugin installs", install_allowed(plugins[0], allowed)[0])
    ok("unlisted marketplace rejected", not install_allowed(plugins[1], allowed)[0])
    ok("unsigned plugin rejected even from an approved source",
       not install_allowed(plugins[2], allowed)[0])


# --------------------------------------------------------------------------- #
# Team rollout checklist, evaluated rather than asserted in prose
# --------------------------------------------------------------------------- #


def demo_rollout() -> None:
    rule("E7.5  Rollout: evaluate the configuration, don't hope")

    config = {
        "managed_settings_deployed": True,
        "secrets_denied_in_managed_policy": True,
        "marketplace_allowlisted": True,
        "project_memory_file_committed": True,
        "secrets_in_project_memory": False,
        "mcp_servers_scoped_per_user": True,
        "hooks_block_secret_paths": True,
        "onboarding_doc_published": False,
        "usage_review_scheduled": True,
    }

    required = [
        ("managed_settings_deployed", True),
        ("secrets_denied_in_managed_policy", True),
        ("marketplace_allowlisted", True),
        ("project_memory_file_committed", True),
        ("secrets_in_project_memory", False),
        ("mcp_servers_scoped_per_user", True),
        ("hooks_block_secret_paths", True),
        ("onboarding_doc_published", True),
        ("usage_review_scheduled", True),
    ]

    failures = [k for k, want in required if config.get(k) != want]
    for key, want in required:
        status = "ok" if config.get(key) == want else "GAP"
        print(f"  [{status:>3}] {key:<36} expected={want} actual={config.get(key)}")

    ok("the checklist catches the missing onboarding doc",
       failures == ["onboarding_doc_published"])
    print(f"  blockers before rollout: {failures}")


# --------------------------------------------------------------------------- #
# AI-assisted workflow: what belongs in the loop and what does not
# --------------------------------------------------------------------------- #


def demo_workflow() -> None:
    rule("E7.6  A defensible AI-assisted delivery loop")

    steps = [
        ("explore", "read code, map dependencies", "no writes; read-only tools"),
        ("plan", "propose a diff plan for review", "human approves the plan"),
        ("implement", "edit files in a branch", "tests + review, never main"),
        ("verify", "run tests, lint, typecheck", "the environment decides, not the model"),
        ("document", "update docs/changelog", "reviewed like code"),
    ]
    for phase, activity, control in steps:
        print(f"  {phase:<10} {activity:<34} control: {control}")

    forbidden = ["rotate production credentials", "apply migrations to prod",
                 "push to main without review", "paste customer data into the prompt"]
    print(f"\n  out of scope for the assistant: {forbidden}")

    ok("verification is environmental, not self-reported", steps[3][2].startswith("the environment"))
    ok("write access is bounded (branch + review)", "never main" in steps[2][2])
    ok("irreversible production actions are excluded", len(forbidden) == 4)


def main() -> None:
    demo_precedence()
    demo_permissions()
    demo_hook()
    demo_marketplace()
    demo_rollout()
    demo_workflow()

    rule("Takeaways")
    print("  1. Managed/server-side settings outrank CLI, project and user settings.")
    print("  2. Deny beats allow; default is ask, not allow.")
    print("  3. Hooks should block, not warn.")
    print("  4. Distribute capabilities through an allowlisted marketplace.")
    print("  5. Evaluate the rollout checklist; a gap is a blocker with an owner.")
    print("  6. The assistant proposes; tests and humans dispose.")


if __name__ == "__main__":
    main()
