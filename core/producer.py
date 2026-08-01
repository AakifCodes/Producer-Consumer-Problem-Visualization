import time
import threading
import random
from state_tracker import ThreadState

class Producer(threading.Thread):
    def __init__(self, pid, buffer, controller, tracker, production_delay=1.0):
        super().__init__()
        self.pid = pid
        self.buffer = buffer
        self.controller = controller
        self.tracker = tracker
        self.production_delay = production_delay
        self.running = True
        self.item_counter = 0
        self.daemon = True  # Allows clean shutdown on main exit

        # Colors based on item types
        self.colors = {
            "Widget": ["#4fc3f7", "#29b6f6", "#039be5", "#0288d1", "#01579b"],
            "Gadget": ["#ab47bc", "#8e24aa", "#7b1fa2", "#6a1b9a", "#4a148c"],
            "Engine": ["#ff7043", "#f4511e", "#e64a19", "#d84315", "#bf360c"],
            "Microchip": ["#66bb6a", "#43a047", "#388e3c", "#2e7d32", "#1b5e20"]
        }

    def run(self):
        thread_name = f"Producer-{self.pid}"
        self.tracker.register_thread(thread_name, "PRODUCER")
        
        while self.running:
            try:
                # 1. Handle Pause / Step-Mode
                self.controller.wait_if_paused()
                if not self.running:
                    break

                # 2. Sleeping state (simulating production cycle duration)
                self.tracker.update_thread_state(thread_name, ThreadState.SLEEPING, "Assembling Item")
                
                # Check for step rate limit or speed modifications
                sleep_start = time.time()
                delay = self.production_delay * self.controller.speed_factor()
                
                # Break sleep into small chunks to keep thread responsive to shutdowns
                while time.time() - sleep_start < delay and self.running:
                    # Wait if paused during sleep
                    self.controller.wait_if_paused()
                    time.sleep(0.05)
                
                if not self.running:
                    break

                # 3. Running state: ready to attempt insertion
                self.tracker.update_thread_state(thread_name, ThreadState.RUNNING, "Acquiring Synchronization Slots")

                # Generate item metadata
                item_type = self.tracker.item_type
                color_list = self.colors.get(item_type, ["#00ff88"])
                item_color = random.choice(color_list)
                
                item = {
                    "id": f"P{self.pid}-{self.item_counter}",
                    "color": item_color,
                    "type": item_type,
                    "timestamp": time.time()
                }

                # 4. Attempt to insert item (this handles semaphores and mutex locks inside, shifting states to WAITING/BLOCKED if needed)
                self.buffer.put(item, thread_name)
                
                # Success
                self.item_counter += 1
                
            except Exception as e:
                # Log crash gracefully
                print(f"Error in {thread_name}: {e}")
                self.tracker.update_thread_state(thread_name, ThreadState.BLOCKED, f"CRASHED: {e}")
                time.sleep(1.0)

        # Cleanup
        self.tracker.unregister_thread(thread_name)

    def stop(self):
        self.running = False