import base64


def build_basic_credentials(token: str) -> str:
    return base64.b64encode(f":{token}".encode()).decode("ascii")
