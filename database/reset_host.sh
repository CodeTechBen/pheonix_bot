
source .env

export PGPASSWORD="$HOSTED_DB_PASSWORD"

echo "Resetting database $HOSTED_DB_NAME..."

psql -U "$HOSTED_DB_USER" -h "$HOSTED_DB_HOST" -p "$HOSTED_PORT" -d "$HOSTED_DB_NAME" -f "$SCHEMA_FILE"

unset PGPASSWORD
