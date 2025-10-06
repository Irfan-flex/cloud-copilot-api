#!/bin/bash

# Download punkt and averaged_perceptron_tagger
# python -m pip install -U nltk
python -m nltk.downloader 'punkt'
python -m nltk.downloader 'punkt_tab'
# python -m nltk.downloader 'averaged_perceptron_tagger'
# python -m nltk.downloader 'averaged_perceptron_tagger_eng'

# Install python-dotenv due to error "load_env not found at application startup"
python -m pip install -U python-dotenv

# # Get the number of CPU cores
# NUM_CORES=$(nproc)

# # Calculate the number of workers
# WORKERS=$((2 * NUM_CORES + 1))

# TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')

# TOTAL_WORKER=$(echo "$TOTAL_RAM / 700" | bc)

# echo "TOTAL_WORKERS:$TOTAL_WORKER"

# Set default values for environment variables if not set
: "${WORKERS:=4}"  # Default to 1 workers if WORKERS is not set

gunicorn --bind=0.0.0.0 --timeout 60 -k gevent --workers "$WORKERS" application:application
