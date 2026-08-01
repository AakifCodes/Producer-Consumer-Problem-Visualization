import time
import threading

class ThreadState:
    RUNNING = "RUNNING"
    WAITING = "WAITING"    # Waiting on Semaphores (Empty/Full)
    BLOCKED = "BLOCKED"    # Blocked on Mutex
    SLEEPING = "SLEEPING"  # Simulated rate delays / sleeping

class StateTracker:
    def __init__(self):
        self.lock = threading.Lock()
        
        # Simulation configs
        self.buffer_capacity = 5
        self.item_type = "Widget"
        
        # State counts
        self.total_produced = 0
        self.total_consumed = 0
        self.producer_block_count = 0
        self.consumer_block_count = 0
        
        # Buffer metrics
        self.buffer_items = []  # List of dicts: {"id": str, "color": str, "type": str, "timestamp": float}
        self.max_occupancy = 0
        self.min_occupancy = 0
        
        # Synchronization stats
        self.mutex_locked_by = None  # None or thread ID
        self.empty_semaphore_val = 5
        self.full_semaphore_val = 0
        
        # Thread registries
        self.threads = {}  # thread_id -> {"id": str, "type": "PRODUCER"/"CONSUMER", "state": ThreadState, "items_processed": int, "wait_time": float, "last_active": float, "current_task": str, "history": list}
        
        # Historical throughput tracking (time, produced_count, consumed_count)
        self.elapsed_time = 0.0
        self.is_running = False
        self.last_time = None
        self.throughput_history = []  # List of (relative_time, produced, consumed)
        
        # Lock wait time counters
        self.max_wait_time = 0.0
        self.total_wait_time = 0.0
        self.wait_time_count = 0
        
        # Educational message
        self.edu_message = "Simulation initialized. Ready to start."
        self.deadlock_detected = False
        self.starvation_detected = False

    def reset(self, buffer_capacity, item_type):
        with self.lock:
            self.buffer_capacity = buffer_capacity
            self.item_type = item_type
            
            self.total_produced = 0
            self.total_consumed = 0
            self.producer_block_count = 0
            self.consumer_block_count = 0
            
            self.buffer_items.clear()
            self.max_occupancy = 0
            self.min_occupancy = 0
            
            self.mutex_locked_by = None
            self.empty_semaphore_val = buffer_capacity
            self.full_semaphore_val = 0
            
            self.threads.clear()
            self.elapsed_time = 0.0
            self.is_running = False
            self.last_time = None
            self.throughput_history.clear()
            
            self.max_wait_time = 0.0
            self.total_wait_time = 0.0
            self.wait_time_count = 0
            
            self.edu_message = "Simulation reset. Ready to start."
            self.deadlock_detected = False
            self.starvation_detected = False

    def start_clock(self):
        with self.lock:
            self.is_running = True
            self.last_time = time.time()

    def pause_clock(self):
        with self.lock:
            if self.is_running and self.last_time is not None:
                self.elapsed_time += (time.time() - self.last_time)
            self.is_running = False
            self.last_time = None

    def resume_clock(self):
        with self.lock:
            if not self.is_running:
                self.is_running = True
                self.last_time = time.time()

    def stop_clock(self):
        with self.lock:
            if self.is_running and self.last_time is not None:
                self.elapsed_time += (time.time() - self.last_time)
            self.is_running = False
            self.last_time = None

    def register_thread(self, thread_id, thread_type):
        with self.lock:
            self.threads[thread_id] = {
                "id": thread_id,
                "type": thread_type,
                "state": ThreadState.SLEEPING,
                "items_processed": 0,
                "wait_time": 0.0,
                "last_active": time.time(),
                "current_task": "Idle",
                "history": [f"[{time.strftime('%H:%M:%S')}] Thread spawned."]
            }

    def unregister_thread(self, thread_id):
        with self.lock:
            if thread_id in self.threads:
                del self.threads[thread_id]

    def update_thread_state(self, thread_id, state, task=None):
        with self.lock:
            if thread_id in self.threads:
                old_state = self.threads[thread_id]["state"]
                self.threads[thread_id]["state"] = state
                self.threads[thread_id]["last_active"] = time.time()
                if task:
                    self.threads[thread_id]["current_task"] = task
                    
                if old_state != state:
                    self.threads[thread_id]["history"].append(
                        f"[{time.strftime('%H:%M:%S')}] State changed to {state} ({task})"
                    )

    def log_thread_block(self, thread_id, duration):
        with self.lock:
            if thread_id in self.threads:
                self.threads[thread_id]["wait_time"] += duration
                self.total_wait_time += duration
                self.wait_time_count += 1
                if duration > self.max_wait_time:
                    self.max_wait_time = duration
                
                # Increment blocks
                if self.threads[thread_id]["type"] == "PRODUCER":
                    self.producer_block_count += 1
                else:
                    self.consumer_block_count += 1
                
                self.threads[thread_id]["history"].append(
                    f"[{time.strftime('%H:%M:%S')}] Blocked for {duration:.2f}s"
                )

    def log_production(self, thread_id, item):
        with self.lock:
            self.total_produced += 1
            self.buffer_items.append(item)
            
            # Update min/max buffer occupancy
            q_size = len(self.buffer_items)
            if q_size > self.max_occupancy:
                self.max_occupancy = q_size
            
            if thread_id in self.threads:
                self.threads[thread_id]["items_processed"] += 1
                self.threads[thread_id]["history"].append(
                    f"[{time.strftime('%H:%M:%S')}] Produced item {item['id']}"
                )

    def log_consumption(self, thread_id, item_id):
        with self.lock:
            self.total_consumed += 1
            
            # Remove item from buffer list by ID
            for i, item in enumerate(self.buffer_items):
                if item["id"] == item_id:
                    self.buffer_items.pop(i)
                    break
                    
            if thread_id in self.threads:
                self.threads[thread_id]["items_processed"] += 1
                self.threads[thread_id]["history"].append(
                    f"[{time.strftime('%H:%M:%S')}] Consumed item {item_id}"
                )

    def update_sync_primitives(self, mutex_owner, empty_val, full_val):
        with self.lock:
            self.mutex_locked_by = mutex_owner
            self.empty_semaphore_val = empty_val
            self.full_semaphore_val = full_val

    def record_throughput_point(self, elapsed):
        with self.lock:
            self.throughput_history.append((elapsed, self.total_produced, self.total_consumed))
            # Keep history under 1000 points
            if len(self.throughput_history) > 1000:
                self.throughput_history.pop(0)

    def set_edu_message(self, message):
        with self.lock:
            self.edu_message = message

    def set_deadlock_flag(self, flag):
        with self.lock:
            self.deadlock_detected = flag

    def set_starvation_flag(self, flag):
        with self.lock:
            self.starvation_detected = flag

    def get_snapshot(self):
        with self.lock:
            # Calculate elapsed time dynamically if currently running
            current_elapsed = self.elapsed_time
            if self.is_running and self.last_time is not None:
                current_elapsed += (time.time() - self.last_time)
                
            # Create a clean, serializable copy of the state
            return {
                "elapsed_time": current_elapsed,
                "total_produced": self.total_produced,
                "total_consumed": self.total_consumed,
                "producer_block_count": self.producer_block_count,
                "consumer_block_count": self.consumer_block_count,
                "buffer_capacity": self.buffer_capacity,
                "buffer_size": len(self.buffer_items),
                "buffer_items": list(self.buffer_items),
                "max_occupancy": self.max_occupancy,
                "min_occupancy": self.min_occupancy,
                "mutex_locked_by": self.mutex_locked_by,
                "empty_semaphore_val": self.empty_semaphore_val,
                "full_semaphore_val": self.full_semaphore_val,
                "threads": {tid: dict(t) for tid, t in self.threads.items()},
                "edu_message": self.edu_message,
                "deadlock_detected": self.deadlock_detected,
                "starvation_detected": self.starvation_detected,
                "max_wait_time": self.max_wait_time,
                "avg_wait_time": (self.total_wait_time / self.wait_time_count) if self.wait_time_count > 0 else 0.0
            }
