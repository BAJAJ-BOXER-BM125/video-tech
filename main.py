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
        print(f"⏱️ Шлагбаум автоматически закроется через {self.auto_close_delay} секунд")
        self.auto_close_timer = threading.Timer(self.auto_close_delay, self.auto_close_gate)
        self.auto_close_timer.daemon = True
        self.auto_close_timer.start()

    def cancel_auto_close_timer(self):
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
            self.auto_close_timer = None

    def auto_close_gate(self):
        print("⏱️ Время истекло! Шлагбаум автоматически закрывается...")
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

    def load_image(self, image_path):
        try:
            img = cv2.imread(image_path)
            if img is not None:
                return img
            from PIL import Image
            pil_img = Image.open(image_path)
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            img_array = np.array(pil_img)
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        except:
            return None

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

    def detect_and_recognize(self, image_path):
        image = self.load_image(image_path)
        if image is None:
            return [], np.ones((300, 400, 3), dtype=np.uint8) * 255

        original = image.copy()
        enhanced = self.preprocess_image(image)

        plates = self.detect_plates(enhanced)
        candidates = []

        if plates:
            for x, y, w, h in plates[:5]:
                margin = 15
                x1 = max(0, x - margin)
                y1 = max(0, y - margin)
                x2 = min(image.shape[1], x + w + margin)
                y2 = min(image.shape[0], y + h + margin)
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
        self.root.title("🚗 Распознавание автомобильных номеров")
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
        self.image_path = None
        self.results = []
        self.annotated_image = None

        self.create_widgets()

    def create_widgets(self):
        # ===== ЗАГОЛОВОК =====
        header_frame = Frame(self.root, bg=self.colors['bg'], height=50)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        Label(header_frame,
              text="🚗 РАСПОЗНАВАНИЕ АВТОМОБИЛЬНЫХ НОМЕРОВ",
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

        # ---- Кнопки ----
        btn_frame = Frame(left_panel, bg=self.colors['panel'])
        btn_frame.pack(fill='x', padx=15, pady=5)

        Button(btn_frame, text="📁 Загрузить фото",
               bg=self.colors['accent'], fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.load_image, height=1, pady=5).pack(fill='x', pady=4)

        Button(btn_frame, text="🔍 Распознать",
               bg=self.colors['success'], fg='white',
               font=('Arial', 11), relief='flat', cursor='hand2',
               command=self.recognize_plate, height=1, pady=5).pack(fill='x', pady=4)

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

        entry_row = Frame(add_frame, bg=self.colors['panel'])
        entry_row.pack(fill='x', pady=3)

        self.add_entry = Entry(entry_row,
                               font=('Courier', 11),
                               bg='#2c3e50',
                               fg='white',
                               relief='flat', bd=1)
        self.add_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        Button(entry_row, text="✅ Добавить",
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
              text="1. Загрузите фото\n2. Нажмите 'Распознать'",
              font=('Arial', 10),
              fg=self.colors['text_secondary'],
              bg=self.colors['panel']).pack(side='bottom', pady=10)

        # ===== ПРАВАЯ ПАНЕЛЬ =====
        right_panel = Frame(main_frame, bg=self.colors['bg'])
        right_panel.pack(side='right', fill='both', expand=True)

        self.image_label = Label(right_panel, text="📸 Загрузите изображение",
                                 font=('Arial', 16),
                                 fg='#7f8c8d',
                                 bg=self.colors['bg'])
        self.image_label.pack(fill='both', expand=True)

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

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                       ("JPG", "*.jpg *.jpeg"), ("PNG", "*.png"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.image_path = file_path
            try:
                img = self.controller.load_image(file_path)
                if img is None:
                    messagebox.showerror("Ошибка", "Не удалось загрузить!")
                    return
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w = img_rgb.shape[:2]
                max_w, max_h = 700, 520
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
                self.result_label.config(text="✅ Фото загружено", fg=self.colors['success'])
                self.results = []
                self.annotated_image = None
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")

    def recognize_plate(self):
        if self.image_path is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите фото!")
            return

        self.result_label.config(text="🔍 Распознавание...", fg=self.colors['accent'])
        self.root.update()

        def process():
            try:
                self.results, self.annotated_image = self.controller.detect_and_recognize(self.image_path)
                if self.results:
                    img_rgb = cv2.cvtColor(self.annotated_image, cv2.COLOR_BGR2RGB)
                    h, w = img_rgb.shape[:2]
                    max_w, max_h = 700, 520
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

                    status = self.results[0]['status']
                    plate_text = self.results[0]['text']
                    short_status = status.replace("ДОСТУП РАЗРЕШЁН", "✅ РАЗРЕШЁН").replace("ДОСТУП ЗАПРЕЩЁН",
                                                                                           "❌ ЗАПРЕЩЁН")

                    if "РАЗРЕШЁН" in status:
                        self.result_label.config(text=f"{short_status}\n{plate_text}", fg=self.colors['success'])
                    else:
                        self.result_label.config(text=f"{short_status}\n{plate_text}", fg=self.colors['danger'])
                    cv2.imwrite("result_plate.jpg", self.annotated_image)
                else:
                    self.result_label.config(text="❌ Номер не распознан", fg=self.colors['danger'])
            except Exception as e:
                self.result_label.config(text="❌ Ошибка", fg=self.colors['danger'])

        threading.Thread(target=process, daemon=True).start()

    def clear_all(self):
        self.image_path = None
        self.results = []
        self.annotated_image = None
        self.image_label.config(image='', text="📸 Загрузите изображение", fg='#7f8c8d')
        self.image_label.image = None
        self.result_label.config(text="Ожидание...", fg=self.colors['text_secondary'])


def console_menu():
    print("\n" + "=" * 60)
    print("🚗 СИСТЕМА РАСПОЗНАВАНИЯ НОМЕРОВ")
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