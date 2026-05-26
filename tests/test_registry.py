"""
Test Cases for MCP Server Registry

Demonstrates registry functionality and API usage.
"""

import json
from registry.models import (
    init_core_registry,
    REGISTRY_CATALOG,
    register_server,
)


def test_registry_initialization():
    """Test that registry initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Registry Initialization")
    print("="*60)
    
    # Initialize
    init_core_registry()
    
    # Check servers are registered
    print(f"\nServers registered: {len(REGISTRY_CATALOG)}")
    
    for server_id, server in REGISTRY_CATALOG.items():
        print(f"\n  [{server.metadata.category:12}] {server.metadata.name:15} v{server.metadata.version}")
        print(f"    Status: {server.metadata.status}")
        print(f"    Auth: {server.metadata.auth_type}")
        print(f"    Package: {server.metadata.package_name}")
        if server.metadata.pip_install_extra:
            print(f"    Install: pip install {server.metadata.package_name}[{server.metadata.pip_install_extra}]")
    
    success = len(REGISTRY_CATALOG) >= 5
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: Found {len(REGISTRY_CATALOG)} servers")
    return success


def test_server_metadata():
    """Test server metadata access."""
    print("\n" + "="*60)
    print("TEST: Server Metadata Access")
    print("="*60)
    
    init_core_registry()
    
    # Get WordPress server
    wordpress = REGISTRY_CATALOG.get("wordpress")
    
    if not wordpress:
        print("❌ FAILED: WordPress not found")
        return False
    
    print(f"\nServer: {wordpress.metadata.name}")
    print(f"  ID: {wordpress.metadata.id}")
    print(f"  Version: {wordpress.metadata.version}")
    print(f"  Status: {wordpress.metadata.status}")
    print(f"  Category: {wordpress.metadata.category}")
    print(f"  Auth Type: {wordpress.metadata.auth_type}")
    print(f"  Maintainer: {wordpress.metadata.maintainer}")
    print(f"  MCP Version: {wordpress.metadata.mcp_version}")
    print(f"  Package: {wordpress.metadata.package_name}")
    print(f"  Install Extra: {wordpress.metadata.pip_install_extra}")
    print(f"  Tags: {', '.join(wordpress.metadata.tags)}")
    
    print(f"\nAuth Config:")
    print(f"  Type: {wordpress.auth_config.auth_type}")
    print(f"  Required: {', '.join(wordpress.auth_config.required_fields)}")
    
    success = (
        wordpress.metadata.name == "WordPress" and
        wordpress.metadata.status == "stable" and
        wordpress.metadata.auth_type == "api_key"
    )
    
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    return success


def test_server_categories():
    """Test filtering by category."""
    print("\n" + "="*60)
    print("TEST: Filter by Category")
    print("="*60)
    
    init_core_registry()
    
    categories = {}
    for server in REGISTRY_CATALOG.values():
        cat = server.metadata.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(server.metadata.name)
    
    print(f"\nServers by category:")
    for cat in sorted(categories.keys()):
        servers = categories[cat]
        print(f"\n  {cat.upper()}: {len(servers)} servers")
        for server in servers:
            print(f"    - {server}")
    
    success = len(categories) >= 3
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: Found {len(categories)} categories")
    return success


def test_semantic_search():
    """Test semantic search functionality."""
    print("\n" + "="*60)
    print("TEST: Semantic Search")
    print("="*60)
    
    init_core_registry()
    
    # Search queries
    search_queries = [
        ("blog", "Blog-related servers"),
        ("email", "Email servers"),
        ("newsletter", "Newsletter servers"),
        ("workspace", "Workspace servers"),
    ]
    
    all_passed = True
    
    for query, description in search_queries:
        print(f"\nSearching for: '{query}' ({description})")
        
        # Simulate semantic search
        results = []
        for server in REGISTRY_CATALOG.values():
            search_text = (
                " ".join(server.metadata.keywords or [])
                + " " + server.metadata.name.lower()
                + " " + server.metadata.description.lower()
                + " " + " ".join(server.metadata.tags)
            )
            
            if query in search_text:
                results.append(server.metadata.name)
        
        if results:
            print(f"  Results: {', '.join(results)}")
        else:
            print(f"  No results found")
            all_passed = False
    
    print(f"\n{'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed


def test_install_command_generation():
    """Test pip install command generation."""
    print("\n" + "="*60)
    print("TEST: Install Command Generation")
    print("="*60)
    
    init_core_registry()
    
    # Simulate getting install command for multiple servers
    server_ids = ["wordpress", "notion", "resend"]
    
    extras = set()
    found_servers = []
    
    for server_id in server_ids:
        if server_id in REGISTRY_CATALOG:
            server = REGISTRY_CATALOG[server_id]
            found_servers.append(server_id)
            
            if server.metadata.pip_install_extra:
                extras.add(server.metadata.pip_install_extra)
    
    # Generate command
    if found_servers and extras:
        package_name = REGISTRY_CATALOG[found_servers[0]].metadata.package_name
        install_cmd = f"pip install {package_name}[{','.join(sorted(extras))}]"
    else:
        package_name = REGISTRY_CATALOG[found_servers[0]].metadata.package_name
        install_cmd = f"pip install {package_name}"
    
    print(f"\nRequested servers: {', '.join(server_ids)}")
    print(f"Found servers: {', '.join(found_servers)}")
    print(f"Extras: {', '.join(sorted(extras))}")
    print(f"\nInstall command:")
    print(f"  {install_cmd}")
    
    success = "wordpress" in install_cmd and "notion" in install_cmd and "resend" in install_cmd
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    return success


def test_registry_export():
    """Test exporting registry to JSON."""
    print("\n" + "="*60)
    print("TEST: Registry Export to JSON")
    print("="*60)
    
    init_core_registry()
    
    # Export registry
    registry_data = {}
    for server_id, server in REGISTRY_CATALOG.items():
        registry_data[server_id] = server.to_dict()
    
    # Show sample
    print(f"\nTotal servers in export: {len(registry_data)}")
    
    # Show one example
    wordpress_data = registry_data.get("wordpress")
    if wordpress_data:
        print(f"\nExample (WordPress):")
        print(f"  {json.dumps(wordpress_data, indent=4)[:500]}...")
    
    success = len(registry_data) >= 5
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    return success


def test_register_new_server():
    """Test registering a new custom server."""
    print("\n" + "="*60)
    print("TEST: Register New Server")
    print("="*60)
    
    init_core_registry()
    
    initial_count = len(REGISTRY_CATALOG)
    
    # Register new server
    new_server = register_server(
        id="custom-cms",
        name="Custom CMS",
        category="cms",
        version="0.1.0",
        description="A custom CMS integration",
        auth_type="api_key",
        status="beta",
        maintainer="test-org",
        repo_url="https://github.com/test-org/custom-cms",
        docs_url="https://docs.test-org.com/custom-cms",
        mcp_version="1.0.0",
        package_name="custom-mcp",
        pip_extra="custom",
        tags=["custom", "cms", "test"],
    )
    
    new_count = len(REGISTRY_CATALOG)
    
    print(f"\nInitial server count: {initial_count}")
    print(f"After registration: {new_count}")
    
    print(f"\nNew server registered:")
    print(f"  ID: {new_server.metadata.id}")
    print(f"  Name: {new_server.metadata.name}")
    print(f"  Category: {new_server.metadata.category}")
    print(f"  Version: {new_server.metadata.version}")
    print(f"  Status: {new_server.metadata.status}")
    
    success = new_count == initial_count + 1 and "custom-cms" in REGISTRY_CATALOG
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    return success


def test_health_status():
    """Test health status tracking."""
    print("\n" + "="*60)
    print("TEST: Health Status Tracking")
    print("="*60)
    
    init_core_registry()
    
    print(f"\nServer health status:")
    
    health_statuses = {}
    for server in REGISTRY_CATALOG.values():
        status = server.health_status
        health_statuses[status] = health_statuses.get(status, 0) + 1
        print(f"  {server.metadata.name:15} — {status:10} ({server.metadata.version})")
    
    print(f"\nHealth summary:")
    for status, count in sorted(health_statuses.items()):
        print(f"  {status}: {count}")
    
    success = len(health_statuses) > 0
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    return success


def run_all_tests():
    """Run all registry tests."""
    print("\n" + "="*60)
    print("MCP SERVER REGISTRY TEST SUITE")
    print("="*60)
    
    tests = [
        ("Registry Initialization", test_registry_initialization),
        ("Server Metadata", test_server_metadata),
        ("Server Categories", test_server_categories),
        ("Semantic Search", test_semantic_search),
        ("Install Command Generation", test_install_command_generation),
        ("Registry Export", test_registry_export),
        ("Register New Server", test_register_new_server),
        ("Health Status", test_health_status),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = passed
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} passed")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    import sys
    sys.exit(0 if success else 1)
