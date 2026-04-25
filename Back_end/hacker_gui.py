"""
Hacker-themed Poker Bot GUI - Matrix style with green aesthetic
Real-time card detection, analysis, and auto-play mode
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
from PIL import Image, ImageTk
import io
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from auto_analyzer import AutomaticPokerAnalyzer
    from screenshot_analyzer import PokerTableAnalyzer
    from poker_engine import analyze_situation
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Hacker Theme Colors
BG_DARK = "#0a0a0a"
BG_DARKER = "#050505"
FG_GREEN = "#00ff00"
FG_GREEN_DIM = "#00aa00"
FG_GREEN_BRIGHT = "#00ffff"
ACCENT_RED = "#ff0000"
BORDER_GREEN = "#00dd00"

class HackerPokerBot:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ POKER BOT - NEURAL INTERFACE ⚡")
        self.root.geometry("1600x1000")
        self.root.configure(bg=BG_DARK)
        
        # Disable resize for consistency
        self.root.resizable(True, True)
        
        # State
        self.is_running = False
        self.auto_mode = False
        self.analysis_thread = None
        self.last_analysis = None
        
        # Analyzers
        try:
            self.analyzer = PokerTableAnalyzer()
            self.auto_analyzer = AutomaticPokerAnalyzer()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize analyzers: {e}")
            return
        
        # Analysis history
        self.analysis_history = []
        
        self._create_hacker_ui()
        self._animate_title()
    
    def _create_hacker_ui(self):
        """Create hacker-themed interface"""
        
        # ===== HEADER =====
        header = tk.Frame(self.root, bg=BG_DARKER, height=80)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)
        
        # Animated title
        self.title_label = tk.Label(
            header,
            text="█ POKER BOT NEURAL INTERFACE █",
            font=("Courier New", 18, "bold"),
            fg=FG_GREEN_BRIGHT,
            bg=BG_DARKER,
            padx=20,
            pady=10
        )
        self.title_label.pack(side=tk.TOP)
        
        # Status line
        self.status_line = tk.Label(
            header,
            text="[SYSTEM] Ready for neural link...",
            font=("Courier New", 9),
            fg=FG_GREEN_DIM,
            bg=BG_DARKER
        )
        self.status_line.pack(side=tk.TOP)
        
        # ===== CONTROL PANEL =====
        control_panel = tk.Frame(self.root, bg=BG_DARK, relief=tk.SUNKEN, bd=2)
        control_panel.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Start button
        self.start_btn = tk.Button(
            control_panel,
            text="▶ INITIALIZE SCAN",
            font=("Courier New", 10, "bold"),
            fg=BG_DARK,
            bg=FG_GREEN,
            activebackground=FG_GREEN_BRIGHT,
            activeforeground=BG_DARK,
            command=self.toggle_analysis,
            padx=15,
            pady=8,
            relief=tk.RAISED,
            bd=2
        )
        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Auto mode toggle
        self.auto_btn = tk.Button(
            control_panel,
            text="🤖 AUTO-EXECUTE OFF",
            font=("Courier New", 10, "bold"),
            fg=FG_GREEN,
            bg=BG_DARK,
            activebackground=BG_DARKER,
            activeforeground=FG_GREEN_BRIGHT,
            command=self.toggle_auto_mode,
            padx=15,
            pady=8,
            relief=tk.SUNKEN,
            bd=2,
            highlightthickness=2,
            highlightbackground=FG_GREEN_DIM,
            highlightcolor=FG_GREEN_BRIGHT
        )
        self.auto_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Status indicator
        self.status_indicator = tk.Label(
            control_panel,
            text="⚫ OFFLINE",
            font=("Courier New", 11, "bold"),
            fg=FG_GREEN_DIM,
            bg=BG_DARK,
            padx=10
        )
        self.status_indicator.pack(side=tk.LEFT, padx=20)
        
        # Clear history button
        clear_btn = tk.Button(
            control_panel,
            text="[CLEAR LOGS]",
            font=("Courier New", 9),
            fg=FG_GREEN_DIM,
            bg=BG_DARK,
            activebackground=ACCENT_RED,
            activeforeground=FG_GREEN,
            command=self.clear_logs,
            relief=tk.SUNKEN,
            bd=1
        )
        clear_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # ===== MAIN CONTENT =====
        content = tk.Frame(self.root, bg=BG_DARK)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left pane: Monitor
        left_pane = tk.Frame(content, bg=BG_DARKER, relief=tk.SUNKEN, bd=2)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        left_header = tk.Label(
            left_pane,
            text="▌ MONITOR FEED",
            font=("Courier New", 10, "bold"),
            fg=FG_GREEN_BRIGHT,
            bg=BG_DARKER,
            anchor=tk.W,
            padx=5,
            pady=3
        )
        left_header.pack(side=tk.TOP, fill=tk.X)
        
        self.monitor_label = tk.Label(
            left_pane,
            bg=BG_DARK,
            fg=FG_GREEN,
            font=("Courier New", 8),
            justify=tk.LEFT,
            padx=10,
            pady=10
        )
        self.monitor_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Right pane: Analysis panels
        right_pane = tk.Frame(content, bg=BG_DARKER, relief=tk.SUNKEN, bd=2)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Analysis panel
        analysis_header = tk.Label(
            right_pane,
            text="▌ NEURAL ANALYSIS",
            font=("Courier New", 10, "bold"),
            fg=FG_GREEN_BRIGHT,
            bg=BG_DARKER,
            anchor=tk.W,
            padx=5,
            pady=3
        )
        analysis_header.pack(side=tk.TOP, fill=tk.X)
        
        self.analysis_text = scrolledtext.ScrolledText(
            right_pane,
            height=20,
            width=50,
            font=("Courier New", 8),
            bg=BG_DARK,
            fg=FG_GREEN,
            insertbackground=FG_GREEN_BRIGHT,
            selectbackground=FG_GREEN_DIM,
            selectforeground=BG_DARK,
            relief=tk.SUNKEN,
            bd=1,
            padx=5,
            pady=5
        )
        self.analysis_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=3, pady=3)
        self.analysis_text.config(state=tk.DISABLED)
        
        # Config tags for colored text
        self.analysis_text.tag_config("header", foreground=FG_GREEN_BRIGHT, font=("Courier New", 8, "bold"))
        self.analysis_text.tag_config("good", foreground=FG_GREEN)
        self.analysis_text.tag_config("warning", foreground="#ffaa00")
        self.analysis_text.tag_config("error", foreground=ACCENT_RED)
        self.analysis_text.tag_config("accent", foreground=FG_GREEN_BRIGHT)
        
        # ===== FOOTER =====
        footer = tk.Frame(self.root, bg=BG_DARKER, height=40)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        footer.pack_propagate(False)
        
        self.footer_label = tk.Label(
            footer,
            text="[READY]",
            font=("Courier New", 8),
            fg=FG_GREEN_DIM,
            bg=BG_DARKER,
            padx=10,
            pady=5
        )
        self.footer_label.pack(side=tk.LEFT)
        
        self.stats_label = tk.Label(
            footer,
            text="",
            font=("Courier New", 8),
            fg=FG_GREEN_DIM,
            bg=BG_DARKER,
            padx=10,
            pady=5
        )
        self.stats_label.pack(side=tk.RIGHT)
    
    def _animate_title(self):
        """Animate title with glitch effect"""
        if self.is_running:
            titles = [
                "█ POKER BOT NEURAL INTERFACE █",
                "▓ POKER BOT NEURAL INTERFACE ▓",
                "▒ POKER BOT NEURAL INTERFACE ▒",
            ]
            idx = int(time.time() * 2) % len(titles)
            self.title_label.config(text=titles[idx])
        
        self.root.after(500, self._animate_title)
    
    def log_analysis(self, text, tag="good"):
        """Log text to analysis panel"""
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.insert(tk.END, text + "\n", tag)
        self.analysis_text.see(tk.END)
        self.analysis_text.config(state=tk.DISABLED)
    
    def toggle_analysis(self):
        """Start/stop analysis"""
        if self.is_running:
            self.is_running = False
            self.start_btn.config(text="▶ INITIALIZE SCAN")
            self.status_indicator.config(text="⚫ OFFLINE", fg=FG_GREEN_DIM)
            self.status_line.config(text="[SYSTEM] Neural link terminated...")
            self.log_analysis("[*] SCAN TERMINATED BY USER", "warning")
        else:
            self.is_running = True
            self.start_btn.config(text="⏹ STOP SCAN")
            self.status_indicator.config(text="🟢 ONLINE", fg=FG_GREEN)
            self.status_line.config(text="[SYSTEM] Neural link established...")
            self.log_analysis("[+] NEURAL INTERFACE ACTIVATED", "accent")
            
            # Start analysis thread
            self.analysis_thread = threading.Thread(target=self._run_analysis, daemon=True)
            self.analysis_thread.start()
    
    def toggle_auto_mode(self):
        """Toggle auto-play mode"""
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.auto_btn.config(
                text="🤖 AUTO-EXECUTE ON",
                fg=FG_GREEN_BRIGHT,
                bg=BG_DARKER,
                activebackground=ACCENT_RED
            )
            self.log_analysis("[*] AUTO-EXECUTE MODE ENABLED - NEURAL AUTOPILOT ACTIVE", "accent")
        else:
            self.auto_btn.config(
                text="🤖 AUTO-EXECUTE OFF",
                fg=FG_GREEN,
                bg=BG_DARK
            )
            self.log_analysis("[*] AUTO-EXECUTE MODE DISABLED", "warning")
    
    def _run_analysis(self):
        """Run continuous analysis"""
        scan_count = 0
        while self.is_running:
            try:
                scan_count += 1
                self.status_line.config(
                    text=f"[SYSTEM] Executing neural scan #{scan_count}..."
                )
                
                # Capture screenshot
                screenshot = self.analyzer.capture_screenshot()
                
                # Display on monitor
                self._display_screenshot(screenshot)
                
                # Analyze with AI
                vision_data = self.analyzer.analyze_table_image(screenshot)
                poker_data = self.analyzer.extract_poker_data(vision_data)
                
                if poker_data['is_poker_screen']:
                    self.log_analysis(f"\n[✓] SCAN #{scan_count} - POKER TABLE DETECTED", "header")
                    self.log_analysis(f"    Method: {poker_data.get('method', 'Unknown')}", "good")
                    
                    if poker_data.get('detected_cards'):
                        self.log_analysis(f"    Cards: {poker_data['detected_cards']}", "accent")
                    
                    if self.auto_mode:
                        self.log_analysis("    [*] AUTO mode: Executing strategy...", "warning")
                    
                    self.stats_label.config(
                        text=f"Scans: {scan_count} | Mode: {'AUTO' if self.auto_mode else 'ADVISOR'}"
                    )
                else:
                    self.log_analysis(f"[✗] SCAN #{scan_count} - NO POKER TABLE DETECTED", "error")
                
                time.sleep(3)  # Analysis interval
            
            except Exception as e:
                self.log_analysis(f"[!] ERROR: {str(e)}", "error")
                time.sleep(2)
    
    def _display_screenshot(self, img):
        """Display screenshot in monitor"""
        try:
            # Resize for display
            img_small = img.copy()
            img_small.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img_small)
            
            # Update monitor (in main thread)
            self.monitor_label.config(image=photo)
            self.monitor_label.image = photo  # Keep a reference
        except Exception as e:
            self.monitor_label.config(text=f"[ERR] Display failed: {e}")
    
    def clear_logs(self):
        """Clear analysis logs"""
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.config(state=tk.DISABLED)
        self.log_analysis("[*] LOGS CLEARED", "warning")


def main():
    """Launch hacker-themed poker bot"""
    root = tk.Tk()
    app = HackerPokerBot(root)
    root.mainloop()


if __name__ == "__main__":
    main()
