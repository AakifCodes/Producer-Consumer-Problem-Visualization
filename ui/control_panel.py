from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QLabel, QSpinBox, QDoubleSpinBox, QComboBox, 
                             QPushButton, QCheckBox, QFileDialog, QSizePolicy,
                             QStylePainter, QStyleOptionButton, QStyle, QSlider)
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

class MarqueeButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._scroll_offset = 0
        self._original_text = text
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scroll)
        self.timer.start(50)  # Update every 50ms for smooth scrolling

    def setText(self, text):
        super().setText(text)
        self._original_text = text
        self._scroll_offset = 0
        self.update()

    def update_scroll(self):
        if not self.isVisible():
            return
        
        fm = self.fontMetrics()
        margin = 12
        available_width = self.width() - margin * 2
        text_width = fm.horizontalAdvance(self._original_text)
        
        if text_width > available_width:
            self._scroll_offset += 1
            spacing = 40
            if self._scroll_offset >= text_width + spacing:
                self._scroll_offset = 0
            self.update()
        else:
            if self._scroll_offset != 0:
                self._scroll_offset = 0
                self.update()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        
        # Draw background and border
        option.text = ""
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)
        
        fm = self.fontMetrics()
        margin = 8
        rect = self.rect().adjusted(margin, 0, -margin, 0)
        available_width = rect.width()
        text_width = fm.horizontalAdvance(self._original_text)
        
        painter.save()
        painter.setClipRect(rect)
        
        # Determine correct text color
        palette = self.palette()
        if not self.isEnabled():
            color = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText)
        else:
            color = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText)
        painter.setPen(color)
        
        painter.setFont(self.font())
        
        if text_width > available_width:
            x_pos = rect.left() - self._scroll_offset
            y_pos = rect.center().y() + fm.ascent() / 2 - 1
            painter.drawText(int(x_pos), int(y_pos), self._original_text)
            
            spacing = 40
            painter.drawText(int(x_pos + text_width + spacing), int(y_pos), self._original_text)
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._original_text)
            
        painter.restore()

class ControlPanel(QWidget):
    theme_changed = pyqtSignal(str)
    
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._init_ui()

    def _init_ui(self):
        # Master layout (horizontal split of GroupBoxes)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)
        
        # -------------------------------------------------------------
        # Group 1: Configuration Panel
        # -------------------------------------------------------------
        config_group = QGroupBox("Factory Setup Parameters", self)
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(4)
        
        # Spinbox Row 1: Threads
        thread_row = QHBoxLayout()
        thread_row.addWidget(QLabel("Producers:"))
        self.prod_spin = QSpinBox(config_group)
        self.prod_spin.setRange(1, 20)
        self.prod_spin.setValue(2)
        thread_row.addWidget(self.prod_spin)
        
        thread_row.addWidget(QLabel("Consumers:"))
        self.cons_spin = QSpinBox(config_group)
        self.cons_spin.setRange(1, 20)
        self.cons_spin.setValue(2)
        thread_row.addWidget(self.cons_spin)
        config_layout.addLayout(thread_row)
        
        # Spinbox Row 2: Capacity
        cap_row = QHBoxLayout()
        cap_row.addWidget(QLabel("Buffer Space:"))
        self.cap_spin = QSpinBox(config_group)
        self.cap_spin.setRange(1, 100)
        self.cap_spin.setValue(5)
        cap_row.addWidget(self.cap_spin)
        
        cap_row.addWidget(QLabel("Item Type:"))
        self.item_combo = QComboBox(config_group)
        self.item_combo.addItems(["Widget", "Gadget", "Engine", "Microchip"])
        cap_row.addWidget(self.item_combo)
        config_layout.addLayout(cap_row)
        
        # Spinbox Row 3: Rates
        rate_row = QHBoxLayout()
        rate_row.addWidget(QLabel("Prod Delay:"))
        self.prod_delay = QDoubleSpinBox(config_group)
        self.prod_delay.setRange(0.1, 10.0)
        self.prod_delay.setValue(1.0)
        self.prod_delay.setSingleStep(0.1)
        self.prod_delay.setSuffix("s")
        rate_row.addWidget(self.prod_delay)
        
        rate_row.addWidget(QLabel("Cons Delay:"))
        self.cons_delay = QDoubleSpinBox(config_group)
        self.cons_delay.setRange(0.1, 10.0)
        self.cons_delay.setValue(1.2)
        self.cons_delay.setSingleStep(0.1)
        self.cons_delay.setSuffix("s")
        rate_row.addWidget(self.cons_delay)
        config_layout.addLayout(rate_row)
        
        # Customizations: Theme & Speed slider
        custom_row = QHBoxLayout()
        custom_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox(config_group)
        self.theme_combo.addItems(["Dark Mode", "Light Mode", "Cyber Theme", "Factory Theme", "Professional Theme"])
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        custom_row.addWidget(self.theme_combo)
        
        # Continuous QSlider for simulation speed
        self.speed_label = QLabel("Speed: 1.0x", config_group)
        custom_row.addWidget(self.speed_label)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal, config_group)
        self.speed_slider.setRange(1, 100)  # Represents 0.1x to 10.0x
        self.speed_slider.setValue(10)      # Default to 1.0x
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.valueChanged.connect(self.update_simulation_speed_slider)
        custom_row.addWidget(self.speed_slider)
        
        config_layout.addLayout(custom_row)
        
        layout.addWidget(config_group)
        
        # -------------------------------------------------------------
        # Group 2: Core Simulation Buttons
        # -------------------------------------------------------------
        controls_group = QGroupBox("Core Simulation Commands", self)
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(6)
        
        btn_row1 = QHBoxLayout()
        self.start_btn = MarqueeButton("Start Simulation", controls_group)
        self.start_btn.setObjectName("action_btn")
        self.start_btn.clicked.connect(self.start_simulation)
        btn_row1.addWidget(self.start_btn)
        
        self.pause_btn = MarqueeButton("Pause", controls_group)
        self.pause_btn.clicked.connect(self.pause_simulation)
        self.pause_btn.setEnabled(False)
        btn_row1.addWidget(self.pause_btn)
        
        self.resume_btn = MarqueeButton("Resume", controls_group)
        self.resume_btn.clicked.connect(self.resume_simulation)
        self.resume_btn.setEnabled(False)
        btn_row1.addWidget(self.resume_btn)
        controls_layout.addLayout(btn_row1)
        
        btn_row2 = QHBoxLayout()
        self.stop_btn = MarqueeButton("Stop", controls_group)
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.clicked.connect(self.stop_simulation)
        self.stop_btn.setEnabled(False)
        btn_row2.addWidget(self.stop_btn)
        
        self.reset_btn = MarqueeButton("Reset Engine", controls_group)
        self.reset_btn.clicked.connect(self.reset_simulation)
        btn_row2.addWidget(self.reset_btn)
        
        self.step_btn = MarqueeButton("Step Mode", controls_group)
        self.step_btn.clicked.connect(self.step_simulation)
        self.step_btn.setEnabled(False)
        btn_row2.addWidget(self.step_btn)
        controls_layout.addLayout(btn_row2)
        
        # dynamic addition/removal row
        btn_row3 = QHBoxLayout()
        self.add_p_btn = MarqueeButton("+ Producer", controls_group)
        self.add_p_btn.clicked.connect(self.controller.add_producer)
        self.add_p_btn.setEnabled(False)
        btn_row3.addWidget(self.add_p_btn)
        
        self.rem_p_btn = MarqueeButton("- Producer", controls_group)
        self.rem_p_btn.clicked.connect(self.controller.remove_producer)
        self.rem_p_btn.setEnabled(False)
        btn_row3.addWidget(self.rem_p_btn)
        
        self.add_c_btn = MarqueeButton("+ Consumer", controls_group)
        self.add_c_btn.clicked.connect(self.controller.add_consumer)
        self.add_c_btn.setEnabled(False)
        btn_row3.addWidget(self.add_c_btn)
        
        self.rem_c_btn = MarqueeButton("- Consumer", controls_group)
        self.rem_c_btn.clicked.connect(self.controller.remove_consumer)
        self.rem_c_btn.setEnabled(False)
        btn_row3.addWidget(self.rem_c_btn)
        controls_layout.addLayout(btn_row3)
        
        layout.addWidget(controls_group)
        
        # -------------------------------------------------------------
        # Group 3: Stress Testing Panel
        # -------------------------------------------------------------
        stress_group = QGroupBox("Runtime Stress & Diagnostic Tools", self)
        stress_layout = QVBoxLayout(stress_group)
        stress_layout.setSpacing(6)
        
        row1 = QHBoxLayout()
        self.force_full_btn = MarqueeButton("Force Full Buffer", stress_group)
        self.force_full_btn.clicked.connect(self.controller.force_buffer_full)
        self.force_full_btn.setEnabled(False)
        row1.addWidget(self.force_full_btn)
        
        self.force_empty_btn = MarqueeButton("Force Empty Buffer", stress_group)
        self.force_empty_btn.clicked.connect(self.controller.force_buffer_empty)
        self.force_empty_btn.setEnabled(False)
        row1.addWidget(self.force_empty_btn)
        stress_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        self.burst_btn = MarqueeButton("Burst Load Spike", stress_group)
        self.burst_btn.clicked.connect(self.controller.random_burst_load)
        self.burst_btn.setEnabled(False)
        row2.addWidget(self.burst_btn)
        
        self.fail_p_btn = MarqueeButton("Fail Producer", stress_group)
        self.fail_p_btn.clicked.connect(self.controller.random_producer_failure)
        self.fail_p_btn.setEnabled(False)
        row2.addWidget(self.fail_p_btn)
        
        self.fail_c_btn = MarqueeButton("Fail Consumer", stress_group)
        self.fail_c_btn.clicked.connect(self.controller.random_consumer_failure)
        self.fail_c_btn.setEnabled(False)
        row2.addWidget(self.fail_c_btn)
        stress_layout.addLayout(row2)
        
        # Reports / Sound Row
        row3 = QHBoxLayout()
        self.report_btn = MarqueeButton("Generate PDF Report", stress_group)
        self.report_btn.clicked.connect(self.generate_pdf_report)
        self.report_btn.setEnabled(False)
        row3.addWidget(self.report_btn)
        
        self.sound_check = QCheckBox("Sound Effects", stress_group)
        self.sound_check.setChecked(False)
        row3.addWidget(self.sound_check)
        stress_layout.addLayout(row3)
        
        layout.addWidget(stress_group)

    def set_theme(self, theme_data):
        self.theme = theme_data

    def start_simulation(self):
        p_cnt = self.prod_spin.value()
        c_cnt = self.cons_spin.value()
        cap = self.cap_spin.value()
        p_delay = self.prod_delay.value()
        c_delay = self.cons_delay.value()
        item_type = self.item_combo.currentText()
        theme = self.theme_combo.currentText()
        
        self.controller.start_sim(p_cnt, c_cnt, cap, p_delay, c_delay, item_type, theme)
        
        # Apply current slider speed
        speed_mult = self.speed_slider.value() / 10.0
        self.controller.set_speed_multiplier(speed_mult)
        
        # Toggle buttons
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.step_btn.setEnabled(True)
        
        # Enable runtime modifiers
        self.add_p_btn.setEnabled(True)
        self.rem_p_btn.setEnabled(True)
        self.add_c_btn.setEnabled(True)
        self.rem_c_btn.setEnabled(True)
        self.force_full_btn.setEnabled(True)
        self.force_empty_btn.setEnabled(True)
        self.burst_btn.setEnabled(True)
        self.fail_p_btn.setEnabled(True)
        self.fail_c_btn.setEnabled(True)
        self.report_btn.setEnabled(True)
        
        # Beep for starting
        self.trigger_sound("start")

    def pause_simulation(self):
        self.controller.pause_sim()
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)

    def resume_simulation(self):
        self.controller.resume_sim()
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)

    def stop_simulation(self):
        self.controller.stop_sim()
        
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        
        # Disable runtime items
        self.add_p_btn.setEnabled(False)
        self.rem_p_btn.setEnabled(False)
        self.add_c_btn.setEnabled(False)
        self.rem_c_btn.setEnabled(False)
        self.force_full_btn.setEnabled(False)
        self.force_empty_btn.setEnabled(False)
        self.burst_btn.setEnabled(False)
        self.fail_p_btn.setEnabled(False)
        self.fail_c_btn.setEnabled(False)
        
        self.trigger_sound("stop")

    def reset_simulation(self):
        self.controller.reset_sim()
        self.prod_spin.setValue(2)
        self.cons_spin.setValue(2)
        self.cap_spin.setValue(5)
        self.prod_delay.setValue(1.0)
        self.cons_delay.setValue(1.2)
        self.speed_slider.setValue(10)
        self.speed_label.setText("Speed: 1.0x")
        
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        self.report_btn.setEnabled(False)

    def step_simulation(self):
        self.controller.step_sim()
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)

    def update_simulation_speed_slider(self, value):
        mult = value / 10.0
        self.speed_label.setText(f"Speed: {mult:.1f}x")
        self.controller.set_speed_multiplier(mult)

    def generate_pdf_report(self):
        snap = self.controller.tracker.get_snapshot()
        path, _ = QFileDialog.getSaveFileName(self, "Export Performance Report PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
            
        # Optional: Save standard plot images to embed in PDF
        from pdf_generator import PDFGenerator
        
        # We will dynamically compile optimization recommendations
        advisor = self.parent().parent().parent().findChild(QWidget, "AIAdvisorWidget") if self.parent() else None
        recs = advisor.get_live_recommendations() if advisor and hasattr(advisor, "get_live_recommendations") else None
        
        PDFGenerator.generate_report(path, snap, recommendations=recs)

    def trigger_sound(self, sound_type):
        """Standard frequencies synthesized natively using PyQt's sound effects or system signals"""
        if not self.sound_check.isChecked():
            return
            
        import sys
        if sys.platform == "win32":
            import winsound
            if sound_type == "start":
                winsound.Beep(880, 150)
                winsound.Beep(1109, 150)
            elif sound_type == "stop":
                winsound.Beep(784, 150)
                winsound.Beep(659, 150)
            elif sound_type == "warn":
                winsound.Beep(440, 300)
