#!/bin/bash

# Set the process name or the script name for your bot (change to your bot's process or name)
BOT_PROCESS_NAME="python3 main.py"
BOT_DIR="/home/ubuntu/pheonix_bot"  # Adjust the bot's directory path as needed

# Navigate to the bot directory
cd "$BOT_DIR"

# Step 1: Check if the bot process is already running
echo "Checking if the bot is already running..."

# Get the process ID (PID) of the bot if it's running
PID=$(ps aux | grep "$BOT_PROCESS_NAME" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "No bot is running, starting the bot..."
else
  echo "Bot process found with PID: $PID. Killing the process..."
  kill -9 "$PID"
fi

# Step 2: Start the bot as a background process
echo "Starting the bot in the background..."
nohup python3 main.py > bot.log 2>&1 & 

# Step 3: Verify the bot is running
NEW_PID=$(ps aux | grep "$BOT_PROCESS_NAME" | grep -v grep | awk '{print $2}')

if [ -n "$NEW_PID" ]; then
  echo "Bot started successfully with PID: $NEW_PID"
else
  echo "Failed to start the bot."
fi
