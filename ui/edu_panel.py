from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTabWidget, QTextBrowser
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class EducationalPanel(QWidget):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.theme = None
        self._init_ui()

    def _init_ui(self):
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 1. Left Card: Live Synchronization Monitor Explainer
        self.live_card = QFrame(self)
        self.live_card.setObjectName("card")
        live_layout = QVBoxLayout(self.live_card)
        live_layout.setContentsMargins(15, 15, 15, 15)
        
        live_title = QLabel("LIVE SYNC EXPLAINER", self.live_card)
        live_title.setObjectName("title")
        live_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        live_layout.addWidget(live_title)
        
        self.live_msg = QLabel("Initializing engine... Ready.", self.live_card)
        self.live_msg.setFont(QFont("Consolas", 11))
        self.live_msg.setWordWrap(True)
        self.live_msg.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.live_msg.setStyleSheet("color: #00ff88; line-height: 1.5;")
        live_layout.addWidget(self.live_msg)
        
        live_hint = QLabel("💡 Watch this panel update as producers and consumers request locks and semaphores.", self.live_card)
        live_hint.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        live_hint.setStyleSheet("color: #888888;")
        live_layout.addWidget(live_hint)
        
        layout.addWidget(self.live_card, stretch=2)
        
        # 2. Right Card: Bounded Buffer Reference Textbook
        self.ref_card = QFrame(self)
        self.ref_card.setObjectName("card")
        ref_layout = QVBoxLayout(self.ref_card)
        ref_layout.setContentsMargins(15, 15, 15, 15)
        
        ref_title = QLabel("OPERATING SYSTEM REFERENCE TEXTBOOK", self.ref_card)
        ref_title.setObjectName("title")
        ref_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        ref_layout.addWidget(ref_title)
        
        # Tabbed browser for different operating system synchronization topics
        self.tabs = QTabWidget(self.ref_card)
        
        self.add_textbook_tab("Bounded Buffer", self.get_bounded_buffer_text())
        self.add_textbook_tab("Semaphores", self.get_semaphore_text())
        self.add_textbook_tab("Mutex Locks", self.get_mutex_text())
        self.add_textbook_tab("Deadlock/Starvation", self.get_deadlock_text())
        
        ref_layout.addWidget(self.tabs)
        layout.addWidget(self.ref_card, stretch=3)

    def add_textbook_tab(self, title, html_content):
        browser = QTextBrowser(self)
        browser.setHtml(html_content)
        browser.setStyleSheet("background-color: transparent; border: none; font-size: 11px;")
        self.tabs.addTab(browser, title)

    def set_theme(self, theme_data):
        self.theme = theme_data
        accent = theme_data.get("accent", "#00ff88")
        self.live_msg.setStyleSheet(f"color: {accent}; line-height: 1.5;")
        
        # Update textbook style based on theme
        txt_color = theme_data.get("text", "#e0e0e0")
        accent_color = theme_data.get("accent", "#00ff88")
        qss = f"""
            QTabWidget::pane {{ border: 1px solid {theme_data["border"]}; border-radius: 4px; background: transparent; }}
            QTabBar::tab {{ background: {theme_data["bg"]}; color: {theme_data["muted"]}; border: 1px solid {theme_data["border"]}; padding: 6px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; }}
            QTabBar::tab:selected {{ background: {theme_data["panel"]}; color: {accent_color}; border-bottom-color: {theme_data["panel"]}; font-weight: bold; }}
            QTextBrowser {{ color: {txt_color}; }}
        """
        self.tabs.setStyleSheet(qss)

    def update_live_explanation(self):
        snap = self.tracker.get_snapshot()
        self.live_msg.setText(snap["edu_message"])

    def get_bounded_buffer_text(self):
        return """
        <h3>The Bounded-Buffer Problem</h3>
        <p>The Bounded-Buffer problem (also called the <b>Producer-Consumer Problem</b>) is a classic multi-process synchronization problem.</p>
        <p><b>Objective:</b> Multiple threads share a common, fixed-size buffer. 
        <ul>
            <li><b>Producers</b> generate items and write them into the buffer.</li>
            <li><b>Consumers</b> retrieve items and read them from the buffer.</li>
        </ul>
        </p>
        <p><b>Constraint Challenges:</b>
        <ol>
            <li><b>Overflow Prevention:</b> Producers must block when trying to add items if the buffer is <b>FULL</b>.</li>
            <li><b>Underflow Prevention:</b> Consumers must block when trying to retrieve items if the buffer is <b>EMPTY</b>.</li>
            <li><b>Mutual Exclusion:</b> Only one thread can modify buffer indices at a time, preventing data corruption.</li>
        </ol>
        </p>
        """

    def get_semaphore_text(self):
        return """
        <h3>Counting and Binary Semaphores</h3>
        <p>A semaphore is an integer variable accessed via two standard atomic operations: <code>wait()</code> (or <code>acquire</code>) and <code>signal()</code> (or <code>release</code>).</p>
        <p>In this simulation, we employ two Semaphores:
        <ul>
            <li><b>Empty Semaphore:</b> Initialized to <b>Buffer Capacity</b>. Tracks the count of available spaces. Producers call <code>acquire()</code> to decrement this count. If 0, producers block.</li>
            <li><b>Full Semaphore:</b> Initialized to <b>0</b>. Tracks the count of occupied items in the buffer. Consumers call <code>acquire()</code> to read. If 0, consumers block.</li>
        </ul>
        </p>
        <p>When a producer finishes putting an item, it signals <code>full.release()</code>. When a consumer extracts an item, it signals <code>empty.release()</code>.</p>
        """

    def get_mutex_text(self):
        return """
        <h3>Mutual Exclusion (Mutex)</h3>
        <p>A <b>Mutex Lock</b> (Mutual Exclusion Lock) is a binary flag (either 0 or 1) used to guard a critical section of code.</p>
        <p><b>Why Mutex?</b> While semaphores manage counts, they do not prevent multiple threads from modifying array indexes simultaneously. If two producers try to write into Slot 3 at the exact same millisecond, data corruption occurs.</p>
        <p><b>How it works:</b>
        <ol>
            <li>Before writing/reading, the thread calls <code>mutex.acquire()</code> (locking the critical section).</li>
            <li>If another thread tries to acquire the lock, the operating system blocks it.</li>
            <li>After modifications, the owner calls <code>mutex.release()</code> (unlocking the section), allowing one waiting thread to enter.</li>
        </ol>
        </p>
        """

    def get_deadlock_text(self):
        return """
        <h3>Deadlock and Starvation</h3>
        <p><b>Deadlock</b> describes a critical state where a set of threads are permanently blocked because each process is holding a resource and waiting for another resource held by someone else in the cycle.</p>
        <p><b>In Producer-Consumer:</b> If synchronization primitives are implemented in the wrong order, deadlocks occur:
        <pre>
        // DEADLOCK PRONE CODE
        producer() {
            mutex.acquire();       // Lock buffer
            empty_sem.acquire();  // If buffer full, block!
            ...
            mutex.release();
        }
        </pre>
        In this bug, the producer locks the mutex, but blocks on empty space. The consumer tries to consume, but blocks on the mutex, causing a permanent freeze!</p>
        <p><b>Starvation:</b> Occurs when a thread is indefinitely delayed because other threads are continuously favored by scheduling policies.</p>
        """
