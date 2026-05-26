"""
Phase 3 Application - MCP Registry + QA Draft-to-Publish Gate

Simple Flask/FastAPI application to run both systems.
Start with: python app.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json

# ============================================================================
# IMPORTS - Phase 3 Systems
# ============================================================================

try:
    from registry_api.api import router as registry_router
    from qa.api import router as qa_router
    from registry.models import init_core_registry, REGISTRY_CATALOG
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project root directory:")
    print("  cd c:\\Projects\\mcp-inspired-contentops")
    raise


# ============================================================================
# STARTUP/SHUTDOWN LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    
    # ==== STARTUP ====
    print("\n" + "="*70)
    print("🚀 STARTING PHASE 3 APPLICATION")
    print("="*70 + "\n")
    
    # Initialize Registry
    print("📦 Initializing MCP Server Registry...")
    try:
        init_core_registry()
        server_count = len(REGISTRY_CATALOG)
        print(f"✅ Registry initialized with {server_count} servers")
        
        # List servers
        for server_id, server in REGISTRY_CATALOG.items():
            print(f"   • {server.metadata.name:15} ({server.metadata.category})")
    except Exception as e:
        print(f"❌ Registry initialization failed: {e}")
    
    # Initialize QA Gate
    print("\n🔍 Initializing QA Draft-to-Publish Gate...")
    try:
        from qa.api import qa_pipeline
        agent_count = len(qa_pipeline.agents)
        print(f"✅ QA Gate initialized with {agent_count} agents")
        
        # List agents
        for agent in qa_pipeline.agents:
            print(f"   • {agent.name:25} (weight: {agent.weight})")
    except Exception as e:
        print(f"❌ QA Gate initialization failed: {e}")
    
    print("\n" + "="*70)
    print("🌐 ENDPOINTS AVAILABLE:")
    print("="*70)
    print("\n📦 REGISTRY:")
    print("  GET  /registry/servers")
    print("  GET  /registry/servers/{id}")
    print("  GET  /registry/servers/search/semantic?q=<query>")
    print("  POST /registry/servers/{id}/health")
    print("  GET  /registry/install?servers=<ids>")
    print("  GET  /registry/categories")
    print("  GET  /registry/stats")
    print("  POST /registry/register")
    
    print("\n🔍 QA GATE:")
    print("  POST /qa/check")
    print("  POST /qa/check/full")
    print("  GET  /qa/agents")
    print("  POST /qa/agents/{name}/check")
    print("  GET  /qa/rules")
    print("  POST /qa/rules/update")
    print("  GET  /qa/scores/weights")
    print("  POST /qa/scores/weights/update")
    print("  POST /qa/batch/check")
    print("  GET  /qa/summary")
    
    print("\n" + "="*70)
    print("✅ APPLICATION READY")
    print("="*70)
    print("\n📝 TEST QUERIES:")
    print("  See: QUICK_TEST_QUERIES.md for copy-paste queries")
    print("  Or:  PHASE3_TESTING_GUIDE.md for detailed instructions")
    print("\n")
    
    yield
    
    # ==== SHUTDOWN ====
    print("\n" + "="*70)
    print("⏹️  SHUTTING DOWN APPLICATION")
    print("="*70 + "\n")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Content Operations - Phase 3",
    description="MCP Server Registry + AI Draft-to-Publish QA Gate",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MOUNT ROUTERS - Phase 3 Systems
# ============================================================================

try:
    app.include_router(registry_router)     # /registry/*
    app.include_router(qa_router)           # /qa/*
    print("✅ Routers mounted")
except Exception as e:
    print(f"❌ Router mounting failed: {e}")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
def root():
    """Root endpoint - API status."""
    return {
        "status": "running",
        "version": "0.3.0",
        "systems": {
            "registry": "active",
            "qa_gate": "active"
        },
        "endpoints": {
            "registry": "/registry/*",
            "qa_gate": "/qa/*",
            "documentation": "/docs"
        }
    }


# ============================================================================
# STATUS ENDPOINT
# ============================================================================

@app.get("/status")
def status():
    """System status and capabilities."""
    from qa.api import qa_pipeline
    
    return {
        "status": "healthy",
        "version": "0.3.0",
        "systems": {
            "orchestrator": "active",
            "registry": {
                "status": "active",
                "servers": len(REGISTRY_CATALOG),
                "servers_list": [s for s in REGISTRY_CATALOG.keys()],
            },
            "qa_gate": {
                "status": "active",
                "agents": len(qa_pipeline.agents),
                "agents_list": [a.name for a in qa_pipeline.agents],
            },
        },
        "endpoints": {
            "registry": 8,
            "qa_gate": 12,
            "total": 20,
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        }
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.3.0"}


# ============================================================================
# MAIN - Run the app
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    print(f"\n📡 Starting FastAPI server on http://0.0.0.0:{port}\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )

# ============================================================================
# QUICK REFERENCE
# ============================================================================

"""
START THE SERVER:
  python app.py
  
  Or with custom port:
  python app.py 8001

TEST ENDPOINTS:
  
  Registry:
    curl http://localhost:8000/registry/servers | jq
    curl http://localhost:8000/registry/servers/wordpress | jq
    curl "http://localhost:8000/registry/servers/search/semantic?q=email" | jq
  
  QA Gate:
    curl -X POST http://localhost:8000/qa/check \
      -H "Content-Type: application/json" \
      -d '{"content": "Your article...", "title": "Title"}' | jq
    
    curl http://localhost:8000/qa/agents | jq

DOCUMENTATION:
  http://localhost:8000/docs          (Swagger UI)
  http://localhost:8000/redoc         (ReDoc)
  
  Or see:
    - QUICK_TEST_QUERIES.md (copy-paste queries)
    - PHASE3_TESTING_GUIDE.md (detailed guide)
    - docs/REGISTRY.md (registry docs)
    - docs/QA_GATE.md (QA docs)
"""
