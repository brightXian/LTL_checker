"""Unit tests for the LTL parser."""

import pytest

from src.parser.ast_nodes import (
    And,
    Atom,
    Finally,
    Globally,
    Imply,
    Next,
    Not,
    Or,
    Until,
)
from src.parser.parser import parse


class TestBasicAtoms:
    """Test basic atomic propositions, including multi-character names."""

    def test_single_char_atom(self):
        """Single character is parsed as an Atom node."""
        result = parse("p")
        expected = Atom(name="p")
        assert result == expected
        assert str(result) == "p"

    def test_multi_char_atom(self):
        """Multi-character lowercase string is parsed as a single Atom."""
        result = parse("req")
        expected = Atom(name="req")
        assert result == expected
        assert str(result) == "req"

    def test_atom_with_digit(self):
        """Atom name with trailing digit is parsed as a single Atom."""
        result = parse("p0")
        expected = Atom(name="p0")
        assert result == expected
        assert str(result) == "p0"


class TestUnaryOperatorsOnAtoms:
    """Test all unary operators applied directly to atoms without parentheses."""

    def test_not_on_atom(self):
        """Unary NOT creates a Not node with the atom as child."""
        result = parse("!p")
        expected = Not(child=Atom(name="p"))
        assert result == expected
        assert str(result) == "!(p)"

    def test_globally_on_atom(self):
        """Unary G creates a Globally node with the atom as child."""
        result = parse("Gp")
        expected = Globally(child=Atom(name="p"))
        assert result == expected
        assert str(result) == "G(p)"

    def test_finally_on_atom(self):
        """Unary F creates a Finally node with the atom as child."""
        result = parse("Fp")
        expected = Finally(child=Atom(name="p"))
        assert result == expected
        assert str(result) == "F(p)"

    def test_next_on_atom(self):
        """Unary X creates a Next node with the atom as child."""
        result = parse("Xp")
        expected = Next(child=Atom(name="p"))
        assert result == expected
        assert str(result) == "X(p)"


class TestBinaryOperators:
    """Test all binary operators with parentheses."""

    def test_and(self):
        """Binary /\\ creates an And node with correct children."""
        result = parse("(p /\\ q)")
        expected = And(left=Atom(name="p"), right=Atom(name="q"))
        assert result == expected
        assert str(result) == "(p /\\ q)"

    def test_or(self):
        """Binary \\/ creates an Or node with correct children."""
        result = parse("(p \\/ q)")
        expected = Or(left=Atom(name="p"), right=Atom(name="q"))
        assert result == expected
        assert str(result) == "(p \\/ q)"

    def test_imply(self):
        """Binary -> creates an Imply node with correct children."""
        result = parse("(p -> q)")
        expected = Imply(left=Atom(name="p"), right=Atom(name="q"))
        assert result == expected
        assert str(result) == "(p -> q)"

    def test_until(self):
        """Binary U creates an Until node with correct children."""
        result = parse("p U q")
        expected = Until(left=Atom(name="p"), right=Atom(name="q"))
        assert result == expected
        assert str(result) == "(p U q)"


class TestDeepNesting:
    """Test formulas with at least 4 levels of nesting."""

    def test_four_levels_globally_finally_next(self):
        """Three unary operators nest correctly: G(F(X(p)))."""
        result = parse("G(F(X(p)))")
        expected = Globally(child=Finally(child=Next(child=Atom(name="p"))))
        assert result == expected
        assert str(result) == "G(F(X(p)))"

    def test_four_levels_triple_negation(self):
        """Three NOT operators nest correctly."""
        result = parse("!(!(!(p)))")
        expected = Not(child=Not(child=Not(child=Atom(name="p"))))
        assert result == expected
        assert str(result) == "!(!(!(p)))"

    def test_four_levels_triple_until(self):
        """Three Until operators nest inside Globally."""
        result = parse("G(p U (q U (r U s)))")
        expected = Globally(
            child=Until(
                left=Atom(name="p"),
                right=Until(
                    left=Atom(name="q"),
                    right=Until(left=Atom(name="r"), right=Atom(name="s")),
                ),
            )
        )
        assert result == expected
        assert str(result) == "G((p U (q U (r U s))))"


class TestMixedOperators:
    """Test mixed operators with correct associativity."""

    def test_globally_imply_finally_or(self):
        """Complex nesting: G contains Imply which contains And and Finally."""
        result = parse("G((p /\\ q) -> F(p \\/ q))")
        expected = Globally(
            child=Imply(
                left=And(left=Atom(name="p"), right=Atom(name="q")),
                right=Finally(child=Or(left=Atom(name="p"), right=Atom(name="q"))),
            )
        )
        assert result == expected
        assert str(result) == "G(((p /\\ q) -> F((p \\/ q))))"

    def test_until_and_finally_globally(self):
        """Formula with explicit parens around each operand.

        The right operand '(F(p) /\\ G(q))' now correctly parses as And with
        Finally and Globally as children, not as Finally wrapping And.
        """
        result = parse("(p -> q) U (F(p) /\\ G(q))")
        expected = Until(
            left=Imply(left=Atom(name="p"), right=Atom(name="q")),
            right=And(
                left=Finally(child=Atom(name="p")), right=Globally(child=Atom(name="q"))
            ),
        )
        assert result == expected
        assert str(result) == "((p -> q) U (F(p) /\\ G(q)))"

    def test_globally_finally_until_next_globally(self):
        """Formula 'G(F(p)) U X(G(q))' where each side is parenthesized.

        The left 'G(F(p))' is parsed as a unary expression.
        The right 'X(G(q))' is parsed as a unary expression after U.
        """
        result = parse("G(F(p)) U X(G(q))")
        expected = Until(
            left=Globally(child=Finally(child=Atom(name="p"))),
            right=Next(child=Globally(child=Atom(name="q"))),
        )
        assert result == expected
        assert str(result) == "(G(F(p)) U X(G(q)))"


class TestUnaryOnBinary:
    """Test unary operators applied to binary expressions."""

    def test_not_on_and(self):
        """Unary NOT applied to a binary And expression."""
        result = parse("!(p /\\ q)")
        expected = Not(child=And(left=Atom(name="p"), right=Atom(name="q")))
        assert result == expected
        assert str(result) == "!((p /\\ q))"

    def test_globally_on_imply(self):
        """Unary G applied to a binary Imply expression."""
        result = parse("G(p -> q)")
        expected = Globally(child=Imply(left=Atom(name="p"), right=Atom(name="q")))
        assert result == expected
        assert str(result) == "G((p -> q))"

    def test_finally_on_until(self):
        """Unary F applied to a binary Until expression."""
        result = parse("F(p U q)")
        expected = Finally(child=Until(left=Atom(name="p"), right=Atom(name="q")))
        assert result == expected
        assert str(result) == "F((p U q))"

    def test_next_on_or(self):
        """Unary X applied to a binary Or expression."""
        result = parse("X(p \\/ q)")
        expected = Next(child=Or(left=Atom(name="p"), right=Atom(name="q")))
        assert result == expected
        assert str(result) == "X((p \\/ q))"


class TestWhitespaceVariations:
    """Test that whitespace variations produce equal ASTs."""

    def test_no_space_vs_with_space_globally_and(self):
        """No-space and with-space versions produce identical ASTs."""
        no_space = parse("G(p/\\q)")
        with_space = parse("G(p /\\ q)")
        assert no_space == with_space
        assert str(no_space) == str(with_space)

    def test_no_space_vs_with_space_until(self):
        """No-space and with-space versions produce identical ASTs."""
        no_space = parse("pUq")
        with_space = parse("p U q")
        assert no_space == with_space
        assert str(no_space) == str(with_space)

    def test_no_space_vs_with_space_imply(self):
        """No-space and with-space versions produce identical ASTs."""
        no_space = parse("(p->q)")
        with_space = parse("(p -> q)")
        assert no_space == with_space
        assert str(no_space) == str(with_space)


class TestParserErrors:
    """Test error cases for invalid input."""

    def test_empty_input(self):
        """Empty input string raises ValueError."""
        with pytest.raises(ValueError):
            parse("")

    def test_operator_without_operand(self):
        """Operator without operand raises ValueError."""
        with pytest.raises(ValueError):
            parse("G")

    def test_chained_unary_without_atom(self):
        """Chained unary operators without operand raises ValueError."""
        with pytest.raises(ValueError):
            parse("!!")

    def test_unclosed_parenthesis(self):
        """Unclosed parenthesis raises ValueError."""
        with pytest.raises(ValueError):
            parse("(p /\\")

    def test_invalid_character(self):
        """Invalid character raises ValueError."""
        with pytest.raises(ValueError):
            parse("@p")

    def test_missing_closing_paren(self):
        """Missing closing parenthesis raises ValueError."""
        with pytest.raises(ValueError):
            parse("(p /\\ q")


class TestAtomNameEdgeCases:
    """Test atoms whose names are lowercase versions of operator keywords."""

    def test_single_g_as_atom(self):
        """Single lowercase 'g' is parsed as Atom, not as G operator."""
        result = parse("Gg")
        expected = Globally(child=Atom(name="g"))
        assert result == expected
        assert str(result) == "G(g)"

    def test_single_f_as_atom(self):
        """Single lowercase 'f' is parsed as Atom, not as F operator."""
        result = parse("Ff")
        expected = Finally(child=Atom(name="f"))
        assert result == expected
        assert str(result) == "F(f)"

    def test_single_x_as_atom(self):
        """Single lowercase 'x' is parsed as Atom, not as X operator."""
        result = parse("Xx")
        expected = Next(child=Atom(name="x"))
        assert result == expected
        assert str(result) == "X(x)"

    def test_until_with_u_atoms(self):
        """Both operands can be atom 'u' (which is not the U operator when lowercase)."""
        result = parse("u U u")
        expected = Until(left=Atom(name="u"), right=Atom(name="u"))
        assert result == expected
        assert str(result) == "(u U u)"

    def test_until_with_gf_atoms(self):
        """Operands can be atoms named after other operators."""
        result = parse("g U f")
        expected = Until(left=Atom(name="g"), right=Atom(name="f"))
        assert result == expected
        assert str(result) == "(g U f)"


class TestTokenBoundaries:
    """Test that operators and atoms are correctly separated without spaces."""

    def test_until_without_spaces(self):
        """'pUq' without spaces equals 'p U q'."""
        no_space = parse("pUq")
        with_space = parse("p U q")
        assert no_space == with_space
        assert str(no_space) == str(with_space)

    def test_consecutive_unary_operators(self):
        """'GFp' creates nested Finally inside Globally."""
        result = parse("GFp")
        expected = Globally(child=Finally(child=Atom(name="p")))
        assert result == expected
        assert str(result) == "G(F(p))"

    def test_not_of_globally(self):
        """'!Gp' creates Not with Globally child."""
        result = parse("!Gp")
        expected = Not(child=Globally(child=Atom(name="p")))
        assert result == expected
        assert str(result) == "!(G(p))"

    def test_globally_of_not(self):
        """'G!p' creates Globally with Not child."""
        result = parse("G!p")
        expected = Globally(child=Not(child=Atom(name="p")))
        assert result == expected
        assert str(result) == "G(!(p))"
