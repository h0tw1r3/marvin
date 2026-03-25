from enum import StrEnum


class TokenType(StrEnum):
    """Authentication scheme to use when sending requests to a VCS API.

    AUTO  - inspect the token at runtime: if it decodes as a valid
            Base64 ``username:password`` string, use Basic auth;
            otherwise fall back to Bearer.
    BEARER - always send ``Authorization: Bearer <token>``.
    BASIC  - always send ``Authorization: Basic <token>`` (token must
             already be Base64-encoded ``username:password``).
    """

    AUTO = "auto"
    BEARER = "bearer"
    BASIC = "basic"
