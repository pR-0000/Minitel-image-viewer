#!/usr/bin/env python3
import os, subprocess, time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import serial
except ImportError:
    subprocess.check_call(["python", "-m", "pip", "install", "pyserial"])
    import serial
import serial.tools.list_ports

try:
    from PIL import Image, ImageTk
except ImportError:
    subprocess.check_call(["python", "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageTk

version = 0.1
DEFAULT_MINITEL_MODEL = "Minitel 1B and later"
ser = None

# Palette Minitel (8 couleurs) en RGB
minitel_palette = [
    (0, 0, 0),       # Noir
    (255, 0, 0),     # Rouge
    (0, 255, 0),     # Vert
    (255, 255, 0),   # Jaune
    (0, 0, 255),     # Bleu
    (255, 0, 255),   # Magenta
    (0, 255, 255),   # Cyan
    (255, 255, 255)  # Blanc
]

minitel_color_names = {
    "Black": (0, 0, 0),
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Yellow": (255, 255, 0),
    "Blue": (0, 0, 255),
    "Magenta": (255, 0, 255),
    "Cyan": (0, 255, 255),
    "White": (255, 255, 255)
}

color_codes = {
    (0, 0, 0):       ("1B40", "1B50"),
    (255, 0, 0):     ("1B41", "1B51"),
    (0, 255, 0):     ("1B42", "1B52"),
    (255, 255, 0):   ("1B43", "1B53"),
    (0, 0, 255):     ("1B44", "1B54"),
    (255, 0, 255):   ("1B45", "1B55"),
    (0, 255, 255):   ("1B46", "1B56"),
    (255, 255, 255): ("1B47", "1B57")
}

pixel_to_g1_code = {
    "000000": "20", "100000": "21", "010000": "22", "110000": "23",
    "001000": "24", "101000": "25", "011000": "26", "111000": "27",
    "000100": "28", "100100": "29", "010100": "2A", "110100": "2B",
    "001100": "2C", "101100": "2D", "011100": "2E", "111100": "2F",
    "000010": "30", "100010": "31", "010010": "32", "110010": "33",
    "001010": "34", "101010": "35", "011010": "36", "111010": "37",
    "000110": "38", "100110": "39", "010110": "3A", "110110": "3B",
    "001110": "3C", "101110": "3D", "011110": "3E", "111110": "3F",
    "000001": "60", "100001": "61", "010001": "62", "110001": "63",
    "001001": "64", "101001": "65", "011001": "66", "111001": "67",
    "000101": "68", "100101": "69", "010101": "6A", "110101": "6B",
    "001101": "6C", "101101": "6D", "011101": "6E", "111101": "6F",
    "000011": "70", "100011": "71", "010011": "72", "110011": "73",
    "001011": "74", "101011": "75", "011011": "76", "111011": "77",
    "000111": "78", "100111": "79", "010111": "7A", "110111": "7B",
    "001111": "7C", "101111": "7D", "011111": "7E", "111111": "7F"
}

def convert_image_to_minitel_palette(image):
    image = image.convert("RGB")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            original_color = pixels[x, y]
            closest_color = min(minitel_palette,
                                key=lambda color: sum((color[i] - original_color[i]) ** 2 for i in range(3)))
            pixels[x, y] = closest_color
    return image

def get_preview_image(filepath, mode="resize", bg_color=(0,0,0)):
    image = Image.open(filepath)
    image = image.convert("RGB")
    target_width, target_height = 80, 72

    if mode == "resize":
        image = image.resize((target_width, target_height), Image.LANCZOS)
    elif mode == "center":
        iw, ih = image.size
        if iw > target_width or ih > target_height:
            scale_factor = min(target_width / iw, target_height / ih)
            new_width = int(iw * scale_factor)
            new_height = int(ih * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
            iw, ih = image.size
        new_img = Image.new("RGB", (target_width, target_height), bg_color)
        left = (target_width - iw) // 2
        top = (target_height - ih) // 2
        new_img.paste(image, (left, top))
        image = new_img

    image = convert_image_to_minitel_palette(image)
    return image

def image_to_G1(filepath, mode="resize", bg_color=(0,0,0)):
    image = get_preview_image(filepath, mode, bg_color)
    mosaic_hex = ""
    target_width, target_height = 80, 72
    for y in range(0, target_height, 3):
        for x in range(0, target_width, 2):
            block_pixels = [
                image.getpixel((x, y)),
                image.getpixel((x+1, y)),
                image.getpixel((x, y+1)),
                image.getpixel((x+1, y+1)),
                image.getpixel((x, y+2)),
                image.getpixel((x+1, y+2))
            ]
            color_count = {}
            for pixel in block_pixels:
                color_count[pixel] = color_count.get(pixel, 0) + 1
            sorted_colors = sorted(color_count.items(), key=lambda item: item[1], reverse=True)
            bg, fg = sorted_colors[0][0], (sorted_colors[1][0] if len(sorted_colors) > 1 else (255,255,255))
            if bg == fg:
                fg = (0,0,0) if bg != (0,0,0) else (255,255,255)
            binary_string = ''.join(['1' if pixel == fg else '0' for pixel in block_pixels])
            g1_code = pixel_to_g1_code.get(binary_string, "7F")
            cell = color_codes[bg][1] + color_codes[fg][0] + g1_code
            mosaic_hex += cell
    return mosaic_hex

def open_gui():
    window = tk.Tk()
    window.title(f"Minitel Image Viewer v{version}")
    window.geometry("600x750")
    window.minsize(600, 750)

    model_var = tk.StringVar(value=DEFAULT_MINITEL_MODEL)
    com_port_var = tk.StringVar()
    baudrate_var = tk.IntVar()
    data_bits_var = tk.IntVar()
    parity_var = tk.StringVar()
    stop_bits_var = tk.IntVar(value=1)
    
    image_file_var = tk.StringVar(value="No files selected")
    mode_var = tk.StringVar(value="resize")
    bg_color_var = tk.StringVar(value="Black")
    preview_mode_var = tk.StringVar(value="Color")
    
    def clear_console():
        console.config(state='normal')
        console.delete('1.0', tk.END)
        console.config(state='disabled')
    
    def log_message(message):
        console.config(state='normal')
        console.insert(tk.END, f"{datetime.now().strftime('[%H:%M:%S] ')}{message}\n")
        console.config(state='disabled')
        console.see(tk.END)
    
    def list_serial_ports():
        ports = serial.tools.list_ports.comports()
        return [f"{port.device} - {port.description}" for port in ports]
    
    def apply_model_settings(*args):
        clear_console()
        model = model_var.get()
        if model == "Minitel 1":
            baudrate_menu['values'] = [1200]
            baudrate_var.set(1200)
            data_bits_var.set(7)
            parity_var.set("Even")
        elif model == "Minitel 1B and later":
            baudrate_menu['values'] = [300, 1200, 4800]
            baudrate_var.set(4800)
            data_bits_var.set(7)
            parity_var.set("Even")
            log_message("Configure the serial port speed on your Minitel:")
            log_message("Fcnt + P, 3: 300 bits/s")
            log_message("Fcnt + P, 1: 1200 bits/s")
            log_message("Fcnt + P, 4: 4800 bits/s")
        elif model == "Minitel 2 or Magis Club":
            baudrate_menu['values'] = [300, 1200, 4800, 9600]
            baudrate_var.set(9600)
            data_bits_var.set(8 if baudrate_var.get() == 9600 else 7)
            parity_var.set("None" if baudrate_var.get() == 9600 else "Even")
            log_message("Configure the serial port speed on your Minitel:")
            log_message("Fcnt + P, 3: 300 bits/s")
            log_message("Fcnt + P, 1: 1200 bits/s")
            log_message("Fcnt + P, 4: 4800 bits/s")
            log_message("Fcnt + P, 9: 9600 bits/s")
    
    def choose_image_file():
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp"), ("All Files", "*.*")]
        )
        if file_path:
            image_file_var.set(file_path)
            log_message(f"Selected file: {file_path}")
            update_preview()
    
    def update_preview():
        if image_file_var.get() == "No files selected":
            blank = Image.new("RGB", (300, int(300 * 72/80)), (255,255,255))
            photo = ImageTk.PhotoImage(blank)
            preview_label.config(image=photo)
            preview_label.image = photo
            return
        mode = mode_var.get()
        bg_color = minitel_color_names.get(bg_color_var.get(), (0,0,0)) if mode == "center" else (0,0,0)
        preview_img = get_preview_image(image_file_var.get(), mode, bg_color)
        max_width = 300
        avail_width = preview_frame.winfo_width()
        if avail_width <= 1:
            avail_width = max_width
        new_width = min(avail_width, max_width)
        new_height = int(new_width * 72 / 80)
        preview_img = preview_img.resize((new_width, new_height), Image.LANCZOS)
        if preview_mode_var.get() == "Grayscale":
            preview_img = preview_img.convert("L")
        photo = ImageTk.PhotoImage(preview_img)
        preview_label.config(image=photo)
        preview_label.image = photo

    def send_image_to_minitel():
        selected_com = com_port_var.get().split(" - ")[0]
        if not selected_com:
            log_message("Error: No COM port selected.")
            return
        if image_file_var.get() == "No files selected":
            log_message("Error: No image file selected.")
            return
        log_message(f"Connect to {selected_com}...")
        try:
            ser_local = serial.Serial(
                port=selected_com,
                baudrate=baudrate_var.get(),
                bytesize=serial.SEVENBITS if data_bits_var.get() == 7 else serial.EIGHTBITS,
                parity=serial.PARITY_EVEN if parity_var.get().lower() == "even" else serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE if stop_bits_var.get() == 1 else serial.STOPBITS_TWO,
                timeout=1
            )
            ser_local.write(b'\x1B\x3B\x60\x58\x52')
            ser_local.write(b'\x14')
            ser_local.write(b'\x0C')
            ser_local.write(b'\x0E')
            ser_local.write(b'\x1B\x3A\x6A\x43')

            mode = mode_var.get()
            bg_color = minitel_color_names.get(bg_color_var.get(), (0,0,0)) if mode == "center" else (0,0,0)
    
            mosaic_hex = image_to_G1(image_file_var.get(), mode, bg_color)
            data_bytes = bytes.fromhex(mosaic_hex)
            ser_local.write(data_bytes)
    
            log_message("Data sent : " + mosaic_hex)
            ser_local.close()
            log_message("Connection closed.")
        except serial.SerialException as e:
            log_message("Serial connection error: " + str(e))

    tk.Label(window, text="Image file:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
    tk.Label(window, textvariable=image_file_var, anchor="w").grid(row=0, column=1, sticky="ew", padx=2, pady=2)
    tk.Button(window, text="Select file", command=choose_image_file).grid(row=0, column=2, sticky="ew", padx=2, pady=2)

    tk.Label(window, text="Resize mode:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
    frame_mode = tk.Frame(window)
    frame_mode.grid(row=1, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
    tk.Radiobutton(frame_mode, text="Stretch (fill screen)", variable=mode_var, value="resize", command=update_preview).pack(side="left", padx=2)
    tk.Radiobutton(frame_mode, text="Crop and center", variable=mode_var, value="center", command=update_preview).pack(side="left", padx=2)
    
    tk.Label(window, text="Background color:").grid(row=2, column=0, sticky="w", padx=2, pady=2)
    bg_color_menu = ttk.Combobox(window, textvariable=bg_color_var, values=list(minitel_color_names.keys()), state='readonly')
    bg_color_menu.grid(row=2, column=1, columnspan=2, sticky="ew", padx=2, pady=2)

    tk.Label(window, text="Preview mode:").grid(row=3, column=0, sticky="w", padx=2, pady=2)
    frame_preview_mode = tk.Frame(window)
    frame_preview_mode.grid(row=3, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
    tk.Radiobutton(frame_preview_mode, text="Color", variable=preview_mode_var, value="Color", command=update_preview).pack(side="left", padx=2)
    tk.Radiobutton(frame_preview_mode, text="Grayscale", variable=preview_mode_var, value="Grayscale", command=update_preview).pack(side="left", padx=2)

    preview_frame = tk.Frame(window, bd=2, relief="sunken", width=320, height=300)
    preview_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=2, pady=2)
    preview_frame.grid_propagate(False)
    preview_label = tk.Label(preview_frame)
    preview_label.grid(row=0, column=0, sticky="nsew")
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(0, weight=1)

    tk.Label(window, text="Minitel Model:").grid(row=5, column=0, sticky="w", padx=2, pady=2)
    model_menu = ttk.Combobox(window, textvariable=model_var, values=["Minitel 1", "Minitel 1B and later", "Minitel 2 or Magis Club"], state='readonly')
    model_menu.grid(row=5, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
    model_menu.bind("<<ComboboxSelected>>", apply_model_settings)
    
    tk.Label(window, text="COM Port:").grid(row=6, column=0, sticky="w", padx=2, pady=2)
    com_port_menu = ttk.Combobox(window, textvariable=com_port_var, values=list_serial_ports(), state='readonly')
    com_port_menu.grid(row=6, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
    
    tk.Label(window, text="Baud Rate:").grid(row=7, column=0, sticky="w", padx=2, pady=2)
    baudrate_menu = ttk.Combobox(window, textvariable=baudrate_var, state='readonly')
    baudrate_menu.grid(row=7, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
    
    tk.Label(window, text="Data Bits:").grid(row=8, column=0, sticky="w", padx=2, pady=2)
    data_bits_menu = ttk.Combobox(window, textvariable=data_bits_var, values=[7, 8], state='readonly')
    data_bits_menu.grid(row=8, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
    
    tk.Label(window, text="Parity:").grid(row=9, column=0, sticky="w", padx=2, pady=2)
    parity_menu = ttk.Combobox(window, textvariable=parity_var, values=["None", "Even"], state='readonly')
    parity_menu.grid(row=9, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
    
    tk.Label(window, text="Stop Bits:").grid(row=10, column=0, sticky="w", padx=2, pady=2)
    stop_bits_menu = ttk.Combobox(window, textvariable=stop_bits_var, values=[1], state='readonly')
    stop_bits_menu.grid(row=10, column=1, columnspan=2, sticky="ew", padx=2, pady=2)

    tk.Button(window, text="Send image to Minitel", command=send_image_to_minitel).grid(row=11, column=0, columnspan=3, sticky="ew", padx=2, pady=5)

    console_frame = tk.Frame(window)
    console_frame.grid(row=12, column=0, columnspan=3, sticky="nsew", padx=2, pady=2)
    console = tk.Text(console_frame, height=8, state='disabled', wrap='word')
    console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    console_scrollbar = tk.Scrollbar(console_frame, command=console.yview)
    console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    console['yscrollcommand'] = console_scrollbar.set

    apply_model_settings()

    window.rowconfigure(12, weight=1)
    window.columnconfigure(0, weight = 1)
    window.columnconfigure(1, weight = 1)
    window.columnconfigure(2, weight = 1)
    window.columnconfigure(3, weight = 1)

    preview_frame.bind("<Configure>", lambda event: update_preview())
    
    window.mainloop()

open_gui()
