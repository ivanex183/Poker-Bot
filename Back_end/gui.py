"""
Poker Bot GUI - Live monitor preview with auto-play mode
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from PIL import Image, ImageTk
import io
from auto_analyzer import AutomaticPokerAnalyzer
from screenshot_analyzer import PokerTableAnalyzer
import queue

class PokerBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎰 POKER BOT - Real-Time Analyzer")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        
        # State variables
        self.is_running = False
        self.auto_mode = False
        self.analysis_queue = queue.Queue()
        
        # Analyzers
        self.analyzer = PokerTableAnalyzer()
        self.auto_analyzer = AutomaticPokerAnalyzer()
        
        # Analysis history
        self.analysis_history = []
        
        self._create_ui()
        self._update_screenshot()
    
    def _create_ui(self):
        """Create the user interface"""
        # Top control panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
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
        
        # Tab 3: Settings
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="⚙ Settings")
        
        settings_frame = ttk.LabelFrame(settings_tab, text="Analysis Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(settings_frame, text="Opponents (default):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.opponents_var = tk.IntVar(value=5)
        ttk.Spinbox(settings_frame, from_=1, to=8, textvariable=self.opponents_var, width=5).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(settings_frame, text="Default stack size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.stack_var = tk.StringVar(value="1000")
        ttk.Entry(settings_frame, textvariable=self.stack_var, width=10).grid(row=1, column=1, sticky=tk.W)
        
        # Action buttons in settings
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="🔄 Reset History", command=self.reset_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Export Data", command=self.export_data).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready to analyze | Waiting for input",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
    
    def toggle_analysis(self):
        """Start/Stop analysis"""
        self.is_running = not self.is_running
        
        if self.is_running:
            self.start_button.config(text="⏹ STOP")
            self.status_label.config(text="🔴 RUNNING", foreground="red")
            self.status_bar.config(text="Analysis running...")
            
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
    
    def _analysis_thread(self):
        """Background analysis thread"""
        while self.is_running:
            try:
                # Capture screenshot
                screenshot = self.analyzer.capture_screenshot()
                
                # Store for display
                self.current_screenshot = screenshot
                
                # Analyze
                vision_data = self.analyzer.analyze_table_image(screenshot)
                extracted = self.auto_analyzer.extract_poker_info_from_text(vision_data['text'])
                
                if extracted['detected_cards'] and len(extracted['detected_cards']) >= 2:
                    game_state = self.auto_analyzer.smart_infer_poker_data(extracted)
                    
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
                    
                    # Update UI (thread-safe)
                    self.root.after(0, self._update_display, analysis_result)
                    
                    if self.auto_mode:
                        self.root.after(0, self._auto_execute, game_state)
                
                # Wait for interval
                time.sleep(self.interval_var.get())
                
            except Exception as e:
                print(f"Analysis error: {e}")
                time.sleep(1)
    
    def _update_screenshot(self):
        """Update screenshot preview every 100ms"""
        if hasattr(self, 'current_screenshot'):
            try:
                # Resize for preview
                img = self.current_screenshot.copy()
                img.thumbnail((600, 450), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)
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
    
    def _auto_execute(self, game_state):
        """Auto-execute recommendation"""
        msg = f"🤖 AUTO-EXECUTING: {game_state['hole_cards']}"
        self.status_bar.config(text=msg)
        print(msg)
    
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
    gui = PokerBotGUI(root)
    root.mainloop()
