"""
A simple GUI application for scraping HTML tags from a specified URL
using:
- CustomTkinter
- Requests
- BeautifulSoup
"""
import threading
import tkinter as tk
from tkinter import filedialog
import csv
from urllib.parse import urlparse
import customtkinter as ctk
import requests
from bs4 import BeautifulSoup

# Set the window theme and styling
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")


class ScraperApp(ctk.CTk):
    """
    A simple GUI application for scraping HTML tags from a specified URL.

    Args:
        ctk.CTk: Inherits from CustomTkinter's CTk class for GUI functionality.
    """
    def __init__(self):
        super().__init__()

        # Configure Main Window
        self.title("Web Scraper")
        self.geometry("800x600")
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Store scraped data for exporting to CSV)
        self.scraped_data = []

        # Input Section: URL and Tag
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(
            row=0, column=0, padx=20, pady=(20, 10), sticky="nsew"
        )
        self.input_frame.grid_columnconfigure(0, weight=1)

        # URL input
        self.url_label = ctk.CTkLabel(
            self.input_frame, text="Target URL:"
        )
        self.url_label.grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        self.url_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="https://example.com",
            height=35,
        )
        self.url_entry.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")

        # HTML Tag input
        self.tag_label = ctk.CTkLabel(
            self.input_frame,
            text="HTML Tag (e.g., h1, p, a, div):",
        )
        self.tag_label.grid(row=0, column=1, padx=15, pady=(10, 2), sticky="w")

        self.tag_entry = ctk.CTkEntry(
            self.input_frame, placeholder_text="p", width=200, height=35
        )
        self.tag_entry.grid(row=1, column=1, padx=15, pady=(0, 15), sticky="e")

        # Action Buttons
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.scrape_btn = ctk.CTkButton(
            self.control_frame,
            text="Start Scraping",
            command=self.start_scrape_thread,
            fg_color="#28a745",
            hover_color="#218838",
            height=40,
        )
        self.scrape_btn.pack(side="left", padx=5)

        self.export_btn = ctk.CTkButton(
            self.control_frame,
            text="Export to CSV",
            command=self.export_data,
            fg_color="#28a745",
            hover_color="#218838",
            height=40,
            state="disabled"  # Initially disabled until data is available
        )
        self.export_btn.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(
            self.control_frame, text="Ready"
        )
        self.status_label.pack(side="right", padx=10)

        # Output label
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(
            row=2, column=0, padx=20, pady=(10, 20), sticky="nsew"
        )
        self.output_frame.grid_rowconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)

        self.results_label = ctk.CTkLabel(
            self.output_frame, text="Results:"
        )
        self.results_label.grid(
            row=0, column=0, padx=15, pady=(10, 2), sticky="w"
        )

        # Scrollable Output Box
        self.result_textbox = ctk.CTkTextbox(
            self.output_frame, activate_scrollbars=True
        )
        self.result_textbox.grid(
            row=1, column=0, padx=15, pady=(0, 15), sticky="nsew"
        )

    def log_message(self, message):
        """
        Helper function to insert clear text updates to the text box.
        """
        self.result_textbox.insert(tk.END, message + "\n")
        self.result_textbox.see(tk.END)

    def update_status(self, text, color="white"):
        """
        Safely updates UI elements tracking operational state.
        """
        self.status_label.configure(text=text, text_color=color)

    def start_scrape_thread(self):
        """
        Spawns background worker thread to prevent GUI freezing.
        """
        # Clean text frame for incoming batch
        self.result_textbox.delete("1.0", tk.END)
        self.scraped_data = []  # Reset scraped data for new session

        # Disable export until new data is available
        self.export_btn.configure(state="disabled")

        url = self.url_entry.get().strip()
        tag = self.tag_entry.get().strip()

        # Input Validation Guardrails
        if not url:
            self.log_message("[Error] Please enter a URL.")
            self.update_status("Error", "red")
            return

        # Simple URL validator
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            self.log_message(
                "[Error] Invalid URL. Please include http:// or https://"
            )
            self.update_status("Error", "red")
            return

        if not tag:
            tag = "p"  # Fallback safely to standard paragraph tag if empty
            self.tag_entry.insert(0, "p")

        # Disable button during query execution
        self.scrape_btn.configure(state="disabled")
        self.update_status("Scraping...", "orange")

        # Hand off networking operation cleanly to separate background thread
        threading.Thread(
            target=self.execute_scraping, args=(url, tag), daemon=True
        ).start()

    def execute_scraping(self, url, tag):
        """
        Core web scraping logic executed off-main-thread.
        
        Args:
            url (str): The target URL to scrape.
            tag (str): The HTML tag to search for.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            found_elements = soup.find_all(tag)

            if not found_elements:
                self.log_message(
                    f"Process complete. No <{tag}> tags found on this page."
                )
                self.update_status("Done (0 Found)", "gray")
            else:
                self.log_message(
                    f"--- Successfully pulled {len(found_elements)} '<{tag}>' tags ---\n"
                )
                for index, element in enumerate(found_elements, 1):
                    clean_text = element.get_text().strip()
                    if clean_text:  # Exclude printing whitespace-only results
                        self.scraped_data.append({
                            "index": index,
                            "tag": tag,
                            "text": clean_text
                        })
                        self.log_message(f"[{index}] {clean_text}\n")
                        self.log_message("-" * 40)

                if self.scraped_data:
                    self.export_btn.configure(state="normal")
                    self.update_status("Success!", "green")
                else:
                    self.update_status("Complete! No Content Found", "green")

        except Exception as e:
            self.log_message(f"[System Error] Call failed: {str(e)}")
            self.update_status("Failed", "red")

        finally:
            # Re-enable the button safely on operational completion
            self.scrape_btn.configure(state="normal")

    def export_data(self):
        """
        Exports the scraped data to a CSV file.
        """
        if not self.scraped_data:
            self.log_message("[Error] No data available to export.")
            self.update_status("No Data", "red")
            return

        # Prompt user for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("TXT files", "*.txt"),
                ("All files", "*.*")
                ],
            title="Save as"
        )

        if not file_path:
            self.log_message("[Info] Export cancelled by user.")
            self.update_status("Export Cancelled", "orange")
            return

        try:
            csv_path = file_path.endswith(".csv")
            txt_path = file_path.endswith(".txt")

            if csv_path or txt_path:
                with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                    fieldnames = ["index", "HTML tag", "Content"]
                    writer = csv.DictWriter(file, fieldnames=fieldnames)

                    writer.writeheader()
                    for row in self.scraped_data:
                        writer.writerow({
                            "index": row["index"],
                            "HTML tag": row["tag"],
                            "Content": row["text"]
                        })
            else:
                with open(file_path, mode="w", encoding="utf-8") as txt_file:
                    txt_file.write(f"Scraped Data from URL: {self.url_entry.get().strip()}\n")
                    for item in self.scraped_data:
                        txt_file.write(f"[{item['index']}] <{item['tag']}>:\n{item['text']}\n")
                        txt_file.write("-" * 40 + "\n")

            self.log_message(f"File saved to {file_path}")
            self.update_status("Exported!", "green")

        except Exception as e:
            self.log_message(f"[Error] Failed to export data: {str(e)}")
            self.update_status("Export Failed", "red")


if __name__ == "__main__":
    app = ScraperApp()
    app.mainloop()
