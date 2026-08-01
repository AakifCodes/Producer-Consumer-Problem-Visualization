from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class AIAdvisorPanel(QWidget):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.theme = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.card = QFrame(self)
        self.card.setObjectName("card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)
        
        title = QLabel("AI PERFORMANCE ADVISOR", self.card)
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        card_layout.addWidget(title)
        
        self.recommendations_lbl = QLabel(
            "Analyzing thread performance metrics... Please start the simulation to trigger analytical evaluations.", 
            self.card
        )
        self.recommendations_lbl.setFont(QFont("Segoe UI", 10))
        self.recommendations_lbl.setWordWrap(True)
        self.recommendations_lbl.setStyleSheet("color: #888888; line-height: 1.4;")
        self.recommendations_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(self.recommendations_lbl)
        
        layout.addWidget(self.card)

    def set_theme(self, theme_data):
        self.theme = theme_data

    def get_live_recommendations(self):
        snap = self.tracker.get_snapshot()
        
        producers = [t for t in snap["threads"].values() if t["type"] == "PRODUCER"]
        consumers = [t for t in snap["threads"].values() if t["type"] == "CONSUMER"]
        
        if not producers or not consumers:
            return ["No active threads. Please start the simulation to evaluate factory throughput balance."]
            
        prod_cnt = len(producers)
        cons_cnt = len(consumers)
        
        avg_wait = snap["avg_wait_time"]
        cap = snap["buffer_capacity"]
        curr_occupancy = snap["buffer_size"]
        
        prod_blocks = snap["producer_block_count"]
        cons_blocks = snap["consumer_block_count"]
        
        recs = []
        
        # 1. Capacity Analysis
        if cap < 3:
            recs.append("<b>ℹ️ Low Buffer Space:</b> The buffer capacity is highly restricted. This forces severe thread switching overhead and frequent blocking. Consider increasing Buffer Size to at least 5 slots to optimize core concurrent throughput.")
        
        # 2. Balance Assessment
        occupancy_ratio = curr_occupancy / cap if cap > 0 else 0
        
        if occupancy_ratio >= 0.8:
            recs.append("<b>⚠️ Write Congestion:</b> The conveyor is currently saturated (Buffer is FULL). Producers are blocked waiting for open space. To resolve this write bottleneck, <i>spawn more Consumer threads</i> or <i>increase the consumption rate</i>.")
        elif occupancy_ratio <= 0.2:
            recs.append("<b>⚠️ Thread Starvation:</b> The conveyor belt is near empty. Consumers are sitting idle waiting for parts. Suggest <i>spawning more Producer threads</i> or <i>speeding up production rates</i> to feed the assembly machines.")
        else:
            recs.append("<b>✅ Perfectly Balanced:</b> Core thread velocities are exceptionally matched! The conveyor belt occupancy is hovering at a healthy stable state (~30-70% capacity). Locking and semaphore handshakes are fully optimized.")
            
        # 3. Block overhead warnings
        total_blocks = prod_blocks + cons_blocks
        if total_blocks > 25:
            recs.append(f"<b>⚡ High Context-Switch Cost:</b> The system has logged {total_blocks} total thread blocking events. If average wait times ({avg_wait:.2f}s) exceed target thread thresholds, consider increasing simulation speed (e.g. 2x, 5x) to compress execution cycles.")
            
        if snap["deadlock_detected"]:
            recs.append("<b>🚨 CRITICAL ERROR:</b> Deadlock detected! Ensure empty/full semaphores are evaluated <i>before</i> attempting to lock mutual exclusion mutexes.")

        return recs

    def update_advisor(self):
        recs = self.get_live_recommendations()
        
        # Join list with bullet formatting
        html = ""
        for rec in recs:
            html += f"<p style='margin-bottom: 8px;'>• {rec}</p>"
            
        self.recommendations_lbl.setText(html)
        self.recommendations_lbl.setStyleSheet("color: #e0e0e0; line-height: 1.4;")
