#!/bin/bash

# Exit if anything fails
set -e

echo "🚀 Connecting to remote server..."

ssh -t  prakash2@65.21.228.101 '
  set -e
  source /home/prakash2/virtualenv/nurseicon.com.np/3.11/bin/activate
cd /home/prakash2/nurseicon.com.np
  echo "✅ Environment ready. You are now inside the server shell."
  exec bash
  # Activate virtual environment and change to project directory
'

