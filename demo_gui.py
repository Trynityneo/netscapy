#!/usr/bin/env python3
"""
Demo script for the Netscapy GUI

This script demonstrates the GUI functionality with sample data
without requiring external tools to be installed.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
import time
from datetime import datetime


class DemoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Netscapy GUI Demo")
        self.root.geometry("800x600")

        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        """Create demo widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")

        # Title
        title = ttk.Label(main_frame, text="Netscapy GUI Demo",
                          font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 20))

        # Description
        desc = ttk.Label(
            main_frame,
            text="This demo shows the GUI interface. In the real application, you would:\n"
                 "1. Enter a target (IP or hostname)\n"
                 "2. Select scanning tools (Nmap, Nikto, WhatWeb)\n"
                 "3. Start the scan and monitor progress\n"
                 "4. View results in summary and JSON formats\n"
                 "5. Export results to files",
            justify='left'
        )
        desc.pack(pady=(0, 20))

        # Demo buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=(0, 20))

        # Demo buttons
        ttk.Button(
            buttons_frame,
            text="Show Sample Target Input",
            command=self.show_target_demo
        ).pack(side='left', padx=(0, 10))

        ttk.Button(
            buttons_frame,
            text="Show Sample Progress",
            command=self.show_progress_demo
        ).pack(side='left', padx=(0, 10))

        ttk.Button(
            buttons_frame,
            text="Show Sample Results",
            command=self.show_results_demo
        ).pack(side='left')

        # Demo output
        self.output_text = scrolledtext.ScrolledText(
            main_frame,
            height=20,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.output_text.pack(fill='both', expand=True)

    def setup_layout(self):
        """Setup layout"""
        pass  # Already done in create_widgets

    def log_message(self, message):
        """Add message to output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        self.output_text.insert(tk.END, formatted)
        self.output_text.see(tk.END)

    def show_target_demo(self):
        """Show target input demo"""
        self.log_message("=== TARGET INPUT DEMO ===")
        self.log_message("Target: scanme.nmap.org")
        self.log_message("Selected Tools: Nmap, WhatWeb")
        self.log_message(
            "This would start a scan of scanme.nmap.org using Nmap and WhatWeb")
        self.log_message("")

    def show_progress_demo(self):
        """Show progress demo"""
        self.log_message("=== PROGRESS DEMO ===")
        self.log_message("Starting scan...")

        def progress_simulation():
            for i in range(1, 11):
                time.sleep(0.5)
                self.root.after(0, self.log_message,
                                f"Progress: {i*10}% - Tool {i} completed")
            self.root.after(0, self.log_message,
                            "Scan completed successfully!")
            self.root.after(0, self.log_message, "")

        threading.Thread(target=progress_simulation, daemon=True).start()

    def show_results_demo(self):
        """Show sample results"""
        sample_results = {
            "target": "scanme.nmap.org",
            "metadata": {
                "start_time": "2024-01-15 10:30:00",
                "end_time": "2024-01-15 10:35:00",
                "tools_used": ["nmap", "whatweb"]
            },
            "scans": {
                "nmap": {
                    "status": "completed",
                    "results_file": "output/reports/nmap_results_scanme.nmap.org.json"
                },
                "whatweb": {
                    "status": "completed",
                    "results_file": "output/reports/whatweb_results_scanme.nmap.org.json"
                }
            }
        }

        self.log_message("=== SAMPLE RESULTS ===")
        self.log_message("Summary:")
        self.log_message(f"  Target: {sample_results['target']}")
        self.log_message(
            f"  Start Time: {sample_results['metadata']['start_time']}")
        self.log_message(
            f"  End Time: {sample_results['metadata']['end_time']}")
        self.log_message(
            f"  Tools Used: {', '.join(sample_results['metadata']['tools_used'])}")
        self.log_message("")
        self.log_message("Raw JSON:")
        self.log_message(json.dumps(sample_results, indent=2))
        self.log_message("")

    def clear_output(self):
        """Clear the output"""
        self.output_text.delete("1.0", tk.END)


def main():
    """Main function"""
    root = tk.Tk()
    app = DemoGUI(root)

    # Add clear button
    clear_button = ttk.Button(
        root,
        text="Clear Output",
        command=app.clear_output
    )
    clear_button.pack(side='bottom', pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
