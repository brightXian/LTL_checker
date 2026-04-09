"""Lexer (tokenizer) for LTL formulas."""

import re
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Token types for LTL grammar."""

    ATOM = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    IMPLY = auto()
    NEXT = auto()
    GLOBALLY = auto()
    FINALLY = auto()
    UNTIL = auto()
    LPAREN = auto()
    RPAREN = auto()


@dataclass
class Token:
    """Represents a single token."""

    type: TokenType
    value: str


def tokenize(formula: str) -> list[Token]:
    """Convert a formula string into a list of tokens.

    Args:
        formula: LTL formula string.

    Returns:
        List of tokens.

    Raises:
        ValueError: If an unexpected character is found.
    """
    tokens: list[Token] = []
    formula = formula.strip()

    # Pattern: atoms (longest match first), then multi-char operators,
    # then single-char operators, then parentheses
    pattern = r"/\\|\\/|->|[a-z][a-z0-9]*|\(|\)|!|U|X|G|F|[0-9]+"

    # Use finditer to track positions and detect gaps (unexpected characters)
    last_end = 0
    for match in re.finditer(pattern, formula):
        # Check if there's any gap between last match and this one
        if match.start() > last_end:
            # Found unexpected characters in the gap
            gap = formula[last_end : match.start()]
            # Find the first unexpected character
            for i, char in enumerate(gap):
                if char not in " \t\n\r\f\v":  # skip whitespace
                    raise ValueError(
                        f"Unexpected character '{char}' at position {last_end + i}"
                    )

        last_end = match.end()

        token_str = match.group()
        if token_str == "!":
            tokens.append(Token(TokenType.NOT, token_str))
        elif token_str == "/\\":
            tokens.append(Token(TokenType.AND, token_str))
        elif token_str == "\\/":
            tokens.append(Token(TokenType.OR, token_str))
        elif token_str == "->":
            tokens.append(Token(TokenType.IMPLY, token_str))
        elif token_str == "U":
            tokens.append(Token(TokenType.UNTIL, token_str))
        elif token_str == "X":
            tokens.append(Token(TokenType.NEXT, token_str))
        elif token_str == "G":
            tokens.append(Token(TokenType.GLOBALLY, token_str))
        elif token_str == "F":
            tokens.append(Token(TokenType.FINALLY, token_str))
        elif token_str == "(":
            tokens.append(Token(TokenType.LPAREN, token_str))
        elif token_str == ")":
            tokens.append(Token(TokenType.RPAREN, token_str))
        else:
            # Atomic proposition
            tokens.append(Token(TokenType.ATOM, token_str))

    # Check for trailing unexpected characters after last match
    if last_end < len(formula):
        remaining = formula[last_end:]
        for i, char in enumerate(remaining):
            if char not in " \t\n\r\f\v":  # skip whitespace
                raise ValueError(
                    f"Unexpected character '{char}' at position {last_end + i}"
                )

    return tokens
