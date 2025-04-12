# PyLBAPI - Transfermarkt Data API

This project provides a FastAPI-based RESTful API service for extracting football data from [Transfermarkt](https://www.transfermarkt.com/) using web scraping techniques.

## Key Features

- **Data Scraping**: Fetches data for competitions, clubs, and players from Transfermarkt.
- **FastAPI**: Built with the modern, fast (high-performance) web framework for building APIs with Python.
- **MongoDB Caching**: Implements a caching layer using MongoDB to store API responses, reducing the need for frequent scraping and minimizing load on Transfermarkt's servers. Cached data expires after a configurable period (default: 3 days).
- **Background Data Refresh**: Includes an asynchronous background service that periodically refreshes player data to keep the cache up-to-date. The refresh intervals and delays are configurable via environment variables.
- **Dockerized**: Provides a `docker-compose` setup for easy deployment and management, including a persistent MongoDB volume.

## Getting Started

Follow these instructions to set up and run the project locally using Docker.

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

### Installation & Running

1.  **Clone the repository:**

    ```bash
    git clone git@github.com:opazenha/pylbapi.git
    cd pylbapi
    ```

2.  **(Optional) Configure Environment Variables:**
    Create a `.env` file in the project root directory to customize settings. You can copy the example:

    ```bash
    cp .env.example .env
    ```

    Modify the variables in `.env` as needed. Key variables include:

    - `BG_REFRESH_ENABLED`: Set to `true` or `false` to enable/disable the background refresh task.
    - `BG_REFRESH_SCRAPE_DELAY`: Delay (in seconds) between individual scraping requests within a refresh cycle.
    - `BG_REFRESH_CYCLE_DELAY`: Delay (in seconds) between full refresh cycles.
    - `RATE_LIMITING_ENABLE`: Set to `true` or `false` to enable/disable API rate limiting.
    - `RATE_LIMITING_FREQUENCY`: Define the rate limit (e.g., `10/minute`).

3.  **Build and Run with Docker Compose:**
    From the project root directory, run:

    ```bash
    docker-compose up --build -d
    ```

    This command will build the Docker images (if they don't exist) and start the API service and the MongoDB database container in detached mode.

4.  **Access the API:**
    The API will be available at `http://localhost:8000`. You can access the interactive Swagger UI documentation at `http://localhost:8000/docs`.

### Stopping the Application

To stop the running containers:

```bash
docker-compose down
```

To stop and remove the data volume (use with caution, as this deletes cached data):

```bash
docker-compose down -v
```

## Project Structure

- `app/`: Contains the main application code.
  - `api/`: FastAPI endpoints, routers.
  - `db/`: Database connection, cache service logic.
  - `schemas/`: Pydantic models for data validation and serialization.
  - `services/`: Web scraping logic for different Transfermarkt sections.
  - `tasks/`: Background tasks (like the data refresh service).
  - `utils/`: Utility functions (regex, XPath, etc.).
  - `main.py`: FastAPI application entry point.
  - `settings.py`: Application settings configuration.
- `docker-compose.yml`: Docker Compose configuration file.
- `Dockerfile`: Instructions for building the API service Docker image.
- `.env.example`: Example environment variables file.
- `README.md`: This file.
