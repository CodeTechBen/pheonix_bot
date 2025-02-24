source .env
echo "Resetting database $DB_NAME..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -f "$SCHEMA_FILE"