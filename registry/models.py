"""
MCP Server Registry Models and Metadata

Defines the structure for all MCP servers in the content operations ecosystem.
Supports semantic search, versioning, and health checks.
"""

from typing import List, Dict, Any, Literal, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# Server Category Types
ServerCategory = Literal["cms", "email", "work_tools", "analytics", "payment", "custom"]

# CMS Servers
CMS_SERVERS = {
    "ghost": "Ghost Blog Platform",
    "wordpress": "WordPress CMS",
    "webflow": "Webflow CMS",
    "beehiiv": "Beehiiv Newsletter",
    "substack": "Substack Newsletter",
}

# Email Servers
EMAIL_SERVERS = {
    "resend": "Resend Email API",
    "loops": "Loops Email Platform",
    "mailchimp": "Mailchimp Email",
}

# Work Tools
WORK_TOOL_SERVERS = {
    "notion": "Notion Workspace",
    "linear": "Linear Issue Tracking",
    "coda": "Coda Workspace",
}


@dataclass
class ServerMetadata:
    """Core metadata for an MCP server."""
    id: str
    name: str
    category: ServerCategory
    version: str
    description: str
    auth_type: Literal["api_key", "oauth2", "basic", "custom"]
    status: Literal["stable", "beta", "deprecated"]
    maintainer: str
    repository_url: str
    documentation_url: str
    mcp_version: str  # e.g., "1.0.0"
    mcp_compatibility: List[str]  # [">= 1.0.0", "< 2.0.0"]
    
    # Package info
    package_name: str
    pip_install_extra: Optional[str] = None  # e.g., "ghost", "wordpress"
    
    # Tags for semantic search
    tags: List[str] = None
    keywords: List[str] = None
    
    # Release info
    released_at: datetime = None
    updated_at: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.released_at:
            data["released_at"] = self.released_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        return data


@dataclass
class HealthCheckConfig:
    """Health check configuration for servers."""
    endpoint: str
    method: str = "GET"
    expected_status: int = 200
    timeout_seconds: int = 5
    retry_count: int = 3
    interval_seconds: int = 3600


@dataclass
class AuthConfig:
    """Authentication configuration."""
    auth_type: str
    required_fields: List[str]
    optional_fields: List[str] = None
    docs_url: str = None
    example_key: str = None


@dataclass
class ServerRegistry:
    """Complete server entry with metadata and config."""
    metadata: ServerMetadata
    auth_config: AuthConfig
    health_check: Optional[HealthCheckConfig] = None
    
    # Runtime state
    is_available: bool = True
    last_health_check: Optional[datetime] = None
    health_status: Literal["healthy", "degraded", "offline"] = "healthy"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "auth_config": asdict(self.auth_config),
            "health_check": asdict(self.health_check) if self.health_check else None,
            "is_available": self.is_available,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_status": self.health_status,
        }


# Predefined server registry catalog
REGISTRY_CATALOG: Dict[str, ServerRegistry] = {}


def register_server(
    id: str,
    name: str,
    category: ServerCategory,
    version: str,
    description: str,
    auth_type: str,
    status: str,
    maintainer: str,
    repo_url: str,
    docs_url: str,
    mcp_version: str,
    package_name: str,
    pip_extra: Optional[str] = None,
    tags: List[str] = None,
    health_endpoint: Optional[str] = None,
) -> ServerRegistry:
    """Register a new MCP server in the catalog."""
    
    metadata = ServerMetadata(
        id=id,
        name=name,
        category=category,
        version=version,
        description=description,
        auth_type=auth_type,
        status=status,
        maintainer=maintainer,
        repository_url=repo_url,
        documentation_url=docs_url,
        mcp_version=mcp_version,
        mcp_compatibility=[f">= {mcp_version}"],
        package_name=package_name,
        pip_install_extra=pip_extra,
        tags=tags or [],
        keywords=(tags or []) + [name.lower(), category],
        released_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    auth_config = AuthConfig(
        auth_type=auth_type,
        required_fields=["api_key"] if auth_type == "api_key" else [],
        optional_fields=[],
        docs_url=f"{docs_url}#authentication",
    )
    
    health_check = None
    if health_endpoint:
        health_check = HealthCheckConfig(
            endpoint=health_endpoint,
            method="GET",
            expected_status=200,
            timeout_seconds=5,
        )
    
    server = ServerRegistry(
        metadata=metadata,
        auth_config=auth_config,
        health_check=health_check,
    )
    
    REGISTRY_CATALOG[id] = server
    return server


# Initialize core servers
def init_core_registry():
    """Initialize the core MCP server registry."""
    
    # CMS Servers
    register_server(
        id="wordpress",
        name="WordPress",
        category="cms",
        version="1.0.0",
        description="WordPress REST API integration for content management",
        auth_type="api_key",
        status="stable",
        maintainer="ContentOps",
        repo_url="https://github.com/contentops/wordpress-mcp",
        docs_url="https://registry.contentops.dev/docs/wordpress",
        mcp_version="1.0.0",
        package_name="contentops-mcp",
        pip_extra="wordpress",
        tags=["cms", "blog", "content"],
        health_endpoint="https://api.wordpress.com/health",
    )
    
    register_server(
        id="ghost",
        name="Ghost",
        category="cms",
        version="1.0.0",
        description="Ghost CMS integration for content publishing",
        auth_type="api_key",
        status="stable",
        maintainer="ContentOps",
        repo_url="https://github.com/contentops/ghost-mcp",
        docs_url="https://registry.contentops.dev/docs/ghost",
        mcp_version="1.0.0",
        package_name="contentops-mcp",
        pip_extra="ghost",
        tags=["cms", "blog", "newsletter"],
    )
    
    register_server(
        id="notion",
        name="Notion",
        category="work_tools",
        version="1.0.0",
        description="Notion workspace integration for content planning",
        auth_type="oauth2",
        status="stable",
        maintainer="ContentOps",
        repo_url="https://github.com/contentops/notion-mcp",
        docs_url="https://registry.contentops.dev/docs/notion",
        mcp_version="1.0.0",
        package_name="contentops-mcp",
        pip_extra="notion",
        tags=["workspace", "planning", "database"],
    )
    
    # Email Servers
    register_server(
        id="resend",
        name="Resend",
        category="email",
        version="1.0.0",
        description="Resend email API for campaign delivery",
        auth_type="api_key",
        status="stable",
        maintainer="ContentOps",
        repo_url="https://github.com/contentops/resend-mcp",
        docs_url="https://registry.contentops.dev/docs/resend",
        mcp_version="1.0.0",
        package_name="contentops-mcp",
        pip_extra="resend",
        tags=["email", "delivery", "marketing"],
    )
    
    register_server(
        id="slack",
        name="Slack",
        category="work_tools",
        version="1.0.0",
        description="Slack integration for team notifications",
        auth_type="oauth2",
        status="stable",
        maintainer="ContentOps",
        repo_url="https://github.com/contentops/slack-mcp",
        docs_url="https://registry.contentops.dev/docs/slack",
        mcp_version="1.0.0",
        package_name="contentops-mcp",
        pip_extra="slack",
        tags=["messaging", "notifications", "integration"],
    )
