import signal
import sys
import os

# Add core directory to sys.path to allow importing backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'core')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.main_window import MainWindow



def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    def shutdown():
        window.ui_timer.stop()
        window.replay_timer.stop()
        window.conveyor_widget.anim_timer.stop()
        window.controller.stop_sim()
        app.quit()

    # Ctrl+C in the terminal: shut down cleanly instead of mid-paint tracebacks
    signal.signal(signal.SIGINT, lambda *_: shutdown())

    # Lets Python handle SIGINT while Qt's event loop is running (Windows + Unix)
    sig_timer = QTimer()
    sig_timer.timeout.connect(lambda: None)
    sig_timer.start(200)

    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        shutdown()
        exit_code = 0

    sys.exit(exit_code)


if __name__ == "__main__":
    main()