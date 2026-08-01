import csv
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QCheckBox, 
                             QFileDialog, QHeaderView)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class LogPanel(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.last_event_id = 0
        self.theme = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Title bar & Export Controls
        header_layout = QHBoxLayout()
        title = QLabel("SYSTEM CONSOLE LOGS", self)
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.clear_btn = QPushButton("Clear Panel", self)
        self.clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_btn)
        
        self.export_csv_btn = QPushButton("Export CSV", self)
        self.export_csv_btn.clicked.connect(self.export_csv)
        header_layout.addWidget(self.export_csv_btn)
        
        self.export_txt_btn = QPushButton("Export TXT", self)
        self.export_txt_btn.clicked.connect(self.export_txt)
        header_layout.addWidget(self.export_txt_btn)
        
        layout.addLayout(header_layout)
        
        # 2. Filter & Search Controls
        filter_layout = QHBoxLayout()
        
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search events...")
        self.search_box.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.search_box)
        
        self.cb_producers = QCheckBox("Producers", self)
        self.cb_producers.setChecked(True)
        self.cb_producers.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.cb_producers)
        
        self.cb_consumers = QCheckBox("Consumers", self)
        self.cb_consumers.setChecked(True)
        self.cb_consumers.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.cb_consumers)
        
        self.cb_system = QCheckBox("System/Alerts", self)
        self.cb_system.setChecked(True)
        self.cb_system.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.cb_system)
        
        layout.addLayout(filter_layout)
        
        # 3. Log Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Timestamp", "Source", "Event", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setFont(QFont("Consolas", 9))
        layout.addWidget(self.table)

    def set_theme(self, theme_data):
        self.theme = theme_data

    def clear_logs(self):
        self.table.setRowCount(0)
        self.last_event_id = 0

    def update_logs(self):
        if not self.controller.sim_id:
            return
            
        events = self.controller.db.get_simulation_events(self.controller.sim_id)
        # Filter for only new events
        new_events = [e for e in events if e[0] > self.last_event_id]
        
        if not new_events:
            return
            
        for event in new_events:
            ev_id, _, timestamp, elapsed, thread_type, thread_id, event_type, details = event
            self.last_event_id = max(self.last_event_id, ev_id)
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Formulate friendly thread source names
            source = f"{thread_type}-{thread_id}" if thread_id != "0" else thread_type
            
            # Items
            id_item = QTableWidgetItem(str(ev_id))
            time_item = QTableWidgetItem(f"[{timestamp}]")
            src_item = QTableWidgetItem(source)
            type_item = QTableWidgetItem(event_type)
            details_item = QTableWidgetItem(details)
            
            # Alignments
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            src_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Colors based on event severity
            if "DEADLOCK" in event_type or "CRITICAL" in details.upper():
                color = "#ff3333"  # Red
            elif "STRESS" in event_type or "BURST" in details.upper():
                color = "#f57c00"  # Orange
            elif "PRODUCE" in event_type:
                color = self.theme.get("producer_color", "#55ff55") if self.theme else "#55ff55"
            elif "CONSUME" in event_type:
                color = self.theme.get("consumer_color", "#55aaff") if self.theme else "#55aaff"
            else:
                color = self.theme.get("text", "#e0e0e0") if self.theme else "#e0e0e0"
                
            from PyQt6.QtGui import QColor
            q_color = QColor(color)
            for item in (id_item, time_item, src_item, type_item, details_item):
                item.setForeground(q_color)
                
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, time_item)
            self.table.setItem(row, 2, src_item)
            self.table.setItem(row, 3, type_item)
            self.table.setItem(row, 4, details_item)
            
        # Autoscroll
        self.table.scrollToBottom()
        self.apply_filter()

    def apply_filter(self):
        search_query = self.search_box.text().lower()
        show_prod = self.cb_producers.isChecked()
        show_cons = self.cb_consumers.isChecked()
        show_sys = self.cb_system.isChecked()
        
        for row in range(self.table.rowCount()):
            source = self.table.item(row, 2).text().upper()
            details = self.table.item(row, 4).text().lower()
            
            # Category filters
            category_match = False
            if "PRODUCER" in source and show_prod:
                category_match = True
            elif "CONSUMER" in source and show_cons:
                category_match = True
            elif ("SYSTEM" in source or "STRESS" in source) and show_sys:
                category_match = True
                
            # Search filter
            search_match = (search_query in details) or (search_query in source.lower())
            
            # Hide/Show row
            if category_match and search_match:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV Logs", "", "CSV Files (*.csv)")
        if not path:
            return
            
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Timestamp", "Source", "Event", "Description"])
                for row in range(self.table.rowCount()):
                    if not self.table.isRowHidden(row):
                        row_data = [self.table.item(row, col).text() for col in range(5)]
                        writer.writerow(row_data)
        except Exception as e:
            print(f"Error exporting CSV: {e}")

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export TXT Logs", "", "Text Files (*.txt)")
        if not path:
            return
            
        try:
            with open(path, "w", encoding="utf-8") as f:
                for row in range(self.table.rowCount()):
                    if not self.table.isRowHidden(row):
                        line = " | ".join(self.table.item(row, col).text() for col in range(5))
                        f.write(line + "\n")
        except Exception as e:
            print(f"Error exporting TXT: {e}")
