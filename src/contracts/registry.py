from dataclasses import dataclass

from pydantic import BaseModel

from .digest import Article, DateEntry, DateListResponse, DigestQueryParams, DigestResponse, DigestStats
from .github import (
    GitHubDateListResponse,
    GitHubFetchResult,
    GitHubProject,
    GitHubQueryParams,
    GitHubTrendingResponse,
    GitHubTrendingStats,
)
from .jobs import (
    GitHubFetchProgressResponse,
    GitHubFetchRunResponse,
    GitHubFetchStatusResponse,
    PipelineProgressResponse,
    PipelineRunResponse,
    PipelineStatusResponse,
)
from .settings import (
    DesktopSettingsSnapshot,
    GitHubTrendingSettings,
    LlmProviderSettings,
    LlmSettings,
    PipelineSettings,
    ValidationIssue,
    ValidationResult,
)


@dataclass(frozen=True)
class ContractDefinition:
    model: type[BaseModel]
    frontend_aliases: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        return self.model.__name__


CONTRACT_DEFINITIONS: tuple[ContractDefinition, ...] = (
    ContractDefinition(Article),
    ContractDefinition(DigestStats),
    ContractDefinition(DigestResponse, frontend_aliases=("DailyDigest",)),
    ContractDefinition(DateEntry),
    ContractDefinition(DateListResponse, frontend_aliases=("DateList",)),
    ContractDefinition(DigestQueryParams, frontend_aliases=("QueryParams",)),
    ContractDefinition(PipelineRunResponse),
    ContractDefinition(PipelineProgressResponse, frontend_aliases=("PipelineProgress",)),
    ContractDefinition(PipelineStatusResponse, frontend_aliases=("PipelineStatus",)),
    ContractDefinition(GitHubProject),
    ContractDefinition(GitHubTrendingStats),
    ContractDefinition(GitHubTrendingResponse, frontend_aliases=("GitHubTrendingData",)),
    ContractDefinition(GitHubFetchResult),
    ContractDefinition(GitHubDateListResponse),
    ContractDefinition(GitHubQueryParams),
    ContractDefinition(GitHubFetchRunResponse),
    ContractDefinition(GitHubFetchProgressResponse, frontend_aliases=("GitHubFetchProgress",)),
    ContractDefinition(GitHubFetchStatusResponse, frontend_aliases=("GitHubFetchStatus",)),
    ContractDefinition(LlmProviderSettings),
    ContractDefinition(LlmSettings),
    ContractDefinition(PipelineSettings),
    ContractDefinition(GitHubTrendingSettings),
    ContractDefinition(DesktopSettingsSnapshot),
    ContractDefinition(ValidationIssue),
    ContractDefinition(ValidationResult),
)

CONTRACT_MODELS: dict[str, type[BaseModel]] = {definition.name: definition.model for definition in CONTRACT_DEFINITIONS}

FRONTEND_COMPAT_ALIASES: dict[str, str] = {
    alias: definition.name for definition in CONTRACT_DEFINITIONS for alias in definition.frontend_aliases
}
