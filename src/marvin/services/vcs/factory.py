from marvin.config import settings
from marvin.libs.constants.vcs_provider import VCSProvider
from marvin.services.vcs.azure_devops.client import AzureDevOpsVCSClient
from marvin.services.vcs.bitbucket_cloud.client import BitbucketCloudVCSClient
from marvin.services.vcs.bitbucket_server.client import BitbucketServerVCSClient
from marvin.services.vcs.gitea.client import GiteaVCSClient
from marvin.services.vcs.github.client import GitHubVCSClient
from marvin.services.vcs.gitlab.client import GitLabVCSClient
from marvin.services.vcs.types import VCSClientProtocol


def get_vcs_client() -> VCSClientProtocol:
    match settings.vcs.provider:
        case VCSProvider.GITEA:
            return GiteaVCSClient()
        case VCSProvider.GITLAB:
            return GitLabVCSClient()
        case VCSProvider.GITHUB:
            return GitHubVCSClient()
        case VCSProvider.AZURE_DEVOPS:
            return AzureDevOpsVCSClient()
        case VCSProvider.BITBUCKET_CLOUD:
            return BitbucketCloudVCSClient()
        case VCSProvider.BITBUCKET_SERVER:
            return BitbucketServerVCSClient()
        case _:
            raise ValueError(f"Unsupported VCS provider: {settings.vcs.provider}")
