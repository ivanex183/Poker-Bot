"""
Poker Bot GUI - Live monitor preview with auto-play mode
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import sys
import os
import queue
import mss

# Try to import PIL/Pillow with fallback
try:
    from PIL import Image, ImageTk
except ImportError:
    try:
        import Image
        import ImageTk
    except ImportError:
        print("Error: Pillow is not installed. Run: pip install pillow")
        sys.exit(1)

# Add Back_end folder to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Back_end'))

from auto_analyzer import AutomaticPokerAnalyzer
from screenshot_analyzer import PokerTableAnalyzer

class PokerBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎰 POKER BOT - Real-Time Analyzer")
        
        # Get available monitors
        with mss.mss() as sct:
            self.monitors = sct.monitors[1:]  # Exclude the "all monitors" entry
        
        # Set default GUI position (secondary monitor if available)
        if len(self.monitors) > 1:
            # Place GUI on second monitor
            monitor = self.monitors[1]
            self.root.geometry(f"700x800+{monitor['left']}+{monitor['top']}")
        else:
            self.root.geometry("1400x900")
        
        self.root.resizable(True, True)
        
        # State variables
        self.is_running = False
        self.auto_mode = False
        self.analysis_queue = queue.Queue()
        self.current_screenshot = None
        self.selected_monitor = 0 if len(self.monitors) == 1 else 1  # Default to second if available
        
        # Analyzers
        self.analyzer = PokerTableAnalyzer()
        self.auto_analyzer = AutomaticPokerAnalyzer()
        
        # Analysis history
        self.analysis_history = []
        self.debug_text = None  # Will be created in UI
        
        self._create_ui()
        self._update_screenshot()
    
    def _create_ui(self):
        """Create the user interface"""
        # Top control panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Monitor selection
        ttk.Label(control_frame, text="📺 Screen:").pack(side=tk.LEFT, padx=5)
        self.monitor_var = tk.StringVar(value="0")  # Store as STRING "0", "1", etc
        monitor_combo = ttk.Combobox(
            control_frame,
            textvariable=self.monitor_var,
            values=[str(i) for i in range(len(self.monitors))],  # Values: "0", "1", "2"
            state="readonly",
            width=12
        )
        monitor_combo.pack(side=tk.LEFT, padx=5)
        monitor_combo.bind("<<ComboboxSelected>>", self._on_monitor_changed)
        # HACK: Show readable labels in combobox
        monitor_combo.current(0)
        
        # Start/Stop button
        self.start_button = ttk.Button(
            control_frame, 
            text="▶ START", 
            command=self.toggle_analysis,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Auto-mode checkbox
        self.auto_mode_var = tk.BooleanVar()
        self.auto_checkbox = ttk.Checkbutton(
            control_frame,
            text="🤖 AUTO-MODE (hands off)",
            variable=self.auto_mode_var,
            command=self.toggle_auto_mode
        )
        self.auto_checkbox.pack(side=tk.LEFT, padx=10)
        
        # Status label
        self.status_label = ttk.Label(
            control_frame,
            text="⚫ READY",
            font=("Arial", 12, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Analysis interval slider
        ttk.Label(control_frame, text="Interval (sec):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.IntVar(value=3)
        interval_slider = ttk.Scale(
            control_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.interval_var,
            length=150
        )
        interval_slider.pack(side=tk.LEFT, padx=5)
        
        # Main content frame
        content_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side: Screenshot preview
        left_frame = ttk.Frame(content_frame)
        content_frame.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="📺 Monitor Preview", font=("Arial", 11, "bold")).pack()
        
        self.screenshot_label = ttk.Label(left_frame, background="black")
        self.screenshot_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side: Analysis results
        right_frame = ttk.Frame(content_frame)
        content_frame.add(right_frame, weight=1)
        
        # Tabs for different views
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Current Analysis
        current_tab = ttk.Frame(self.notebook)
        self.notebook.add(current_tab, text="📊 Current Analysis")
        
        ttk.Label(current_tab, text="Latest Hand:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        self.current_analysis = scrolledtext.ScrolledText(
            current_tab, 
            height=15, 
            width=40,
            font=("Courier", 9),
            bg="#f0f0f0"
        )
        self.current_analysis.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 2: History
        history_tab = ttk.Frame(self.notebook)
        self.notebook.add(history_tab, text="📜 History")
        
        self.history_text = scrolledtext.ScrolledText(
            history_tab,
            height=20,
            width=40,
            font=("Courier", 8),
            bg="#f9f9f9"
        )
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 3: Debug Info
        debug_tab = ttk.Frame(self.notebook)
        self.notebook.add(debug_tab, text="🔍 Debug")
        
        self.debug_text = scrolledtext.ScrolledText(
            debug_tab,
            height=20,
            width=40,
            font=("Courier", 7),
            bg="#fff8dc"
        )
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready to analyze | Waiting for input",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Bottom action buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="🔄 Reset History", command=self.reset_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Export Data", command=self.export_data).pack(side=tk.LEFT, padx=5)
    
    def toggle_analysis(self):
        """Start/Stop analysis"""
        self.is_running = not self.is_running
        
        if self.is_running:
            self.start_button.config(text="⏹ STOP")
            self.status_label.config(text="🔴 RUNNING", foreground="red")
            self.status_bar.config(text="Analysis running...")
            
            # Clear debug tab
            self.debug_text.delete('1.0', tk.END)
            
            # Start analysis thread
            thread = threading.Thread(target=self._analysis_thread, daemon=True)
            thread.start()
        else:
            self.start_button.config(text="▶ START")
            self.status_label.config(text="⚫ STOPPED", foreground="black")
            self.status_bar.config(text="Analysis stopped")
    
    def toggle_auto_mode(self):
        """Toggle auto-play mode"""
        self.auto_mode = self.auto_mode_var.get()
        if self.auto_mode:
            self.status_bar.config(text="🤖 AUTO-MODE: Hands off! Bot will auto-execute recommendations")
        else:
            self.status_bar.config(text="Manual mode: Review each recommendation")
    
    def _on_monitor_changed(self, event=None):
        """Handle monitor selection change"""
        self.selected_monitor = self.monitor_var.get()
        monitor = self.monitors[self.selected_monitor]
        self.status_bar.config(text=f"📺 Switched to Monitor {self.selected_monitor + 1}")
    
    def _write_debug(self, msg):
        """Write to debug tab (thread-safe)"""
        self.root.after(0, lambda: self.debug_text.insert(tk.END, msg + "\n"))
        self.root.after(0, lambda: self.debug_text.see(tk.END))
        print(msg)
    
    def _analysis_thread(self):
        """Background analysis thread"""
        last_hand_id = None
        self._write_debug("[✓] Analysis thread STARTED")
        
        while self.is_running:
            try:
                # Get selected monitor
                monitor_idx = int(self.monitor_var.get())
                self._write_debug(f"[→] Checking Monitor {monitor_idx}...")
                
                # Capture screenshot from selected monitor
                try:
                    with mss.mss() as sct:
                        # +1 because monitors[0] is "all monitors"
                        if monitor_idx + 1 >= len(sct.monitors):
                            self._write_debug(f"[✗] Monitor {monitor_idx} not found! Available: {len(sct.monitors)-1}")
                            time.sleep(1)
                            continue
                        
                        monitor = sct.monitors[monitor_idx + 1]
                        screenshot_mss = sct.grab(monitor)
                except Exception as e:
                    self._write_debug(f"[✗] Screenshot error: {e}")
                    time.sleep(1)
                    continue
                
                # Convert to PIL Image
                screenshot = Image.frombytes('RGB', screenshot_mss.size, screenshot_mss.rgb)
                
                # Store for display (FIRST!)
                self.current_screenshot = screenshot
                self._write_debug(f"[✓] Screenshot: {screenshot.size}")
                
                # Try YOLO detection first (for card graphics)
                self._write_debug(f"[→] Attempting YOLO card detection...")
                yolo_result = self.auto_analyzer.extract_poker_info_from_image(screenshot)
                
                if yolo_result and yolo_result['detected_cards']:
                    # YOLO found cards
                    extracted = yolo_result
                    self._write_debug(f"[✓] YOLO detected: {extracted['detected_cards']}")
                else:
                    # Fallback to OCR text analysis
                    self._write_debug(f"[→] YOLO failed, trying OCR fallback...")
                    vision_data = self.analyzer.analyze_table_image(screenshot)
                    ocr_text = vision_data['text'][:100] if vision_data['text'] else "(empty)"
                    self._write_debug(f"[✓] OCR text: {ocr_text}...")
                    
                    extracted = self.auto_analyzer.extract_poker_info_from_text(vision_data['text'])
                    self._write_debug(f"[✓] OCR detected: {extracted['detected_cards']}")
                
                if extracted['detected_cards'] and len(extracted['detected_cards']) >= 2:
                    self._write_debug(f"[→] Analyzing game state...")
                    game_state = self.auto_analyzer.smart_infer_poker_data(extracted)
                    self._write_debug(f"[✓] Hand: {game_state['hole_cards']} | Pot: {game_state['pot_size']} | Stack: {game_state['stack']}")
                    
                    # Check if new hand
                    hand_id = str(game_state['hole_cards'])
                    if hand_id == last_hand_id:
                        self._write_debug(f"[⊙] Same hand - skipping")
                        time.sleep(self.interval_var.get())
                        continue
                    
                    last_hand_id = hand_id
                    
                    # Add to history
                    analysis_result = {
                        'timestamp': time.strftime("%H:%M:%S"),
                        'hole_cards': str(game_state['hole_cards']),
                        'community': str(game_state['community']),
                        'pot': game_state['pot_size'],
                        'call': game_state['call_amount'],
                        'stack': game_state['stack']
                    }
                    
                    self.analysis_history.append(analysis_result)
                    self._write_debug(f"[✓] Results updated")
                    
                    # Update UI (thread-safe)
                    self.root.after(0, self._update_display, analysis_result)
                    
                    if self.auto_mode:
                        self.root.after(0, self._auto_execute, game_state)
                else:
                    self._write_debug(f"[✗] Not enough cards detected")
                
                # Wait for interval
                time.sleep(self.interval_var.get())
                
            except Exception as e:
                self._write_debug(f"[✗] ERROR: {e}")
                import traceback
                self._write_debug(traceback.format_exc())
                time.sleep(1)
    
    def _update_screenshot(self):
        """Update screenshot preview every 100ms"""
        if self.current_screenshot:
            try:
                # Resize for preview
                img = self.current_screenshot.copy()
                # Use LANCZOS if available (Pillow 10+), else ANTIALIAS
                resample_filter = getattr(Image, 'LANCZOS', Image.ANTIALIAS)
                img.thumbnail((600, 450), resample_filter)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)
                self.screenshot_label.config(image=photo)
                self.screenshot_label.image = photo
            except Exception as e:
                # Show error temporarily
                pass
        else:
            # Show placeholder if no screenshot yet
            try:
                placeholder = Image.new('RGB', (600, 450), color='gray20')
                photo = ImageTk.PhotoImage(placeholder)
                self.screenshot_label.config(image=photo)
                self.screenshot_label.image = photo
            except:
                pass
        
        self.root.after(100, self._update_screenshot)
    
    def _update_display(self, analysis):
        """Update the display with new analysis"""
        text = f"""
╔═══════════════════════════════╗
║     POKER HAND ANALYSIS       ║
╚═══════════════════════════════╝

Time        : {analysis['timestamp']}
Hole Cards  : {analysis['hole_cards']}
Community   : {analysis['community']}
Pot Size    : {analysis['pot']} chips
Call Amount : {analysis['call']} chips
Stack Size  : {analysis['stack']} chips

Status: ✅ Analysis Complete
"""
        self.current_analysis.delete('1.0', tk.END)
        self.current_analysis.insert('1.0', text)
        
        # Add to history
        history_entry = f"[{analysis['timestamp']}] {analysis['hole_cards']} vs Pot: {analysis['pot']}\n"
        self.history_text.insert(tk.END, history_entry)
        self.history_text.see(tk.END)
        
        # Add debug info if available
        if self.debug_text:
            debug_info = f"Detected: {analysis['hole_cards']} | Community: {analysis['community']}\n"
            self.debug_text.insert(tk.END, debug_info)
            self.debug_text.see(tk.END)
    
    def _auto_execute(self, game_state):
        """Auto-execute recommendation (for future mouse automation)"""
        msg = f"🤖 AUTO-EXECUTING: {game_state['hole_cards']}"
        self.status_bar.config(text=msg, foreground="green")
        print(f"[AUTO-MODE] {msg}")
        
        # Future: Add pyautogui for mouse clicks
        # For now, just show the action
        import tkinter.messagebox as mb
        recommendation = f"""
        AUTO-MODE RECOMMENDATION
        
        Hand: {game_state['hole_cards']}
        Community: {game_state['community']}
        
        Stack: {game_state['stack']} chips
        Pot: {game_state['pot_size']} chips
        
        ✅ READY TO EXECUTE
        """
        # Uncomment if you want visual popup
        # mb.showinfo("Auto-Mode", recommendation)
    
    def reset_history(self):
        """Clear analysis history"""
        self.analysis_history = []
        self.history_text.delete('1.0', tk.END)
        self.status_bar.config(text="History cleared")
    
    def export_data(self):
        """Export analysis history to file"""
        filename = f"poker_analysis_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w') as f:
                for entry in self.analysis_history:
                    f.write(str(entry) + '\n')
            self.status_bar.config(text=f"✅ Data exported to {filename}")
        except Exception as e:
            self.status_bar.config(text=f"❌ Export failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    
    # Get available monitors to position GUI on secondary monitor
    with mss.mss() as sct:
        monitors = sct.monitors[1:]  # Exclude "all monitors"
    
    # Create GUI
    gui = PokerBotGUI(root)
    
    # Position window on secondary monitor if available
    if len(monitors) > 1:
        monitor = monitors[1]
        root.geometry(f"700x850+{monitor['left']}+{monitor['top']}")
        print(f"🖥️  GUI positioned on Monitor 2")
    else:
        print(f"⚠️  Only 1 monitor detected. GUI will open on primary monitor")
    
    root.mainloop()
