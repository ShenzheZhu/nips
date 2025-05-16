#!/bin/bash

# Define model lists
BUYER_MODELS=("deepseek-chat" "deepseek-reasoner" "gpt-4o-mini" "gpt-3.5-turbo" "qwen2.5-7b-instruct" "qwen2.5-14b-instruct")
SELLER_MODELS=("deepseek-chat" "deepseek-reasoner" "gpt-4o-mini" "gpt-3.5-turbo" "qwen2.5-7b-instruct" "qwen2.5-14b-instruct")
SUMMARY_MODEL="gpt-4o-mini"  # Using deepseek-chat for all summary tasks

# Set common parameters
PRODUCTS_FILE="dataset/products_mini.json"
OUTPUT_DIR="results"
LOGS_DIR="logs"
MAX_TURNS=30  # Increased from 10 to 20 as a safety mechanism
NUM_EXPERIMENTS=1
MAX_PARALLEL_JOBS=16  # Control how many jobs can run in parallel

# Create output directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOGS_DIR"

# Function to check if current time is past end time (20:30)
check_end_time() {
  current_time=$(date +%s)
  end_time=$(date -d "$(date +%Y-%m-%d) 20:30:00" +%s)
  if [ $current_time -ge $end_time ]; then
    return 0  # true, time to end
  else
    return 1  # false, continue
  fi
}

# Function to wait until a specific time (12:30)
wait_until_start_time() {
  echo "Script started at $(date)"
  echo "Waiting to start experiments at 12:30..."
  
  # Get current time
  current_time=$(date +%s)
  
  # Calculate target time (today at 12:30)
  target_time=$(date -d "$(date +%Y-%m-%d) 12:30:00" +%s)
  
  # If current time is after 12:30, we'll start immediately
  if [ $current_time -ge $target_time ]; then
    echo "Current time is already past 12:30, starting immediately."
    return
  fi
  
  # Calculate sleep duration in seconds
  sleep_seconds=$((target_time - current_time))
  
  echo "Will sleep for $sleep_seconds seconds ($(echo "scale=2; $sleep_seconds/60" | bc) minutes)"
  echo "Expected start time: $(date -d "@$target_time")"
  
  # Sleep until target time
  sleep $sleep_seconds
  
  echo "Wake up! Starting experiments now at $(date)"
}

# Wait until the scheduled start time (12:30)
wait_until_start_time

# Log start time
echo "Starting all experiments at $(date)"
echo "Running 4x4 model combination experiments (16 combinations total) with 5 budget scenarios per product"
echo "Running max $MAX_PARALLEL_JOBS experiments in parallel at a time"
echo "Summary model: $SUMMARY_MODEL"
echo "Safety max turns: $MAX_TURNS"
echo "End time set to 20:30"
echo "==============================================================="

# Function to wait until we have fewer than MAX_PARALLEL_JOBS running
wait_for_job_slot() {
  while [[ $(jobs -r | wc -l) -ge $MAX_PARALLEL_JOBS ]]; do
    sleep 5
    # Check if we've reached the end time
    if check_end_time; then
      echo "Reached end time (20:30), stopping new job creation"
      return 1
    fi
  done
  return 0
}

# Track running processes
declare -a PIDS=()

# Loop through all model combinations and run them in controlled parallel
for SELLER in "${SELLER_MODELS[@]}"; do
  for BUYER in "${BUYER_MODELS[@]}"; do
    # Check if we've reached the end time
    if check_end_time; then
      echo "Reached end time (20:30), stopping experiment creation"
      break 2
    fi
    
    # Wait for a job slot to become available
    if ! wait_for_job_slot; then
      break 2
    fi
    
    LOG_FILE="$LOGS_DIR/${SELLER}_vs_${BUYER}.log"
    
    echo "Starting experiments with Seller: $SELLER, Buyer: $BUYER"
    
    # Run the experiment in the background
    (
      echo "===============================================================" > "$LOG_FILE"
      echo "Running experiments with:" >> "$LOG_FILE"
      echo "Seller: $SELLER" >> "$LOG_FILE"
      echo "Buyer: $BUYER" >> "$LOG_FILE"
      echo "Start time: $(date)" >> "$LOG_FILE"
      echo "Budget scenarios: Retail Price*1.2, Retail Price, (Retail+Wholesale)/2, Wholesale Price, Wholesale Price*0.8" >> "$LOG_FILE"
      echo "===============================================================" >> "$LOG_FILE"
      
      # Run the experiment for this model combination
      python main.py \
        --products-file "$PRODUCTS_FILE" \
        --buyer-model "$BUYER" \
        --seller-model "$SELLER" \
        --summary-model "$SUMMARY_MODEL" \
        --max-turns "$MAX_TURNS" \
        --num-experiments "$NUM_EXPERIMENTS" \
        --output-dir "$OUTPUT_DIR" >> "$LOG_FILE" 2>&1
      
      echo "===============================================================" >> "$LOG_FILE"
      echo "Completed $SELLER vs $BUYER at $(date)" >> "$LOG_FILE"
      echo "Completed experiments with Seller: $SELLER, Buyer: $BUYER"
    ) &
    
    # Record the process ID
    PIDS+=($!)
    
    echo "Started job for $SELLER vs $BUYER with PID $!"
  done
done

echo "All jobs have been queued. Waiting for completion..."
echo "Running with max $MAX_PARALLEL_JOBS parallel jobs"
echo "Will stop at 20:30"

# Wait for all background processes to complete or until end time
while [[ $(jobs -r | wc -l) -gt 0 ]]; do
  if check_end_time; then
    echo "Reached end time (20:30), stopping all running jobs"
    kill $(jobs -p) 2>/dev/null
    break
  fi
  sleep 5
done

echo ""
echo "==============================================================="
echo "Experiments completed at $(date)"
echo "Results saved to $OUTPUT_DIR"
echo "Logs saved to $LOGS_DIR"
echo "Budget scenarios run for each product:"
echo "- High: Retail Price * 1.2"
echo "- Retail: Retail Price"
echo "- Mid: (Retail Price + Wholesale Price) / 2"
echo "- Wholesale: Wholesale Price"
echo "- Low: Wholesale Price * 0.8"