"""
IRSA (IAM Roles for Service Accounts) credential acquisition for Kubernetes/EKS.

This module exchanges a Kubernetes-injected web identity token for temporary AWS
credentials via STS AssumeRoleWithWebIdentity, enabling Marvin to run inside a
pod without static AWS keys.

Supported partitions:
- Commercial (us-east-1, eu-west-1, etc.) - fully supported
- GovCloud (us-gov-east-1, us-gov-west-1) - fully supported; STS endpoints follow
  the same sts.{region}.amazonaws.com pattern and the XML namespace is identical

Not supported by default:
- China (cn-north-1, cn-northwest-1) - STS uses amazonaws.com.cn, which breaks
  the auto-generated endpoint pattern.

Override: set AWS_ENDPOINT_URL_STS to any custom STS URL (e.g. a FIPS endpoint
like https://sts-fips.us-east-1.amazonaws.com or a China endpoint) to bypass
the auto-generated regional URL entirely.
"""
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import httpx

from marvin.libs.aws.signv4 import AwsCredentials

_STS_NS = {"sts": "https://sts.amazonaws.com/doc/2011-06-15/"}
_STS_VERSION = "2011-06-15"


class IRSACredentialsError(Exception):
    pass


def _sts_endpoint(region: str) -> str:
    # AWS_ENDPOINT_URL_STS overrides the auto-generated endpoint. Use this for
    # FIPS endpoints (e.g. https://sts-fips.us-east-1.amazonaws.com) or any
    # custom STS URL, including China (amazonaws.com.cn).
    override = os.environ.get("AWS_ENDPOINT_URL_STS")
    if override:
        return override.rstrip("/") + "/"
    if region.startswith("cn-"):
        raise IRSACredentialsError(
            f"China region {region!r} is not supported via automatic STS endpoint "
            "construction (STS uses amazonaws.com.cn, not amazonaws.com). "
            "Set AWS_ENDPOINT_URL_STS to the correct China STS endpoint "
            "(e.g. https://sts.cn-north-1.amazonaws.com.cn)."
        )
    return f"https://sts.{region}.amazonaws.com/"


async def assume_irsa_credentials(
    region: str,
    verify: bool | str = True,
    proxy_url: str | None = None,
    timeout: float = 120,
) -> AwsCredentials:
    token_file = os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE")
    role_arn = os.environ.get("AWS_ROLE_ARN")

    if not token_file:
        raise IRSACredentialsError(
            "AWS_WEB_IDENTITY_TOKEN_FILE is not set. "
            "Ensure the pod is configured with an IRSA service account."
        )
    if not role_arn:
        raise IRSACredentialsError(
            "AWS_ROLE_ARN is not set. "
            "Ensure the pod is configured with an IRSA service account."
        )

    try:
        token = Path(token_file).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise IRSACredentialsError(
            f"Could not read web identity token file at {token_file!r}: {exc}"
        ) from exc

    session_name = os.environ.get("AWS_ROLE_SESSION_NAME") or f"marvin-{os.getpid()}"

    try:
        async with httpx.AsyncClient(verify=verify, proxy=proxy_url, timeout=timeout) as client:
            response = await client.post(
                _sts_endpoint(region),
                content=_build_form_body(role_arn, token, session_name),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as exc:
        raise IRSACredentialsError(
            f"STS request failed: {type(exc).__name__}: {exc}"
        ) from exc

    if response.status_code != 200:
        aws_error = _extract_aws_error(response.text)
        raise IRSACredentialsError(
            f"STS returned HTTP {response.status_code}{aws_error}. "
            "Check that the IAM role trust policy allows this service account."
        )

    return _parse_sts_response(response.text)


def _build_form_body(role_arn: str, token: str, session_name: str) -> bytes:
    params = {
        "Action": "AssumeRoleWithWebIdentity",
        "Version": _STS_VERSION,
        "RoleArn": role_arn,
        "WebIdentityToken": token,
        "RoleSessionName": session_name,
    }
    return urlencode(params).encode()


def _extract_aws_error(xml_text: str) -> str:
    """Best-effort extraction of AWS error Code and Message from an STS error response."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return ""
    # STS error responses use no namespace on the Error element
    code_el = root.find(".//Code")
    message_el = root.find(".//Message")
    code = code_el.text if code_el is not None and code_el.text else ""
    message = message_el.text if message_el is not None and message_el.text else ""
    if code or message:
        return f" ({code}: {message})" if code and message else f" ({code or message})"
    return ""


def _parse_sts_response(xml_text: str) -> AwsCredentials:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise IRSACredentialsError(
            f"STS response could not be parsed as XML: {exc}"
        ) from exc

    creds_el = root.find(".//sts:Credentials", _STS_NS)
    if creds_el is None:
        raise IRSACredentialsError(
            "STS response did not contain a Credentials element. "
            "Verify the IAM role and OIDC provider configuration."
        )

    def _text(tag: str) -> str:
        el = creds_el.find(f"sts:{tag}", _STS_NS)
        if el is None or el.text is None:
            raise IRSACredentialsError(
                f"STS Credentials element is missing expected field: {tag}"
            )
        return el.text

    return AwsCredentials(
        access_key=_text("AccessKeyId"),
        secret_key=_text("SecretAccessKey"),
        session_token=_text("SessionToken"),
    )
