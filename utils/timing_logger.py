"""
Timing logger utility for the bathroom layout generator.
This module provides functions to track and log the time taken for various operations.
"""

import time
import os
import datetime
from pathlib import Path
import csv
from typing import Dict, Any, Optional, List

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Log file path
LOG_FILE = logs_dir / "layout_timing.log"
CSV_FILE = logs_dir / "layout_timing.csv"

# CSV header fields
CSV_FIELDS = [
    "timestamp", 
    "operation", 
    "duration_ms", 
    "layout_id", 
    "room_width", 
    "room_depth",
    "num_objects",
    "additional_info"
]

# Initialize CSV file if it doesn't exist
if not CSV_FILE.exists():
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()

def log_time(operation: str, duration_ms: float, layout_id: str = "", 
             room_size: tuple = None, num_objects: int = 0,
             additional_info: Dict[str, Any] = None) -> None:
    """
    Log the time taken for an operation.
    
    Args:
        operation: Name of the operation being timed (e.g., "generation", "scoring")
        duration_ms: Duration in milliseconds
        layout_id: Identifier for the layout being processed (optional)
        room_size: Tuple of (width, depth) of the room (optional)
        num_objects: Number of objects being processed (optional)
        additional_info: Additional information to include in the log (optional)
    """
    timestamp = datetime.datetime.now().isoformat()
    room_width = room_size[0] if room_size else 0
    room_depth = room_size[1] if room_size else 0
    
    # Format the log message
    log_message = f"{timestamp} | {operation} | {duration_ms:.4f}ms | Layout: {layout_id}"
    if room_size:
        log_message += f" | Room: {room_width}x{room_depth}cm"
    if num_objects > 0:
        log_message += f" | Objects: {num_objects}"
    if additional_info:
        log_message += f" | Info: {additional_info}"
    
    # Write to the log file
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + "\n")
    
    # Write to CSV file
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow({
            "timestamp": timestamp,
            "operation": operation,
            "duration_ms": f"{duration_ms:.4f}",
            "layout_id": layout_id,
            "room_width": room_width,
            "room_depth": room_depth,
            "num_objects": num_objects,
            "additional_info": str(additional_info) if additional_info else ""
        })

class TimingContext:
    """
    Context manager for timing code blocks and logging the results.
    
    Example usage:
    with TimingContext("layout_generation", layout_id="abc123", room_size=(200, 250)) as tc:
        # Code to time goes here
        # You can also add additional info during execution
        tc.add_info({"key": "value"})
    """
    
    def __init__(self, operation: str, layout_id: str = "", 
                 room_size: tuple = None, num_objects: int = 0):
        self.operation = operation
        self.layout_id = layout_id
        self.room_size = room_size
        self.num_objects = num_objects
        self.additional_info: Dict[str, Any] = {}
        self.start_time = 0
        
    def __enter__(self):
        # Record exact timestamp when entering the context
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Calculate duration when exiting the context
        end_time = time.time()
        duration_sec = (end_time - self.start_time)
        duration_ms = duration_sec * 1000  # Convert seconds to milliseconds
        
        # Ensure we never log zero durations by using at least 0.01ms
        if duration_ms < 0.01:
            duration_ms = 0.01
        
        # Add timing information to additional info for reference
        self.additional_info["start_timestamp"] = datetime.datetime.fromtimestamp(self.start_time).isoformat()
        self.additional_info["end_timestamp"] = datetime.datetime.fromtimestamp(end_time).isoformat()
        
        # Log the timing information
        log_time(
            self.operation, 
            duration_ms, 
            self.layout_id, 
            self.room_size, 
            self.num_objects, 
            self.additional_info
        )
        
    def add_info(self, info: Dict[str, Any]) -> None:
        """Add additional information to the log entry."""
        self.additional_info.update(info)

def get_timing_summary(operation: Optional[str] = None, 
                      start_time: Optional[datetime.datetime] = None,
                      end_time: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """
    Get summary statistics for timing logs within a specified time range.
    
    Args:
        operation: Filter by operation type (optional)
        start_time: Start time for filtering (optional)
        end_time: End time for filtering (optional)
        
    Returns:
        Dictionary containing summary statistics
    """
    if not CSV_FILE.exists():
        return {"error": "No timing data available"}
    
    try:
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        # Filter by operation if specified
        if operation:
            data = [row for row in data if row["operation"] == operation]
        
        # Filter by time range if specified
        if start_time:
            data = [row for row in data if datetime.datetime.fromisoformat(row["timestamp"]) >= start_time]
        if end_time:
            data = [row for row in data if datetime.datetime.fromisoformat(row["timestamp"]) <= end_time]
        
        if not data:
            return {"message": "No matching timing data found"}
        
        # Calculate statistics
        durations = [float(row["duration_ms"]) for row in data]
        
        return {
            "count": len(durations),
            "avg_ms": sum(durations) / len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "total_ms": sum(durations),
            "operations": {op: len([row for row in data if row["operation"] == op]) 
                         for op in set(row["operation"] for row in data)}
        }
        
    except Exception as e:
        return {"error": f"Error analyzing timing data: {str(e)}"}
