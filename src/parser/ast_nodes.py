"""AST node types for LTL formulas."""

from dataclasses import dataclass


@dataclass
class ASTNode:
    """Base class for all AST nodes."""

    def __str__(self) -> str:
        raise NotImplementedError


@dataclass
class UnaryNode(ASTNode):
    """Base class for unary operators (single child)."""

    child: "ASTNode"


@dataclass
class BinaryNode(ASTNode):
    """Base class for binary operators (left and right)."""

    left: "ASTNode"
    right: "ASTNode"


@dataclass
class Atom(ASTNode):
    """Atomic proposition."""

    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Not(UnaryNode):
    """Negation operator (neg)."""

    def __str__(self) -> str:
        return f"!({self.child})"


@dataclass
class And(BinaryNode):
    """Conjunction operator (and)."""

    def __str__(self) -> str:
        return f"({self.left} /\\ {self.right})"


@dataclass
class Or(BinaryNode):
    """Disjunction operator (or)."""

    def __str__(self) -> str:
        return f"({self.left} \\/ {self.right})"


@dataclass
class Imply(BinaryNode):
    """Implication operator (implies)."""

    def __str__(self) -> str:
        return f"({self.left} -> {self.right})"


@dataclass
class Next(UnaryNode):
    """Next operator (X)."""

    def __str__(self) -> str:
        return f"X({self.child})"


@dataclass
class Globally(UnaryNode):
    """Globally operator (G)."""

    def __str__(self) -> str:
        return f"G({self.child})"


@dataclass
class Finally(UnaryNode):
    """Finally operator (F)."""

    def __str__(self) -> str:
        return f"F({self.child})"


@dataclass
class Until(BinaryNode):
    """Until operator (U)."""

    def __str__(self) -> str:
        return f"({self.left} U {self.right})"
