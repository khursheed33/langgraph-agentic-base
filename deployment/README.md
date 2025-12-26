# Deployment Guide

This directory contains all Docker-related deployment files for the LangGraph Agentic Base application.

## Structure

- `Dockerfile` - Main application Docker image definition
- `docker-compose.yml` - Main application service (LangGraph API)
- `docker-compose.dependencies.yml` - External dependencies (Neo4j, etc.)

## Quick Start

### 1. Start Dependencies First

Start Neo4j and other dependencies:

```bash
cd deployment
docker-compose -f docker-compose.dependencies.yml up -d
```

### 2. Start the Application

Start the main application:

```bash
docker-compose -f docker-compose.yml up -d
```

### 3. Start Everything Together

You can also start everything at once using multiple compose files:

```bash
cd deployment
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml up -d
```

## Individual Service Management

### Start Only Dependencies

```bash
cd deployment
docker-compose -f docker-compose.dependencies.yml up -d
```

### Start Only Application

```bash
cd deployment
docker-compose -f docker-compose.yml up -d
```

### Stop Services

```bash
# Stop application
docker-compose -f docker-compose.yml down

# Stop dependencies
docker-compose -f docker-compose.dependencies.yml down

# Stop everything
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml down
```

### View Logs

```bash
# Application logs
docker-compose -f docker-compose.yml logs -f

# Dependencies logs
docker-compose -f docker-compose.dependencies.yml logs -f

# All logs
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml logs -f
```

## Environment Variables

Both compose files read from the `.env` file in the project root (one level up from `deployment/`).

You can specify a custom `.env` file path:

```bash
ENV_FILE=/path/to/your/.env docker-compose -f docker-compose.yml up -d
```

## Network Configuration

The application and dependencies share the `langgraph-network` network:

- **Dependencies compose file** creates the network
- **Application compose file** uses the existing network

This allows the application to connect to Neo4j using the service name `neo4j`.

## Rebuilding the Application

After making code changes:

```bash
cd deployment
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d
```

## Production Deployment

For production, consider:

1. **Use specific image tags** instead of `latest`
2. **Set resource limits** in compose files
3. **Use Docker secrets** for sensitive data
4. **Configure log rotation**
5. **Set up monitoring and alerting**
6. **Use a reverse proxy** (nginx, traefik) in front of the API

## Troubleshooting

### Network Not Found

If you see "network langgraph-network not found":

```bash
# Start dependencies first to create the network
docker-compose -f docker-compose.dependencies.yml up -d
```

### Application Can't Connect to Neo4j

1. Verify Neo4j is running: `docker ps | grep neo4j`
2. Check network: `docker network inspect langgraph-network`
3. Verify service name: The app connects to `neo4j:7687` (service name, not container name)

### Port Conflicts

If ports are already in use, update the `.env` file:

```env
API_PORT=3302
NEO4J_HTTP_PORT=7475
NEO4J_BOLT_PORT=7688
```

## File Paths

All paths in the compose files are relative to the `deployment/` directory:

- `context: ..` - Build context is the project root
- `dockerfile: deployment/Dockerfile` - Dockerfile location
- `../.env` - Environment file in project root
- `../logs` - Logs directory in project root
- `../tasks` - Tasks directory in project root

