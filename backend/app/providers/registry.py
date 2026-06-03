from typing import Dict
from app.providers.base import ProviderAdapter
from app.providers.github_adapter import GitHubAdapter
from app.providers.gitlab_adapter import GitLabAdapter
from app.providers.azure_devops_adapter import AzureDevOpsAdapter


_registry: Dict[str, ProviderAdapter] = {
    "github": GitHubAdapter(),
    "gitlab": GitLabAdapter(),
    "azure_devops": AzureDevOpsAdapter(),
}


def get_adapter(provider: str) -> ProviderAdapter:
    adapter = _registry.get(provider.lower())
    if not adapter:
        raise ValueError(f"No adapter registered for provider: {provider}")
    return adapter
