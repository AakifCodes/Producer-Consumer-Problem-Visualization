import time
import threading
from state_tracker import StateTracker
from sync_engine import BoundedBuffer

def test_bounded_buffer():
    print("[TEST] Starting automated BoundedBuffer thread contention tests...")
    
    tracker = StateTracker()
    tracker.reset(buffer_capacity=5, item_type="Widget")
    
    # 5 slots BoundedBuffer
    buffer = BoundedBuffer(5, tracker)
    
    produced_items = set()
    consumed_items = set()
    
    prod_lock = threading.Lock()
    cons_lock = threading.Lock()
    
    class TestController:
        def wait_if_paused(self):
            pass
        def speed_factor(self):
            return 1.0
        _speed_multiplier = 1.0
        
    controller = TestController()
    
    # Spawning 10 producers and 10 consumers pushing 50 items each
    total_items_to_push = 30
    
    def producer_worker(pid):
        for i in range(total_items_to_push):
            item = {
                "id": f"P{pid}-{i}",
                "color": "#fff",
                "type": "Widget",
                "timestamp": time.time()
            }
            # Put item into buffer (blocks if full)
            buffer.put(item, f"Producer-{pid}")
            with prod_lock:
                produced_items.add(item["id"])
            time.sleep(0.01)

    def consumer_worker(cid):
        for i in range(total_items_to_push):
            # Get item from buffer (blocks if empty)
            item = buffer.get(f"Consumer-{cid}")
            if item:
                with cons_lock:
                    consumed_items.add(item["id"])
            time.sleep(0.01)

    threads = []
    
    # Spawn 3 producers and 3 consumers
    for i in range(3):
        p = threading.Thread(target=producer_worker, args=(i+1,))
        c = threading.Thread(target=consumer_worker, args=(i+1,))
        threads.extend([p, c])
        p.start()
        c.start()
        
    # Wait for all to complete
    for t in threads:
        t.join()
        
    print(f"[TEST] Total Produced: {len(produced_items)}")
    print(f"[TEST] Total Consumed: {len(consumed_items)}")
    
    # Assertions
    assert len(produced_items) == 90, f"Expected 90 produced, got {len(produced_items)}"
    assert len(consumed_items) == 90, f"Expected 90 consumed, got {len(consumed_items)}"
    assert produced_items == consumed_items, "Mismatch between produced and consumed items!"
    
    print("[TEST] SUCCESS! No race conditions, no double consumption, and zero item loss under load.")

if __name__ == "__main__":
    test_bounded_buffer()
