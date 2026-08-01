import time
import threading
from state_tracker import ThreadState

class Consumer(threading.Thread):
    def __init__(self, cid, buffer, controller, tracker, consumption_delay=1.2):
        super().__init__()
        self.cid = cid
        self.buffer = buffer
        self.controller = controller
        self.tracker = tracker
        self.consumption_delay = consumption_delay
        self.running = True
        self.item_counter = 0
        self.daemon = True  # Allows clean shutdown on main exit

    def run(self):
        thread_name = f"Consumer-{self.cid}"
        self.tracker.register_thread(thread_name, "CONSUMER")
        
        while self.running:
            try:
                # 1. Handle Pause / Step-Mode
                self.controller.wait_if_paused()
                if not self.running:
                    break

                # 2. Sleeping state (simulating consumption processing time)
                self.tracker.update_thread_state(thread_name, ThreadState.SLEEPING, "Processing Item")
                
                # Check for step rate limit or speed modifications
                sleep_start = time.time()
                delay = self.consumption_delay * self.controller.speed_factor()
                
                # Break sleep into small chunks to keep thread responsive to shutdowns
                while time.time() - sleep_start < delay and self.running:
                    # Wait if paused during sleep
                    self.controller.wait_if_paused()
                    time.sleep(0.05)
                
                if not self.running:
                    break

                # 3. Running state: ready to attempt extraction
                self.tracker.update_thread_state(thread_name, ThreadState.RUNNING, "Waiting for Buffered Items")

                # 4. Attempt to retrieve item (this handles semaphores and mutex locks inside, shifting states to WAITING/BLOCKED if needed)
                item = self.buffer.get(thread_name)
                
                # Success
                if item:
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