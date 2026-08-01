import sqlite3
import json
import os
import time

class SimulationDB:
    def __init__(self, db_path="simulation_data.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Simulations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    duration REAL DEFAULT 0,
                    producers INTEGER,
                    consumers INTEGER,
                    buffer_capacity INTEGER,
                    production_rate REAL,
                    consumption_rate REAL,
                    item_type TEXT,
                    theme TEXT
                )
            """)

            # Events Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER,
                    timestamp TEXT,
                    relative_time REAL,
                    thread_type TEXT, -- 'PRODUCER', 'CONSUMER', 'SYSTEM'
                    thread_id TEXT,
                    event_type TEXT, -- 'PRODUCE', 'CONSUME', 'WAIT', 'BLOCK', 'DEADLOCK', 'SYSTEM'
                    details TEXT,
                    FOREIGN KEY(simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
                )
            """)

            # Statistics Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER,
                    total_produced INTEGER,
                    total_consumed INTEGER,
                    peak_throughput REAL,
                    avg_throughput REAL,
                    max_wait_time REAL,
                    avg_wait_time REAL,
                    producer_block_count INTEGER,
                    consumer_block_count INTEGER,
                    FOREIGN KEY(simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
                )
            """)

            # Replay Data Table - Stores complete JSON state frames to reconstruct the exact system state
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS replay_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER,
                    sequence_order INTEGER,
                    state_snapshot TEXT, -- JSON serialization of StateTracker
                    FOREIGN KEY(simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
                )
            """)

            conn.commit()

    def start_simulation(self, producers, consumers, buffer_capacity, production_rate, consumption_rate, item_type, theme):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO simulations (producers, consumers, buffer_capacity, production_rate, consumption_rate, item_type, theme)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (producers, consumers, buffer_capacity, production_rate, consumption_rate, item_type, theme))
            conn.commit()
            return cursor.lastrowid

    def update_duration(self, sim_id, duration):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE simulations SET duration = ? WHERE id = ?", (duration, sim_id))
            conn.commit()

    def log_event(self, sim_id, thread_type, thread_id, event_type, details, relative_time):
        timestamp = time.strftime("%H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (simulation_id, timestamp, relative_time, thread_type, thread_id, event_type, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sim_id, timestamp, relative_time, thread_type, thread_id, event_type, details))
            conn.commit()

    def log_statistics(self, sim_id, total_produced, total_consumed, peak_throughput, avg_throughput, max_wait_time, avg_wait_time, prod_blocks, cons_blocks):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO statistics (simulation_id, total_produced, total_consumed, peak_throughput, avg_throughput, max_wait_time, avg_wait_time, producer_block_count, consumer_block_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sim_id, total_produced, total_consumed, peak_throughput, avg_throughput, max_wait_time, avg_wait_time, prod_blocks, cons_blocks))
            conn.commit()

    def log_replay_frame(self, sim_id, seq_order, state_dict):
        state_snapshot = json.dumps(state_dict)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO replay_data (simulation_id, sequence_order, state_snapshot)
                VALUES (?, ?, ?)
            """, (sim_id, seq_order, state_snapshot))
            conn.commit()

    def get_simulations(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM simulations ORDER BY id DESC")
            return cursor.fetchall()

    def get_simulation_events(self, sim_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE simulation_id = ? ORDER BY id ASC", (sim_id,))
            return cursor.fetchall()

    def get_simulation_statistics(self, sim_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM statistics WHERE simulation_id = ?", (sim_id,))
            return cursor.fetchone()

    def get_replay_frames(self, sim_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sequence_order, state_snapshot FROM replay_data WHERE simulation_id = ? ORDER BY sequence_order ASC", (sim_id,))
            frames = cursor.fetchall()
            return [json.loads(f[1]) for f in frames]

    def delete_simulation(self, sim_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM simulations WHERE id = ?", (sim_id,))
            conn.commit()
