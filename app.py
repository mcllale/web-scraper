import threading
import tkinter as tk
from urllib.parse import urlparse
import customtkinter as ctk
import requests
from bs4 import BeautifulSoup

# Window theme and styling
ctk.set_appearance_mode("System")  # Inherits the system's light/dark mode setting
ctk.set_default_color_theme("light-blue")

