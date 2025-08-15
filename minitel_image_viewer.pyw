#!/usr/bin/env python3
import os, sys, subprocess, time, threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Dépendances --------------------------------------------------------------
try:
    import serial
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
    import serial
import serial.tools.list_ports

try:
    from PIL import Image, ImageTk
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageTk

# --- Version & Constantes -----------------------------------------------------
version = "0.2.1"
CHAR_WIDTH, CHAR_HEIGHT = 2, 3
TARGET_W, TARGET_H = 80, 72  # pixels Minitel en mode mosaïque (2x3 par caractère)
RLE_MAX = 63

# --- Détection Minitel --------------------------------------------------------
def detect_and_configure_minitel(port_name):
    import serial, time
    types = {
        0x62: ("Minitel 1", 1200),
        0x63: ("Minitel 1", 1200),
        0x64: ("Minitel 10", 1200),
        0x65: ("Minitel 1 Couleur", 1200),
        0x66: ("Minitel 10", 1200),
        0x67: ("Émulateur", 9600),
        0x72: ("Minitel 1", 1200),
        0x73: ("Minitel 1 Couleur", 1200),
        0x74: ("Terminatel 252", 1200),
        0x75: ("Minitel 1 Bi-standard", 4800),
        0x76: ("Minitel 2", 9600),
        0x77: ("Minitel 10 Bi-standard", 4800),
        0x78: ("Thomson ?", 1200),
        0x79: ("Minitel 5", 1200),
        0x7A: ("Minitel 12", 1200),
    }
    # PROBE 7E1 UNIQUEMENT, y compris à 9600 bps
    speeds_to_try = [
        (1200, serial.SEVENBITS, serial.PARITY_EVEN),
        (4800, serial.SEVENBITS, serial.PARITY_EVEN),
        (9600, serial.SEVENBITS, serial.PARITY_EVEN),
    ]
    for baud, bits, parity in speeds_to_try:
        try:
            ser = serial.Serial(
                port=port_name, baudrate=baud, bytesize=bits, parity=parity,
                stopbits=serial.STOPBITS_ONE, timeout=1
            )
            ser.reset_input_buffer()
            ser.write(b'\x1B\x39\x7B')  # ESC 9 {
            time.sleep(0.5)
            resp = ser.read(5)
            ser.close()
            if len(resp) >= 5 and resp[0] == 0x01 and resp[4] == 0x04:
                type_code = resp[2]
                model_info, target_speed = types.get(type_code, ("Inconnu", 1200))
                # Tenter de fixer la VITESSE côté Minitel (framing non modifié)
                if target_speed != baud:
                    try:
                        ser = serial.Serial(
                            port=port_name, baudrate=baud, bytesize=bits, parity=parity,
                            stopbits=serial.STOPBITS_ONE, timeout=1
                        )
                        speed_bits = {4800: 0b110, 9600: 0b111}.get(target_speed, 0b100)  # 1200=100
                        config_byte = (1 << 6) | (speed_bits << 3) | speed_bits  # P=0,1,E, R
                        ser.write(b'\x1B\x3A\x6B' + bytes([config_byte]))  # ESC : k
                        time.sleep(0.2)
                        ser.close()
                    except Exception:
                        pass
                return model_info, target_speed
        except Exception:
            pass
    return "Inconnu", 1200

# --- Séquence d'initialisation VDT (echo off, curseur off, CLS, clear line 0, HOME, G1)
def build_init_sequence():
    # ESC ; ` X R  = désactiver écho local (séquence standard Tulipe)
    # DC4 (0x14)   = masquer le curseur
    # FF  (0x0C)   = effacer l'écran
    # US,row,col   = positionner en (ligne 0, col 1) puis EL (0x18) deux fois pour être sûr
    # RS  (0x1E)   = HOME (ligne 0, col 0)
    # SO  (0x0E)   = passer en jeu de caractères mosaïque G1 (requis pour l’affichage)
    return (
        b'\x1B\x3B\x60\x58\x52'  # désactiver écho local
        b'\x14'                  # masquer curseur
        b'\x0C'                  # effacer écran
        b'\x1F\x40\x41'          # US + row=0x40 (ligne 0), col=0x41 (col 1)
        b'\x18\x18'              # EL ×2 (effacer ligne 0)
        b'\x1E'                  # HOME (0,0)
        b'\x0E'                  # G1
    )

# --- Palette Minitel ----------------------------------------------------------
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
    "White": (255, 255, 255),
}

# Codes couleur (en hex) -> précompilés en octets (paper puis ink)
color_codes = {
    (0, 0, 0): ("1B40", "1B50"),
    (255, 0, 0): ("1B41", "1B51"),
    (0, 255, 0): ("1B42", "1B52"),
    (255, 255, 0): ("1B43", "1B53"),
    (0, 0, 255): ("1B44", "1B54"),
    (255, 0, 255): ("1B45", "1B55"),
    (0, 255, 255): ("1B46", "1B56"),
    (255, 255, 255): ("1B47", "1B57"),
}
def _hexbytes(s): return bytes.fromhex(s)
COLOR_SET = { rgb: (_hexbytes(v[1]), _hexbytes(v[0])) for rgb, v in color_codes.items() }
#            { rgb: (paper_bytes, ink_bytes) }

# Table bits -> code G1 (précompilée en octet unique)
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
    "001111": "7C", "101111": "7D", "011111": "7E", "111111": "7F",
}
PIXEL_TO_G1 = { k: int(v, 16) for k, v in pixel_to_g1_code.items() }

# --- Quantification vers palette Minitel -------------------------------------
def convert_image_to_minitel_palette(img, dither=True):
    """Quantize l'image sur la palette 8 couleurs Minitel (mode 'P')."""
    img = img.convert("RGB")
    pal_img = Image.new("P", (1, 1))
    flat = sum(minitel_palette, ()) + (0,) * ((256 - 8) * 3)
    pal_img.putpalette(flat)
    d = Image.FLOYDSTEINBERG if dither else Image.NONE
    q = img.quantize(palette=pal_img, dither=d)
    return q  # mode 'P' indices 0..7

# --- Préparation image -------------------------------------------------------
def get_preview_image(filepath, mode="resize", bg_color=(0, 0, 0), dither=True):
    image = Image.open(filepath).convert("RGB")
    target_width, target_height = TARGET_W, TARGET_H

    if mode == "resize":  # stretch
        image = image.resize((target_width, target_height), Image.LANCZOS)
    elif mode == "center":  # scale & pad
        iw, ih = image.size
        scale = min(target_width / iw, target_height / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        image = image.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGB", (target_width, target_height), bg_color)
        left, top = (target_width - nw) // 2, (target_height - nh) // 2
        canvas.paste(image, (left, top))
        image = canvas

    imgP = convert_image_to_minitel_palette(image, dither=dither)
    return imgP

# --- Conversion G1 optimisée -------------------------------------------------
def image_P_to_G1_bytes(imgP):
    w, h = imgP.size
    assert (w, h) == (TARGET_W, TARGET_H)
    pix = imgP.load()
    chars_x, chars_y = w // CHAR_WIDTH, h // CHAR_HEIGHT

    out = bytearray()
    last_bg = None
    last_fg = None

    for y in range(chars_y):
        x = 0
        while x < chars_x:
            x0, y0 = x * 2, y * 3
            block = [pix[x0 + dx, y0 + dy] for dy in range(3) for dx in range(2)]

            # histogramme
            hist = [0]*8
            for v in block: hist[v] += 1
            bg = max(range(8), key=lambda k: hist[k])
            fg = max((k for k in range(8) if k != bg), key=lambda k: hist[k], default=bg)

            bits = ''.join('1' if v == fg else '0' for v in block)

            # --- RUN DE BLOCS VIDES (même couleur de fond)
            if bits == '000000':
                run = 1
                run_bg = bg
                while x + run < chars_x:
                    xr = x + run
                    xr0 = xr * 2
                    blk = [pix[xr0 + dx, y0 + dy] for dy in range(3) for dx in range(2)]
                    h2 = [0]*8
                    for v in blk: h2[v] += 1
                    bgr = max(range(8), key=lambda k: h2[k])
                    fgr = max((k for k in range(8) if k != bgr), key=lambda k: h2[k], default=bgr)
                    bitsr = ''.join('1' if v == fgr else '0' for v in blk)
                    if bitsr != '000000' or bgr != run_bg:
                        break
                    run += 1

                if last_bg != run_bg:
                    bg_rgb = minitel_palette[run_bg]
                    out.extend(COLOR_SET[bg_rgb][0])  # PAPER
                    last_bg = run_bg

                remaining = run
                while remaining > 0:
                    batch = min(64, remaining)
                    out.append(0x20)                      # espace mosaïque
                    if batch > 1:
                        out.extend((0x12, 0x40 + (batch - 1)))  # RLE
                    remaining -= batch

                x += run
                continue

            # Couleurs (paper+ink) si changement
            if (bg != last_bg) or (fg != last_fg):
                bg_rgb = minitel_palette[bg]
                fg_rgb = minitel_palette[fg]
                out.extend(COLOR_SET[bg_rgb][0])  # PAPER
                out.extend(COLOR_SET[fg_rgb][1])  # INK
                last_bg, last_fg = bg, fg

            code = PIXEL_TO_G1.get(bits, 0x20)
            out.append(code)

            # RLE vers la droite
            r = 0
            while r < RLE_MAX and (x + 1 + r) < chars_x:
                xr = x + 1 + r
                xr0 = xr * 2
                blockR = [pix[xr0 + dx, y0 + dy] for dy in range(3) for dx in range(2)]
                histR = [0]*8
                for v in blockR: histR[v] += 1
                bgR = max(range(8), key=lambda k: histR[k])
                fgR = max((k for k in range(8) if k != bgR), key=lambda k: histR[k], default=bgR)
                if (bgR != bg) or (fgR != fg):
                    break
                bitsR = ''.join('1' if v == fg else '0' for v in blockR)
                if bitsR != bits:
                    break
                r += 1

            if r:
                out.extend((0x12, 0x40 + r))
                x += 1 + r
            else:
                x += 1

    return bytes(out)

def image_to_G1(filepath, mode="resize", bg_color=(0, 0, 0), dither=True):
    imgP = get_preview_image(filepath, mode, bg_color, dither=dither)
    return image_P_to_G1_bytes(imgP)

# --- GUI ---------------------------------------------------------------------
def open_gui():
    window = tk.Tk()
    window.title(f"Minitel Image Viewer v{version}")
    window.geometry("700x800")
    window.minsize(640, 760)
    for c in range(3):
        window.columnconfigure(c, weight=1)
    window.rowconfigure(13, weight=1)

    com_port_var = tk.StringVar()
    baudrate_var, data_bits_var = tk.IntVar(), tk.IntVar()
    parity_var, stop_bits_var = tk.StringVar(), tk.IntVar(value=1)
    auto_connect_var = tk.BooleanVar(value=True)

    image_file_var = tk.StringVar(value="No files selected")
    mode_var = tk.StringVar(value="resize")
    bg_color_var = tk.StringVar(value="Black")
    preview_mode_var = tk.StringVar(value="Color")
    dither_var = tk.BooleanVar(value=False)
    wrap_stx_etx_var = tk.BooleanVar(value=False)

    # --- Console helpers
    def clear_console():
        console.config(state='normal'); console.delete('1.0', tk.END); console.config(state='disabled')

    def log_message(message):
        console.config(state='normal')
        console.insert(tk.END, f"{datetime.now().strftime('[%H:%M:%S] ')}{message}\n")
        console.config(state='disabled'); console.see(tk.END)

    # --- Ports
    def list_serial_ports():
        ports = serial.tools.list_ports.comports()
        return [f"{port.device} - {port.description}" for port in ports]

    def refresh_ports():
        com_port_menu['values'] = list_serial_ports()
        log_message("Ports rafraîchis.")

    def toggle_manual_fields():
        state = 'disabled' if auto_connect_var.get() else 'readonly'
        baudrate_menu.configure(state=state)
        data_bits_menu.configure(state=state)
        parity_menu.configure(state=state)
        stop_bits_menu.configure(state=state)

    # --- Image & Preview
    def choose_image_file():
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All Files", "*.*")]
        )
        if file_path:
            image_file_var.set(file_path)
            log_message(f"Selected file: {file_path}")
            update_preview()

    def update_preview():
        if image_file_var.get() == "No files selected":
            blank = Image.new("RGB", (300, int(300 * TARGET_H / TARGET_W)), (255, 255, 255))
            photo = ImageTk.PhotoImage(blank)
            preview_label.config(image=photo); preview_label.image = photo
            return
        mode = mode_var.get()
        bg_color = minitel_color_names.get(bg_color_var.get(), (0, 0, 0)) if mode == "center" else (0, 0, 0)
        imgP = get_preview_image(image_file_var.get(), mode, bg_color, dither=dither_var.get())
        preview_img = imgP.convert("RGB")
        if preview_mode_var.get() == "Grayscale":
            preview_img = preview_img.convert("L").convert("RGB")
        max_width = 400
        avail_width = preview_frame.winfo_width() or max_width
        new_width = min(avail_width, max_width)
        new_height = int(new_width * TARGET_H / TARGET_W)
        preview_img = preview_img.resize((new_width, new_height), Image.NEAREST)
        photo = ImageTk.PhotoImage(preview_img)
        preview_label.config(image=photo); preview_label.image = photo

    # --- Génération & Envoi
    def build_stream():
        mode = mode_var.get()
        bg_color = minitel_color_names.get(bg_color_var.get(), (0, 0, 0)) if mode == "center" else (0, 0, 0)
        data_bytes = image_to_G1(image_file_var.get(), mode, bg_color, dither=dither_var.get())
        return data_bytes

    def save_vdt_file():
        if image_file_var.get() == "No files selected":
            messagebox.showwarning("No file", "Please select an image first.")
            return
        payload = build_stream()                   # image seule
        vdt = build_init_sequence() + payload      # init + image
        if wrap_stx_etx_var.get():
            vdt = b'\x02' + vdt + b'\x03'         # STX/ETX (optionnel)
        path = filedialog.asksaveasfilename(
            title="Exporter en .vdt",
            defaultextension=".vdt",
            filetypes=[("Videotex .vdt", "*.vdt"), ("Tous fichiers", "*.*")]
        )
        if not path:
            return
        with open(path, "wb") as f:
            f.write(vdt)
        log_message(f"Export VDT: {path} ({len(vdt)} octets)")

    def send_worker(selected_com, serial_kwargs, payload):
        try:
            with serial.Serial(port=selected_com, **serial_kwargs) as ser:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                # Initialisation écran (une seule fois)
                ser.write(build_init_sequence())
                # Envoi image
                t0 = time.time()
                ser.write(payload)
                ser.flush()
                dt = time.time() - t0
            log_message(f"Envoi terminé. Durée réelle: {dt:.2f}s")
        except serial.SerialException as e:
            log_message("Serial connection error: " + str(e))
        finally:
            send_btn.config(state="normal")
            vdt_btn.config(state="normal")

    def send_image_to_minitel():
        selected = com_port_var.get()
        selected_com = selected.split(" - ")[0] if selected else ""
        if not selected_com:
            log_message("Error: No COM port selected.")
            return
        if image_file_var.get() == "No files selected":
            log_message("Error: No image selected.")
            return

        # Auto-détect vitesse (NE CHANGE PAS 7E1/8N1 automatiquement)
        if auto_connect_var.get():
            model_detected, speed = detect_and_configure_minitel(selected_com)
            baudrate_var.set(speed)
            log_message(f"Auto-detection: {model_detected} à {speed} bps")

        payload = build_stream()
        size = len(payload)
        baud = baudrate_var.get()
        bits = 7 if data_bits_var.get() == 7 else 8
        parity = parity_var.get().lower()
        stop = stop_bits_var.get()
        t_est = size * 10 / max(baud, 1)
        log_message(f"Payload: {size} octets — Estimé: {t_est:.2f}s @ {baud} bps")

        serial_kwargs = dict(
            baudrate=baudrate_var.get(),
            bytesize=serial.SEVENBITS if bits == 7 else serial.EIGHTBITS,
            parity=serial.PARITY_EVEN if parity == "even" else serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE if stop == 1 else serial.STOPBITS_TWO,
            timeout=2
        )

        log_message(f"Connexion {selected_com} ({baud} bps, {bits} bits, parity={parity.upper()}, stop={stop})")
        send_btn.config(state="disabled"); vdt_btn.config(state="disabled")
        threading.Thread(target=send_worker, args=(selected_com, serial_kwargs, payload), daemon=True).start()

    # --- UI layout
    tk.Label(window, text="Image file:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    tk.Label(window, textvariable=image_file_var, anchor="w").grid(row=0, column=1, sticky="ew", padx=6, pady=4)
    tk.Button(window, text="Select file", command=choose_image_file).grid(row=0, column=2, sticky="ew", padx=6, pady=4)

    tk.Label(window, text="Resize mode:").grid(row=1, column=0, sticky="w", padx=6, pady=2)
    frame_mode = tk.Frame(window); frame_mode.grid(row=1, column=1, columnspan=2, sticky="w", padx=6, pady=2)
    tk.Radiobutton(frame_mode, text="Stretch (fill screen)", variable=mode_var, value="resize", command=update_preview).pack(side="left", padx=4)
    tk.Radiobutton(frame_mode, text="Crop and center", variable=mode_var, value="center", command=update_preview).pack(side="left", padx=12)

    tk.Label(window, text="Background color:").grid(row=2, column=0, sticky="w", padx=6, pady=2)
    bg_color_menu = ttk.Combobox(window, textvariable=bg_color_var, values=list(minitel_color_names.keys()), state='readonly')
    bg_color_menu.grid(row=2, column=1, columnspan=2, sticky="ew", padx=6, pady=2)

    tk.Label(window, text="Preview mode:").grid(row=3, column=0, sticky="w", padx=6, pady=2)
    frame_preview_mode = tk.Frame(window); frame_preview_mode.grid(row=3, column=1, columnspan=2, sticky="w", padx=6, pady=2)
    tk.Radiobutton(frame_preview_mode, text="Color", variable=preview_mode_var, value="Color", command=update_preview).pack(side="left", padx=4)
    tk.Radiobutton(frame_preview_mode, text="Grayscale", variable=preview_mode_var, value="Grayscale", command=update_preview).pack(side="left", padx=12)

    dither_cb = tk.Checkbutton(window, text="Dithering (Floyd–Steinberg)", variable=dither_var, command=update_preview)
    dither_cb.grid(row=4, column=0, columnspan=3, sticky="w", padx=6, pady=2)

    wrap_cb = tk.Checkbutton(window, text="Ajouter STX/ETX (pour certains lecteurs VDT)", variable=wrap_stx_etx_var)
    wrap_cb.grid(row=4, column=1, columnspan=2, sticky="w", padx=6, pady=2)

    preview_frame = tk.Frame(window, bd=2, relief="sunken", width=500, height=360)
    preview_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=6, pady=6)
    preview_frame.grid_propagate(False)
    preview_label = tk.Label(preview_frame); preview_label.grid(row=0, column=0, sticky="nsew")
    preview_frame.columnconfigure(0, weight=1); preview_frame.rowconfigure(0, weight=1)
    preview_frame.bind("<Configure>", lambda event: update_preview())

    # Connexion
    auto_checkbox = tk.Checkbutton(window, text="Auto-connection at maximum speed", variable=auto_connect_var, command=toggle_manual_fields)
    auto_checkbox.grid(row=6, column=0, columnspan=3, sticky="w", padx=6, pady=4)

    tk.Label(window, text="COM Port:").grid(row=7, column=0, sticky="w", padx=6, pady=2)
    com_port_menu = ttk.Combobox(window, textvariable=com_port_var, values=list_serial_ports(), state='readonly')
    com_port_menu.grid(row=7, column=1, sticky="ew", padx=6, pady=2)
    tk.Button(window, text="Refresh", command=refresh_ports).grid(row=7, column=2, sticky="ew", padx=6, pady=2)

    tk.Label(window, text="Baud Rate:").grid(row=8, column=0, sticky="w", padx=6, pady=2)
    baudrate_menu = ttk.Combobox(window, textvariable=baudrate_var, values=[1200, 4800, 9600], state='readonly')
    baudrate_menu.grid(row=8, column=1, columnspan=2, sticky="ew", padx=6, pady=2)

    tk.Label(window, text="Data Bits:").grid(row=9, column=0, sticky="w", padx=6, pady=2)
    data_bits_menu = ttk.Combobox(window, textvariable=data_bits_var, values=[7, 8], state='readonly')
    data_bits_menu.grid(row=9, column=1, columnspan=2, sticky="ew", padx=6, pady=2)

    tk.Label(window, text="Parity:").grid(row=10, column=0, sticky="w", padx=6, pady=2)
    parity_menu = ttk.Combobox(window, textvariable=parity_var, values=["None", "Even"], state='readonly')
    parity_menu.grid(row=10, column=1, columnspan=2, sticky="ew", padx=6, pady=2)

    tk.Label(window, text="Stop Bits:").grid(row=11, column=0, sticky="w", padx=6, pady=2)
    stop_bits_menu = ttk.Combobox(window, textvariable=stop_bits_var, values=[1, 2], state='readonly')
    stop_bits_menu.grid(row=11, column=1, columnspan=2, sticky="ew", padx=6, pady=2)

    # Actions
    btns = tk.Frame(window); btns.grid(row=12, column=0, columnspan=3, sticky="ew", padx=6, pady=6)
    send_btn = tk.Button(btns, text="Send image to Minitel", command=send_image_to_minitel)
    send_btn.pack(side="left", expand=True, fill="x", padx=4)
    vdt_btn = tk.Button(btns, text="Export .vdt (Videotex)", command=save_vdt_file)
    vdt_btn.pack(side="left", expand=True, fill="x", padx=4)
    clear_btn = tk.Button(btns, text="Clear log", command=clear_console)
    clear_btn.pack(side="left", padx=4)

    # Console
    console_frame = tk.Frame(window)
    console_frame.grid(row=13, column=0, columnspan=3, sticky="nsew", padx=6, pady=6)
    console = tk.Text(console_frame, height=8, state='disabled', wrap='word')
    console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    console_scrollbar = tk.Scrollbar(console_frame, command=console.yview)
    console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    console['yscrollcommand'] = console_scrollbar.set

    # Defaults
    baudrate_var.set(1200)
    data_bits_var.set(7)
    parity_var.set("Even")
    stop_bits_var.set(1)
    toggle_manual_fields()

    window.mainloop()

if __name__ == "__main__":
    open_gui()
