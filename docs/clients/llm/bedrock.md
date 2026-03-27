# AWS Bedrock

## Authentication

Bedrock supports two auth paths. **Static credentials take precedence** when both are configured; IRSA is used when no static credentials are set.

### Static credentials

```yaml
llm:
  provider: BEDROCK
  http_client:
    region: us-east-1
    access_key: ${AWS_ACCESS_KEY_ID}
    secret_key: ${AWS_SECRET_ACCESS_KEY}
    session_token: ${AWS_SESSION_TOKEN}   # optional, for temporary credentials
```

Providing only one of `access_key` / `secret_key` is a config error and fails at startup.

### IRSA (Kubernetes / EKS)

Omit `access_key` and `secret_key`. Kubernetes injects the required env vars automatically when the pod is configured with an IRSA service account.

```yaml
llm:
  provider: BEDROCK
  http_client:
    region: us-east-1
```

Required env vars (injected by EKS):

| Variable | Description |
|---|---|
| `AWS_WEB_IDENTITY_TOKEN_FILE` | Path to the pod's OIDC token file |
| `AWS_ROLE_ARN` | IAM role to assume |
| `AWS_ROLE_SESSION_NAME` | Session name (optional; defaults to `marvin-{pid}`) |

Credentials are fetched once via STS `AssumeRoleWithWebIdentity` and cached for the process lifetime. No credential refresh is performed (Marvin is short-lived).

## Partitions and endpoints

| Partition | Support | Notes |
|---|---|---|
| Commercial (us-east-1, etc.) | Full | Auto-generated endpoint |
| GovCloud (us-gov-*) | Full | Same `sts.{region}.amazonaws.com` pattern |
| FIPS | Via override | Set `AWS_ENDPOINT_URL_STS` |
| China (cn-*) | Via override | Set `AWS_ENDPOINT_URL_STS` |

`AWS_ENDPOINT_URL_STS` overrides the auto-generated STS endpoint entirely. Use it for FIPS
(`https://sts-fips.us-east-1.amazonaws.com`) or China (`https://sts.cn-north-1.amazonaws.com.cn`).
Without this override, `cn-*` regions raise an error at credential acquisition time.
