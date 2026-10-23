"""Propositional logic for Questions 2 to 4, following AIMA Chapter 7.

* `tt_check_all` / `tt_entails`  : TT-ENTAILS, Figure 7.10 (model enumeration)
* `pl_true`                      : PL-TRUE?, used by TT-CHECK-ALL
* `to_cnf`                       : the CNF conversion steps of Section 7.5.2
* `pl_resolution`                : PL-RESOLUTION, Figure 7.12
* `pl_resolve`                   : PL-RESOLVE (resolvents of two clauses)

Sentence syntax for `parse`:  ~A  A & B  A | B  A ==> B  A <=> B  ( )
Precedence, highest first: ~, &, |, ==>, <=>  (as in AIMA Section 7.4.1).
"""

import itertools
import re


# --------------------------------------------------------------------- sentences
class Expr:
    """A sentence: a symbol (op is the name, no args) or an operator with args."""

    def __init__(self, op, *args):
        self.op = op
        self.args = tuple(args)

    def is_symbol(self):
        return not self.args and self.op not in ("~", "&", "|", "==>", "<=>")

    def __eq__(self, o):
        return isinstance(o, Expr) and self.op == o.op and self.args == o.args

    def __hash__(self):
        return hash((self.op, self.args))

    def __repr__(self):
        if self.is_symbol():
            return self.op
        if self.op == "~":
            a = self.args[0]
            return "~" + (repr(a) if a.is_symbol() or a.op == "~" else f"({a!r})")
        parts = []
        for a in self.args:
            parts.append(repr(a) if a.is_symbol() or a.op == "~" else f"({a!r})")
        return f" {self.op} ".join(parts)


TRUE, FALSE = Expr("True"), Expr("False")


def symbols(s):
    """PROPOSITION-SYMBOLS(s), sorted so truth tables come out in a fixed order."""
    if s in (TRUE, FALSE):
        return []
    if s.is_symbol():
        return [s.op]
    out = set()
    for a in s.args:
        out.update(symbols(a))
    return sorted(out)


# --------------------------------------------------------------------- parser
_TOKEN = re.compile(r"\s*(<=>|==>|[~&|()]|[A-Za-z_][A-Za-z_0-9]*)")


def parse(text):
    tokens = _TOKEN.findall(text)
    if "".join(tokens) != re.sub(r"\s+", "", text):
        raise ValueError(f"cannot parse {text!r}")
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take(expected=None):
        nonlocal pos
        t = tokens[pos]
        if expected and t != expected:
            raise ValueError(f"expected {expected} got {t}")
        pos += 1
        return t

    def binary(next_level, op, right_assoc=False):
        def rule():
            left = next_level()
            while peek() == op:
                take()
                right = rule() if right_assoc else next_level()
                left = Expr(op, left, right)
                if right_assoc:
                    break
            return left
        return rule

    def unary():
        if peek() == "~":
            take()
            return Expr("~", unary())
        if peek() == "(":
            take("(")
            e = iff()
            take(")")
            return e
        name = take()
        return TRUE if name == "True" else FALSE if name == "False" else Expr(name)

    conj = binary(unary, "&")
    disj = binary(conj, "|")
    impl = binary(disj, "==>", right_assoc=True)
    iff = binary(impl, "<=>")
    e = iff()
    if pos != len(tokens):
        raise ValueError(f"unexpected {tokens[pos]!r}")
    return e


def as_expr(s):
    return parse(s) if isinstance(s, str) else s


# --------------------------------------------------------------------- semantics
def pl_true(s, model):
    """PL-TRUE?(s, model): truth value of sentence s in a complete model."""
    s = as_expr(s)
    if s == TRUE:
        return True
    if s == FALSE:
        return False
    if s.is_symbol():
        return model[s.op]
    a = [pl_true(x, model) for x in s.args]
    if s.op == "~":
        return not a[0]
    if s.op == "&":
        return all(a)
    if s.op == "|":
        return any(a)
    if s.op == "==>":
        return (not a[0]) or a[1]
    if s.op == "<=>":
        return a[0] == a[1]
    raise ValueError(s.op)


def all_models(syms):
    """Every assignment of True/False to syms (2^n models)."""
    for values in itertools.product([False, True], repeat=len(syms)):
        yield dict(zip(syms, values))


def tt_entails(kb, alpha):
    """TT-ENTAILS?(KB, alpha), Figure 7.10."""
    kb, alpha = as_expr(kb), as_expr(alpha)
    syms = sorted(set(symbols(kb)) | set(symbols(alpha)))
    return tt_check_all(kb, alpha, syms, {})


def tt_check_all(kb, alpha, syms, model):
    """TT-CHECK-ALL(KB, alpha, symbols, model), Figure 7.10."""
    if not syms:
        if pl_true(kb, model):
            return pl_true(alpha, model)
        return True  # when KB is false, always return true
    p, rest = syms[0], syms[1:]
    return (tt_check_all(kb, alpha, rest, {**model, p: True}) and
            tt_check_all(kb, alpha, rest, {**model, p: False}))


def truth_table(s, syms=None):
    """Rows (model, value) for every model of the given symbols."""
    s = as_expr(s)
    syms = syms or symbols(s)
    return [(m, pl_true(s, m)) for m in all_models(syms)]


def classify(s):
    """'valid', 'unsatisfiable' or 'satisfiable' (neither valid nor unsatisfiable)."""
    values = [v for _, v in truth_table(s)]
    if all(values):
        return "valid"
    if not any(values):
        return "unsatisfiable"
    return "satisfiable"


def count_models(s, vocabulary):
    """Number of models of s over the given vocabulary (Question 3)."""
    s = as_expr(s)
    return sum(1 for m in all_models(list(vocabulary)) if pl_true(s, m))


# --------------------------------------------------------------------- CNF (Section 7.5.2)
def eliminate_biconditional(s):
    if s.is_symbol():
        return s
    args = [eliminate_biconditional(a) for a in s.args]
    if s.op == "<=>":
        a, b = args
        return Expr("&", Expr("==>", a, b), Expr("==>", b, a))
    return Expr(s.op, *args)


def eliminate_implication(s):
    if s.is_symbol():
        return s
    args = [eliminate_implication(a) for a in s.args]
    if s.op == "==>":
        a, b = args
        return Expr("|", Expr("~", a), b)
    return Expr(s.op, *args)


def move_not_inwards(s):
    """De Morgan and double negation, until ~ only applies to symbols."""
    if s.is_symbol():
        return s
    if s.op == "~":
        a = s.args[0]
        if a.is_symbol():
            return s
        if a.op == "~":
            return move_not_inwards(a.args[0])
        if a.op == "&":
            return Expr("|", *[move_not_inwards(Expr("~", x)) for x in a.args])
        if a.op == "|":
            return Expr("&", *[move_not_inwards(Expr("~", x)) for x in a.args])
    return Expr(s.op, *[move_not_inwards(a) for a in s.args])


def distribute_or(s):
    """Distribute | over & so the result is a conjunction of disjunctions."""
    if s.is_symbol() or s.op == "~":
        return s
    args = [distribute_or(a) for a in s.args]
    if s.op == "&":
        return Expr("&", *args)
    # s.op == "|": collect conjunct lists of each side and take all combinations
    a, b = args
    a_parts = conjuncts(a)
    b_parts = conjuncts(b)
    clauses = [Expr("|", x, y) for x in a_parts for y in b_parts]
    out = clauses[0]
    for c in clauses[1:]:
        out = Expr("&", out, c)
    return out


def conjuncts(s):
    if not s.is_symbol() and s.op == "&":
        return [c for a in s.args for c in conjuncts(a)]
    return [s]


def disjuncts(s):
    if not s.is_symbol() and s.op == "|":
        return [d for a in s.args for d in disjuncts(a)]
    return [s]


def to_cnf_steps(s):
    """The four steps of Section 7.5.2, returning every intermediate sentence."""
    s = as_expr(s)
    steps = [("original", s)]
    s = eliminate_biconditional(s); steps.append(("1. eliminate <=>", s))
    s = eliminate_implication(s); steps.append(("2. eliminate ==>", s))
    s = move_not_inwards(s); steps.append(("3. move ~ inwards", s))
    s = distribute_or(s); steps.append(("4. distribute | over &", s))
    return steps


def to_cnf(s):
    return to_cnf_steps(s)[-1][1]


def literal(text):
    """A literal as a string: 'P' or '~P'."""
    return text


def clauses_of(s):
    """CNF sentence -> set of clauses, each a frozenset of literal strings.

    Duplicate literals are merged and tautological clauses (P | ~P) dropped,
    which is the simplification step that makes clauses sets (Section 7.5.2).
    """
    out = set()
    for c in conjuncts(to_cnf(as_expr(s))):
        lits = set()
        for d in disjuncts(c):
            if d == TRUE:
                lits = None
                break
            if d == FALSE:
                continue
            lits.add(repr(d))
        if lits is None or any(negate(l) in lits for l in lits):
            continue
        out.add(frozenset(lits))
    return out


def negate(lit):
    return lit[1:] if lit.startswith("~") else "~" + lit


# --------------------------------------------------------------------- resolution (Figure 7.12)
def pl_resolve(ci, cj):
    """PL-RESOLVE: all clauses from resolving ci and cj on one complementary pair."""
    resolvents = set()
    for lit in ci:
        if negate(lit) in cj:
            new = (ci - {lit}) | (cj - {negate(lit)})
            if not any(negate(l) in new for l in new):  # drop tautologies
                resolvents.add(frozenset(new))
    return resolvents


def pl_resolution(kb, alpha, trace=None):
    """PL-RESOLUTION(KB, alpha), Figure 7.12. Returns True if KB entails alpha.

    clauses <- the set of clauses in the CNF representation of KB & ~alpha
    loop: for each pair of clauses, add their resolvents; if the empty clause
    appears, return true; if nothing new was added, return false.

    If `trace` is a list, every resolution step that produced a new clause is
    appended as (Ci, Cj, resolvent).
    """
    kb, alpha = as_expr(kb), as_expr(alpha)
    clauses = clauses_of(Expr("&", kb, Expr("~", alpha)))
    if trace is not None:
        trace.append(("start", sorted(map(sorted, clauses)), None))
    new = set()
    while True:
        pairs = list(itertools.combinations(sorted(clauses, key=sorted), 2))
        for ci, cj in pairs:
            for r in pl_resolve(ci, cj):
                if r not in clauses and r not in new and trace is not None:
                    trace.append((set(ci), set(cj), set(r)))
                if not r:
                    return True
                new.add(r)
        if new <= clauses:
            return False
        clauses |= new


def is_valid_by_resolution(s):
    """s is valid iff True entails s, i.e. ~s is unsatisfiable."""
    return pl_resolution(TRUE, s)
