from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QProgressBar
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class SyncMonitor(QWidget):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.theme = None
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 1. Mutex Status Card
        self.mutex_card = QFrame(self)
        self.mutex_card.setObjectName("card")
        mutex_layout = QVBoxLayout(self.mutex_card)
        mutex_layout.setContentsMargins(15, 15, 15, 15)
        
        mutex_title = QLabel("MUTEX LOCK", self.mutex_card)
        mutex_title.setObjectName("title")
        mutex_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        mutex_layout.addWidget(mutex_title)
        
        self.mutex_val = QLabel("UNLOCKED", self.mutex_card)
        self.mutex_val.setObjectName("value")
        self.mutex_val.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.mutex_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mutex_layout.addWidget(self.mutex_val)
        
        self.mutex_details = QLabel("Owner: None", self.mutex_card)
        self.mutex_details.setFont(QFont("Segoe UI", 9))
        self.mutex_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mutex_layout.addWidget(self.mutex_details)
        
        layout.addWidget(self.mutex_card)
        
        # 2. Empty Semaphore Card
        self.empty_card = QFrame(self)
        self.empty_card.setObjectName("card")
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setContentsMargins(15, 15, 15, 15)
        
        empty_title = QLabel("EMPTY SEMAPHORE", self.empty_card)
        empty_title.setObjectName("title")
        empty_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        empty_layout.addWidget(empty_title)
        
        self.empty_val = QLabel("0", self.empty_card)
        self.empty_val.setObjectName("value")
        self.empty_val.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.empty_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_val)
        
        self.empty_progress = QProgressBar(self.empty_card)
        self.empty_progress.setTextVisible(False)
        self.empty_progress.setFixedHeight(8)
        empty_layout.addWidget(self.empty_progress)
        
        layout.addWidget(self.empty_card)
        
        # 3. Full Semaphore Card
        self.full_card = QFrame(self)
        self.full_card.setObjectName("card")
        full_layout = QVBoxLayout(self.full_card)
        full_layout.setContentsMargins(15, 15, 15, 15)
        
        full_title = QLabel("FULL SEMAPHORE", self.full_card)
        full_title.setObjectName("title")
        full_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        full_layout.addWidget(full_title)
        
        self.full_val = QLabel("0", self.full_card)
        self.full_val.setObjectName("value")
        self.full_val.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.full_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        full_layout.addWidget(self.full_val)
        
        self.full_progress = QProgressBar(self.full_card)
        self.full_progress.setTextVisible(False)
        self.full_progress.setFixedHeight(8)
        full_layout.addWidget(self.full_progress)
        
        layout.addWidget(self.full_card)

        # 4. Waiting Threads Registry Card
        self.wait_card = QFrame(self)
        self.wait_card.setObjectName("card")
        wait_layout = QVBoxLayout(self.wait_card)
        wait_layout.setContentsMargins(15, 15, 15, 15)
        
        wait_title = QLabel("THREAD LOCK QUEUES", self.wait_card)
        wait_title.setObjectName("title")
        wait_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        wait_layout.addWidget(wait_title)
        
        self.producers_waiting = QLabel("Waiting Producers: None", self.wait_card)
        self.producers_waiting.setFont(QFont("Segoe UI", 9))
        self.producers_waiting.setWordWrap(True)
        wait_layout.addWidget(self.producers_waiting)
        
        self.consumers_waiting = QLabel("Waiting Consumers: None", self.wait_card)
        self.consumers_waiting.setFont(QFont("Segoe UI", 9))
        self.consumers_waiting.setWordWrap(True)
        wait_layout.addWidget(self.consumers_waiting)
        
        layout.addWidget(self.wait_card)

    def set_theme(self, theme_data):
        self.theme = theme_data
        
        # Style sheets are managed by the parent, but we can set inline adjustments
        accent = theme_data["accent"]
        self.empty_progress.setStyleSheet(f"""
            QProgressBar::chunk {{ background-color: {accent}; border-radius: 4px; }}
            QProgressBar {{ background-color: {theme_data["border"]}; border-radius: 4px; border: none; }}
        """)
        self.full_progress.setStyleSheet(f"""
            QProgressBar::chunk {{ background-color: {accent}; border-radius: 4px; }}
            QProgressBar {{ background-color: {theme_data["border"]}; border-radius: 4px; border: none; }}
        """)

    def update_monitor(self):
        snap = self.tracker.get_snapshot()
        
        # 1. Mutex Status
        owner = snap["mutex_locked_by"]
        if owner:
            self.mutex_val.setText("LOCKED")
            self.mutex_val.setStyleSheet("color: #ff3333; font-size: 16px; font-weight: bold;")
            self.mutex_details.setText(f"Held by: {owner}")
        else:
            self.mutex_val.setText("FREE")
            self.mutex_val.setStyleSheet("color: #00ff88; font-size: 16px; font-weight: bold;")
            self.mutex_details.setText("Held by: None")
            
        # 2. Empty Semaphore
        cap = snap["buffer_capacity"]
        empty_val = snap["empty_semaphore_val"]
        self.empty_val.setText(str(empty_val))
        self.empty_progress.setMaximum(cap)
        self.empty_progress.setValue(max(0, empty_val))
        
        # 3. Full Semaphore
        full_val = snap["full_semaphore_val"]
        self.full_val.setText(str(full_val))
        self.full_progress.setMaximum(cap)
        self.full_progress.setValue(max(0, full_val))
        
        # 4. Waiting list queues
        producers_wait_list = []
        consumers_wait_list = []
        
        for tid, t in snap["threads"].items():
            if t["state"] in ["WAITING", "BLOCKED"]:
                if t["type"] == "PRODUCER":
                    producers_wait_list.append(t["id"])
                else:
                    consumers_wait_list.append(t["id"])
                    
        if producers_wait_list:
            self.producers_waiting.setText(f"<b>Blocked Producers:</b> {', '.join(producers_wait_list)}")
            self.producers_waiting.setStyleSheet("color: #ffff55;")
        else:
            self.producers_waiting.setText("Blocked Producers: None")
            self.producers_waiting.setStyleSheet("color: #888888;")
            
        if consumers_wait_list:
            self.consumers_waiting.setText(f"<b>Blocked Consumers:</b> {', '.join(consumers_wait_list)}")
            self.consumers_waiting.setStyleSheet("color: #ffff55;")
        else:
            self.consumers_waiting.setText("Blocked Consumers: None")
            self.consumers_waiting.setStyleSheet("color: #888888;")
