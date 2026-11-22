"""Custom Cosmic Ray mutation operators modelling NEMO Temporary Physical Access business-rule defects.

Area 1 Owner: Jaweria Abdul Hameed (24I-3025)

Operators:
  1. FlipApprovalStatusOperator (BR-3 / FR-07 / FR-08):
     Swaps RequestStatus.APPROVED <-> RequestStatus.DENIED and mutates
     RequestStatus.PENDING -> RequestStatus.APPROVED in state checks/assignments.
  2. SkipGrantCreationOperator (BR-3 / PR-04):
     Replaces `create_temporary_access(...)` call statements with `pass`, simulating
     an approval that fails to persist TemporaryPhysicalAccess grant records.
  3. BypassReviewerCheckOperator (BR-2 / BR-4 / PR-02):
     Replaces `is_user_a_reviewer(user)` calls with `True`, simulating broken
     reviewer role enforcement on list/edit views.
  4. RelaxBuddyMinimumOperator (BR-1 / PR-06):
     Replaces `minimum_total_users - 1` with `minimum_total_users - 2`, simulating
     an off-by-one boundary relaxation on buddy-count validation.
"""

import parso
import parso.python.tree

from cosmic_ray.operators.operator import Example, Operator


class FlipApprovalStatusOperator(Operator):
    """BR-3 state-transition defect: flips RequestStatus.APPROVED/DENIED/PENDING constants."""

    _SWAPS = {
        "RequestStatus.APPROVED": "RequestStatus.DENIED",
        "RequestStatus.DENIED": "RequestStatus.APPROVED",
        "RequestStatus.PENDING": "RequestStatus.EXPIRED",
    }

    def mutation_positions(self, node):
        if isinstance(node, parso.python.tree.PythonNode) and node.type == "atom_expr":
            code = node.get_code().strip()
            if code in self._SWAPS:
                yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        raw = node.get_code()
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        target = self._SWAPS[raw.strip()]
        return parso.parse(f"{leading}{target}{trailing}")

    @classmethod
    def examples(cls):
        return (
            Example("x = RequestStatus.APPROVED", "x = RequestStatus.DENIED"),
            Example("x = RequestStatus.DENIED", "x = RequestStatus.APPROVED"),
            Example("if s != RequestStatus.PENDING: pass", "if s != RequestStatus.EXPIRED: pass"),
        )


class SkipGrantCreationOperator(Operator):
    """BR-3 / PR-04 side-effect defect: drops create_temporary_access(...) calls."""

    def mutation_positions(self, node):
        if isinstance(node, parso.python.tree.PythonNode) and node.type == "simple_stmt":
            if node.get_code().strip().startswith("create_temporary_access("):
                yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        raw = node.get_code()
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = "\n" if raw.endswith("\n") else ""
        return parso.parse(f"{leading}pass{trailing}")

    @classmethod
    def examples(cls):
        return (Example("create_temporary_access(access_request)\n", "pass\n"),)


class BypassReviewerCheckOperator(Operator):
    """BR-2 / BR-4 / PR-02 authorization defect: forces is_user_a_reviewer(...) to True."""

    def mutation_positions(self, node):
        if isinstance(node, parso.python.tree.PythonNode) and node.type == "atom_expr":
            if node.get_code().strip().startswith("is_user_a_reviewer("):
                yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        raw = node.get_code()
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        return parso.parse(f"{leading}True{trailing}")

    @classmethod
    def examples(cls):
        return (Example("user_is_reviewer = is_user_a_reviewer(user)", "user_is_reviewer = True"),)


class RelaxBuddyMinimumOperator(Operator):
    """BR-1 / PR-06 boundary defect: relaxes `minimum_total_users - 1` to `minimum_total_users - 2`."""

    def mutation_positions(self, node):
        if isinstance(node, parso.python.tree.PythonNode) and node.type == "arith_expr":
            if node.get_code().strip() == "minimum_total_users - 1":
                yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        raw = node.get_code()
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        return parso.parse(f"{leading}minimum_total_users - 2{trailing}")

    @classmethod
    def examples(cls):
        return (Example("if other_users < minimum_total_users - 1: pass", "if other_users < minimum_total_users - 2: pass"),)
