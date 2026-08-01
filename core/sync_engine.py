import time
import threading
from state_tracker import ThreadState

class MutexWrapper:
    def __init__(self, state_tracker):
        self.lock = threading.Lock()
        self.tracker = state_tracker
        self.owner = None

    def acquire(self, thread_id):
        # Check if the lock can be acquired immediately without blocking
        acquired = self.lock.acquire(blocking=False)
        if acquired:
            self.owner = thread_id
            self.tracker.update_sync_primitives(self.owner, self.tracker.empty_semaphore_val, self.tracker.full_semaphore_val)
            return True

        # If it would block, log the blocked state
        self.tracker.update_thread_state(thread_id, ThreadState.BLOCKED, "Waiting for Mutex Lock")
        start_time = time.time()
        
        # Block until acquired
        self.lock.acquire(blocking=True)
        
        wait_duration = time.time() - start_time
        self.owner = thread_id
        self.tracker.log_thread_block(thread_id, wait_duration)
        self.tracker.update_thread_state(thread_id, ThreadState.RUNNING, "Acquired Mutex Lock")
        self.tracker.update_sync_primitives(self.owner, self.tracker.empty_semaphore_val, self.tracker.full_semaphore_val)
        return True

    def release(self):
        self.owner = None
        self.lock.release()
        self.tracker.update_sync_primitives(None, self.tracker.empty_semaphore_val, self.tracker.full_semaphore_val)


class SemaphoreWrapper:
    def __init__(self, initial_value, state_tracker, name):
        self.sem = threading.Semaphore(initial_value)
        self.tracker = state_tracker
        self.name = name  # "empty" or "full"
        self.val = initial_value
        self.val_lock = threading.Lock()
        self.waiting_threads = []

    def acquire(self, thread_id):
        # We need to see if we will block
        with self.val_lock:
            will_block = (self.val <= 0)
            if will_block:
                self.waiting_threads.append(thread_id)

        if will_block:
            self.tracker.update_thread_state(thread_id, ThreadState.WAITING, f"Waiting on Semaphore ({self.name})")
            
            # Formulate detailed educational descriptions
            if self.name == "empty":
                self.tracker.set_edu_message(f"Producer thread {thread_id} is waiting because the buffer is FULL.")
            else:
                self.tracker.set_edu_message(f"Consumer thread {thread_id} is waiting because the buffer is EMPTY.")
            
            start_time = time.time()
            self.sem.acquire()
            wait_duration = time.time() - start_time
            
            with self.val_lock:
                if thread_id in self.waiting_threads:
                    self.waiting_threads.remove(thread_id)
                self.val -= 1
            
            self.tracker.log_thread_block(thread_id, wait_duration)
            self.tracker.update_thread_state(thread_id, ThreadState.RUNNING, f"Acquired Semaphore ({self.name})")
        else:
            self.sem.acquire()
            with self.val_lock:
                self.val -= 1
                
        # Update semaphore values in state tracker
        if self.name == "empty":
            self.tracker.update_sync_primitives(self.tracker.mutex_locked_by, self.val, self.tracker.full_semaphore_val)
        else:
            self.tracker.update_sync_primitives(self.tracker.mutex_locked_by, self.tracker.empty_semaphore_val, self.val)
            
        return True

    def release(self):
        with self.val_lock:
            self.val += 1
        self.sem.release()
        
        # Update semaphore values in state tracker
        if self.name == "empty":
            self.tracker.update_sync_primitives(self.tracker.mutex_locked_by, self.val, self.tracker.full_semaphore_val)
        else:
            self.tracker.update_sync_primitives(self.tracker.mutex_locked_by, self.tracker.empty_semaphore_val, self.val)

    def force_adjust(self, diff):
        """Forces adjustment of the semaphore count directly without acquiring/releasing locks, useful for stress testing"""
        with self.val_lock:
            self.val += diff
            if diff > 0:
                for _ in range(diff):
                    self.sem.release()
            elif diff < 0:
                for _ in range(abs(diff)):
                    self.sem.acquire(blocking=False)


class BoundedBuffer:
    def __init__(self, capacity, state_tracker):
        self.capacity = capacity
        self.tracker = state_tracker
        self.items = []
        self.items_lock = threading.Lock()
        
        # Primitives
        self.mutex = MutexWrapper(state_tracker)
        self.empty_sem = SemaphoreWrapper(capacity, state_tracker, "empty")
        self.full_sem = SemaphoreWrapper(0, state_tracker, "full")

    def resize(self, new_capacity):
        with self.items_lock:
            diff = new_capacity - self.capacity
            if diff > 0:
                # Capacity increased: add empty slots
                self.empty_sem.force_adjust(diff)
            elif diff < 0:
                # Capacity decreased: try to reduce empty slots
                self.empty_sem.force_adjust(diff)
            self.capacity = new_capacity
            self.tracker.buffer_capacity = new_capacity
            self.tracker.empty_semaphore_val = self.empty_sem.val

    def put(self, item, producer_id):
        # Wait on Empty slots semaphore
        self.empty_sem.acquire(producer_id)
        
        # Wait on Mutex
        self.mutex.acquire(producer_id)
        
        # Produce!
        with self.items_lock:
            self.items.append(item)
        
        self.tracker.log_production(producer_id, item)
        self.tracker.set_edu_message(f"Producer {producer_id} acquired Mutex and added Item {item['id']} to buffer.")
        
        # Release Mutex
        self.mutex.release()
        
        # Signal Full slots semaphore
        self.full_sem.release()

    def get(self, consumer_id):
        # Wait on Full slots semaphore
        self.full_sem.acquire(consumer_id)
        
        # Wait on Mutex
        self.mutex.acquire(consumer_id)
        
        # Consume!
        item = None
        with self.items_lock:
            if len(self.items) > 0:
                item = self.items.pop(0)
        
        if item:
            self.tracker.log_consumption(consumer_id, item["id"])
            self.tracker.set_edu_message(f"Consumer {consumer_id} acquired Mutex and retrieved Item {item['id']} from buffer.")
        
        # Release Mutex
        self.mutex.release()
        
        # Signal Empty slots semaphore
        self.empty_sem.release()
        
        return item

    def force_clear(self):
        """Drains all items immediately (stress test)"""
        with self.items_lock:
            removed_count = len(self.items)
            self.items.clear()
            self.tracker.buffer_items.clear()
            
            # Rebalance semaphores
            self.empty_sem.force_adjust(removed_count)
            self.full_sem.force_adjust(-removed_count)

    def force_fill(self):
        """Fills the buffer to capacity instantly with dummy items (stress test)"""
        with self.items_lock:
            current_count = len(self.items)
            added_count = self.capacity - current_count
            if added_count > 0:
                import random
                colors = ["#ff5555", "#55ff55", "#5555ff", "#ffff55", "#ff55ff", "#55ffff"]
                for i in range(added_count):
                    item = {
                        "id": f"SYS-{random.randint(1000, 9999)}",
                        "color": random.choice(colors),
                        "type": "Manual-Fill",
                        "timestamp": time.time()
                    }
                    self.items.append(item)
                    self.tracker.log_production("SYSTEM", item)
                
                # Rebalance semaphores
                self.empty_sem.force_adjust(-added_count)
                self.full_sem.force_adjust(added_count)
