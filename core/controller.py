import time
import threading
import random
from state_tracker import ThreadState
from producer import Producer
from consumer import Consumer
from sync_engine import BoundedBuffer

class Controller:
    def __init__(self, tracker, db):
        self.tracker = tracker
        self.db = db
        self.buffer = None
        
        self.producers = []
        self.consumers = []
        
        self.num_producers = 0
        self.num_consumers = 0
        self.buffer_capacity = 5
        self.prod_rate = 1.0
        self.cons_rate = 1.2    
        self.item_type = "Widget"
        self.theme = "Dark Mode"
        
        self._paused = True
        self._speed_multiplier = 1.0  # Speed factor (e.g. 1x, 2x, 0.5x)
        self.pause_event = threading.Event()
        self.pause_event.clear()  # Clear means paused (threads wait)
        
        self.sim_id = None
        self.step_mode = False
        self.is_replay = False
        self.replay_frames = []
        self.replay_index = 0
        
        # Thread list lock
        self.pool_lock = threading.Lock()

    def start_sim(self, num_producers, num_consumers, buffer_capacity, prod_rate, cons_rate, item_type, theme):
        self.stop_sim()
        
        self.num_producers = num_producers
        self.num_consumers = num_consumers
        self.buffer_capacity = buffer_capacity
        self.prod_rate = prod_rate
        self.cons_rate = cons_rate
        self.item_type = item_type
        self.theme = theme
        self.is_replay = False
        
        # 1. Reset tracker
        self.tracker.reset(buffer_capacity, item_type)
        
        # 2. Database record
        self.sim_id = self.db.start_simulation(
            producers=num_producers,
            consumers=num_consumers,
            buffer_capacity=buffer_capacity,
            production_rate=prod_rate,
            consumption_rate=cons_rate,
            item_type=item_type,
            theme=theme
        )
        
        # 3. Create synchronization buffer
        self.buffer = BoundedBuffer(buffer_capacity, self.tracker)
        
        # 4. Spawning threads
        self.producers.clear()
        self.consumers.clear()
        
        with self.pool_lock:
            for i in range(num_producers):
                p = Producer(i + 1, self.buffer, self, self.tracker, prod_rate)
                self.producers.append(p)
                p.start()
                
            for i in range(num_consumers):
                c = Consumer(i + 1, self.buffer, self, self.tracker, cons_rate)
                self.consumers.append(c)
                c.start()
                
        # 5. Start unpaused
        self._paused = False
        self.step_mode = False
        self.pause_event.set()
        self.tracker.start_clock()
        
        self.db.log_event(self.sim_id, "SYSTEM", "0", "SYSTEM", "Simulation started successfully.", 0.0)
        self.tracker.set_edu_message("Simulation started. Producers and Consumers are running.")

    def pause_sim(self):
        self._paused = True
        self.pause_event.clear()
        self.tracker.pause_clock()
        self.tracker.set_edu_message("Simulation paused.")
        if self.sim_id and not self.is_replay:
            self.db.log_event(self.sim_id, "SYSTEM", "0", "SYSTEM", "Simulation paused.", self.tracker.get_snapshot()["elapsed_time"])

    def resume_sim(self):
        self._paused = False
        self.step_mode = False
        self.pause_event.set()
        self.tracker.resume_clock()
        self.tracker.set_edu_message("Simulation resumed.")
        if self.sim_id and not self.is_replay:
            self.db.log_event(self.sim_id, "SYSTEM", "0", "SYSTEM", "Simulation resumed.", self.tracker.get_snapshot()["elapsed_time"])

    def stop_sim(self):
        self.pause_event.set()  # Let blocked threads run so they read self.running=False
        
        with self.pool_lock:
            for p in self.producers:
                p.stop()
            for c in self.consumers:
                c.stop()
                
        # Wait slightly for clean shutdowns
        time.sleep(0.1)
        self.producers.clear()
        self.consumers.clear()
        
        self._paused = True
        self.pause_event.clear()
        self.tracker.stop_clock()
        
        if self.sim_id and not self.is_replay:
            snap = self.tracker.get_snapshot()
            self.db.update_duration(self.sim_id, snap["elapsed_time"])
            self.db.log_statistics(
                self.sim_id,
                snap["total_produced"],
                snap["total_consumed"],
                snap.get("peak_throughput", 0.0),
                0.0,  # calculated later
                snap["max_wait_time"],
                snap["avg_wait_time"],
                snap["producer_block_count"],
                snap["consumer_block_count"]
            )
            self.db.log_event(self.sim_id, "SYSTEM", "0", "SYSTEM", "Simulation stopped.", snap["elapsed_time"])
            self.sim_id = None
        self.tracker.set_edu_message("Simulation stopped.")

    def reset_sim(self):
        self.stop_sim()
        self.tracker.reset(self.buffer_capacity, self.item_type)
        self.tracker.set_edu_message("Simulation reset. Ready to configure.")

    def step_sim(self):
        """Advances simulation by releasing paused threads for exactly one loop step"""
        self.step_mode = True
        self.pause_event.set()
        # Briefly sleep to let threads execute one step, then pause again
        time.sleep(0.1)
        self.pause_event.clear()
        self.tracker.set_edu_message("Advanced by 1 simulation step.")

    def wait_if_paused(self):
        self.pause_event.wait()
        if self.step_mode:
            # Add a small delay to step through cleanly
            time.sleep(0.01)

    def add_producer(self):
        if not self.buffer:
            return
        with self.pool_lock:
            next_id = len(self.producers) + 1
            p = Producer(next_id, self.buffer, self, self.tracker, self.prod_rate)
            self.producers.append(p)
            p.start()
            self.num_producers += 1
            self.tracker.set_edu_message(f"Added Producer-{next_id} dynamically.")
            if self.sim_id:
                self.db.log_event(self.sim_id, "SYSTEM", str(next_id), "SYSTEM", f"Producer-{next_id} added at runtime.", self.tracker.get_snapshot()["elapsed_time"])

    def remove_producer(self):
        with self.pool_lock:
            if len(self.producers) > 0:
                p = self.producers.pop()
                p.stop()
                self.num_producers -= 1
                self.tracker.set_edu_message(f"Stopped and removed Producer-{p.pid} dynamically.")
                if self.sim_id:
                    self.db.log_event(self.sim_id, "SYSTEM", str(p.pid), "SYSTEM", f"Producer-{p.pid} removed at runtime.", self.tracker.get_snapshot()["elapsed_time"])

    def add_consumer(self):
        if not self.buffer:
            return
        with self.pool_lock:
            next_id = len(self.consumers) + 1
            c = Consumer(next_id, self.buffer, self, self.tracker, self.cons_rate)
            self.consumers.append(c)
            c.start()
            self.num_consumers += 1
            self.tracker.set_edu_message(f"Added Consumer-{next_id} dynamically.")
            if self.sim_id:
                self.db.log_event(self.sim_id, "SYSTEM", str(next_id), "SYSTEM", f"Consumer-{next_id} added at runtime.", self.tracker.get_snapshot()["elapsed_time"])

    def remove_consumer(self):
        with self.pool_lock:
            if len(self.consumers) > 0:
                c = self.consumers.pop()
                c.stop()
                self.num_consumers -= 1
                self.tracker.set_edu_message(f"Stopped and removed Consumer-{c.cid} dynamically.")
                if self.sim_id:
                    self.db.log_event(self.sim_id, "SYSTEM", str(c.cid), "SYSTEM", f"Consumer-{c.cid} removed at runtime.", self.tracker.get_snapshot()["elapsed_time"])

    def adjust_production_rate(self, change):
        self.prod_rate = max(0.1, self.prod_rate + change)
        with self.pool_lock:
            for p in self.producers:
                p.production_delay = self.prod_rate
        self.tracker.set_edu_message(f"Production delay adjusted to {self.prod_rate:.2f}s.")

    def adjust_consumption_rate(self, change):
        self.cons_rate = max(0.1, self.cons_rate + change)
        with self.pool_lock:
            for c in self.consumers:
                c.consumption_delay = self.cons_rate
        self.tracker.set_edu_message(f"Consumption delay adjusted to {self.cons_rate:.2f}s.")

    def speed_factor(self):
        # High speed factor = shorter delay
        return 1.0 / self._speed_multiplier

    def set_speed_multiplier(self, value):
        self._speed_multiplier = float(value)

    # --- STRESS TESTING MODULES ---
    
    def force_buffer_full(self):
        if self.buffer:
            self.buffer.force_fill()
            self.tracker.set_edu_message("STRESS TEST: Forced buffer to maximum capacity!")
            if self.sim_id:
                self.db.log_event(self.sim_id, "SYSTEM", "0", "STRESS", "Forced buffer FULL", self.tracker.get_snapshot()["elapsed_time"])

    def force_buffer_empty(self):
        if self.buffer:
            self.buffer.force_clear()
            self.tracker.set_edu_message("STRESS TEST: Drained buffer instantly!")
            if self.sim_id:
                self.db.log_event(self.sim_id, "SYSTEM", "0", "STRESS", "Forced buffer EMPTY", self.tracker.get_snapshot()["elapsed_time"])

    def random_burst_load(self):
        """Temporarily increases production rate of all producers to maximum for 5 seconds"""
        if not self.producers:
            return
        
        def burst():
            old_delays = [p.production_delay for p in self.producers]
            for p in self.producers:
                p.production_delay = 0.05  # Ultra fast
            self.tracker.set_edu_message("STRESS TEST: High burst load injected!")
            time.sleep(4.0)
            for p, old_delay in zip(self.producers, old_delays):
                p.production_delay = old_delay
            self.tracker.set_edu_message("STRESS TEST: Burst load subsided.")

        threading.Thread(target=burst, daemon=True).start()

    def random_producer_failure(self):
        """Simulates a random producer thread getting locked or crashing"""
        with self.pool_lock:
            if self.producers:
                p = random.choice(self.producers)
                p.stop()
                self.tracker.set_edu_message(f"STRESS TEST: Random Failure! Producer-{p.pid} crashed.")
                if self.sim_id:
                    self.db.log_event(self.sim_id, "SYSTEM", str(p.pid), "STRESS", f"Simulated CRASH on Producer-{p.pid}", self.tracker.get_snapshot()["elapsed_time"])

    def random_consumer_failure(self):
        """Simulates a random consumer thread getting locked or crashing"""
        with self.pool_lock:
            if self.consumers:
                c = random.choice(self.consumers)
                c.stop()
                self.tracker.set_edu_message(f"STRESS TEST: Random Failure! Consumer-{c.cid} crashed.")
                if self.sim_id:
                    self.db.log_event(self.sim_id, "SYSTEM", str(c.cid), "STRESS", f"Simulated CRASH on Consumer-{c.cid}", self.tracker.get_snapshot()["elapsed_time"])

    # --- REPLAY MODULES ---
    
    def start_replay(self, sim_id):
        self.stop_sim()
        self.replay_frames = self.db.get_replay_frames(sim_id)
        if not self.replay_frames:
            self.tracker.set_edu_message(f"Error: No replay frames found for Simulation ID {sim_id}")
            return False
            
        self.sim_id = sim_id
        self.is_replay = True
        self.replay_index = 0
        self._paused = False
        
        # Load simulation config for representation
        sims = self.db.get_simulations()
        for s in sims:
            if s[0] == sim_id:
                self.num_producers = s[3]
                self.num_consumers = s[4]
                self.buffer_capacity = s[5]
                self.prod_rate = s[6]
                self.cons_rate = s[7]
                self.item_type = s[8]
                self.theme = s[9]
                break
                
        self.tracker.reset(self.buffer_capacity, self.item_type)
        self.tracker.set_edu_message("Started simulation playback.")
        return True

    def step_replay(self):
        if not self.is_replay or self.replay_index >= len(self.replay_frames):
            return False
            
        frame = self.replay_frames[self.replay_index]
        
        # Apply the snapshot to tracker directly (mocking thread actions)
        with self.tracker.lock:
            self.tracker.elapsed_time = frame["elapsed_time"]
            self.tracker.total_produced = frame["total_produced"]
            self.tracker.total_consumed = frame["total_consumed"]
            self.tracker.producer_block_count = frame["producer_block_count"]
            self.tracker.consumer_block_count = frame["consumer_block_count"]
            self.tracker.buffer_items = list(frame["buffer_items"])
            self.tracker.max_occupancy = frame["max_occupancy"]
            self.tracker.min_occupancy = frame["min_occupancy"]
            self.tracker.mutex_locked_by = frame["mutex_locked_by"]
            self.tracker.empty_semaphore_val = frame["empty_semaphore_val"]
            self.tracker.full_semaphore_val = frame["full_semaphore_val"]
            self.tracker.threads = dict(frame["threads"])
            self.tracker.edu_message = frame["edu_message"]
            self.tracker.deadlock_detected = frame["deadlock_detected"]
            self.tracker.starvation_detected = frame["starvation_detected"]
            self.tracker.max_wait_time = frame["max_wait_time"]
            self.tracker.total_wait_time = frame.get("total_wait_time", 0.0)
            self.tracker.wait_time_count = frame.get("wait_time_count", 0)
            
        self.replay_index += 1
        return True