"""Narrative prose generator with deterministic template variation."""

from __future__ import annotations

import hashlib
from typing import Protocol

from polsim.history.log import HistoryEntry


class Narrator(Protocol):
    def narrate(self, entry: HistoryEntry) -> str:
        ...


class TemplateNarrator:
    """Generates rich historical prose from structured history records.

    Variation is selected by hashing the entry ID so it is strictly deterministic
    and consumes no simulation random number generator state.
    """

    def _select_template(self, entry_id: str, templates: list[str]) -> str:
        h = int(hashlib.sha256(entry_id.encode("utf-8")).hexdigest()[:8], 16)
        return templates[h % len(templates)]

    def narrate(self, entry: HistoryEntry) -> str:
        t = entry.entry_type
        d = entry.details
        eid = entry.id
        date = entry.date

        if t == "election":
            winner = d.get("winner", "a coalition")
            turnout = d.get("turnout", 0.0) * 100.0
            seats = d.get("seats", {})
            top_shares = d.get("shares", {})
            majority = d.get("majority", False)

            if majority:
                templates = [
                    f"In {date}, general election returns confirmed a historic victory for {winner}, securing an outright parliamentary majority with {turnout:.1f}% national turnout.",
                    f"Voters went to the polls in {date}. In a decisive result, {winner} captured an absolute majority of seats as national turnout reached {turnout:.1f}%.",
                ]
            else:
                templates = [
                    f"In {date}, parliamentary elections produced a fragmented chamber with {turnout:.1f}% voter turnout. {winner} emerged as the largest party but fell short of an outright majority.",
                    f"The general election of {date} resulted in a hung parliament. {winner} claimed the plurality of seats amid spirited national turnout of {turnout:.1f}%.",
                ]
            return self._select_template(eid, templates)

        elif t == "coalition":
            leader = d.get("leader", "the formateur")
            partners = d.get("members", [])
            partner_str = ", ".join(p for p in partners if p != leader) or "allied independents"
            templates = [
                f"Following intense negotiations in {date}, {leader} successfully formed a coalition government with {partner_str}.",
                f"In {date}, an agreement was reached establishing a governing alliance between {leader} and {partner_str}.",
            ]
            return self._select_template(eid, templates)

        elif t == "collapse":
            leader = d.get("leader", "the Prime Minister")
            templates = [
                f"In {date}, internal discord culminated in the collapse of the government led by {leader} following a vote of no confidence.",
                f"The administration led by {leader} fractured in {date}, triggering political crisis and the loss of parliamentary confidence.",
            ]
            return self._select_template(eid, templates)

        elif t == "split":
            parent = d.get("parent", "the party")
            faction = d.get("faction", "dissidents")
            new_party = d.get("new_party", "a new movement")
            templates = [
                f"Ideological rifts within {parent} reached a boiling point in {date}. The {faction} faction seceded to establish {new_party}.",
                f"In {date}, deep factional discontent fractured {parent}, leading the {faction} wing to break away and launch {new_party}.",
            ]
            return self._select_template(eid, templates)

        elif t == "merger":
            parties = d.get("parties", ["two parties"])
            merged_name = d.get("merged_name", "a united alliance")
            p_str = " and ".join(parties)
            templates = [
                f"In {date}, {p_str} concluded historic unification talks, merging into {merged_name}.",
                f"Seeking greater electoral leverage, {p_str} formally amalgamated into {merged_name} in {date}.",
            ]
            return self._select_template(eid, templates)

        elif t == "event":
            title = entry.title
            desc = d.get("description", "")
            templates = [
                f"In {date}, national attention was gripped by {title}: {desc}",
                f"{title} unfolded in {date}. {desc}",
            ]
            return self._select_template(eid, templates)

        elif t == "legislation":
            gov = d.get("government", "Parliament")
            templates = [
                f"In {date}, {gov} successfully steered flagship legislation through the legislature.",
                f"Major policy reforms were codified by {gov} in {date} following parliamentary debate.",
            ]
            return self._select_template(eid, templates)

        return entry.title
