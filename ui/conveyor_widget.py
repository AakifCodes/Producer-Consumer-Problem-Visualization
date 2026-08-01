import re
import time
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import QTimer, QRectF, Qt
from state_tracker import ThreadState

class VisualItem:
    def __init__(self, item_id, color, label, start_x, start_y):
        self.item_id = item_id
        self.color = QColor(color)
        self.label = label
        self.x = float(start_x)
        self.y = float(start_y)
        self.target_x = float(start_x)
        self.target_y = float(start_y)
        self.speed = 0.12  # Interpolation factor (fraction of remaining distance per frame)
        self.finished = False

    def update_position(self, speed_mult=1.0):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        step = min(1.0, self.speed * speed_mult)
        if dist < 1.5:
            self.x = self.target_x
            self.y = self.target_y
            return True

        self.x += dx * step
        self.y += dy * step
        return False


class ConveyorWidget(QWidget):
    def __init__(self, tracker, controller, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.controller = controller
        
        self.setMinimumHeight(350)
        self.theme = None
        
        # Smooth animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_frame)
        self.anim_timer.start(16)  # ~60 FPS
        
        # Track items in transition
        self.visual_items = {}  # item_id -> VisualItem
        self._last_buffer_ids = set()
        self._item_meta = {}  # item_id -> {"color", "type", "producer_pid", "consumer_cid"}

        # Theme configuration
        self.state_colors = {
            ThreadState.RUNNING: QColor("#55ff55"),   # Glowing Green
            ThreadState.WAITING: QColor("#ffff55"),   # Warning Yellow
            ThreadState.BLOCKED: QColor("#ff5555"),   # Blocked Red
            ThreadState.SLEEPING: QColor("#55aaff"),  # Idle Blue
        }

    def set_theme(self, theme_data):
        self.theme = theme_data
        # Customize state colors according to the theme
        if theme_data["name"] == "Cyber Theme":
            self.state_colors[ThreadState.RUNNING] = QColor("#00f0ff") # Neon Cyan
            self.state_colors[ThreadState.WAITING] = QColor("#ffea00") # Neon Yellow
            self.state_colors[ThreadState.BLOCKED] = QColor("#ff007f") # Neon Pink
            self.state_colors[ThreadState.SLEEPING] = QColor("#7a7a9a") # Dark Slate
        else:
            self.state_colors[ThreadState.RUNNING] = QColor(theme_data.get("producer_color", "#55ff55"))
            self.state_colors[ThreadState.WAITING] = QColor("#ffff55")
            self.state_colors[ThreadState.BLOCKED] = QColor("#ff5555")
            self.state_colors[ThreadState.SLEEPING] = QColor(theme_data.get("consumer_color", "#55aaff"))

    def clear_visual_state(self):
        self.visual_items.clear()
        self._last_buffer_ids.clear()
        self._item_meta.clear()

    def _track_geometry(self):
        margin = 150
        track_width = max(100, self.width() - margin * 2)
        belt_y = self.height() / 2
        return margin, track_width, belt_y

    def _slot_position(self, index, capacity):
        margin, track_width, belt_y = self._track_geometry()
        if capacity <= 1:
            slot_x = margin + track_width / 2
        else:
            slot_step = track_width / (capacity - 1)
            slot_x = margin + index * slot_step
        return slot_x, belt_y

    def _parse_producer_pid(self, item_id):
        match = re.match(r"P(\d+)-", str(item_id))
        return int(match.group(1)) if match else None

    def _parse_consumer_cid(self, item_id):
        return self._item_meta.get(item_id, {}).get("consumer_cid")

    def _producer_coords(self, pid, producers):
        if pid is None or not producers:
            return 65.0, self.height() / 3
        try:
            idx = next(i for i, p in enumerate(producers) if p["id"] == f"Producer-{pid}")
        except StopIteration:
            idx = min(pid - 1, len(producers) - 1)
        h_step = (self.height() - 40) / len(producers)
        y_coord = 25 + idx * h_step + h_step / 2
        return 65.0, y_coord

    def _consumer_coords(self, cid, consumers):
        if cid is None or not consumers:
            return float(self.width() - 65), self.height() / 2
        try:
            idx = next(i for i, c in enumerate(consumers) if c["id"] == f"Consumer-{cid}")
        except StopIteration:
            idx = min((cid or 1) - 1, len(consumers) - 1)
        h_step = (self.height() - 40) / len(consumers)
        y_coord = 25 + idx * h_step + h_step / 2
        return float(self.width() - 65), y_coord

    def _short_label(self, item_id, label):
        if label and len(label) <= 4:
            return label[:4]
        parts = str(item_id).split("-")
        return parts[-1][-3:] if parts else str(item_id)[-3:]

    def _spawn_visual_item(self, item, start_x, start_y):
        i_id = item["id"]
        self._item_meta[i_id] = {
            "color": item.get("color", "#4fc3f7"),
            "type": item.get("type", ""),
            "producer_pid": self._parse_producer_pid(i_id),
        }
        label = item.get("type", i_id)
        self.visual_items[i_id] = VisualItem(i_id, item["color"], label, start_x, start_y)

    def animate_frame(self):
        if self.width() <= 0 or self.height() <= 0:
            return

        if (
            not self.controller.is_replay
            and not self.controller.producers
            and not self.controller.consumers
            and self.visual_items
        ):
            self.clear_visual_state()
            self.update()
            return

        speed_mult = self.controller._speed_multiplier
        to_remove = []

        for item_id, v_item in list(self.visual_items.items()):
            reached = v_item.update_position(speed_mult)
            if reached and v_item.finished:
                to_remove.append(item_id)

        for r_id in to_remove:
            self.visual_items.pop(r_id, None)
            self._item_meta.pop(r_id, None)

        snap = self.tracker.get_snapshot()
        buffer_items = snap["buffer_items"]
        capacity = snap["buffer_capacity"]
        threads = snap["threads"]
        producers = [t for t in threads.values() if t["type"] == "PRODUCER"]
        consumers = [t for t in threads.values() if t["type"] == "CONSUMER"]

        current_ids = {item["id"] for item in buffer_items}
        removed_ids = self._last_buffer_ids - current_ids

        for i_id in removed_ids:
            if i_id in self.visual_items:
                continue
            meta = self._item_meta.get(i_id, {})
            belt_x, belt_y = self._slot_position(0, capacity)
            spawn_x, spawn_y = belt_x, belt_y
            if meta.get("producer_pid"):
                spawn_x, spawn_y = self._producer_coords(meta["producer_pid"], producers)
            item_stub = {
                "id": i_id,
                "color": meta.get("color", "#4fc3f7"),
                "type": meta.get("type", ""),
            }
            self._spawn_visual_item(item_stub, spawn_x, spawn_y)

        for idx, item in enumerate(buffer_items):
            i_id = item["id"]
            slot_x, slot_y = self._slot_position(idx, capacity)

            if i_id not in self.visual_items:
                pid = self._parse_producer_pid(i_id)
                start_x, start_y = self._producer_coords(pid, producers)
                self._spawn_visual_item(item, start_x, start_y)
            else:
                v_item = self.visual_items[i_id]
                v_item.color = QColor(item["color"])
                v_item.label = item.get("type", v_item.label)
                v_item.finished = False

            self.visual_items[i_id].target_x = slot_x
            self.visual_items[i_id].target_y = slot_y
            self._item_meta[i_id] = {
                "color": item.get("color", "#4fc3f7"),
                "type": item.get("type", ""),
                "producer_pid": self._parse_producer_pid(i_id),
            }

        for i_id, v_item in list(self.visual_items.items()):
            if i_id in current_ids or v_item.finished:
                continue
            cid = self._parse_consumer_cid(i_id)
            if cid is None and consumers:
                cid = (hash(i_id) % len(consumers)) + 1
            target_x, target_y = self._consumer_coords(cid, consumers)
            v_item.target_x = target_x
            v_item.target_y = target_y
            v_item.finished = True

        self._last_buffer_ids = current_ids
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background based on theme
        bg_color = QColor(self.theme["panel"] if self.theme else "#1e1e1e")
        painter.fillRect(self.rect(), bg_color)
        
        # Get simulation snapshots
        snap = self.tracker.get_snapshot()
        threads = snap["threads"]
        capacity = snap["buffer_capacity"]
        
        # 1. DRAW SIDE PANELS FOR THREADS
        # Left Panel (Producers)
        painter.setPen(QPen(QColor(self.theme["border"] if self.theme else "#2d2d2d"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(self.theme["bg"] if self.theme else "#121212")))
        painter.drawRoundedRect(QRectF(10, 10, 110, self.height() - 20), 6.0, 6.0)
        
        # Right Panel (Consumers)
        painter.drawRoundedRect(QRectF(self.width() - 120, 10, 110, self.height() - 20), 6.0, 6.0)
        
        # 2. DRAW BELT TRACK
        belt_y = self.height() / 2
        margin = 150
        track_width = max(100, self.width() - margin * 2)
        
        painter.setPen(QPen(QColor(self.theme["border"] if self.theme else "#2d2d2d"), 4))
        painter.setBrush(QBrush(QColor(self.theme["bg"] if self.theme else "#121212")))
        painter.drawRoundedRect(QRectF(margin - 25, belt_y - 20, track_width + 50, 40), 15.0, 15.0)
        
        # Draw dynamic slot dividers (aligned with animation slot math)
        painter.setPen(QPen(QColor(self.theme["border"] if self.theme else "#2d2d2d"), 1))

        for idx in range(capacity):
            slot_x, _ = self._slot_position(idx, capacity)
            painter.drawEllipse(QRectF(slot_x - 15, belt_y - 15, 30, 30))
            # Draw slot index number
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(QColor(self.theme["muted"] if self.theme else "#888888")))
            painter.drawText(QRectF(slot_x - 15, belt_y - 32, 30, 15), Qt.AlignmentFlag.AlignCenter, str(idx + 1))
            painter.setPen(QPen(QColor(self.theme["border"] if self.theme else "#2d2d2d"), 1))
            
        # Draw Conveyor Belt texture lines (simple visual markers)
        painter.setPen(QPen(QColor(self.theme["border"] if self.theme else "#2d2d2d"), 2))
        pulse_shift = (time.time() * 20 * self.controller._speed_multiplier) % 30
        for l_x in range(margin - 10, self.width() - margin + 10, 30):
            shifted_x = l_x + pulse_shift
            if margin - 15 < shifted_x < self.width() - margin + 15:
                painter.drawLine(int(shifted_x), int(belt_y + 12), int(shifted_x - 8), int(belt_y + 19))
                
        # 3. DRAW PRODUCERS (LEFT)
        producers = [t for t in threads.values() if t["type"] == "PRODUCER"]
        if producers:
            h_step = (self.height() - 40) / len(producers)
            for i, p in enumerate(producers):
                y_coord = 25 + i * h_step + h_step / 2
                self.draw_thread_node(painter, p, 65, y_coord, "P")
                
        # 4. DRAW CONSUMERS (RIGHT)
        consumers = [t for t in threads.values() if t["type"] == "CONSUMER"]
        if consumers:
            h_step = (self.height() - 40) / len(consumers)
            for i, c in enumerate(consumers):
                y_coord = 25 + i * h_step + h_step / 2
                self.draw_thread_node(painter, c, self.width() - 65, y_coord, "C")
                
        # 5. DRAW VISUAL TRANSITIONAL ITEMS
        for item_id, v_item in self.visual_items.items():
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setBrush(QBrush(v_item.color))
            painter.drawRoundedRect(QRectF(v_item.x - 12, v_item.y - 12, 24, 24), 4, 4)
            
            # Print item name inside
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#000000")))
            painter.drawText(
                QRectF(v_item.x - 12, v_item.y - 12, 24, 24),
                Qt.AlignmentFlag.AlignCenter,
                self._short_label(v_item.item_id, v_item.label),
            )

        # 6. OVERFLOW / UNDERFLOW ALERTS
        sim_running = bool(self.controller.producers or self.controller.consumers or self.controller.is_replay)
        if snap["buffer_size"] >= capacity:
            self.draw_warning_banner(painter, "QUEUE OVERFLOW WARNING: BUFFER FULL")
        elif snap["buffer_size"] == 0 and sim_running and not self.controller._paused:
            self.draw_warning_banner(painter, "QUEUE UNDERFLOW WARNING: BUFFER EMPTY")
            
        # DEADLOCK WARNINGS
        if snap["deadlock_detected"]:
            self.draw_critical_banner(painter, "CRITICAL ERROR: DEADLOCK DETECTED! ALL THREADS BLOCKED")
        elif snap["starvation_detected"]:
            self.draw_critical_banner(painter, "ALERT: THREAD STARVATION DETECTED")

    def draw_thread_node(self, painter, thread, x, y, letter):
        state = thread["state"]
        color = self.state_colors.get(state, QColor("#888888"))
        
        # Node shell (glowing outline if running)
        painter.setPen(QPen(color, 2 if state == ThreadState.RUNNING else 1))
        painter.setBrush(QBrush(QColor(self.theme["panel"] if self.theme else "#1e1e1e")))
        painter.drawEllipse(QRectF(x - 20, y - 20, 40, 40))
        
        # State pulse logic
        if state == ThreadState.RUNNING:
            pulse_rad = 20 + math.sin(time.time() * 10) * 4
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 100), 1))
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawEllipse(QRectF(x - pulse_rad, y - pulse_rad, pulse_rad * 2, pulse_rad * 2))
            
        # Draw central ID text
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(self.theme["text"] if self.theme else "#ffffff")))
        short_id = thread["id"].split("-")[-1]
        painter.drawText(QRectF(x - 20, y - 20, 40, 40), Qt.AlignmentFlag.AlignCenter, f"{letter}{short_id}")
        
        # Compact State Text Under Node
        painter.setFont(QFont("Arial", 7))
        painter.setPen(QPen(color))
        painter.drawText(QRectF(x - 40, y + 22, 80, 10), Qt.AlignmentFlag.AlignCenter, state)

    def draw_warning_banner(self, painter, msg):
        painter.setPen(QPen(QColor("#f57c00"), 1))
        painter.setBrush(QBrush(QColor(245, 124, 0, 30)))
        painter.drawRoundedRect(QRectF(self.width()/2 - 170, 15, 340, 24), 4.0, 4.0)
        
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#ffb300")))
        painter.drawText(QRectF(self.width()/2 - 170, 15, 340, 24), Qt.AlignmentFlag.AlignCenter, msg)

    def draw_critical_banner(self, painter, msg):
        painter.setPen(QPen(QColor("#ff3333"), 1))
        painter.setBrush(QBrush(QColor(255, 51, 51, 35)))
        painter.drawRoundedRect(QRectF(self.width()/2 - 220, self.height() - 40, 440, 26), 4.0, 4.0)
        
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#ff3333")))
        painter.drawText(QRectF(self.width()/2 - 220, self.height() - 40, 440, 26), Qt.AlignmentFlag.AlignCenter, msg)

    def mousePressEvent(self, event):
        """Allows Thread Inspector triggering on node clicks"""
        click_pos = event.position()
        snap = self.tracker.get_snapshot()
        threads = snap["threads"]
        
        # Check producers
        producers = [t for t in threads.values() if t["type"] == "PRODUCER"]
        if producers:
            h_step = (self.height() - 40) / len(producers)
            for i, p in enumerate(producers):
                y_coord = 25 + i * h_step + h_step / 2
                dist = math.sqrt((click_pos.x() - 65)**2 + (click_pos.y() - y_coord)**2)
                if dist < 20:
                    self.show_inspector(p["id"])
                    return
                    
        # Check consumers
        consumers = [t for t in threads.values() if t["type"] == "CONSUMER"]
        if consumers:
            h_step = (self.height() - 40) / len(consumers)
            for i, c in enumerate(consumers):
                y_coord = 25 + i * h_step + h_step / 2
                dist = math.sqrt((click_pos.x() - (self.width() - 65))**2 + (click_pos.y() - y_coord)**2)
                if dist < 20:
                    self.show_inspector(c["id"])
                    return

    def show_inspector(self, thread_name):
        from ui.inspector_dialog import InspectorDialog
        dialog = InspectorDialog(thread_name, self.tracker, self)
        dialog.exec()
