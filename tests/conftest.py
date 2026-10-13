"""Shared pytest configuration."""

import os

from hypothesis import settings

settings.register_profile("ci", derandomize=True, deadline=None, print_blob=True)
settings.load_profile("ci" if os.environ.get("CI") else "default")
