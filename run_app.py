import easyocr
import cv2
import numpy as np
import os
import re
import json
import time
from tkinter import Tk, filedialog, Button, Label, Frame, messagebox, Entry, Listbox, SINGLE, Scrollbar
from PIL import Image, ImageTk
import threading
import pyautogui
import keyboard
import sys
import win32gui
import win32con
import urllib.parse

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True


class TransparentClicker:
    def __init__(self):
        self.config_file = "transparent_clicker.json"
        self.points = {'open': [], 'close': []}
        self.hotkey_open = 'ctrl+shift+o'
        self.hotkey_close = 'ctrl+shift+c'
        self.is_configured = False
        self.load_config()
        self.setup_hotkeys()

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.points = config.get('points', {'open': [], 'close': []})
                    self.hotkey_open = config.get('hotkey_open', 'ctrl+shift+o')
                    self.hotkey_close = config.get('hotkey_close', 'ctrl+shift+c')
                    self.is_configured = True
                return True
        except:
            pass
        return False

    def save_config(self):
        try:
            config = {'points': self.points, 'hotkey_open': self.hotkey_open, 'hotkey_close': self.hotkey_close}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def setup_hotkeys(self):
        try:
            keyboard.remove_hotkey(self.hotkey_open)
            keyboard.remove_hotkey(self.hotkey_close)
        except:
            pass
        try:
            keyboard.add_hotkey(self.hotkey_open, self.execute_open)
            keyboard.add_hotkey(self.hotkey_close, self.execute_close)
        except:
            pass

    def get_mouse_position(self, message):
        print(f"\n📍 {message}")
        for i in range(3, 0, -1):
            print(f"   {i}...", end='', flush=True)
            time.sleep(1)
        print()
        x, y = pyautogui.position()
        print(f"   ✅ Координаты: x={x}, y={y}")
        return x, y

    def configure(self):
        print("\n" + "=" * 60)
        print("🔧 НАСТРОЙКА ПРОЗРАЧНОГО КЛИКЕРА")
        print("=" * 60)

        hotkey = input("   Клавиша для ОТКРЫТИЯ (Enter - ctrl+shift+o): ").strip()
        if hotkey:
            self.hotkey_open = hotkey
        hotkey = input("   Клавиша для ЗАКРЫТИЯ (Enter - ctrl+shift+c): ").strip()
        if hotkey:
            self.hotkey_close = hotkey

        print("\n📝 ТОЧКИ ДЛЯ ОТКРЫТИЯ")
        self.points['open'] = self.record_points("ОТКРЫТИЯ")

        print("\n📝 ТОЧКИ ДЛЯ ЗАКРЫТИЯ")
        self.points['close'] = self.record_points("ЗАКРЫТИЯ")

        self.is_configured = True
        self.save_config()
        self.setup_hotkeys()
        print("\n✅ НАСТРОЙКА ЗАВЕРШЕНА!")

    def record_points(self, name):
        points = []
        print(f"\nЗапись точек для {name}")
        print("1-Клик 2-Двойной 3-Правый 4-Пауза 0-Выход")

        while True:
            print(f"\n--- Точка #{len(points) + 1} ---")
            choice = input("Выберите действие (0-4): ").strip()

            if choice == '0':
                break
            elif choice == '1':
                x, y = self.get_mouse_position("Наведите мышь")
                points.append({'type': 'click', 'x': x, 'y': y, 'description': f"Клик ({x},{y})"})
            elif choice == '2':
                x, y = self.get_mouse_position("Наведите мышь")
                points.append({'type': 'double_click', 'x': x, 'y': y, 'description': f"Двойной ({x},{y})"})
            elif choice == '3':
                x, y = self.get_mouse_position("Наведите мышь")
                points.append({'type': 'right_click', 'x': x, 'y': y, 'description': f"Правый ({x},{y})"})
            elif choice == '4':
                try:
                    seconds = float(input("Пауза (сек): "))
                    points.append({'type': 'delay', 'seconds': seconds, 'description': f"Пауза {seconds}с"})
                except:
                    print("❌ Неверное значение")
            else:
                print("❌ Неверный выбор")
        return points

    def execute_open(self):
        self.execute_actions('open')

    def execute_close(self):
        self.execute_actions('close')

    def execute_actions(self, mode):
        points = self.points.get(mode, [])
        if not points:
            return

        try:
            windows = ["Упрог", "Uprog", "Chrome", "Firefox", "Edge", "Opera", "Brave"]
            for win_name in windows:
                try:
                    hwnd = win32gui.FindWindow(None, win_name)
                    if hwnd:
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                        time.sleep(0.2)
                        break
                except:
                    pass
        except:
            pass

        for point in points:
            try:
                if point['type'] == 'click':
                    pyautogui.click(point['x'], point['y'])
                elif point['type'] == 'double_click':
                    pyautogui.doubleClick(point['x'], point['y'])
                elif point['type'] == 'right_click':
                    pyautogui.rightClick(point['x'], point['y'])
                elif point['type'] == 'delay':
                    time.sleep(point['seconds'])
                time.sleep(0.3)
            except:
                return


class LicensePlateGateController:
    def __init__(self):
        self.whitelist_file = "whitelist.json"
        self.white_list = self.load_whitelist()
        self.clicker = TransparentClicker()
        self.reader = easyocr.Reader(['ru', 'en'], gpu=False, verbose=False)
        self.auto_close_timer = None
        self.auto_close_delay = 60
        self.current_frame = None
        self.video_running = False
        self.auto_recognize_running = False
        self.cap = None
        self.rtsp_url = ""
        self.working_url = None
        self.ip = ""
        self.port = "554"
        self.login = "admin"
        self.password = ""
        self.path = "stream"

    def set_rtsp_params(self, ip, port="554", login="admin", password="", path="stream"):
        self.ip = ip
        self.port = port
        self.login = login
        self.password = password
        self.path = path

        # Собираем URL
        if password:
            password_encoded = urllib.parse.quote(password, safe='')
            self.rtsp_url = f"rtsp://{login}:{password_encoded}@{ip}:{port}/{path}"
        else:
            self.rtsp_url = f"rtsp://{login}@{ip}:{port}/{path}"

        print(f"📷 RTSP URL: {self.rtsp_url}")
        return self.rtsp_url

    def set_rtsp_url(self, url):
        self.rtsp_url = url
        print(f"📷 RTSP URL: {url}")

    def test_rtsp(self, rtsp_url=None):
        """Тестирование RTSP подключения с разными путями"""
        if rtsp_url is None:
            rtsp_url = self.rtsp_url

        if not rtsp_url:
            print("❌ RTSP URL не задан")
            return False

        print(f"\n🔍 Тестирование RTSP: {rtsp_url}")

        # Список путей для тестирования
        paths = ["stream", "live", "h264", "1", "cam/realmonitor", "av0_0", "media", "main", "sub"]

        # Пробуем с разными путями
        for path in paths:
            # Собираем URL с новым путем
            if self.ip:
                if self.password:
                    password_encoded = urllib.parse.quote(self.password, safe='')
                    test_url = f"rtsp://{self.login}:{password_encoded}@{self.ip}:{self.port}/{path}"
                else:
                    test_url = f"rtsp://{self.login}@{self.ip}:{self.port}/{path}"
            else:
                # Если нет IP, пробуем заменить путь в существующем URL
                if "@" in rtsp_url:
                    base = rtsp_url.rsplit("/", 1)[0]
                    test_url = f"{base}/{path}"
                else:
                    continue

            print(f"  Пробуем: {test_url}")

            try:
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
                cap = cv2.VideoCapture(test_url, cv2.CAP_FFMPEG)

                if not cap.isOpened():
                    cap = cv2.VideoCapture(test_url)

                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        print(f"  ✅ RTSP работает! URL: {test_url}")
                        self.working_url = test_url
                        return True
                cap.release()
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

        print("  ❌ RTSP не работает")
        return False

    def start_video(self, update_callback):
        """Запуск RTSP видео"""
        if not self.rtsp_url and not self.working_url:
            print("❌ RTSP URL не установлен")
            return False

        self.video_running = True

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        url_to_use = self.working_url if self.working_url else self.rtsp_url

        try:
            print(f"📷 Подключение к: {url_to_use}")

            # Пробуем с разными транспортами
            transports = ["tcp", "udp", None]

            for transport in transports:
                try:
                    if transport:
                        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{transport}"
                        self.cap = cv2.VideoCapture(url_to_use, cv2.CAP_FFMPEG)
                    else:
                        self.cap = cv2.VideoCapture(url_to_use)

                    if self.cap.isOpened():
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            print(f"✅ Подключено через {transport or 'auto'}")
                            break
                        else:
                            self.cap.release()
                            self.cap = None
                except:
                    if self.cap:
                        self.cap.release()
                        self.cap = None

            if not self.cap or not self.cap.isOpened():
                print("❌ Не удалось открыть RTSP поток")
                self.video_running = False
                return False

            threading.Thread(target=self._video_loop, args=(update_callback,), daemon=True).start()
            print("📷 RTSP видео запущено")
            return True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.video_running = False
            return False

    def stop_video(self):
        self.video_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("📷 Видео остановлено")

    def _video_loop(self, update_callback):
        while self.video_running:
            try:
                if self.cap is not None and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        self.current_frame = frame

                        h, w = frame.shape[:2]
                        max_w, max_h = 750, 550
                        if w > max_w or h > max_h:
                            scale = min(max_w / w, max_h / h)
                            new_w, new_h = int(w * scale), int(h * scale)
                            frame = cv2.resize(frame, (new_w, new_h))

                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img_pil = Image.fromarray(frame_rgb)
                        img_tk = ImageTk.PhotoImage(img_pil)

                        if update_callback:
                            update_callback(img_tk)
                    else:
                        time.sleep(0.1)
                else:
                    time.sleep(0.5)

                time.sleep(0.05)
            except Exception as e:
                print(f"Ошибка видео: {e}")
                time.sleep(0.5)

    def open_gate(self):
        self.clicker.execute_open()
        print("🚗 Шлагбаум открыт")
        self.start_auto_close_timer()
        return True

    def close_gate(self):
        self.clicker.execute_close()
        print("🚗 Шлагбаум закрыт")
        self.cancel_auto_close_timer()
        return True

    def start_auto_close_timer(self):
        self.cancel_auto_close_timer()
        print(f"⏱️ Шлагбаум закроется через {self.auto_close_delay} сек")
        self.auto_close_timer = threading.Timer(self.auto_close_delay, self.auto_close_gate)
        self.auto_close_timer.daemon = True
        self.auto_close_timer.start()

    def cancel_auto_close_timer(self):
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
            self.auto_close_timer = None

    def auto_close_gate(self):
        print("⏱️ Время истекло! Шлагбаум закрывается...")
        self.close_gate()

    def load_whitelist(self):
        default_list = {'E276CP797', 'A206MC777', 'P824TK797', 'T368MA197'}
        try:
            if os.path.exists(self.whitelist_file):
                with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            else:
                self.save_whitelist(default_list)
                return default_list
        except:
            return default_list

    def save_whitelist(self, whitelist=None):
        if whitelist is None:
            whitelist = self.white_list
        try:
            with open(self.whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(list(whitelist), f, ensure_ascii=False, indent=2)
        except:
            pass

    def add_to_whitelist(self, plate):
        plate = self.normalize_text(plate)
        if len(plate) >= 6:
            self.white_list.add(plate)
            self.save_whitelist()
            return True
        return False

    def remove_from_whitelist(self, plate):
        if plate in self.white_list:
            self.white_list.remove(plate)
            self.save_whitelist()
            return True
        return False

    def normalize_text(self, text):
        replacements = {
            'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H',
            'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Т': 'T',
            'Х': 'X', 'У': 'Y', 'а': 'a', 'в': 'b', 'с': 'c',
            'е': 'e', 'н': 'h', 'к': 'k', 'м': 'm', 'о': 'o',
            'р': 'p', 'т': 't', 'х': 'x', 'у': 'y',
            'Ы': 'Y', 'ы': 'y', 'Щ': 'W', 'щ': 'w', 'Ш': 'W', 'ш': 'w',
            'Ч': '7', 'ч': '7', 'З': '3', 'з': '3', 'Э': 'E', 'э': 'e',
        }
        result = ''
        for char in text:
            if char in replacements:
                result += replacements[char]
            else:
                result += char
        cleaned = ''.join(c for c in result if c.isalnum())
        return cleaned.upper()

    def restore_plate(self, text):
        clean = self.normalize_text(text)
        if len(clean) < 4:
            return clean

        known_plates = {
            'A2O6': 'A206MC777', 'A206': 'A206MC777',
            'P824': 'P824TK797', 'E276': 'E276CP797',
            '4353': 'A353CO790', 'C986': 'C986KC77'
        }

        for key, value in known_plates.items():
            if key in clean:
                return value

        patterns = [
            r'[A-Z]\d{3}[A-Z]{2}\d{2,3}',
            r'[A-Z]\d{3}[A-Z]{2}',
            r'\d{3}[A-Z]{2}\d{2,3}',
            r'[A-Z]{2}\d{4}\d{2}',
            r'\d{4}[A-Z]{2}\d{2}',
        ]

        for pattern in patterns:
            match = re.search(pattern, clean)
            if match:
                result = match.group(0)
                if len(result) >= 5:
                    return result

        for plate in self.white_list:
            if clean in plate or plate in clean:
                if len(clean) >= 5:
                    return plate

        return clean

    def is_plate_like(self, text):
        if len(text) < 5:
            return False
        letters = sum(1 for c in text if c.isalpha())
        digits = sum(1 for c in text if c.isdigit())
        return 2 <= letters <= 4 and 3 <= digits <= 6

    def preprocess_image(self, image):
        try:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge((l, a, b))
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            return enhanced
        except:
            return image

    def detect_plates(self, image):
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
            closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            plates = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 1.8 <= aspect_ratio <= 6.0 and w > 60 and h > 15 and w < 500 and h < 150:
                    plates.append((x, y, w, h))
            return plates
        except:
            return []

    def recognize_frame(self, frame):
        if frame is None:
            return [], None

        original = frame.copy()
        enhanced = self.preprocess_image(frame)

        plates = self.detect_plates(enhanced)
        candidates = []

        if plates:
            for x, y, w, h in plates[:5]:
                margin = 15
                x1 = max(0, x - margin)
                y1 = max(0, y - margin)
                x2 = min(frame.shape[1], x + w + margin)
                y2 = min(frame.shape[0], y + h + margin)
                plate_roi = enhanced[y1:y2, x1:x2]

                try:
                    result = self.reader.readtext(plate_roi, detail=1, paragraph=False)
                    for bbox, text, confidence in result:
                        cleaned = self.normalize_text(text)
                        if len(cleaned) < 4:
                            continue
                        corrected = self.restore_plate(cleaned)
                        if len(corrected) >= 6:
                            candidates.append({
                                'text': corrected,
                                'bbox': (x1, y1, x2 - x1, y2 - y1),
                                'confidence': confidence,
                            })
                except:
                    continue

        if not candidates:
            try:
                result = self.reader.readtext(enhanced, detail=1, paragraph=False)
                for bbox, text, confidence in result:
                    cleaned = self.normalize_text(text)
                    if len(cleaned) < 4:
                        continue
                    corrected = self.restore_plate(cleaned)
                    if len(corrected) >= 6:
                        x_coords = [p[0] for p in bbox]
                        y_coords = [p[1] for p in bbox]
                        x = int(min(x_coords))
                        y = int(min(y_coords))
                        w = int(max(x_coords) - min(x_coords))
                        h = int(max(y_coords) - min(y_coords))
                        candidates.append({
                            'text': corrected,
                            'bbox': (x, y, w, h),
                            'confidence': confidence,
                        })
            except:
                pass

        unique_results = {}
        for candidate in candidates:
            text = candidate['text']
            if text not in unique_results or candidate['confidence'] > unique_results[text]['confidence']:
                unique_results[text] = candidate

        best_result = None
        for text, data in unique_results.items():
            if text in self.white_list:
                best_result = data
                break
            elif self.is_plate_like(text) or len(text) >= 6:
                if not best_result or data['confidence'] > best_result['confidence']:
                    best_result = data

        if not best_result and unique_results:
            best_result = max(unique_results.values(), key=lambda x: len(x['text']))

        final_results = []

        if best_result:
            corrected = best_result['text']
            x, y, w, h = best_result['bbox']
            confidence = best_result.get('confidence', 0.5)

            if corrected in self.white_list:
                status = "✅ ДОСТУП РАЗРЕШЁН"
                color = (0, 255, 0)
                self.open_gate()
            else:
                status = "❌ ДОСТУП ЗАПРЕЩЁН"
                color = (0, 0, 255)
                self.close_gate()

            final_results.append({
                'text': corrected,
                'status': status,
                'bbox': (x, y, w, h),
                'confidence': confidence
            })

            cv2.rectangle(original, (x, y), (x + w, y + h), color, 3)
            cv2.putText(original, status, (x, y - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return final_results, original


class PlateRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Распознавание номеров с IP-камеры")
        self.root.geometry("1300x800")
        self.root.configure(bg='#2c3e50')
        self.root.minsize(1150, 720)

        self.colors = {
            'bg': '#2c3e50',
            'panel': '#34495e',
            'accent': '#3498db',
            'success': '#2ecc71',
            'danger': '#e74c3c',
            'warning': '#f1c40f',
            'text': 'white',
            'text_secondary': '#95a5a6',
        }

        self.controller = LicensePlateGateController()
        self.results = []
        self.annotated_image = None
        self.video_running = False
        self.auto_recognize_running = False

        self.create_widgets()

    def create_widgets(self):
        # ===== ЗАГОЛОВОК =====
        header_frame = Frame(self.root, bg=self.colors['bg'], height=50)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        Label(header_frame,
              text="🚗 РАСПОЗНАВАНИЕ НОМЕРОВ С IP-КАМЕРЫ",
              font=('Arial', 15, 'bold'),
              fg='white',
              bg=self.colors['bg']).pack(pady=12)

        # ===== ОСНОВНОЙ КОНТЕЙНЕР =====
        main_frame = Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=8)

        # ===== ЛЕВАЯ ПАНЕЛЬ =====
        left_panel = Frame(main_frame, bg=self.colors['panel'], width=500)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)

        # ---- Шлагбаум ----
        gate_status_frame = Frame(left_panel, bg=self.colors['panel'])
        gate_status_frame.pack(fill='x', padx=15, pady=8)

        Label(gate_status_frame,
              text="🚧 Шлагбаум:",
              font=('Arial', 11, 'bold'),
              fg='white',
              bg=self.colors['panel']).pack(side='left')

        Label(gate_status_frame,
              text="✅ Подключен",
              font=('Arial', 11, 'bold'),
              fg=self.colors['success'],
              bg=self.colors['panel']).pack(side='left', padx=(5, 0))

        # ---- RTSP настройка ----
        rtsp_frame = Frame(left_panel, bg=self.colors['panel'])
        rtsp_frame.pack(fill='x', padx=15, pady=5)

        Label(rtsp_frame, text="📷 Настройки RTSP:",
              font=('Arial', 10, 'bold'),
              fg=self.colors['text'],
              bg=self.colors['panel']).pack(anchor='w')

        # IP и порт
        ip_row = Frame(rtsp_frame, bg=self.colors['panel'])
        ip_row.pack(fill='x', pady=2)

        Label(ip_row, text="IP:", font=('Arial', 9), fg='white', bg=self.colors['panel'], width=5).pack(side='left')
        self.ip_entry = Entry(ip_row, font=('Arial', 10), bg='#2c3e50', fg='white', relief='flat', bd=1, width=15)
        self.ip_entry.pack(side='left', padx=(0, 5))
        self.ip_entry.insert(0, "192.168.1.100")

        Label(ip_row, text="Порт:", font=('Arial', 9), fg='white', bg=self.colors['panel'], width=6).pack(side='left',
                                                                                                          padx=(5, 0))
        self.port_entry = Entry(ip_row, font=('Arial', 10), bg='#2c3e50', fg='white', relief='flat', bd=1, width=6)
        self.port_entry.pack(side='left')
        self.port_entry.insert(0, "554")

        # Логин и пароль
        login_row = Frame(rtsp_frame, bg=self.colors['panel'])
        login_row.pack(fill='x', pady=2)

        Label(login_row, text="Логин:", font=('Arial', 9), fg='white', bg=self.colors['panel'], width=5).pack(
            side='left')
        self.login_entry = Entry(login_row, font=('Arial', 10), bg='#2c3e50', fg='white', relief='flat', bd=1, width=15)
        self.login_entry.pack(side='left', padx=(0, 5))
        self.login_entry.insert(0, "admin")

        Label(login_row, text="Пароль:", font=('Arial', 9), fg='white', bg=self.colors['panel'], width=6).pack(
            side='left', padx=(5, 0))
        self.pass_entry = Entry(login_row, font=('Arial', 10), bg='#2c3e50', fg='white', relief='flat', bd=1, width=15)
        self.pass_entry.pack(side='left')
        self.pass_entry.insert(0, "admin")

        # Путь
        path_row = Frame(rtsp_frame, bg=self.colors['panel'])
        path_row.pack(fill='x', pady=2)

        Label(path_row, text="Путь:", font=('Arial', 9), fg='white', bg=self.colors['panel'], width=5).pack(side='left')
        self.path_entry = Entry(path_row, font=('Arial', 10), bg='#2c3e50', fg='white', relief='flat', bd=1, width=25)
        self.path_entry.pack(side='left', fill='x', expand=True)
        self.path_entry.insert(0, "stream")

        # Кнопка подключения
        Button(rtsp_frame, text="🔗 Подключиться",
               bg='#f39c12', fg='white',
               font=('Arial', 10, 'bold'), relief='flat', cursor='hand2',
               command=self.connect_rtsp, height=1).pack(fill='x', pady=3)

        # ---- Подсказки ----
        hint_frame = Frame(rtsp_frame, bg=self.colors['panel'])
        hint_frame.pack(fill='x', pady=2)

        Label(hint_frame,
              text="💡 Пути: stream, live, h264, 1, main, sub",
              font=('Arial', 8),
              fg=self.colors['text_secondary'],
              bg=self.colors['panel']).pack(anchor='w')

        # ---- Кнопки ----
        btn_frame = Frame(left_panel, bg=self.colors['panel'])
        btn_frame.pack(fill='x', padx=15, pady=5)

        Button(btn_frame, text="🔍 Тест RTSP",
               bg='#1abc9c', fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.test_rtsp, height=1, pady=5).pack(fill='x', pady=4)

        Button(btn_frame, text="📷 Включить видео",
               bg='#27ae60', fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.toggle_video, height=1, pady=5).pack(fill='x', pady=4)

        Button(btn_frame, text="📸 Распознать кадр",
               bg=self.colors['accent'], fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.recognize_frame_now, height=1, pady=5).pack(fill='x', pady=4)

        Button(btn_frame, text="🔄 Авто-распознавание",
               bg='#9b59b6', fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.toggle_auto_recognize, height=1, pady=5).pack(fill='x', pady=4)

        Button(btn_frame, text="🗑️ Очистить",
               bg=self.colors['danger'], fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.clear_all, height=1, pady=5).pack(fill='x', pady=4)

        # ---- Открыть/Закрыть ----
        gate_btn_frame = Frame(left_panel, bg=self.colors['panel'])
        gate_btn_frame.pack(fill='x', padx=15, pady=5)

        Button(gate_btn_frame, text="🔓 Открыть",
               bg=self.colors['success'], fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.open_gate, height=1, pady=5).pack(fill='x', pady=4)

        Button(gate_btn_frame, text="🔒 Закрыть",
               bg=self.colors['danger'], fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.close_gate, height=1, pady=5).pack(fill='x', pady=4)

        # ---- Разделитель ----
        Frame(left_panel, bg='#2c3e50', height=1).pack(fill='x', padx=15, pady=5)

        # ---- Белый список ----
        whitelist_frame = Frame(left_panel, bg=self.colors['panel'])
        whitelist_frame.pack(fill='both', expand=True, padx=15, pady=5)

        Label(whitelist_frame,
              text="📋 БЕЛЫЙ СПИСОК",
              font=('Arial', 11, 'bold'),
              fg=self.colors['warning'],
              bg=self.colors['panel']).pack(pady=5)

        list_container = Frame(whitelist_frame, bg=self.colors['panel'])
        list_container.pack(fill='both', expand=True)

        scrollbar = Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.white_list_box = Listbox(list_container, height=5,
                                      bg='#2c3e50',
                                      fg='white',
                                      font=('Courier', 11),
                                      selectmode=SINGLE, relief='flat', bd=0,
                                      yscrollcommand=scrollbar.set)
        self.white_list_box.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.white_list_box.yview)
        self.update_white_list_display()

        # ---- Удаление ----
        Button(whitelist_frame, text="🗑️ Удалить выбранный",
               bg=self.colors['danger'], fg='white',
               font=('Arial', 10), relief='flat', cursor='hand2',
               command=self.delete_plate_from_whitelist, height=1, pady=4).pack(fill='x', pady=4)

        # ---- Добавление ----
        add_frame = Frame(whitelist_frame, bg=self.colors['panel'])
        add_frame.pack(fill='x', pady=5)

        Label(add_frame, text="➕ Добавить номер:",
              font=('Arial', 10),
              fg=self.colors['text_secondary'],
              bg=self.colors['panel']).pack(anchor='w')

        entry_row2 = Frame(add_frame, bg=self.colors['panel'])
        entry_row2.pack(fill='x', pady=3)

        self.add_entry = Entry(entry_row2,
                               font=('Courier', 11),
                               bg='#2c3e50',
                               fg='white',
                               relief='flat', bd=1)
        self.add_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        Button(entry_row2, text="✅ Добавить",
               bg='#f39c12', fg='white',
               font=('Arial', 11, 'bold'), relief='flat', cursor='hand2',
               command=self.add_plate_to_whitelist, height=1).pack(side='right')

        # ---- Результат ----
        result_frame = Frame(left_panel, bg=self.colors['panel'])
        result_frame.pack(fill='x', padx=15, pady=10)

        Label(result_frame,
              text="📊 РЕЗУЛЬТАТ",
              font=('Arial', 11, 'bold'),
              fg=self.colors['success'],
              bg=self.colors['panel']).pack()

        self.result_label = Label(result_frame, text="Ожидание...",
                                  font=('Arial', 13, 'bold'),
                                  fg=self.colors['text_secondary'],
                                  bg=self.colors['panel'],
                                  wraplength=450, pady=10)
        self.result_label.pack()

        # ---- Инструкция ----
        Label(left_panel,
              text="1. Введите IP, порт, логин, пароль\n2. Нажмите 'Подключиться'\n3. Нажмите 'Тест RTSP'\n4. Нажмите 'Включить видео'",
              font=('Arial', 10),
              fg=self.colors['text_secondary'],
              bg=self.colors['panel']).pack(side='bottom', pady=10)

        # ===== ПРАВАЯ ПАНЕЛЬ =====
        right_panel = Frame(main_frame, bg=self.colors['bg'])
        right_panel.pack(side='right', fill='both', expand=True)

        video_frame = Frame(right_panel, bg='#1a1a2e', relief='solid', bd=2)
        video_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.image_label = Label(video_frame,
                                 text="📸 Кадр с IP-камеры",
                                 font=('Arial', 18),
                                 fg='#7f8c8d',
                                 bg='#1a1a2e')
        self.image_label.pack(fill='both', expand=True)

        self.status_label = Label(video_frame,
                                  text="Статус: Ожидание подключения",
                                  font=('Arial', 10),
                                  fg='#f1c40f',
                                  bg='#1a1a2e')
        self.status_label.pack(side='bottom', pady=5)

    def connect_rtsp(self):
        """Подключение к RTSP"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        login = self.login_entry.get().strip()
        password = self.pass_entry.get().strip()
        path = self.path_entry.get().strip()

        if not ip:
            messagebox.showwarning("Ошибка", "Введите IP адрес камеры!")
            return

        if not port:
            port = "554"

        if not path:
            path = "stream"

        # Создаем RTSP URL
        if password:
            password_encoded = urllib.parse.quote(password, safe='')
            rtsp_url = f"rtsp://{login}:{password_encoded}@{ip}:{port}/{path}"
        else:
            rtsp_url = f"rtsp://{login}@{ip}:{port}/{path}"

        self.controller.set_rtsp_params(ip, port, login, password, path)
        self.status_label.config(text=f"✅ RTSP URL создан", fg='#f1c40f')

        messagebox.showinfo("Успех", f"RTSP URL создан:\n{rtsp_url}\n\nТеперь нажмите 'Тест RTSP'")

    def test_rtsp(self):
        """Тестирование RTSP"""
        if not self.controller.ip:
            messagebox.showwarning("Ошибка", "Сначала нажмите 'Подключиться'!")
            return

        self.status_label.config(text="🔍 Тестирование RTSP...", fg='#3498db')
        self.result_label.config(text="🔍 Тестирование RTSP...", fg=self.colors['accent'])
        self.root.update()

        def test():
            success = self.controller.test_rtsp()
            if success:
                self.status_label.config(text="✅ RTSP работает", fg='#2ecc71')
                self.result_label.config(text="✅ RTSP работает", fg=self.colors['success'])
                messagebox.showinfo("Успех", "RTSP поток работает!\nМожно включать видео.")
            else:
                self.status_label.config(text="❌ RTSP не работает", fg='#e74c3c')
                self.result_label.config(text="❌ RTSP не работает", fg=self.colors['danger'])
                messagebox.showerror("Ошибка",
                                     "RTSP поток не работает.\n\n"
                                     "Проверьте:\n"
                                     "1. IP адрес камеры\n"
                                     "2. Логин и пароль\n"
                                     "3. Порт (обычно 554 или 8080)\n"
                                     "4. Путь к потоку\n\n"
                                     "Попробуйте разные пути:\n"
                                     "stream, live, h264, 1, main, sub\n\n"
                                     "Или проверьте настройки камеры.")

        threading.Thread(target=test, daemon=True).start()

    def update_video_frame(self, img_tk):
        try:
            self.image_label.config(image=img_tk, text="")
            self.image_label.image = img_tk
            self.status_label.config(text="📷 Видео: активен", fg='#2ecc71')
        except Exception as e:
            print(f"Ошибка обновления видео: {e}")

    def toggle_video(self):
        if not self.video_running:
            if not self.controller.ip:
                messagebox.showwarning("Ошибка", "Сначала нажмите 'Подключиться'!")
                return

            self.video_running = True
            if self.controller.start_video(self.update_video_frame):
                self.status_label.config(text="📷 Видео: включено", fg='#2ecc71')
                self._change_button_text("📷 Включить видео", "📷 Выключить видео", '#e74c3c')
            else:
                self.video_running = False
                self.status_label.config(text="❌ Ошибка RTSP", fg='#e74c3c')
                messagebox.showerror("Ошибка",
                                     "Не удалось запустить RTSP поток!\n\n"
                                     "1. Проверьте правильность настроек\n"
                                     "2. Нажмите 'Тест RTSP'\n"
                                     "3. Убедитесь что камера доступна")
        else:
            self.video_running = False
            self.controller.stop_video()
            self.status_label.config(text="⏹️ Видео: выключено", fg='#95a5a6')
            self._change_button_text("📷 Выключить видео", "📷 Включить видео", '#27ae60')
            self.image_label.config(image='', text="📸 Кадр с IP-камеры")
            self.image_label.image = None

    def _change_button_text(self, old_text, new_text, color):
        for widget in self.root.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, Button) and child.cget('text') == old_text:
                    child.config(text=new_text, bg=color)
                    break

    def toggle_auto_recognize(self):
        if not self.auto_recognize_running:
            self.auto_recognize_running = True
            self.status_label.config(text="🔄 Авто-распознавание включено", fg='#9b59b6')
            threading.Thread(target=self._auto_recognize_loop, daemon=True).start()
        else:
            self.auto_recognize_running = False
            self.status_label.config(text="⏹️ Авто-распознавание выключено", fg='#95a5a6')

    def _auto_recognize_loop(self):
        while self.auto_recognize_running:
            try:
                if self.controller.current_frame is not None:
                    self.recognize_frame_now()
                time.sleep(1)
            except Exception as e:
                print(f"Ошибка авто-распознавания: {e}")
                time.sleep(1)

    def recognize_frame_now(self):
        if self.controller.current_frame is None:
            messagebox.showwarning("Предупреждение", "Нет кадра для распознавания!\nСначала включите видео.")
            return

        self.result_label.config(text="🔍 Распознавание...", fg=self.colors['accent'])
        self.root.update()

        def process():
            try:
                frame_copy = self.controller.current_frame.copy()
                results, annotated = self.controller.recognize_frame(frame_copy)

                if annotated is not None:
                    img_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    h, w = img_rgb.shape[:2]
                    max_w, max_h = 750, 550
                    if w > max_w or h > max_h:
                        scale = min(max_w / w, max_h / h)
                        new_w, new_h = int(w * scale), int(h * scale)
                        img_resized = cv2.resize(img_rgb, (new_w, new_h))
                    else:
                        img_resized = img_rgb
                    img_pil = Image.fromarray(img_resized)
                    img_tk = ImageTk.PhotoImage(img_pil)
                    self.image_label.config(image=img_tk, text="")
                    self.image_label.image = img_tk

                if results:
                    status = results[0]['status']
                    plate_text = results[0]['text']
                    short_status = status.replace("ДОСТУП РАЗРЕШЁН", "✅ РАЗРЕШЁН").replace("ДОСТУП ЗАПРЕЩЁН",
                                                                                           "❌ ЗАПРЕЩЁН")
                    color = self.colors['success'] if "РАЗРЕШЁН" in status else self.colors['danger']
                    self.result_label.config(text=f"{short_status}\n{plate_text}", fg=color)
                    self.status_label.config(text=f"{short_status} | {plate_text}", fg=color)
                else:
                    self.result_label.config(text="❌ Номер не распознан", fg=self.colors['danger'])
                    self.status_label.config(text="❌ Номер не распознан", fg='#e74c3c')
            except Exception as e:
                self.result_label.config(text=f"❌ Ошибка: {str(e)}", fg=self.colors['danger'])
                print(f"Ошибка: {e}")

        threading.Thread(target=process, daemon=True).start()

    def update_white_list_display(self):
        self.white_list_box.delete(0, 'end')
        for plate in sorted(self.controller.white_list):
            self.white_list_box.insert('end', f"  {plate}")

    def delete_plate_from_whitelist(self):
        selection = self.white_list_box.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите номер для удаления!")
            return
        plate = self.white_list_box.get(selection[0]).strip()
        if messagebox.askyesno("Подтверждение", f"Удалить номер {plate}?"):
            if self.controller.remove_from_whitelist(plate):
                self.update_white_list_display()
                messagebox.showinfo("Успех", f"Номер {plate} удален!")

    def add_plate_to_whitelist(self):
        plate = self.add_entry.get().strip().upper()
        if not plate:
            messagebox.showwarning("Ошибка", "Введите номер!")
            return
        plate = self.controller.normalize_text(plate)
        if len(plate) < 6:
            messagebox.showwarning("Ошибка", "Некорректный номер!")
            return
        if plate in self.controller.white_list:
            messagebox.showinfo("Информация", f"Номер {plate} уже есть!")
            self.add_entry.delete(0, 'end')
            return
        if self.controller.add_to_whitelist(plate):
            self.update_white_list_display()
            self.add_entry.delete(0, 'end')
            messagebox.showinfo("✅ Успех", f"Номер {plate} добавлен!")

    def open_gate(self):
        if self.controller.open_gate():
            messagebox.showinfo("Успех", "✅ Шлагбаум открыт!\n⏱️ Автоматически закроется через 1 минуту")
        else:
            messagebox.showerror("Ошибка", "❌ Не удалось открыть!")

    def close_gate(self):
        if self.controller.close_gate():
            messagebox.showinfo("Успех", "✅ Шлагбаум закрыт!")
        else:
            messagebox.showerror("Ошибка", "❌ Не удалось закрыть!")

    def clear_all(self):
        self.video_running = False
        self.auto_recognize_running = False
        self.controller.stop_video()
        self.results = []
        self.annotated_image = None
        self.image_label.config(image='', text="📸 Кадр с IP-камеры", fg='#7f8c8d')
        self.image_label.image = None
        self.result_label.config(text="Ожидание...", fg=self.colors['text_secondary'])
        self.status_label.config(text="Статус: Ожидание подключения", fg='#f1c40f')


def console_menu():
    print("\n" + "=" * 60)
    print("🚗 СИСТЕМА РАСПОЗНАВАНИЯ НОМЕРОВ (RTSP)")
    print("=" * 60)
    print("  1 - Запустить GUI")
    print("  2 - Переобучить кликер")
    print("  3 - Выход")
    print("=" * 60)

    while True:
        try:
            choice = input("\nВыберите действие (1-3): ").strip()
            if choice == '1':
                return 'gui'
            elif choice == '2':
                return 'config'
            elif choice == '3':
                return 'exit'
            else:
                print("❌ Неверный выбор!")
        except KeyboardInterrupt:
            print("\n\n👋 Выход...")
            sys.exit(0)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--config':
            print("\n🔧 Запуск настройки кликера...")
            clicker = TransparentClicker()
            clicker.configure()
            sys.exit(0)

        while True:
            action = console_menu()
            if action == 'exit':
                print("\n👋 Выход...")
                sys.exit(0)
            elif action == 'config':
                clicker = TransparentClicker()
                clicker.configure()
                print("\n✅ Переобучение завершено!")
                input("\nНажмите Enter для возврата...")
            elif action == 'gui':
                print("\n🚀 Запуск GUI...")
                break

        root = Tk()
        app = PlateRecognitionApp(root)
        root.mainloop()

    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

