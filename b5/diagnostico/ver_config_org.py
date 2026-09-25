"""Mostra (só leitura) o system_prompt e os overrides de prompt da org."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402
from bot_env import bootstrap  # noqa: E402

sub = bootstrap(os.path.join(dc.DIAG_DIR, "memory"))
import asyncio  # noqa: E402

cfg = asyncio.new_event_loop().run_until_complete(sub.get_org_config(dc.ORG))
print("SYSTEM_PROMPT (who_am_i):\n", cfg.system_prompt)
for k, v in vars(cfg.prompts).items():
    if v:
        print(f"\n===== override {k} ({len(v)} chars) =====\n{v}")
