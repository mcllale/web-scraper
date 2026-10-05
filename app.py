"""
A simple GUI application for scraping HTML tags from a specified URL
using:
- CustomTkinter
- Requests
- BeautifulSoup
"""
import threading
import tkinter as tk
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
            height=40,
        )
        self.scrape_btn.pack(side="left", padx=5)

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

        # CustomTkinter Scrollable Text Box
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
                "[Error] Invalid URL structure. Please include http:// or https://"
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
                        self.log_message(f"[{index}] {clean_text}\n")
                        self.log_message("-" * 40)

                self.update_status("Success!", "green")

        except requests.exceptions.Timeout:
            self.log_message("[Error] The request timed out. Server took too long to reply.")
            self.update_status("Timeout", "red")
        except requests.exceptions.HTTPError as http_err:
            self.log_message(f"[HTTP Error] Server returned code: {http_err.response.status_code}")
            self.update_status("HTTP Error", "red")
        except Exception as e:
            self.log_message(f"[System Error] Call failed: {str(e)}")
            self.update_status("Failed", "red")

        finally:
            # Re-enable the button safely on operational completion
            self.scrape_btn.configure(state="normal")


if __name__ == "__main__":
    app = ScraperApp()
    app.mainloop()
