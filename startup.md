# Startup Guide

This guide will help you get the LangGraph Agentic Base system up and running using Docker.

## Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- At least one LLM API key (Groq, OpenAI, or Anthropic)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd langgraph-agentic-base
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` file and set your API keys:

```env
# Required: At least one LLM API key
GROQ_API_KEY=your_groq_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Customize Neo4j password (default: password)
NEO4J_PASSWORD=your_secure_password
NEO4J_AUTH=neo4j/your_secure_password

# Optional: Customize API port (default: 3301)
API_PORT=3301
```

**Important Notes:**
- Docker Compose reads the `.env` file path specified in `docker-compose.yml` (defaults to `.env` in project root)
- You can specify a custom `.env` file path by setting `ENV_FILE` environment variable:
  ```bash
  ENV_FILE=/path/to/your/.env docker-compose up -d
  ```
- Environment variables in `.env` will be loaded into containers
- Variables in the `environment:` section override `.env` file values
- Shell environment variables take highest precedence

### 3. Start the Services

The deployment files are organized in the `deployment/` folder with separate compose files for the application and dependencies.

**Start Dependencies First (Neo4j):**

```bash
cd deployment
docker-compose -f docker-compose.dependencies.yml up -d
```

**Start the Application:**

```bash
docker-compose -f docker-compose.yml up -d
```

**Or Start Everything Together:**

```bash
cd deployment
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml up -d
```

**Using a Custom .env File Path:**

If your `.env` file is in a different location, specify it using the `ENV_FILE` environment variable:

```bash
# Use a custom .env file path
cd deployment
ENV_FILE=/path/to/your/.env docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml up -d

# Or export it first
export ENV_FILE=/path/to/your/.env
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml up -d
```

This will:
- Build the LangGraph API container
- Pull and start Neo4j Community Edition with APOC plugin
- Create necessary volumes for data persistence
- Set up networking between services
- Load environment variables from the specified `.env` file (defaults to `.env` in project root)

**Note:** See [deployment/README.md](deployment/README.md) for detailed deployment instructions.

### 4. Verify Services are Running

Check container status:

```bash
docker-compose ps
```

You should see both services running:
- `langgraph-agentic-base` (API service)
- `langgraph-neo4j` (Neo4j database)

### 5. Check Service Health

View logs to ensure everything started correctly:

```bash
# API service logs
docker-compose logs langgraph-api

# Neo4j logs
docker-compose logs neo4j

# Follow logs in real-time
docker-compose logs -f
```

### 6. Access the Services

- **API**: http://localhost:3301
- **API Documentation**: http://localhost:3301/docs
- **API Health Check**: http://localhost:3301/health
- **Neo4j Browser**: http://localhost:7474
- **Neo4j Bolt**: bolt://localhost:7687

## Default Credentials

- **Neo4j Username**: `neo4j`
- **Neo4j Password**: `password` (change this in production!)

## Environment Variables

Docker Compose reads environment variables in this order (highest priority first):

1. **Shell environment variables** (exported in your terminal)
2. **`.env` file** (in project root)
3. **Defaults** (in `docker-compose.yml`)

### Available Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENV_FILE` | Path to .env file | `.env` | No |
| `GROQ_API_KEY` | Groq API key | - | Yes* |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes* |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | Yes* |
| `NEO4J_URI` | Neo4j connection URI | `bolt://neo4j:7687` | No |
| `NEO4J_USER` | Neo4j username | `neo4j` | No |
| `NEO4J_PASSWORD` | Neo4j password | `password` | No |
| `NEO4J_AUTH` | Neo4j auth (user/pass) | `neo4j/password` | No |
| `API_HOST` | API bind host | `0.0.0.0` | No |
| `API_PORT` | API port | `3301` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `NEO4J_HTTP_PORT` | Neo4j HTTP port | `7474` | No |
| `NEO4J_BOLT_PORT` | Neo4j Bolt port | `7687` | No |

*At least one LLM API key is required

## Common Operations

### Stop Services

```bash
cd deployment

# Stop application
docker-compose -f docker-compose.yml stop

# Stop dependencies
docker-compose -f docker-compose.dependencies.yml stop

# Stop everything
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml stop
```

### Start Services

```bash
cd deployment

# Start dependencies first
docker-compose -f docker-compose.dependencies.yml start

# Then start application
docker-compose -f docker-compose.yml start
```

### Restart Services

```bash
cd deployment
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml restart
```

### Stop and Remove Containers

```bash
cd deployment

# Stop and remove application
docker-compose -f docker-compose.yml down

# Stop and remove dependencies
docker-compose -f docker-compose.dependencies.yml down

# Stop and remove everything
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml down
```

### Stop and Remove Containers + Volumes

**Warning**: This will delete all Neo4j data!

```bash
cd deployment
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml down -v
```

### Rebuild Containers

After making changes to the Dockerfile or code:

```bash
cd deployment
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d
```

### View Logs

```bash
cd deployment

# Application logs
docker-compose -f docker-compose.yml logs -f

# Dependencies logs
docker-compose -f docker-compose.dependencies.yml logs -f

# All logs
docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml logs -f
```

### Execute Commands in Containers

```bash
cd deployment

# Access API container shell
docker-compose -f docker-compose.yml exec langgraph-api bash

# Access Neo4j container shell
docker-compose -f docker-compose.dependencies.yml exec neo4j bash

# Run Cypher queries
docker-compose -f docker-compose.dependencies.yml exec neo4j cypher-shell -u neo4j -p password
```

## Troubleshooting

### Neo4j Container Fails to Start

**Issue**: Container shows as unhealthy or fails to start

**Solutions**:
1. Check Neo4j logs: `cd deployment && docker-compose -f docker-compose.dependencies.yml logs neo4j`
2. Ensure password is not the default `neo4j` (Neo4j requires a different password)
3. Remove volumes and restart: `cd deployment && docker-compose -f docker-compose.dependencies.yml down -v && docker-compose -f docker-compose.dependencies.yml up -d`
4. Check if ports 7474 and 7687 are already in use
5. Ensure dependencies are started before the application

### API Container Fails to Start

**Issue**: API service fails health checks

**Solutions**:
1. Check API logs: `cd deployment && docker-compose -f docker-compose.yml logs langgraph-api`
2. Verify API key is set in `.env` file
3. Check if port 3301 is already in use
4. Rebuild the container: `cd deployment && docker-compose -f docker-compose.yml build langgraph-api`
5. Ensure Neo4j is running and the network exists: `docker network ls | grep langgraph-network`

### Environment Variables Not Working

**Issue**: Changes to `.env` file not taking effect

**Solutions**:
1. Restart containers: `cd deployment && docker-compose -f docker-compose.dependencies.yml -f docker-compose.yml restart`
2. Ensure `.env` file path is correct (defaults to `.env` in project root, one level up from `deployment/`)
3. If using a custom path, verify `ENV_FILE` environment variable is set correctly
4. Check for typos in variable names
5. Verify no conflicting shell environment variables
6. Check that `env_file` directive in compose files points to the correct file (`../.env` by default)

### Port Already in Use

**Issue**: Error about ports being already in use

**Solutions**:
1. Change ports in `.env` file:
   ```env
   API_PORT=3302
   NEO4J_HTTP_PORT=7475
   NEO4J_BOLT_PORT=7688
   ```
2. Or stop the service using the port

### Neo4j APOC Plugin Not Loading

**Issue**: APOC procedures not available

**Solutions**:
1. Check Neo4j logs for plugin installation messages
2. Verify `NEO4J_PLUGINS=["apoc"]` is set in docker-compose.yml
3. Restart Neo4j: `docker-compose restart neo4j`

## Production Considerations

### Security

1. **Change Default Passwords**: Never use default passwords in production
2. **Use Strong Passwords**: Set secure passwords via environment variables
3. **Limit Network Exposure**: Only expose necessary ports
4. **Use Secrets Management**: Consider using Docker secrets or external secret managers
5. **Regular Updates**: Keep Docker images updated

### Performance

1. **Resource Limits**: Set appropriate CPU and memory limits in docker-compose.yml
2. **Volume Management**: Use named volumes for better performance
3. **Logging**: Configure log rotation to prevent disk space issues

### Backup

1. **Neo4j Data**: Backup the `neo4j_data` volume regularly
2. **Application Data**: Backup `logs` and `tasks` directories
3. **Configuration**: Keep `.env` file backed up securely (without secrets)

## Next Steps

- Read the [README.md](README.md) for project overview
- Check [docs/WORKFLOW.md](docs/WORKFLOW.md) for workflow details
- Explore the API documentation at http://localhost:3301/docs
- Access Neo4j Browser at http://localhost:7474

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review documentation in `docs/` directory
- Open an issue on the repository

