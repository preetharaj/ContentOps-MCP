"""
MCP Server Registry API

Provides endpoints for discovering, searching, and monitoring MCP servers.
- GET /servers - List all servers
- GET /servers/{id} - Get specific server
- GET /servers/search - Semantic search
- POST /servers/{id}/health - Health check
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from registry.models import (
    ServerRegistry,
    REGISTRY_CATALOG,
    init_core_registry,
)

# Initialize registry on module load
init_core_registry()

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("/servers", response_model=List[Dict[str, Any]])
def list_servers(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
):
    """
    List all MCP servers with optional filtering.
    
    Query Parameters:
    - category: Filter by server category (cms, email, work_tools)
    - status: Filter by status (stable, beta, deprecated)
    - tag: Filter by tag
    """
    servers = list(REGISTRY_CATALOG.values())
    
    if category:
        servers = [s for s in servers if s.metadata.category == category]
    
    if status:
        servers = [s for s in servers if s.metadata.status == status]
    
    if tag:
        servers = [s for s in servers if tag in s.metadata.tags]
    
    return [s.to_dict() for s in servers]


@router.get("/servers/{server_id}", response_model=Dict[str, Any])
def get_server(server_id: str):
    """Get detailed information about a specific server."""
    if server_id not in REGISTRY_CATALOG:
        raise HTTPException(
            status_code=404,
            detail=f"Server '{server_id}' not found in registry"
        )
    
    server = REGISTRY_CATALOG[server_id]
    return server.to_dict()


@router.get("/servers/search/semantic")
def semantic_search(q: str) -> List[Dict[str, Any]]:
    """
    Semantic search across all servers using keywords and tags.
    
    Examples:
    - GET /servers/search/semantic?q=blog
    - GET /servers/search/semantic?q=email%20delivery
    - GET /servers/search/semantic?q=newsletter
    """
    query = q.lower().strip()
    results = []
    
    for server in REGISTRY_CATALOG.values():
        # Search in keywords, tags, name, description
        search_text = (
            " ".join(server.metadata.keywords or [])
            + " " + server.metadata.name.lower()
            + " " + server.metadata.description.lower()
            + " " + " ".join(server.metadata.tags)
        )
        
        if query in search_text:
            results.append(server.to_dict())
    
    return results


@router.post("/servers/{server_id}/health")
def check_server_health(server_id: str) -> Dict[str, Any]:
    """
    Perform health check on a specific server.
    
    Returns:
    - status: healthy, degraded, or offline
    - last_check: timestamp
    - latency_ms: response time
    """
    if server_id not in REGISTRY_CATALOG:
        raise HTTPException(
            status_code=404,
            detail=f"Server '{server_id}' not found in registry"
        )
    
    server = REGISTRY_CATALOG[server_id]
    
    # Simulate health check (in production, would call actual endpoint)
    server.last_health_check = datetime.now()
    server.health_status = "healthy" if server.is_available else "offline"
    
    return {
        "server_id": server_id,
        "status": server.health_status,
        "last_check": server.last_health_check.isoformat(),
        "available": server.is_available,
        "version": server.metadata.version,
    }


@router.get("/categories")
def list_categories() -> Dict[str, List[str]]:
    """List all available server categories and their servers."""
    categories = {}
    
    for server in REGISTRY_CATALOG.values():
        category = server.metadata.category
        if category not in categories:
            categories[category] = []
        categories[category].append(server.metadata.id)
    
    return categories


@router.get("/stats")
def registry_stats() -> Dict[str, Any]:
    """Get registry statistics."""
    servers = list(REGISTRY_CATALOG.values())
    
    stats_by_status = {}
    stats_by_category = {}
    
    for server in servers:
        status = server.metadata.status
        category = server.metadata.category
        
        stats_by_status[status] = stats_by_status.get(status, 0) + 1
        stats_by_category[category] = stats_by_category.get(category, 0) + 1
    
    return {
        "total_servers": len(servers),
        "by_status": stats_by_status,
        "by_category": stats_by_category,
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/install")
def get_install_command(
    servers: List[str] = Query(...)
) -> Dict[str, str]:
    """
    Get pip install command for specified servers.
    
    Example: GET /install?servers=ghost&servers=notion&servers=resend
    
    Returns: pip install command with all required packages
    """
    extras = set()
    found_servers = []
    
    for server_id in servers:
        if server_id not in REGISTRY_CATALOG:
            raise HTTPException(
                status_code=404,
                detail=f"Server '{server_id}' not found"
            )
        
        server = REGISTRY_CATALOG[server_id]
        found_servers.append(server_id)
        
        if server.metadata.pip_install_extra:
            extras.add(server.metadata.pip_install_extra)
    
    # Build pip install command
    if extras:
        install_cmd = f"pip install {server.metadata.package_name}[{','.join(sorted(extras))}]"
    else:
        install_cmd = f"pip install {server.metadata.package_name}"
    
    return {
        "servers": found_servers,
        "install_command": install_cmd,
        "package_name": server.metadata.package_name,
        "extras": list(extras),
    }


@router.post("/register")
def register_new_server(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Register a new MCP server in the registry.
    
    Requires:
    - id: unique identifier
    - name: display name
    - category: cms|email|work_tools|custom
    - version: semver version
    - description: brief description
    - auth_type: api_key|oauth2|basic|custom
    - status: stable|beta|deprecated
    - maintainer: organization/person
    - repository_url: GitHub/source URL
    - documentation_url: docs URL
    """
    try:
        from registry.models import register_server
        
        server = register_server(
            id=payload["id"],
            name=payload["name"],
            category=payload["category"],
            version=payload["version"],
            description=payload["description"],
            auth_type=payload["auth_type"],
            status=payload["status"],
            maintainer=payload["maintainer"],
            repo_url=payload["repository_url"],
            docs_url=payload["documentation_url"],
            mcp_version=payload.get("mcp_version", "1.0.0"),
            package_name=payload.get("package_name", "contentops-mcp"),
            pip_extra=payload.get("pip_install_extra"),
            tags=payload.get("tags", []),
        )
        
        return {
            "status": "success",
            "server_id": payload["id"],
            "message": f"Server '{payload['name']}' registered successfully",
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Registration failed: {str(e)}"
        )
