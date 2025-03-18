# Load environment variables from .env file
source .env

# Connect to the PostgreSQL database
export PGPASSWORD=$HOSTED_DB_PASSWORD
echo "$HOSTED_DB_HOST"
echo "$HOSTED_DB_USER"
echo "$HOSTED_DB_NAME"
echo "$HOSTED_PORT"
psql -h "$HOSTED_DB_HOST" -U "$HOSTED_DB_USER" -d "$HOSTED_DB_NAME" -p "$HOSTED_PORT"
