#!/usr/bin/env python3
"""
GUI for Network Mapping and Scanning Tool

A tkinter-based GUI that provides an intuitive interface for the netscapy tool.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import os
from pathlib import Path
from datetime import datetime
import queue
import time

# Import the main scanner
from main import NetworkScanner, TOOL_REGISTRY
from utils.logger import get_logger

logger = get_logger()


class ScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Netscapy - Network Scanning Tool")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # Configure style
        self.setup_styles()

        # Initialize variables
        self.scanner = None
        self.scan_thread = None
        self.scan_queue = queue.Queue()
        self.current_scan_results = {}

        # Create GUI components
        self.create_widgets()
        self.setup_layout()

        # Start message processing
        self.process_messages()

    def setup_styles(self):
        """Configure ttk styles for a modern look"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 10))

        # Configure button styles
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='green')
        style.configure('Warning.TButton', background='orange')

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")

        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="Netscapy Network Scanner",
            style='Title.TLabel'
        )

        # Target input frame
        self.target_frame = ttk.LabelFrame(
            self.main_frame, text="Target Configuration", padding="10")

        # Target input
        ttk.Label(self.target_frame, text="Target:").grid(
            row=0, column=0, sticky='w', padx=(0, 5))
        self.target_var = tk.StringVar()
        self.target_entry = ttk.Entry(
            self.target_frame, textvariable=self.target_var, width=40)
        self.target_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))

        # Tool selection
        ttk.Label(self.target_frame, text="Tools:").grid(
            row=1, column=0, sticky='w', padx=(0, 5), pady=(10, 0))
        self.tool_vars = {}
        self.tool_checkboxes = {}

        for i, tool in enumerate(TOOL_REGISTRY.keys()):
            var = tk.BooleanVar(value=tool == 'nmap')  # Default to nmap
            self.tool_vars[tool] = var
            cb = ttk.Checkbutton(
                self.target_frame,
                text=tool.title(),
                variable=var
            )
            cb.grid(row=1, column=i+1, sticky='w', padx=(0, 10), pady=(10, 0))
            self.tool_checkboxes[tool] = cb

        # Scan control buttons
        self.scan_button = ttk.Button(
            self.target_frame,
            text="Start Scan",
            command=self.start_scan,
            style='Action.TButton'
        )
        self.scan_button.grid(row=2, column=0, columnspan=len(
            TOOL_REGISTRY)+1, pady=(15, 0))

        self.stop_button = ttk.Button(
            self.target_frame,
            text="Stop Scan",
            command=self.stop_scan,
            state='disabled'
        )
        self.stop_button.grid(row=2, column=len(
            TOOL_REGISTRY)+1, pady=(15, 0), padx=(10, 0))

        # Configure grid weights
        self.target_frame.columnconfigure(1, weight=1)

        # Progress frame
        self.progress_frame = ttk.LabelFrame(
            self.main_frame, text="Scan Progress", padding="10")

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', pady=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Ready to scan")
        self.status_label = ttk.Label(
            self.progress_frame,
            textvariable=self.status_var,
            style='Status.TLabel'
        )
        self.status_label.pack(anchor='w')

        # Log output
        self.log_frame = ttk.LabelFrame(
            self.main_frame, text="Scan Log", padding="10")
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=8,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill='both', expand=True)

        # Results frame
        self.results_frame = ttk.LabelFrame(
            self.main_frame, text="Scan Results", padding="10")

        # Results notebook
        self.results_notebook = ttk.Notebook(self.results_frame)
        self.results_notebook.pack(fill='both', expand=True)

        # Summary tab
        self.summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.summary_frame, text="Summary")

        self.summary_text = scrolledtext.ScrolledText(
            self.summary_frame,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.summary_text.pack(fill='both', expand=True)

        # Raw JSON tab
        self.raw_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.raw_frame, text="Raw JSON")

        self.raw_text = scrolledtext.ScrolledText(
            self.raw_frame,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.raw_text.pack(fill='both', expand=True)

        # Action buttons for results
        self.results_buttons_frame = ttk.Frame(self.results_frame)
        self.results_buttons_frame.pack(fill='x', pady=(10, 0))

        self.refresh_button = ttk.Button(
            self.results_buttons_frame,
            text="Refresh Results",
            command=self.refresh_results
        )
        self.refresh_button.pack(side='left', padx=(0, 10))

        self.export_button = ttk.Button(
            self.results_buttons_frame,
            text="Export Results",
            command=self.export_results
        )
        self.export_button.pack(side='left', padx=(0, 10))

        self.open_folder_button = ttk.Button(
            self.results_buttons_frame,
            text="Open Results Folder",
            command=self.open_results_folder
        )
        self.open_folder_button.pack(side='left')

    def setup_layout(self):
        """Setup the main layout"""
        self.main_frame.pack(fill='both', expand=True)

        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        # Results frame gets extra space
        self.main_frame.rowconfigure(4, weight=1)

        # Pack widgets
        self.title_label.pack(pady=(0, 20))
        self.target_frame.pack(fill='x', pady=(0, 10))
        self.progress_frame.pack(fill='x', pady=(0, 10))
        self.log_frame.pack(fill='both', expand=True, pady=(0, 10))
        self.results_frame.pack(fill='both', expand=True)

    def log_message(self, message, level="INFO"):
        """Add a message to the log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"

        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)

        # Limit log size
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete("1.0", "500.0")

    def start_scan(self):
        """Start the scanning process"""
        target = self.target_var.get().strip()
        if not target:
            messagebox.showerror("Error", "Please enter a target")
            return

        # Get selected tools
        selected_tools = [tool for tool,
                          var in self.tool_vars.items() if var.get()]
        if not selected_tools:
            messagebox.showerror("Error", "Please select at least one tool")
            return

        # Update UI
        self.scan_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_var.set(0)
        self.status_var.set("Initializing scan...")

        # Clear previous results
        self.summary_text.delete("1.0", tk.END)
        self.raw_text.delete("1.0", tk.END)

        # Start scan in separate thread
        self.scan_thread = threading.Thread(
            target=self.run_scan_thread,
            args=(target, selected_tools),
            daemon=True
        )
        self.scan_thread.start()

    def run_scan_thread(self, target, tools):
        """Run the scan in a separate thread"""
        try:
            # Create scanner
            self.scanner = NetworkScanner(target)

            # Update status
            self.scan_queue.put(
                ("status", f"Starting scan of {target} with tools: {', '.join(tools)}"))
            self.scan_queue.put(("progress", 10))

            # Run scans
            results = self.scanner.run_scans(tools, max_workers=len(tools))

            # Update results
            self.current_scan_results = results
            self.scan_queue.put(("results", results))
            self.scan_queue.put(("status", "Scan completed successfully"))
            self.scan_queue.put(("progress", 100))

        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            self.scan_queue.put(("error", error_msg))
            logger.error(error_msg)

    def stop_scan(self):
        """Stop the current scan"""
        if self.scan_thread and self.scan_thread.is_alive():
            # Note: This is a basic implementation. For proper cancellation,
            # we'd need to implement signal handling in the scanner classes
            self.status_var.set("Stopping scan...")
            self.scan_queue.put(("status", "Scan stopped by user"))
            self.scan_queue.put(("progress", 0))

        self.scan_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def process_messages(self):
        """Process messages from the scan thread"""
        try:
            while True:
                try:
                    msg_type, data = self.scan_queue.get_nowait()

                    if msg_type == "status":
                        self.status_var.set(data)
                        self.log_message(data)
                    elif msg_type == "progress":
                        self.progress_var.set(data)
                    elif msg_type == "results":
                        self.display_results(data)
                    elif msg_type == "error":
                        self.status_var.set("Scan failed")
                        self.log_message(data, "ERROR")
                        messagebox.showerror("Scan Error", data)
                        self.scan_button.config(state='normal')
                        self.stop_button.config(state='disabled')

                except queue.Empty:
                    break

        except Exception as e:
            logger.error(f"Error processing messages: {e}")

        # Schedule next check
        self.root.after(100, self.process_messages)

    def display_results(self, results):
        """Display scan results"""
        try:
            # Update summary
            summary = self.generate_summary(results)
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert("1.0", summary)

            # Update raw JSON
            self.raw_text.delete("1.0", tk.END)
            self.raw_text.insert("1.0", json.dumps(results, indent=2))

            # Update UI
            self.scan_button.config(state='normal')
            self.stop_button.config(state='disabled')

            self.log_message("Results displayed successfully")

        except Exception as e:
            error_msg = f"Error displaying results: {str(e)}"
            self.log_message(error_msg, "ERROR")
            logger.error(error_msg)

    def generate_summary(self, results):
        """Generate a human-readable summary of scan results"""
        summary = []
        summary.append("=" * 60)
        summary.append("SCAN SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Target: {results.get('target', 'Unknown')}")
        summary.append(
            f"Start Time: {results.get('metadata', {}).get('start_time', 'Unknown')}")
        summary.append(
            f"End Time: {results.get('metadata', {}).get('end_time', 'Unknown')}")
        summary.append(
            f"Tools Used: {', '.join(results.get('metadata', {}).get('tools_used', []))}")
        summary.append("")

        # Tool-specific results
        scans = results.get('scans', {})
        for tool, scan_info in scans.items():
            summary.append(f"{tool.upper()} SCAN:")
            summary.append("-" * 30)
            status = scan_info.get('status', 'unknown')
            summary.append(f"Status: {status}")

            if 'error' in scan_info and scan_info['error']:
                summary.append(f"Error: {scan_info['error']}")
            elif 'results_file' in scan_info:
                summary.append(f"Results File: {scan_info['results_file']}")

            summary.append("")

        return "\n".join(summary)

    def refresh_results(self):
        """Refresh the results display"""
        if self.current_scan_results:
            self.display_results(self.current_scan_results)
            self.log_message("Results refreshed")
        else:
            messagebox.showinfo("Info", "No results to refresh")

    def export_results(self):
        """Export results to a file"""
        if not self.current_scan_results:
            messagebox.showinfo("Info", "No results to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Scan Results"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.current_scan_results, f, indent=2)
                self.log_message(f"Results exported to {filename}")
                messagebox.showinfo(
                    "Success", f"Results exported to {filename}")
            except Exception as e:
                error_msg = f"Error exporting results: {str(e)}"
                self.log_message(error_msg, "ERROR")
                messagebox.showerror("Export Error", error_msg)

    def open_results_folder(self):
        """Open the results folder in file explorer"""
        results_dir = Path("output/reports")
        if results_dir.exists():
            os.startfile(str(results_dir.absolute()))
        else:
            messagebox.showinfo("Info", "Results folder does not exist yet")


def main():
    """Main function to start the GUI"""
    root = tk.Tk()
    app = ScannerGUI(root)

    # Handle window close
    def on_closing():
        if app.scan_thread and app.scan_thread.is_alive():
            if messagebox.askokcancel("Quit", "A scan is in progress. Do you want to quit?"):
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
