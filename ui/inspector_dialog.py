from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QFrame
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class InspectorDialog(QDialog):
    def __init__(self, thread_name, tracker, parent=None):
        super().__init__(parent)
        self.thread_name = thread_name
        self.tracker = tracker
        self.theme = parent.theme if parent else None
        
        self.setMinimumSize(400, 450)
        self.setWindowTitle(f"Thread Inspector: {thread_name}")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Apply theme stylesheet to dialog window
        if self.theme:
            self.setStyleSheet(f"""
                QDialog {{ background-color: {self.theme["bg"]}; }}
                QLabel {{ color: {self.theme["text"]}; }}
                QFrame#card {{ background-color: {self.theme["panel"]}; border: 1px solid {self.theme["border"]}; border-radius: 6px; }}
                QListWidget {{ background-color: {self.theme["panel"]}; border: 1px solid {self.theme["border"]}; border-radius: 6px; color: {self.theme["text"]}; }}
                QPushButton {{ background-color: {self.theme["border"]}; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; color: {self.theme["text"]}; }}
                QPushButton:hover {{ background-color: {self.theme["accent"]}; color: {self.theme["bg"]}; }}
            """)
            
        snap = self.tracker.get_snapshot()
        thread_info = snap["threads"].get(self.thread_name)
        
        if not thread_info:
            err_label = QLabel(f"Thread '{self.thread_name}' is no longer active or registered.", self)
            err_label.setFont(QFont("Segoe UI", 10))
            layout.addWidget(err_label)
            
            close_btn = QPushButton("Close", self)
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn)
            return

        # 1. Header Card
        header_card = QFrame(self)
        header_card.setObjectName("card")
        header_layout = QVBoxLayout(header_card)
        
        name_lbl = QLabel(f"THREAD ID: {self.thread_name}", header_card)
        name_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {self.theme['accent'] if self.theme else '#00ff88'};")
        header_layout.addWidget(name_lbl)
        
        type_lbl = QLabel(f"Role: {thread_info['type']}", header_card)
        type_lbl.setFont(QFont("Segoe UI", 10))
        header_layout.addWidget(type_lbl)
        
        layout.addWidget(header_card)
        
        # 2. Stats Grid Card
        stats_card = QFrame(self)
        stats_card.setObjectName("card")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setSpacing(6)
        
        # Current State
        state_layout = QHBoxLayout()
        state_title = QLabel("Current State:", stats_card)
        state_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        
        state_val = QLabel(thread_info["state"], stats_card)
        state_val.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        
        # Apply coloring based on state
        state_colors = {"RUNNING": "#55ff55", "WAITING": "#ffff55", "BLOCKED": "#ff5555", "SLEEPING": "#55aaff"}
        state_color = state_colors.get(thread_info["state"], "#888888")
        state_val.setStyleSheet(f"color: {state_color};")
        
        state_layout.addWidget(state_title)
        state_layout.addWidget(state_val)
        state_layout.addStretch()
        stats_layout.addLayout(state_layout)
        
        # Processed Count
        proc_layout = QHBoxLayout()
        proc_title = QLabel("Items Processed:", stats_card)
        proc_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        proc_val = QLabel(str(thread_info["items_processed"]), stats_card)
        proc_layout.addWidget(proc_title)
        proc_layout.addWidget(proc_val)
        proc_layout.addStretch()
        stats_layout.addLayout(proc_layout)
        
        # Total Wait Time
        wait_layout = QHBoxLayout()
        wait_title = QLabel("Accumulated Wait Time:", stats_card)
        wait_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        wait_val = QLabel(f"{thread_info['wait_time']:.2f} seconds", stats_card)
        wait_layout.addWidget(wait_title)
        wait_layout.addWidget(wait_val)
        wait_layout.addStretch()
        stats_layout.addLayout(wait_layout)
        
        # Current Task
        task_layout = QHBoxLayout()
        task_title = QLabel("Current Task:", stats_card)
        task_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        task_val = QLabel(thread_info["current_task"], stats_card)
        task_layout.addWidget(task_title)
        task_layout.addWidget(task_val)
        task_layout.addStretch()
        stats_layout.addLayout(task_layout)
        
        layout.addWidget(stats_card)
        
        # 3. History Log Card
        history_title = QLabel("STATE CHANGE TRANSACTION HISTORY", self)
        history_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(history_title)
        
        self.history_list = QListWidget(self)
        self.history_list.setFont(QFont("Consolas", 9))
        for log_entry in thread_info["history"]:
            self.history_list.addItem(log_entry)
        # Scroll to bottom
        self.history_list.scrollToBottom()
        layout.addWidget(self.history_list)
        
        # Close Button
        close_btn = QPushButton("Dismiss Inspector", self)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
