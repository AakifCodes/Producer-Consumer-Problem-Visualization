import os
import time
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QSplitter, QMenuBar, QMenu, 
                             QFileDialog, QMessageBox, QInputDialog)
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtCore import QTimer, Qt

# Components
from database import SimulationDB
from state_tracker import StateTracker, ThreadState
from controller import Controller
from theme_manager import ThemeManager

from ui.conveyor_widget import ConveyorWidget
from ui.sync_monitor import SyncMonitor
from ui.log_panel import LogPanel
from ui.analytics_panel import AnalyticsPanel
from ui.edu_panel import EducationalPanel
from ui.ai_advisor import AIAdvisorPanel
from ui.control_panel import ControlPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Setup core engine
        self.db = SimulationDB()
        self.tracker = StateTracker()
        self.controller = Controller(self.tracker, self.db)
        
        # Timers
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui_frame)
        self.ui_timer.start(33)  # ~30 FPS polling
        
        self.replay_timer = QTimer(self)
        self.replay_timer.timeout.connect(self.play_next_replay_frame)
        
        # Replay frame rate recorder
        self.last_recording_time = time.time()
        self.record_sequence = 0
        self.sim_elapsed_start = 0.0
        
        # Window settings
        self.setWindowTitle("Smart Factory Producer–Consumer Synchronization Simulator")
        self.setMinimumSize(1200, 850)
        
        # Setup menu bar and UI
        self._init_menu_bar()
        self._init_ui()
        
        # Initial theme setup
        self.apply_theme("Dark Mode")

    def _init_menu_bar(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("Replay Database")
        
        load_action = QAction("Load Simulation Replay", self)
        load_action.triggered.connect(self.load_replay_dialog)
        file_menu.addAction(load_action)
        
        delete_action = QAction("Manage Saved Simulations", self)
        delete_action.triggered.connect(self.manage_simulations_dialog)
        file_menu.addAction(delete_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit Simulator", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _init_ui(self):
        # Central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        # Master vertical layout
        master_layout = QVBoxLayout(self.central_widget)
        master_layout.setContentsMargins(10, 10, 10, 10)
        master_layout.setSpacing(10)
        
        # 1. TOP STATISTICS BAR CARD GRID
        self.stats_bar = QFrame(self.central_widget)
        self.stats_bar.setFixedHeight(80)
        stats_layout = QHBoxLayout(self.stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(10)
        
        self.stat_cards = {}
        stat_configs = [
            ("total_produced", "TOTAL PRODUCED", "0 items"),
            ("total_consumed", "TOTAL CONSUMED", "0 items"),
            ("buffer_occupancy", "BUFFER OCCUPANCY", "0 / 5"),
            ("buffer_util", "BUFFER UTILIZATION", "0 %"),
            ("avg_wait_time", "AVERAGE WAIT TIME", "0.00 s"),
            ("blocked_threads", "ACTIVE BLOCKED", "0 threads"),
            ("throughput", "CURRENT THROUGHPUT", "0.00 /s"),
            ("sim_time", "SIMULATION DURATION", "0.0 s")
        ]
        
        for key, title, default in stat_configs:
            card = QFrame(self.stats_bar)
            card.setObjectName("card")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 10, 10, 10)
            c_layout.setSpacing(2)
            
            title_lbl = QLabel(title, card)
            title_lbl.setObjectName("title")
            title_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            c_layout.addWidget(title_lbl)
            
            value_lbl = QLabel(default, card)
            value_lbl.setObjectName("value")
            value_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            c_layout.addWidget(value_lbl)
            
            stats_layout.addWidget(card)
            self.stat_cards[key] = value_lbl
            
        master_layout.addWidget(self.stats_bar)
        
        # 2. MIDDLE DASHBOARD SPLIT
        mid_splitter = QSplitter(Qt.Orientation.Vertical, self.central_widget)
        
        # Conveyor Visual Canvas Frame
        self.conveyor_widget = ConveyorWidget(self.tracker, self.controller, mid_splitter)
        self.conveyor_widget.setMaximumHeight(380)
        mid_splitter.addWidget(self.conveyor_widget)
        
        # Synchronization Monitor & Explainer Cards (Horizontal Split)
        sync_section = QWidget(mid_splitter)
        sync_layout = QHBoxLayout(sync_section)
        sync_layout.setContentsMargins(0, 0, 0, 0)
        sync_layout.setSpacing(10)
        
        self.sync_monitor = SyncMonitor(self.tracker, sync_section)
        sync_layout.addWidget(self.sync_monitor, stretch=3)
        
        self.edu_panel = EducationalPanel(self.tracker, sync_section)
        sync_layout.addWidget(self.edu_panel, stretch=2)
        
        mid_splitter.addWidget(sync_section)
        
        # Bottom middle: Analytics Graphs & Log Panel & AI Advisor (Vertical layout or split)
        bottom_mid = QWidget(mid_splitter)
        bottom_mid_layout = QHBoxLayout(bottom_mid)
        bottom_mid_layout.setContentsMargins(0, 0, 0, 0)
        bottom_mid_layout.setSpacing(10)
        
        self.log_panel = LogPanel(self.controller, bottom_mid)
        bottom_mid_layout.addWidget(self.log_panel, stretch=3)
        
        self.analytics_panel = AnalyticsPanel(self.tracker, bottom_mid)
        bottom_mid_layout.addWidget(self.analytics_panel, stretch=4)
        
        self.ai_advisor = AIAdvisorPanel(self.tracker, bottom_mid)
        self.ai_advisor.setObjectName("AIAdvisorWidget")
        bottom_mid_layout.addWidget(self.ai_advisor, stretch=2)
        
        mid_splitter.addWidget(bottom_mid)
        
        # Set stretch factors so conveyor doesn't balloon and other panels expand nicely
        mid_splitter.setStretchFactor(0, 0)
        mid_splitter.setStretchFactor(1, 1)
        mid_splitter.setStretchFactor(2, 2)
        
        master_layout.addWidget(mid_splitter, stretch=1)
        
        # 3. CONTROL PANEL
        self.control_panel = ControlPanel(self.controller, self.central_widget)
        self.control_panel.theme_changed.connect(self.apply_theme)
        master_layout.addWidget(self.control_panel)

    def apply_theme(self, theme_name):
        theme_data = ThemeManager.get_theme(theme_name)
        self.setStyleSheet(theme_data["qss"])
        
        # Propagate themes to custom rendered widgets
        self.conveyor_widget.set_theme(theme_data)
        self.sync_monitor.set_theme(theme_data)
        self.edu_panel.set_theme(theme_data)
        self.log_panel.set_theme(theme_data)
        self.analytics_panel.set_theme(theme_data)
        self.ai_advisor.set_theme(theme_data)
        self.control_panel.set_theme(theme_data)
        
        # Update styling of active cards manually to match themes
        for card_val in self.stat_cards.values():
            card_val.setStyleSheet(f"color: {theme_data['accent']}; font-size: 14px; font-weight: bold;")

    def update_ui_frame(self):
        """30 FPS main GUI loop"""
        snap = self.tracker.get_snapshot()
        
        # Re-register simulator duration time
        if not self.controller._paused and not self.controller.is_replay:
            self.tracker.record_throughput_point(snap["elapsed_time"])
            
            # --- REPLAY SYSTEM: STATE RECORDING IN SQLite (EVERY 300ms) ---
            now = time.time()
            if now - self.last_recording_time >= 0.3:
                self.last_recording_time = now
                self.db.log_replay_frame(self.controller.sim_id, self.record_sequence, snap)
                self.record_sequence += 1
                
        # 1. Update Statistics Bar
        self.stat_cards["total_produced"].setText(f"{snap['total_produced']} items")
        self.stat_cards["total_consumed"].setText(f"{snap['total_consumed']} items")
        
        cap = snap["buffer_capacity"]
        sz = snap["buffer_size"]
        self.stat_cards["buffer_occupancy"].setText(f"{sz} / {cap}")
        
        util_pct = (sz / cap) * 100 if cap > 0 else 0
        self.stat_cards["buffer_util"].setText(f"{util_pct:.1f} %")
        
        self.stat_cards["avg_wait_time"].setText(f"{snap['avg_wait_time']:.2f} s")
        
        # Count blocked threads
        blocked_cnt = len([t for t in snap["threads"].values() if t["state"] in ["WAITING", "BLOCKED"]])
        self.stat_cards["blocked_threads"].setText(f"{blocked_cnt} threads")
        
        # Compute instant throughput average (over last 10 points)
        if len(self.analytics_panel.prod_throughput_history) > 0:
            tp = sum(self.analytics_panel.prod_throughput_history[-10:]) / min(10, len(self.analytics_panel.prod_throughput_history))
            self.stat_cards["throughput"].setText(f"{tp:.2f} /s")
            
        self.stat_cards["sim_time"].setText(f"{snap['elapsed_time']:.1f} s")
        
        # 2. Update panel child components
        self.sync_monitor.update_monitor()
        self.log_panel.update_logs()
        self.edu_panel.update_live_explanation()
        self.ai_advisor.update_advisor()
        self.analytics_panel.update_charts()
        
        # 3. DETECT DEADLOCKS & STARVATION
        self.detect_critical_scenarios(snap)

    def detect_critical_scenarios(self, snap):
        threads = snap["threads"]
        active_cnt = len(threads)
        
        if active_cnt > 0:
            # Deadlock: ALL active threads are in WAITING or BLOCKED
            blocked_cnt = len([t for t in threads.values() if t["state"] in [ThreadState.WAITING, ThreadState.BLOCKED]])
            if blocked_cnt == active_cnt and not self.tracker.deadlock_detected:
                self.tracker.set_deadlock_flag(True)
                self.tracker.set_edu_message("🚨 CRITICAL OS DEADLOCK DETECTED! All active threads are locked. Simulation halted.")
                self.db.log_event(self.controller.sim_id, "SYSTEM", "0", "DEADLOCK", "Deadlock condition detected! All threads are blocked in mutual wait state.", snap["elapsed_time"])
                self.control_panel.trigger_sound("warn")
            elif blocked_cnt < active_cnt and self.tracker.deadlock_detected:
                self.tracker.set_deadlock_flag(False)
                
            # Starvation: Check if any thread has wait time > 15 seconds
            starving = False
            for tid, t in threads.items():
                if t["wait_time"] > 15.0 and t["state"] in [ThreadState.WAITING, ThreadState.BLOCKED]:
                    starving = True
                    if not self.tracker.starvation_detected:
                        self.tracker.set_starvation_flag(True)
                        self.tracker.set_edu_message(f"⚠️ THREAD STARVATION ALERT: {tid} has spent {t['wait_time']:.1f}s blocked on resources.")
                        self.db.log_event(self.controller.sim_id, "SYSTEM", tid, "STARVATION", f"Thread {tid} is experiencing starvation. Wait time exceeds 15 seconds.", snap["elapsed_time"])
                        self.control_panel.trigger_sound("warn")
                    break
            if not starving and self.tracker.starvation_detected:
                self.tracker.set_starvation_flag(False)

    # --- REPLAY PLAYBACK LOOP ---
    
    def load_replay_dialog(self):
        sims = self.db.get_simulations()
        if not sims:
            QMessageBox.information(self, "Load Replay", "No saved simulations found in SQLite database.")
            return
            
        items = [f"Sim ID: {s[0]} | Date: {s[1]} | Size: {s[3]}P/{s[4]}C | Delay: {s[2]:.1f}s" for s in sims]
        item, ok = QInputDialog.getItem(self, "Load Simulation Replay", "Select a simulation record:", items, 0, False)
        
        if ok and item:
            sim_id = int(item.split("Sim ID: ")[1].split(" |")[0])
            self.stop_replay()
            
            # Start Replay
            success = self.controller.start_replay(sim_id)
            if success:
                self.conveyor_widget.clear_visual_state()
                # Reset layout sliders to match replay stats
                self.control_panel.prod_spin.setValue(self.controller.num_producers)
                self.control_panel.cons_spin.setValue(self.controller.num_consumers)
                self.control_panel.cap_spin.setValue(self.controller.buffer_capacity)
                self.control_panel.prod_delay.setValue(self.controller.prod_rate)
                self.control_panel.cons_delay.setValue(self.controller.cons_rate)
                self.control_panel.item_combo.setCurrentText(self.controller.item_type)
                self.control_panel.theme_combo.setCurrentText(self.controller.theme)
                
                # Apply styles
                self.apply_theme(self.controller.theme)
                self.analytics_panel.reset()
                
                # Configure control panel widgets
                self.control_panel.start_btn.setEnabled(False)
                self.control_panel.pause_btn.setEnabled(True)
                self.control_panel.resume_btn.setEnabled(False)
                self.control_panel.stop_btn.setEnabled(True)
                
                # Start replay frame timer matching the original playback speeds
                replay_interval = int(300 / self.controller._speed_multiplier)  # original recording is 300ms
                self.replay_timer.start(max(10, replay_interval))

    def play_next_replay_frame(self):
        if self.controller._paused:
            return
            
        advanced = self.controller.step_replay()
        if not advanced:
            self.stop_replay()
            QMessageBox.information(self, "Replay Finished", "Simulation replay playback completed.")

    def stop_replay(self):
        self.replay_timer.stop()
        self.controller.is_replay = False
        self.control_panel.stop_simulation()

    def manage_simulations_dialog(self):
        sims = self.db.get_simulations()
        if not sims:
            QMessageBox.information(self, "Manage Simulations", "No saved simulations found.")
            return
            
        items = [f"Sim ID: {s[0]} | Date: {s[1]} | Size: {s[3]}P/{s[4]}C" for s in sims]
        item, ok = QInputDialog.getItem(self, "Delete Saved Record", "Select a simulation record to REMOVE:", items, 0, False)
        
        if ok and item:
            sim_id = int(item.split("Sim ID: ")[1].split(" |")[0])
            self.db.delete_simulation(sim_id)
            QMessageBox.information(self, "Record Deleted", f"Simulation record ID {sim_id} was successfully deleted from database.")

    def closeEvent(self, event):
        """Cleanup threads and timers before closing app"""
        self.ui_timer.stop()
        self.replay_timer.stop()
        self.conveyor_widget.anim_timer.stop()
        self.controller.stop_sim()
        event.accept()
