# Take-Home Coding Task – Senior Python Backend Engineer

**DO NOT COMMIT TO THIS REPO -- MAKE YOUR OWN REPO**

## Overall Design
This project should implement an asynchronous API service that:

1. Provides an authenticated FastAPI endpoint to query Tao dividends from the Bittensor blockchain
2. Caches blockchain query results in Redis for 2 minutes
3. Optionally triggers background stake/unstake operations based on Twitter sentiment:
   - Queries Twitter via Datura.ai API for tweets about the subnet
   - Analyzes tweet sentiment using Chutes.ai LLM
   - Stakes or unstakes TAO proportional to sentiment score (-100 to +100)
4. Uses Celery workers to handle async blockchain and sentiment analysis tasks
5. Stores historical data in a high-concurrency asynchronous database

The architecture follows modern async patterns:
- FastAPI handles HTTP requests
- Redis serves as cache and message broker
- Celery workers process background tasks
- Async database stores results
- Docker containers orchestrate all components

The goal is a production-grade service that can handle ~1000 concurrent requests while maintaining responsive API endpoints through effective use of async operations and background processing.

## Objectives

### 1. Blockchain Data Endpoint (Tao Dividends Query & Stake)
Overall goal: Implement an async API endpoint that returns blockchain data and optionally triggers a staking extrinsic based on an llm analysis of twitter sentiment:

- **Async Blockchain Query**: Use Bittensor's AsyncSubtensor class here: https://github.com/opentensor/bittensor/blob/d6ad9f869c583b95250d8b86ab32bac2465651b2/bittensor/core/async_subtensor.py#L100 to query the chain state for TaoDividendsPerSubnet​ here: https://github.com/opentensor/subtensor/blob/b61dd30202ff6e970a18b5a5231b62183b6ba972/pallets/subtensor/src/lib.rs#L913. This query provides the "last total dividend for a hotkey on a subnet" given a netuid (subnet ID) and a hotkey (account). The call should be fully asynchronous (using asyncio and the provided async interface). Here is an example of how to construct the call and get the data: https://github.com/opentensor/async-substrate-interface/pull/84

- **Caching Layer**: Store or cache the query result in Redis, so that subsequent requests for the same netuid+hotkey can be served quickly without hitting the chain repeatedly. You can use Redis both as a cache and as a message broker for background tasks (via Celery). Cache the result for 2 minutes by keys netuid and hotkey.

- **Authenticated API Endpoint**: Expose the data through a FastAPI endpoint (e.g. GET /api/v1/tao_dividends?netuid={id}&hotkey={address}&trade=false). Both netuid and hotkey parameters are optional - if netuid is omitted, returns data for all netuids and their hotkeys; if hotkey is omitted, returns data for all hotkeys on the specified netuid. The trade parameter is optional and defaults to false. Netuid and hotkey defaults are provided below. Protect this endpoint with authentication (such as a Bearer token or OAuth2) so only authorized clients can access it.

- **Optional Stake Extrinsic & Sentiment-Based Adjustment**: When the endpoint is called with trade=true:

  1. First, gather sentiment data:
     - Using Datura.ai, search recent tweets for "Bittensor netuid {netuid}" to analyze subnet sentiment using this endpoint: https://docs.datura.ai/guides/capabilities/twitter-search or the sdk: https://docs.datura.ai/guides/daturaSdks/py-sdk#basic-twitter-search-method
     - Feed tweets into Chutes.ai API for a llama LLM and prompt it to get a sentiment score (-100 to +100) from the tweets. https://chutes.ai/app/chute/20acffc0-0c5f-58e3-97af-21fc0b261ec4
     - Handle this analysis asynchronously via Celery task

  2. Then submit appropriate stake/unstake extrinsic based on sentiment:
     - For positive sentiment: add_stake (of amount .01 tao * sentiment score)
     - For negative sentiment: unstake (of amount .01 tao * sentiment score)
     - Use default parameters in the extrinsic call if not specified in the API request:
       - hotkey = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
       - netuid = 18

  3. Implementation details:
     - Use Bittensor wallet (created via btwallet sdk: https://github.com/opentensor/btwallet)
     - Submit extrinsics via AsyncSubtensor:
       - add_stake: https://github.com/opentensor/bittensor/blob/d6ad9f869c583b95250d8b86ab32bac2465651b2/bittensor/core/async_subtensor.py#L2814
       - unstake: https://github.com/opentensor/bittensor/blob/d6ad9f869c583b95250d8b86ab32bac2465651b2/bittensor/core/async_subtensor.py#L3670
     - Use testnet for all operations
     - Get testnet tokens by transferring up to 40 tao from wallet: "diamond like interest affair safe clarify lawsuit innocent beef van grief color"
     - Can regenerate wallet using btcli: https://github.com/opentensor/btcli/blob/fe486075576e8c6bd1ed28783c7cfe893e340588/bittensor_cli/src/commands/wallets.py#L50
     - Can transfer tokens using: https://github.com/opentensor/btcli/blob/fe486075576e8c6bd1ed28783c7cfe893e340588/bittensor_cli/src/commands/wallets.py#L1106
     - Handle extrinsic responses asynchronously and log results
     - Use Datura API KEY = 'dt_$q4qWC2K5mwT5BnNh0ZNF9MfeMDJenJ-pddsi_rE1FZ8'
     - Use Chutes API KEY = 'cpk_9402c24cc755440b94f4b0931ebaa272.7a748b60e4a557f6957af9ce25778f49.8huXjHVlrSttzKuuY0yU2Fy4qEskr5J0'

- **Integration**: This sentiment analysis process could be triggered automatically when the data endpoint is called with trade=true or perhaps as a separate background routine. For simplicity, you may execute the Twitter search and sentiment analysis within the same request flow (but asynchronously), or dispatch it as a background Celery task upon each API call. In either case, ensure the stake adjustment extrinsic is submitted without blocking the main API response (e.g., the API can return the TaoDividends data immediately, and perform the stake/unstake in background). Ensure everything is done asynchronously.

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

- If using MongoDB, use an async client like Motor.
- If using SQL (PostgreSQL, MySQL, etc.), use an async ORM or driver (such as Tortoise ORM, GINO, or SQLModel/SQLAlchemy with async support).
- Design your schema minimally – for example, you might store a history of hotkey stake actions or cache of Twitter sentiments if needed.

### Dockerized Setup
Provide a Docker setup so that the reviewers can easily run your project. This should include a Dockerfile for the FastAPI app (and Celery worker, which could be the same image) and a docker-compose.yml (or similar) to orchestrate the app, Redis, and the database. The Docker setup should aim for one-command startup. Clearly document how to build and run the containers. Include a sample .env.example file for environment variables (and ensure secrets or keys can be supplied via env vars).

### Authentication & Security
Secure the API endpoints with authentication. A simple approach is to use Bearer tokens or API keys checked on each request (FastAPI's Depends(OAuth2PasswordBearer) or a custom header check). You do not need a full OAuth2 server setup unless you choose to; a static token or simple token validation is acceptable for this task. Document how to obtain or set the token (for example, via an environment variable or a config file). Additionally, handle sensitive data (like API keys for Datura/Chutes or blockchain wallet seeds) via environment variables and do not commit secrets to the repository.

### Code Quality and Structure
Organize the project in a clean, logical structure. Use Python packages and modules to separate concerns (e.g., an api module, a services module for external integrations, a models or db module for database interactions, etc.). Make use of classes and subclasses where it makes sense (for instance, a class to encapsulate the Bittensor interactions, or a class for managing sentiment analysis logic). Use decorators and middleware for cross-cutting concerns (authentication, logging, error handling). The code should be written with readability and maintainability in mind, as one would expect in a production-grade service.

### Testing (Pytest)
Include a test suite using Pytest. Aim for high coverage on critical logic. Write unit tests for your utility functions and classes (for example, test that the sentiment analysis function correctly interprets sample inputs, or that the caching logic works). Also include concurrency tests – for instance, simulate many concurrent requests to the FastAPI endpoint (you can use AsyncIO or threading in tests to call the endpoint multiple times, or use test client with asyncio.gather) to ensure your service can handle it. If using an async database, test that concurrent data access is handled properly.

### GitHub Best Practices
Treat this project as if it were a real-world team repository. Make frequent commits with clear and descriptive commit messages. It's recommended to structure your work into feature branches and open Pull Requests (PRs) as if you were collaborating (you can open PRs even in your own fork to show the history of feature development). Each PR can, for example, correspond to one of the objectives or a set of related changes, and should include a descriptive summary of what was done. While working solo, this is not strictly necessary, but demonstrating good git hygiene is a plus. Make sure to include a concise but meaningful README (this file) and ensure the repository is clean (no unnecessary files, secrets, or large data).

## Project Setup and Usage
Follow these steps to get your project up and running:
1. **Create your own Repository**

2. **Build and Run with Docker**: Use Docker Compose to build and start all services:
   ```bash
   docker-compose up --build
   ```
   This should start up the FastAPI application (and Celery worker, if configured in the compose file), a Redis instance, and the database. Adjust resource allocations as needed.
   - The FastAPI server should be accessible at http://localhost:8000 (or whichever port is exposed). Check http://localhost:8000/docs for the interactive API documentation.
   - Redis will be running on its default port (6379) internally, and the database on its port (27017 for Mongo, 5432 for Postgres, etc.), unless changed.

3. **Running without Docker (Alternative)**: If you prefer or need to run locally without containers, ensure you have Python 3.9+ and all dependencies. You can install requirements with pip install -r requirements.txt or any other package manager. You'll also need a local Redis server and database service running. Then start the FastAPI app with Uvicorn:
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
```bash
curl -X GET "http://localhost:8000/api/v1/tao_dividends?netuid=18&hotkey=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v" -H "Authorization: Bearer your_token_here"
```
Response:
```json
{
  "netuid": 1,
  "hotkey": "5GrwvaEF...ABC",
  "dividend": 123456789,
  "cached": true,
  "stake_tx_triggered": true
}
```

The above is an illustrative example; you can define the response schema as appropriate (perhaps indicating whether the data was returned from cache and whether the stake extrinsic was enqueued).

### (Optional) Other Endpoints
If you implement additional endpoints (for example, a POST to manually trigger sentiment analysis, or a health check, or an auth login endpoint), document them as well. However, the primary focus is the one described above.

Make sure to include error responses in your documentation. For instance:
- Unauthorized requests should return 401 Unauthorized
- Missing parameters might return 422 Unprocessable Entity (FastAPI does this validation automatically)  
- Any internal errors should return a 500 Internal Server Error with a useful message

## Submission Instructions
When you have completed the task, prepare the repository for review:

1. **Push to GitHub**: Ensure all your code is committed and pushed to a public GitHub repository ON YOUR OWN ACCOUNT. Double-check that no sensitive information is in the repo.

2. **Review README**: Create a clear README.md file that describes the project, its purpose, and how to run it. Ensure the setup instructions are accurate and that someone else can follow them to run your project.

3. **Pull Requests**: If you utilized a PR workflow, ensure those PRs are merged to your main branch.

4. **Final Checklist**: Make sure the project builds and runs without errors in a fresh environment (try re-running the Docker setup from scratch to catch any missing steps). Run the tests one last time to ensure everything passes.

After submitting, we will review your code for correctness, completeness relative to the requirements, code quality, and how you approached the task. They will also run the service and tests. Good documentation (both in-code and in the README) will help us understand your work quickly.

## Bonus / Stretch Goals
If you have extra time or want to showcase additional skills, consider the following optional enhancements. These are not required, but going above and beyond can make your submission stand out:

### Robust Error Handling & Logging
Anticipate failure points and handle exceptions gracefully. For example:
- Timeouts from external APIs
- Failures in the blockchain extrinsic submission
- Redis unavailability
Use Python's logging library to log important events (startup, calls made, errors, successes). Implement custom exception handlers in FastAPI to return friendlier error messages or to sanitize exceptions.

### Complete Type Annotations
Use Python type hints throughout the code. This improves readability and helps catch errors with static analysis. Aim for 100% type coverage on function signatures and consider using mypy for type checking.

### API Rate Limiting
Implement rate limiting on the API to prevent abuse (especially since one of the endpoints triggers on-chain transactions). This could be as simple as an in-memory check or using a package like slowapi or a middleware to limit requests per IP or token. Document your rate limiting policy if implemented (e.g., "max 5 requests per minute per user").

### Custom Middleware
Showcase usage of FastAPI middleware or dependencies for cross-cutting concerns. Examples:
- Middleware to log request timings
- Dependency that checks auth token and fetches user from database
- Middleware for performance profiling
- Request ID attachment for tracing

### Additional Tests (Load Testing)
If possible, write a small load test or use a tool to simulate high concurrency (1000 requests) to demonstrate the service handling it. This could even be a script using asyncio to call your API many times and asserting responses.

### Performance Optimizations
Consider:
- Using asyncio features like gathering tasks for concurrent external calls
- Caching results of sentiment analysis for a subnet
- Ensuring Redis cache keys have appropriate TTL (time-to-live)

### Documentation & Comments
While this README provides the overview, consider adding:
- Docstrings to your functions
- Architecture overview with diagrams or flow descriptions
- Discussion of design decisions and assumptions
- Testing methodology

## Final Section: Screen Recording Demonstration

As a final step, please record a short screen demonstration that walks through your entire workflow. This recording should be included or linked in your GitHub submission (for example, you can upload the video directly or provide a link in your README). In the screen recording, please show:

1. Cloning the repository and pulling it into a fresh environment.
2. Starting the services (e.g., using docker-compose up --build or your local commands).
3. Performing a sample request to GET /api/v1/tao_dividends with trade turned off (verify no stake or unstake is triggered).
4. Performing another sample request with trade=true, with different combinations of netuid and hotkey (including leaving them blank).
5. Observing/logging how the background tasks (sentiment analysis, staking extrinsic) behave.
6. Briefly discussing your implementation:
   - The structure of your code (folders, modules, etc.).
   - Why you chose particular libraries or design patterns.
   - Any tradeoffs or assumptions made during development.

This demonstration helps us understand how everything works end to end and provides insight into your reasoning and implementation process. It also serves as a final confirmation that your solution is production-ready under the specified requirements.

Good luck with the implementation! We look forward to reviewing your code and demonstration.

Good luck with the implementation! We look forward to reviewing your code. This assignment is an opportunity to demonstrate not just that you can solve the problem, but that you write clean, production-ready code and can architect a solution that is scalable and maintainable. Have fun, and feel free to document any assumptions or choices you make along the way.
