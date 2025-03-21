# Take-Home Coding Task – Senior Python Backend Engineer

## Introduction
This repository contains a take-home assignment for a Senior Python Backend Engineer position. The goal is to implement an asynchronous, production-grade API service that interacts with a blockchain network (Bittensor), external APIs (for data and sentiment analysis), and modern backend components (FastAPI, Redis, Celery, and a database). The task is designed to assess your proficiency in Python async development, API design, integration of external services, and overall code quality. It is expected to take approximately 6–8 hours of focused development time.

> **Figure**: Example asynchronous architecture with FastAPI as the client, Redis as a message broker/backend, and Celery workers handling background tasks. In this task, you'll implement a similar architecture where incoming API requests trigger asynchronous operations (blockchain queries, external API calls) that are processed in the background, leveraging Redis and Celery to avoid blocking the main FastAPI event loop.

## Objectives

### 1. Blockchain Data Endpoint (Tao Dividends Query & Stake)
Implement an async API endpoint that returns blockchain data and triggers a staking extrinsic:

- **Async Blockchain Query**: Use Bittensor's AsyncSubtensor interface to query the chain state for TaoDividendsPerSubnet​ [DOCS.BITTENSOR.COM]. This query provides the "last total root dividend for a hotkey on a subnet" given a netuid (subnet ID) and a hotkey (account)​ [DOCS.BITTENSOR.COM]. The call should be fully asynchronous (using asyncio and the provided async interface).

- **Caching Layer**: Store or cache the query result in Redis, so that subsequent requests for the same netuid+hotkey can be served quickly without hitting the chain repeatedly. You can use Redis both as a cache and as a message broker for background tasks (via Celery).

- **Authenticated API Endpoint**: Expose the data through a FastAPI endpoint (e.g. GET /api/v1/tao_dividends?netuid=<id>&hotkey=<address>). Protect this endpoint with authentication (such as a Bearer token or OAuth2) so only authorized clients can access it.

- **Trigger Stake Extrinsic**: When the endpoint is called, initiate a blockchain staking extrinsic using the given parameters. Specifically, use a Bittensor wallet (created via btwallet) to submit an add_stake extrinsic on the test network with the provided netuid and hotkey. The extrinsic should stake a certain amount (e.g. 1 TAO by default) to that hotkey on the subnet. The call to add_stake should be made asynchronously and in a non-blocking way (potentially offloaded to a Celery task). Bittensor's Subtensor.add_stake method "adds the specified amount of stake to a neuron identified by the hotkey SS58 address"​ [DOCS.BITTENSOR.COM]. Ensure you handle the response or result of this extrinsic (success/failure) and log or store it as needed.

### 2. Sentiment-Driven Stake Adjustment
Enhance the service with a sentiment analysis flow that influences staking:

- **Twitter Sentiment Analysis**: Using Datura.ai (an external AI-powered data platform), search recent tweets on Twitter for the query "Netuid {netuid}". Essentially, gather public sentiment about the given subnet ID. This likely involves using Datura's Twitter search API endpoint to fetch relevant tweets (you may need an API key and to follow their documentation).

- **LLM Sentiment Classification**: Take the content of the tweets and feed them into an LLM model to determine sentiment. For this, use Chutes.ai (which provides a hosted Large Language Model pipeline for sentiment analysis via a specified chute endpoint). The LLM should analyze whether the overall sentiment for the subnet (as gleaned from tweets) is positive or negative. Handle this step asynchronously, as it may involve network calls and processing time.

- **Conditional Stake/Unstake**: Based on the sentiment result, trigger either an add_stake or a remove_stake (unstake) extrinsic for the same netuid and hotkey:
  - If sentiment is positive (e.g. supportive tweets about the subnet), call add_stake (increasing the stake by 1 unit, or a configured amount).
  - If sentiment is negative, call the corresponding extrinsic to remove stake (unstake 1 unit) for that hotkey on the subnet. Bittensor provides an extrinsic (e.g. unstake or remove_stake) to decrease a neuron's stake; you should use the appropriate method similar to add_stake (for example, Subtensor.unstake or undelegate, as applicable in the Bittensor SDK).

- **Integration**: This sentiment analysis process could be triggered automatically when the data endpoint is called or perhaps as a separate background routine. For simplicity, you may execute the Twitter search and sentiment analysis within the same request flow (but asynchronously), or dispatch it as a background Celery task upon each API call. In either case, ensure the stake adjustment extrinsic is submitted without blocking the main API response (e.g., the API can return the TaoDividends data immediately, and perform the stake/unstake in background).

- **Defaults**: Assume a default stake amount of 1 TAO for add or remove stake actions (unless specified otherwise). You can make this configurable via environment or settings if needed.

## Technical Requirements
Your implementation must meet the following technical criteria:

### Asynchronous Design
Leverage asyncio and non-blocking IO throughout the service. All external calls (blockchain queries, extrinsic submissions, HTTP requests to Datura/Chutes, database operations) should be done using async frameworks or libraries. Avoid blocking calls or threading except where absolutely necessary. Ensure that the FastAPI endpoints are async def and make use of await for I/O.

### FastAPI Framework
Use FastAPI to implement the REST API service. FastAPI should handle request routing, validation, and documentation (the auto-generated docs at /docs or /redoc). You can structure the API with logical endpoints (e.g., under /api/v1/...). If you prefer to use Django for certain parts (such as an admin interface or ORM), you may integrate it, but the core API should be accessible via FastAPI for its async capabilities and ease of writing background tasks.

### Redis & Celery for Background Tasks
Use Redis as a caching layer and as a message broker for background jobs. Integrate Celery with FastAPI to offload long-running tasks (such as the sentiment analysis pipeline or even the extrinsic submission) to worker processes. The API call can quickly enqueue a task (or utilize an async task queue) and return a response while the heavy lifting happens in the background. Ensure a Celery worker is set up to consume tasks. Redis will serve as the broker (and can also be used as a result backend if needed) for Celery.

### Persistence (Database)
For any persistent data (e.g., storing results of queries, logging actions, or user/auth data), use an asynchronous-compatible database. This could be either MongoDB or an SQL database. The choice is yours, but it should handle high concurrency (aim for support of ~1000 concurrent requests):

- If using MongoDB, consider an async client like Motor.
- If using SQL (PostgreSQL, MySQL, etc.), use an async ORM or driver (such as Tortoise ORM, GINO, or SQLModel/SQLAlchemy with async support).
- Design your schema minimally – for example, you might store a history of hotkey stake actions or cache of Twitter sentiments if needed.

### Dockerized Setup
Provide a Docker setup so that the reviewers can easily run your project. This should include a Dockerfile for the FastAPI app (and Celery worker, which could be the same image) and a docker-compose.yml (or similar) to orchestrate the app, Redis, and the database. The Docker setup should aim for one-command startup. Clearly document how to build and run the containers. Include a sample .env.example file for environment variables (and ensure secrets or keys can be supplied via env vars).

### Authentication & Security
Secure the API endpoints with authentication. A simple approach is to use Bearer tokens or API keys checked on each request (FastAPI's Depends(OAuth2PasswordBearer) or a custom header check). You do not need a full OAuth2 server setup unless you choose to; a static token or simple token validation is acceptable for this task. Document how to obtain or set the token (for example, via an environment variable or a config file). Additionally, handle sensitive data (like API keys for Datura/Chutes or blockchain wallet seeds) via environment variables and do not commit secrets to the repository.

### Code Quality and Structure
Organize the project in a clean, logical structure. Use Python packages and modules to separate concerns (e.g., an api module, a services module for external integrations, a models or db module for database interactions, etc.). Make use of classes and subclasses where it makes sense (for instance, a class to encapsulate the Bittensor interactions, or a class for managing sentiment analysis logic). Use decorators and middleware for cross-cutting concerns (authentication, logging, error handling). The code should be written with readability and maintainability in mind, as one would expect in a production-grade service.

### Testing (Pytest)
Include a comprehensive test suite using Pytest. Aim for high coverage on critical logic. Write unit tests for your utility functions and classes (for example, test that the sentiment analysis function correctly interprets sample inputs, or that the caching logic works). Also include concurrency tests – for instance, simulate many concurrent requests to the FastAPI endpoint (you can use AsyncIO or threading in tests to call the endpoint multiple times, or use test client with asyncio.gather) to ensure your service can handle it. If using an async database, test that concurrent data access is handled properly.

### GitHub Best Practices
Treat this project as if it were a real-world team repository. Make frequent commits with clear and descriptive commit messages. It's recommended to structure your work into feature branches and open Pull Requests (PRs) as if you were collaborating (you can open PRs even in your own fork to show the history of feature development). Each PR can, for example, correspond to one of the objectives or a set of related changes, and should include a descriptive summary of what was done. While working solo, this is not strictly necessary, but demonstrating good git hygiene is a plus. Make sure to include a concise but meaningful README (this file) and ensure the repository is clean (no unnecessary files, secrets, or large data).

## Project Setup and Usage
Follow these steps to get the project up and running:

1. **Clone the Repository**: Fork this repo to your own GitHub and clone it locally, or simply clone if provided to you.
   ```bash
   git clone https://github.com/yourname/senior-backend-task.git
   ```

2. **Environment Variables**: Copy the provided .env.example to .env and fill in required values. This likely includes:
   - BITTENSOR_NETWORK or related settings for connecting to the Bittensor test network (if needed, e.g. endpoint URLs).
   - Credentials for Datura.ai and Chutes.ai (API keys or tokens) so you can access their services.
   - A secret token or key for your API authentication (e.g. API_TOKEN=mysecrettoken to secure the endpoint).
   - Database connection URL (e.g. DATABASE_URL or MONGODB_URI).
   - Redis connection URL (if not using the default in Docker).
   - Any other config (wallet path, etc.).
   Make sure not to hard-code secrets in the code – use these env vars.

3. **Build and Run with Docker**: Ensure you have Docker installed. Then, use Docker Compose to build and start all services:
   ```bash
   docker-compose up --build
   ```
   This should start up the FastAPI application (and Celery worker, if configured in the compose file), a Redis instance, and the database. Adjust resource allocations as needed.
   - The FastAPI server should be accessible at http://localhost:8000 (or whichever port is exposed). Check http://localhost:8000/docs for the interactive API documentation.
   - Redis will be running on its default port (6379) internally, and the database on its port (27017 for Mongo, 5432 for Postgres, etc.), unless changed.

4. **Running without Docker (Alternative)**: If you prefer or need to run locally without containers, ensure you have Python 3.9+ and all dependencies. You can install requirements with pip install -r requirements.txt. You'll also need a local Redis server and database service running. Then start the FastAPI app with Uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```
   and start a Celery worker in another terminal:
   ```bash
   celery -A app.worker worker --loglevel=info
   ```
   (The exact import path for the Celery app may vary based on your project structure).

5. **Running Tests**: After installation, run pytest (or pytest -sv for verbose output) to execute the test suite. If using Docker, you might add a service in docker-compose.yml for tests, or run tests locally in your environment. Ensure that the app (and required services like Redis/DB) is running or use a test setup that starts those (you can use a local SQLite or a test Mongo database for tests if needed). The tests should confirm that all features work as expected, including handling of concurrent requests.

## API Documentation
The FastAPI framework automatically provides an interactive API docs UI. Once the server is running, navigate to /docs (Swagger UI) or /redoc (ReDoc) in your browser to view and interact with the API endpoints. You should document at least the following endpoint(s):

### GET /api/v1/tao_dividends
Protected endpoint that returns the Tao dividends data for a given subnet and hotkey. Query parameters: netuid (integer subnet ID) and hotkey (string account ID or public key). Requires an Authorization header with the bearer token (or whatever auth scheme you choose). On success, returns a JSON response with the dividend value (and possibly a timestamp or other metadata). This call will also trigger a background stake operation on the blockchain.

Example request: