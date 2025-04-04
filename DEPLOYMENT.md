# Setting Up and Running the Bittensor API Service

This document provides instructions for deploying and running the Bittensor API service.

Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)
- curl or another HTTP client for testing endpoints

## Step 1: Environment Configuration

1. Clone the repository and navigate to the project directory
2. Create a `.env` file based on `.env.example`
```bash
cp .env.example .env
```
3. Edit the `.env` file and populate all required values

## Step 2: Building and Running the Service

Use Docker Compose to build and start all services:
```bash
docker compose up --build
```

The first build may take a few minutes as it installs all dependencies.

## Step 3: Verify the Deployment

Once all services are running, you can verify the deployment by accessing the health check endpoint:

```bash
curl -X GET "http://localhost:8000/"
```

## Step 4: Testing the Protected API Endpoint

To query TAO dividends data, use the following command:

```bash
curl -X GET "http://localhost:8000/api/v1/tao_dividends" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>"
```

Replace <YOUR_API_TOKEN> with the value you set in the `.env` file.

To specify subnet ID and hotkey:

```bash
curl -X GET "http://localhost:8000/api/v1/tao_dividends?netuid=18&hotkey=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>"
```

## Step 5: Accessing API Documentation

The API documentation is available at `http://localhost:8000/docs`

