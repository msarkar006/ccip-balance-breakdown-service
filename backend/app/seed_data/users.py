"""Seed personas: the single source of truth for demo sign-in credentials (mirrored in the README)."""

from __future__ import annotations

from typing import NamedTuple


class Persona(NamedTuple):
    key: str
    username: str
    password: str
    role: str


PERSONAS: dict[str, Persona] = {
    "customer01": Persona("customer01", "synthetic.customer01", "Prototype!2026", "customer"),
    "customer02": Persona("customer02", "synthetic.customer02", "Prototype!2026", "customer"),
    "admin01": Persona("admin01", "synthetic.admin01", "Prototype!2026", "administrator"),
}
