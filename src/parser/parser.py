"""Recursive descent parser for LTL formulas."""

from src.parser.ast_nodes import (
    And,
    ASTNode,
    Atom,
    Finally,
    Globally,
    Imply,
    Next,
    Not,
    Or,
    Until,
)
from src.parser.lexer import Token, TokenType, tokenize


class Parser:
    """Recursive descent parser for LTL formulas."""

    def __init__(self, tokens: list[Token]) -> None:
        """Initialize parser with tokens.

        Args:
            tokens: List of tokens to parse.
        """
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        """Get current token without advancing.

        Returns:
            Current token.

        Raises:
            ValueError: If past end of input.
        """
        if self.pos >= len(self.tokens):
            raise ValueError("Unexpected end of input")
        return self.tokens[self.pos]

    def advance(self) -> Token:
        """Consume and return current token.

        Returns:
            Current token before advancing.
        """
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """Consume expected token type.

        Args:
            token_type: Expected token type.

        Returns:
            Consumed token.

        Raises:
            ValueError: If token type doesn't match.
        """
        token = self.current()
        if token.type != token_type:
            raise ValueError(
                f"Expected {token_type.name} but got {token.type.name} at position {self.pos}"
            )
        return self.advance()

    def parse(self) -> ASTNode:
        """Parse tokens into AST.

        Returns:
            Root AST node.

        Raises:
            ValueError: If there's a syntax error.
        """
        node = self.parse_formula()
        if self.pos < len(self.tokens):
            raise ValueError(
                f"Unexpected token {self.tokens[self.pos].type.name} after formula"
            )
        return node

    def parse_primary(self) -> ASTNode:
        """Parse exactly one syntactic unit (atom, unary operator, or parenthesized expression).

        This method does NOT consume binary operators - it stops at them.

        Grammar:
            - ATOM token -> Atom
            - unary operator (! X G F) + parse_primary() -> unary node
            - LPAREN + parse_formula() + RPAREN -> result

        Returns:
            AST node for a single syntactic unit.
        """
        token = self.current()

        if token.type == TokenType.ATOM:
            self.advance()
            return Atom(name=token.value)

        if token.type in (
            TokenType.NOT,
            TokenType.NEXT,
            TokenType.GLOBALLY,
            TokenType.FINALLY,
        ):
            op = self.advance()
            child = self.parse_primary()
            if op.type == TokenType.NOT:
                return Not(child=child)
            elif op.type == TokenType.NEXT:
                return Next(child=child)
            elif op.type == TokenType.GLOBALLY:
                return Globally(child=child)
            elif op.type == TokenType.FINALLY:
                return Finally(child=child)

        if token.type == TokenType.LPAREN:
            self.advance()
            result = self.parse_formula()
            self.expect(TokenType.RPAREN)
            return result

        raise ValueError(f"Unexpected token {token.type.name} at position {self.pos}")

    def parse_formula(self) -> ASTNode:
        """Parse a complete formula (possibly with binary operators).

        Grammar:
            - parse_primary() for left operand
            - optional binary operator + parse_formula() for right operand

        Returns:
            AST node.
        """
        left = self.parse_primary()

        if self.pos < len(self.tokens):
            op_token = self.current()
            if op_token.type in (
                TokenType.UNTIL,
                TokenType.AND,
                TokenType.OR,
                TokenType.IMPLY,
            ):
                self.advance()
                right = self.parse_formula()

                if op_token.type == TokenType.UNTIL:
                    return Until(left=left, right=right)
                elif op_token.type == TokenType.AND:
                    return And(left=left, right=right)
                elif op_token.type == TokenType.OR:
                    return Or(left=left, right=right)
                else:
                    return Imply(left=left, right=right)

        return left


def parse(formula: str) -> ASTNode:
    """Parse an LTL formula string into an AST.

    Args:
        formula: LTL formula string.

    Returns:
        Root AST node.

    Raises:
        ValueError: If there's a syntax error.
    """
    tokens = tokenize(formula)
    parser = Parser(tokens)
    return parser.parse()
