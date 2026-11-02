"""MMO-12 operators, copied as data from design 01 §5."""

from .proof import MutantOp, MutationOperator

MMO_12: list[MutationOperator] = [
    MutationOperator(
        op=MutantOp.M1, fault="ignore currency in the amount check", rules_broken=["R03"]
    ),
    MutationOperator(op=MutantOp.M2, fault="skip capture-status check", rules_broken=["R01"]),
    MutationOperator(op=MutantOp.M3, fault="confirm without approval", rules_broken=["R06"]),
    MutationOperator(
        op=MutantOp.M4, fault="remove the per-order lock (two tabs)", rules_broken=["R05"]
    ),
    MutationOperator(
        op=MutantOp.M5, fault="random PayPal-Request-Id on retry", rules_broken=["R05", "R10"]
    ),
    MutationOperator(op=MutantOp.M6, fault="money as float", rules_broken=["R02", "R16"]),
    MutationOperator(
        op=MutantOp.M7, fault="take amount/currency from the browser", rules_broken=["R12", "R02"]
    ),
    MutationOperator(
        op=MutantOp.M8, fault="skip webhook signature verification", rules_broken=["R08"]
    ),
    MutationOperator(
        op=MutantOp.M9,
        fault="read order id from related_resources instead of supplementary_data.related_ids",
        rules_broken=["R01"],
    ),
    MutationOperator(
        op=MutantOp.M10, fault="case-sensitive signature header lookup", rules_broken=["R08"]
    ),
    MutationOperator(
        op=MutantOp.M11,
        fault="keep approved-but-uncaptured state only in memory",
        rules_broken=["R14"],
    ),
    MutationOperator(op=MutantOp.M12, fault="no refund-state check", rules_broken=["R11"]),
]
MUTANT_OPERATORS = {row.op: row for row in MMO_12}
