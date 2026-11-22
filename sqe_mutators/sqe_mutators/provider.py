"""Cosmic Ray operator-provider plugin for NEMO business-rule mutation operators."""

from .operators import (
    BypassReviewerCheckOperator,
    FlipApprovalStatusOperator,
    RelaxBuddyMinimumOperator,
    SkipGrantCreationOperator,
)

_OPERATORS = {
    op.__name__: op
    for op in (
        FlipApprovalStatusOperator,
        SkipGrantCreationOperator,
        BypassReviewerCheckOperator,
        RelaxBuddyMinimumOperator,
    )
}


class NemoBusinessRuleProvider:
    """Exposes custom NEMO business-rule mutation operators under `nemo_br/*`."""

    def __iter__(self):
        return iter(_OPERATORS)

    def __getitem__(self, name):
        return _OPERATORS[name]
