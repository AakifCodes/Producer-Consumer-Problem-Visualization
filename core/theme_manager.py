class ThemeManager:
    THEMES = {
        "Dark Mode": {
            "name": "Dark Mode",
            "bg": "#121212",
            "panel": "#1e1e1e",
            "text": "#e0e0e0",
            "muted": "#888888",
            "border": "#2d2d2d",
            "accent": "#00ff88",
            "accent_bg": "#123020",
            "producer_color": "#00ff88",
            "consumer_color": "#29b6f6",
            "qss": """
                QMainWindow { background-color: #121212; }
                QWidget { color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; }
                QFrame#card { background-color: #1e1e1e; border: 1px solid #2d2d2d; border-radius: 8px; }
                QLabel#title { font-weight: bold; font-size: 14px; color: #00ff88; }
                QLabel#value { font-weight: bold; font-size: 22px; color: #ffffff; }
                QGroupBox { border: 1px solid #2d2d2d; border-radius: 8px; margin-top: 12px; font-weight: bold; color: #00ff88; padding: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
                QPushButton { background-color: #2b2b2b; border: 1px solid #3d3d3d; border-radius: 4px; padding: 6px 12px; font-weight: bold; min-width: 60px; }
                QPushButton:hover { background-color: #3d3d3d; border-color: #00ff88; }
                QPushButton:pressed { background-color: #123020; border-color: #00ff88; color: #00ff88; }
                QPushButton#action_btn { background-color: #0e3a24; border-color: #00ff88; color: #00ff88; }
                QPushButton#action_btn:hover { background-color: #00ff88; color: #121212; }
                QPushButton#stop_btn { background-color: #3a0e0e; border-color: #ff3333; color: #ff3333; }
                QPushButton#stop_btn:hover { background-color: #ff3333; color: #121212; }
                QSpinBox, QDoubleSpinBox, QComboBox { background-color: #252525; border: 1px solid #3d3d3d; border-radius: 4px; padding: 4px; color: #ffffff; }
                QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #00ff88; }
                QComboBox::drop-down { border: none; }
                QTableWidget { background-color: #1e1e1e; border: 1px solid #2d2d2d; border-radius: 6px; gridline-color: #2d2d2d; }
                QHeaderView::section { background-color: #252525; border: none; border-bottom: 1px solid #2d2d2d; color: #888888; font-weight: bold; padding: 6px; }
                QScrollBar:vertical { background: #121212; width: 8px; margin: 0px; }
                QScrollBar::handle:vertical { background: #3d3d3d; border-radius: 4px; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #00ff88; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """
        },
        "Light Mode": {
            "name": "Light Mode",
            "bg": "#f5f6fa",
            "panel": "#ffffff",
            "text": "#2f3640",
            "muted": "#718093",
            "border": "#dcdde1",
            "accent": "#0097e6",
            "accent_bg": "#e6f2ff",
            "producer_color": "#44bd32",
            "consumer_color": "#0097e6",
            "qss": """
                QMainWindow { background-color: #f5f6fa; }
                QWidget { color: #2f3640; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; }
                QFrame#card { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 8px; }
                QLabel#title { font-weight: bold; font-size: 14px; color: #0097e6; }
                QLabel#value { font-weight: bold; font-size: 22px; color: #2f3640; }
                QGroupBox { border: 1px solid #dcdde1; border-radius: 8px; margin-top: 12px; font-weight: bold; color: #0097e6; padding: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
                QPushButton { background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 4px; padding: 6px 12px; font-weight: bold; min-width: 60px; }
                QPushButton:hover { background-color: #f0f0f0; border-color: #0097e6; }
                QPushButton:pressed { background-color: #e6f2ff; border-color: #0097e6; color: #0097e6; }
                QPushButton#action_btn { background-color: #e6f2ff; border-color: #0097e6; color: #0097e6; }
                QPushButton#action_btn:hover { background-color: #0097e6; color: #ffffff; }
                QPushButton#stop_btn { background-color: #ffe6e6; border-color: #ff3333; color: #ff3333; }
                QPushButton#stop_btn:hover { background-color: #ff3333; color: #ffffff; }
                QSpinBox, QDoubleSpinBox, QComboBox { background-color: #ffffff; border: 1px solid #ccc; border-radius: 4px; padding: 4px; color: #2f3640; }
                QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #0097e6; }
                QComboBox::drop-down { border: none; }
                QTableWidget { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; gridline-color: #f5f6fa; }
                QHeaderView::section { background-color: #f5f6fa; border: none; border-bottom: 1px solid #dcdde1; color: #718093; font-weight: bold; padding: 6px; }
                QScrollBar:vertical { background: #f5f6fa; width: 8px; margin: 0px; }
                QScrollBar::handle:vertical { background: #ccc; border-radius: 4px; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #0097e6; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """
        },
        "Cyber Theme": {
            "name": "Cyber Theme",
            "bg": "#06060c",
            "panel": "#0c0c16",
            "text": "#00f0ff",
            "muted": "#7a7a9a",
            "border": "#ec008c",
            "accent": "#00f0ff",
            "accent_bg": "#240038",
            "producer_color": "#00f0ff",
            "consumer_color": "#ec008c",
            "qss": """
                QMainWindow { background-color: #06060c; }
                QWidget { color: #00f0ff; font-family: 'Consolas', monospace; font-size: 12px; }
                QFrame#card { background-color: #0c0c16; border: 1px solid #ec008c; border-radius: 4px; }
                QLabel#title { font-weight: bold; font-size: 14px; color: #ec008c; text-transform: uppercase; }
                QLabel#value { font-weight: bold; font-size: 22px; color: #00f0ff; text-shadow: 0 0 5px #00f0ff; }
                QGroupBox { border: 1px solid #00f0ff; border-radius: 4px; margin-top: 12px; font-weight: bold; color: #ec008c; padding: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
                QPushButton { background-color: #101025; border: 1px solid #ec008c; border-radius: 2px; padding: 6px 12px; font-weight: bold; color: #ec008c; }
                QPushButton:hover { background-color: #ec008c; color: #06060c; }
                QPushButton:pressed { background-color: #00f0ff; color: #06060c; }
                QPushButton#action_btn { background-color: #0a2528; border-color: #00f0ff; color: #00f0ff; }
                QPushButton#action_btn:hover { background-color: #00f0ff; color: #06060c; }
                QPushButton#stop_btn { background-color: #280a0a; border-color: #ff007f; color: #ff007f; }
                QPushButton#stop_btn:hover { background-color: #ff007f; color: #06060c; }
                QSpinBox, QDoubleSpinBox, QComboBox { background-color: #0c0c16; border: 1px solid #00f0ff; border-radius: 2px; padding: 4px; color: #00f0ff; }
                QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #ec008c; }
                QComboBox::drop-down { border: none; }
                QTableWidget { background-color: #0c0c16; border: 1px solid #ec008c; border-radius: 2px; gridline-color: #240038; }
                QHeaderView::section { background-color: #101025; border: none; border-bottom: 1px solid #ec008c; color: #7a7a9a; font-weight: bold; padding: 6px; }
                QScrollBar:vertical { background: #06060c; width: 8px; margin: 0px; }
                QScrollBar::handle:vertical { background: #ec008c; border-radius: 0px; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #00f0ff; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """
        },
        "Factory Theme": {
            "name": "Factory Theme",
            "bg": "#1c1c1f",
            "panel": "#26262b",
            "text": "#d8d9da",
            "muted": "#7f8487",
            "border": "#f57c00",
            "accent": "#ffb300",
            "accent_bg": "#3e2723",
            "producer_color": "#ffb300",
            "consumer_color": "#ff5722",
            "qss": """
                QMainWindow { background-color: #1c1c1f; }
                QWidget { color: #d8d9da; font-family: 'Trebuchet MS', Arial, sans-serif; font-size: 12px; }
                QFrame#card { background-color: #26262b; border: 2px dashed #f57c00; border-radius: 4px; }
                QLabel#title { font-weight: bold; font-size: 14px; color: #ffb300; }
                QLabel#value { font-weight: bold; font-size: 22px; color: #ffffff; }
                QGroupBox { border: 2px solid #ffb300; border-radius: 4px; margin-top: 12px; font-weight: bold; color: #f57c00; padding: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
                QPushButton { background-color: #35353c; border: 1px solid #f57c00; border-radius: 4px; padding: 6px 12px; font-weight: bold; color: #ffb300; }
                QPushButton:hover { background-color: #ffb300; color: #1c1c1f; }
                QPushButton:pressed { background-color: #f57c00; color: #1c1c1f; }
                QPushButton#action_btn { background-color: #3e2723; border-color: #ffb300; color: #ffb300; }
                QPushButton#action_btn:hover { background-color: #ffb300; color: #1c1c1f; }
                QPushButton#stop_btn { background-color: #3a1c1c; border-color: #ff5722; color: #ff5722; }
                QPushButton#stop_btn:hover { background-color: #ff5722; color: #1c1c1f; }
                QSpinBox, QDoubleSpinBox, QComboBox { background-color: #1c1c1f; border: 1px solid #f57c00; border-radius: 4px; padding: 4px; color: #ffffff; }
                QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #ffb300; }
                QComboBox::drop-down { border: none; }
                QTableWidget { background-color: #26262b; border: 1px solid #f57c00; border-radius: 4px; gridline-color: #f57c00; }
                QHeaderView::section { background-color: #35353c; border: none; border-bottom: 2px solid #ffb300; color: #7f8487; font-weight: bold; padding: 6px; }
                QScrollBar:vertical { background: #1c1c1f; width: 8px; margin: 0px; }
                QScrollBar::handle:vertical { background: #f57c00; border-radius: 4px; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #ffb300; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """
        },
        "Professional Theme": {
            "name": "Professional Theme",
            "bg": "#0f172a",
            "panel": "#1e293b",
            "text": "#f1f5f9",
            "muted": "#64748b",
            "border": "#334155",
            "accent": "#3b82f6",
            "accent_bg": "#1d4ed8",
            "producer_color": "#10b981",
            "consumer_color": "#3b82f6",
            "qss": """
                QMainWindow { background-color: #0f172a; }
                QWidget { color: #f1f5f9; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; }
                QFrame#card { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
                QLabel#title { font-weight: bold; font-size: 13px; color: #3b82f6; }
                QLabel#value { font-weight: bold; font-size: 22px; color: #ffffff; }
                QGroupBox { border: 1px solid #334155; border-radius: 8px; margin-top: 12px; font-weight: bold; color: #3b82f6; padding: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
                QPushButton { background-color: #1e293b; border: 1px solid #475569; border-radius: 6px; padding: 7px 14px; font-weight: bold; }
                QPushButton:hover { background-color: #334155; border-color: #3b82f6; }
                QPushButton:pressed { background-color: #1e3a8a; border-color: #3b82f6; color: #ffffff; }
                QPushButton#action_btn { background-color: #1e3a8a; border-color: #3b82f6; color: #93c5fd; }
                QPushButton#action_btn:hover { background-color: #2563eb; color: #ffffff; }
                QPushButton#stop_btn { background-color: #7f1d1d; border-color: #ef4444; color: #fca5a5; }
                QPushButton#stop_btn:hover { background-color: #b91c1c; color: #ffffff; }
                QSpinBox, QDoubleSpinBox, QComboBox { background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 4px; color: #f1f5f9; }
                QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #3b82f6; }
                QComboBox::drop-down { border: none; }
                QTableWidget { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; gridline-color: #334155; }
                QHeaderView::section { background-color: #0f172a; border: none; border-bottom: 1px solid #334155; color: #64748b; font-weight: bold; padding: 6px; }
                QScrollBar:vertical { background: #0f172a; width: 8px; margin: 0px; }
                QScrollBar::handle:vertical { background: #334155; border-radius: 4px; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #3b82f6; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """
        }
    }

    @classmethod
    def get_theme(cls, name):
        return cls.THEMES.get(name, cls.THEMES["Dark Mode"])
