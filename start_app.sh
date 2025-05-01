#!/usr/bin/env zsh

# Configuration
POSTGRES_CONTAINER_NAME="my-postgres"  # Change this if you named your container differently
POSTGRES_PASSWORD="password"          #  DO NOT USE "password" IN PRODUCTION!  Change this!
POSTGRES_INIT_SCRIPTS_DIR="./postgres_init_scripts" # Directory for your SQL scripts
FASTAPI_APP_COMMAND="uvicorn main:app --reload" # Start FastAPI in watch mode

# Function to check if a Docker container is running
is_container_running() {
  docker ps -q -f "name=$1" | grep -q .
}

# Function to start the PostgreSQL container
start_postgres() {
  if is_container_running "$POSTGRES_CONTAINER_NAME"; then
    echo "PostgreSQL container ($POSTGRES_CONTAINER_NAME) is running.  Removing it first..."
    docker stop "$POSTGRES_CONTAINER_NAME"
    docker rm "$POSTGRES_CONTAINER_NAME"
  else
    echo "PostgreSQL container ($POSTGRES_CONTAINER_NAME) is not running."
  fi

  echo "Starting PostgreSQL container ($POSTGRES_CONTAINER_NAME) with initialization scripts..."
  # Ensure the postgres volume exists before attempting to run the container.
  if ! docker volume ls | grep -q "postgres_data"; then
    docker volume create postgres_data
    echo "Created docker volume postgres_data"
  fi

  docker run --name "$POSTGRES_CONTAINER_NAME" \
    -e POSTGRES_USER=mydatabaseuser \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -p 5432:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    -v "$POSTGRES_INIT_SCRIPTS_DIR":/docker-entrypoint-initdb.d \
    -d postgres:latest
  if [ $? -eq 0 ]; then
    echo "PostgreSQL container ($POSTGRES_CONTAINER_NAME) started successfully."
  else
    echo "Failed to start PostgreSQL container ($POSTGRES_CONTAINERNAME)."
    exit 1
  fi
  #give it a few seconds to start
  sleep 5
}

# Function to start the FastAPI application
start_fastapi() {
  echo "Starting FastAPI application in watch mode..."
  sleep 5 # Add a 5-second sleep before starting FastAPI
  eval "$FASTAPI_APP_COMMAND" # Use eval to execute the command string
  if [ $? -eq 0 ]; then
    echo "FastAPI application started."
  else
    echo "Failed to start FastAPI application."
    exit 1
  fi
}

# Main script logic
start_postgres
start_fastapi # Start FastAPI after PostgreSQL

echo "PostgreSQL setup and FastAPI started."
