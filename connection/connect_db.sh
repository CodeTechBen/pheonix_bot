source .env

# Check if the necessary environment variables are set
if [ -z "$BD_DNS" ] || [ -z "$USER" ] || [ -z "$PRIVATE_KEY_PATH" ]; then
  echo "Error: BOT_PRIVATE_IP, USER, or PRIVATE_KEY_PATH not set in .env"
  exit 1
fi

chmod 400 "$PRIVATE_KEY_PATH"

# SSH into the EC2 instance
echo "Connecting to EC2 instance at $DB_DNS..."
ssh -i "$PRIVATE_KEY_PATH" "$USER@$DB_DNS"
