"""What JARVIS and its agents are allowed to do.

The policy engine answers one question: given this capability, this agent and
this task, does the work run, does it wait for the user, or is it refused?

Two things decide it. Risk gives a sane default - reading a public page runs,
deploying to production asks - and stored rules override that default where the
user has an opinion. The narrowest matching rule wins, and a deny beats an
allow of equal narrowness, so a broad "agents may browse" never quietly
re-enables a specific "this agent may not".
"""

import logging

from assistant.control.capabilities import describe, is_known, risk_for
from assistant.control.models import Decision, EventType, PolicyRule, RiskLevel

logger = logging.getLogger(__name__)

# What happens when no stored rule has an opinion.
RISK_DEFAULTS = {
    RiskLevel.LOW: Decision.ALLOW,
    RiskLevel.MEDIUM: Decision.ALLOW,
    RiskLevel.HIGH: Decision.REQUIRE_APPROVAL,
    RiskLevel.CRITICAL: Decision.REQUIRE_APPROVAL,
}


class Judgement:
    """The answer, with enough context to explain it to a person."""

    def __init__(self, capability, decision, risk, reason, rule=None):
        self.capability = capability
        self.decision = decision
        self.risk = risk
        self.reason = reason
        self.rule = rule

    @property
    def allowed(self):
        return self.decision == Decision.ALLOW

    @property
    def needs_approval(self):
        return self.decision == Decision.REQUIRE_APPROVAL

    @property
    def denied(self):
        return self.decision == Decision.DENY

    def to_dict(self):
        return {
            "capability": self.capability,
            "decision": self.decision.value,
            "risk": self.risk.value,
            "reason": self.reason,
            "rule_id": self.rule.id if self.rule else "",
            "description": describe(self.capability),
        }

    def __repr__(self):
        return f"<Judgement {self.capability} {self.decision.value} ({self.risk.value})>"


class PolicyEngine:
    """Stores rules and evaluates capability requests against them."""

    def __init__(self, store):
        self.store = store

    # -- rules --------------------------------------------------------------

    def add_rule(self, capability, decision, agent_id="", task_id="",
                 resource="", reason=""):
        rule = PolicyRule(capability=capability, decision=Decision(decision),
                          agent_id=agent_id, task_id=task_id, resource=resource,
                          reason=reason)
        self.store.save_policy_rule(rule)
        return rule

    def list_rules(self):
        return self.store.list_policy_rules()

    def remove_rule(self, rule_id):
        return self.store.delete_policy_rule(rule_id)

    # -- evaluation ---------------------------------------------------------

    def evaluate(self, capability, agent_id="", task_id="", resource=""):
        """Decide one request. Never raises: an unknown capability is critical."""
        risk = risk_for(capability)
        rule = self._winning_rule(capability, agent_id, task_id, resource)

        if rule is not None:
            reason = rule.reason or f"A rule for {rule.capability} says {rule.decision.value}."
            return Judgement(capability, rule.decision, risk, reason, rule=rule)

        if not is_known(capability):
            return Judgement(
                capability, Decision.REQUIRE_APPROVAL, risk,
                "JARVIS does not recognise this capability, so it asks first.")

        decision = RISK_DEFAULTS[risk]
        reason = (f"{describe(capability)} is {risk.value} risk."
                  if decision == Decision.ALLOW
                  else f"{describe(capability)} is {risk.value} risk, so it needs you.")
        return Judgement(capability, decision, risk, reason)

    def _winning_rule(self, capability, agent_id, task_id, resource):
        """The narrowest matching rule. A deny wins a tie."""
        matches = [rule for rule in self.store.list_policy_rules()
                   if rule.matches(capability, agent_id, task_id, resource)]
        if not matches:
            return None

        matches.sort(key=lambda rule: (rule.specificity,
                                       rule.decision == Decision.DENY,
                                       rule.decision == Decision.REQUIRE_APPROVAL),
                     reverse=True)
        return matches[0]
