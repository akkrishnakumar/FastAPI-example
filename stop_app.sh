POSTGRES_CONTAINER_NAME="my-postgres" 

is_container_running() {
  docker ps -q -f "name=$1" | grep -q .
}

stop_postgres() {
  if is_container_running "$POSTGRES_CONTAINER_NAME"; then
    echo "Stopping PostgreSQL container ($POSTGRES_CONTAINER_NAME)..."
    docker stop "$POSTGRES_CONTAINER_NAME"
    if [ $? -eq 0 ]; then
      echo "PostgreSQL container ($POSTGRES_CONTAINER_NAME) stopped successfully."
      docker rm "$POSTGRES_CONTAINER_NAME" #remove the container
      if [ $? -eq 0 ]; then
        echo "PostgreSQL container ($POSTGRES_CONTAINER_NAME) removed successfully."
      else
        echo "Failed to remove PostgreSQL container ($POSTGRES_CONTAINER_NAME)."
        exit 1
      fi
    else
      echo "Failed to stop PostgreSQL container ($POSTGRES_CONTAINER_NAME)."
      exit 1
    fi
  else
    echo "PostgreSQL container ($POSTGRES_CONTAINER_NAME) is not running."
  fi
}

stop_postgres