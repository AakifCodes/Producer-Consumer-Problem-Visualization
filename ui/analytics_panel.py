import time
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame
import pyqtgraph as pg
from pyqtgraph import PlotWidget, BarGraphItem

class AnalyticsPanel(QWidget):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.theme = None
        
        # Historical arrays for plotting
        self.time_history = []
        self.occupancy_history = []
        self.prod_throughput_history = []
        self.cons_throughput_history = []
        
        # Throughput computation variables
        self.last_update_time = time.time()
        self.last_produced_cnt = 0
        self.last_consumed_cnt = 0
        
        self._init_ui()

    def _init_ui(self):
        # Master layout (horizontal split)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Set up dark plotting defaults for pyqtgraph
        pg.setConfigOption('background', '#18181f')
        pg.setConfigOption('foreground', '#d8d9da')
        
        # 1. Left Chart: Buffer Occupancy & Throughput
        self.chart_frame1 = QFrame(self)
        self.chart_frame1.setObjectName("card")
        c1_layout = QVBoxLayout(self.chart_frame1)
        
        # Buffer Occupancy Chart
        self.occupancy_plot = PlotWidget(title="Live Buffer Occupancy (Time vs Slots)")
        self.occupancy_plot.showGrid(x=True, y=True, alpha=0.3)
        self.occupancy_plot.setLabel('left', 'Buffer Usage', units='slots')
        self.occupancy_plot.setLabel('bottom', 'Elapsed Time', units='s')
        self.occupancy_curve = self.occupancy_plot.plot(pen=pg.mkPen('#00ff88', width=2))
        self.capacity_line = self.occupancy_plot.plot(pen=pg.mkPen('#ff3333', width=1, style=pg.QtCore.Qt.PenStyle.DashLine))
        
        c1_layout.addWidget(self.occupancy_plot)
        layout.addWidget(self.chart_frame1)
        
        # 2. Right Chart: Throughput Metrics & Wait Times
        self.chart_frame2 = QFrame(self)
        self.chart_frame2.setObjectName("card")
        c2_layout = QVBoxLayout(self.chart_frame2)
        
        # Throughput Chart
        self.throughput_plot = PlotWidget(title="System Throughput (Items/s)")
        self.throughput_plot.showGrid(x=True, y=True, alpha=0.3)
        self.throughput_plot.setLabel('left', 'Items Processed', units='qty/s')
        self.throughput_plot.setLabel('bottom', 'Elapsed Time', units='s')
        self.prod_curve = self.throughput_plot.plot(pen=pg.mkPen('#ffb300', width=2), name="Production")
        self.cons_curve = self.throughput_plot.plot(pen=pg.mkPen('#3b82f6', width=2), name="Consumption")
        
        # Thread Wait Times Bar Chart
        self.wait_plot = PlotWidget(title="Thread Wait Times Breakdown (Total Blocked s)")
        self.wait_plot.showGrid(x=True, y=True, alpha=0.3)
        self.wait_plot.setLabel('left', 'Total Wait', units='s')
        self.wait_plot.setLabel('bottom', 'Thread ID')
        self.wait_bar = None
        
        c2_layout.addWidget(self.throughput_plot)
        c2_layout.addWidget(self.wait_plot)
        layout.addWidget(self.chart_frame2)

    def set_theme(self, theme_data):
        self.theme = theme_data
        bg_hex = theme_data.get("panel", "#1e1e1e")
        text_hex = theme_data.get("text", "#e0e0e0")
        accent_hex = theme_data.get("accent", "#00ff88")
        
        pg.setConfigOption('background', bg_hex)
        pg.setConfigOption('foreground', text_hex)
        
        self.occupancy_plot.setBackground(bg_hex)
        self.throughput_plot.setBackground(bg_hex)
        self.wait_plot.setBackground(bg_hex)
        
        # Redraw lines
        self.occupancy_curve.setPen(pg.mkPen(accent_hex, width=2))
        self.prod_curve.setPen(pg.mkPen(theme_data.get("producer_color", "#ffb300"), width=2))
        self.cons_curve.setPen(pg.mkPen(theme_data.get("consumer_color", "#3b82f6"), width=2))

    def reset(self):
        self.time_history.clear()
        self.occupancy_history.clear()
        self.prod_throughput_history.clear()
        self.cons_throughput_history.clear()
        
        self.last_update_time = time.time()
        self.last_produced_cnt = 0
        self.last_consumed_cnt = 0
        
        self.occupancy_curve.setData([], [])
        self.capacity_line.setData([], [])
        self.prod_curve.setData([], [])
        self.cons_curve.setData([], [])
        self.wait_plot.clear()

    def update_charts(self):
        snap = self.tracker.get_snapshot()
        elapsed = snap["elapsed_time"]
        
        # Calculate instant throughput (items per second)
        now = time.time()
        time_diff = now - self.last_update_time
        
        if time_diff >= 0.5:  # every half-second
            prod_cnt = snap["total_produced"]
            cons_cnt = snap["total_consumed"]
            
            p_rate = (prod_cnt - self.last_produced_cnt) / time_diff
            c_rate = (cons_cnt - self.last_consumed_cnt) / time_diff
            
            self.last_update_time = now
            self.last_produced_cnt = prod_cnt
            self.last_consumed_cnt = cons_cnt
            
            # Record historical analytics
            self.time_history.append(elapsed)
            self.occupancy_history.append(snap["buffer_size"])
            self.prod_throughput_history.append(p_rate)
            self.cons_throughput_history.append(c_rate)
            
            # Capping data to last 100 points
            if len(self.time_history) > 100:
                self.time_history.pop(0)
                self.occupancy_history.pop(0)
                self.prod_throughput_history.pop(0)
                self.cons_throughput_history.pop(0)
                
            # Render occupancy
            self.occupancy_curve.setData(self.time_history, self.occupancy_history)
            
            cap = snap["buffer_capacity"]
            self.capacity_line.setData(self.time_history, [cap] * len(self.time_history))
            
            # Render throughput
            self.prod_curve.setData(self.time_history, self.prod_throughput_history)
            self.cons_curve.setData(self.time_history, self.cons_throughput_history)
            
        # Render wait time bar chart (do this at 30 FPS for reactive visuals)
        threads = snap["threads"]
        if threads:
            names = []
            waits = []
            colors = []
            
            for tid, t in sorted(threads.items()):
                names.append(tid)
                waits.append(t["wait_time"])
                if t["type"] == "PRODUCER":
                    colors.append('#ffb300')
                else:
                    colors.append('#3b82f6')
                    
            self.wait_plot.clear()
            
            # Set up ticks
            x_indices = list(range(len(names)))
            ticks = [[(idx, name) for idx, name in enumerate(names)]]
            self.wait_plot.getAxis('bottom').setTicks(ticks)
            
            # Render bar items
            bg_item = BarGraphItem(x=x_indices, height=waits, width=0.6, brushes=colors, pens=colors)
            self.wait_plot.addItem(bg_item)
