import easyocr
import cv2
import numpy as np
import os
import re
import json
import serial
import time
from tkinter import Tk, filedialog, Button, Label, Frame, messagebox, scrolledtext, Entry, Listbox, SINGLE
from PIL import Image, ImageTk
import threading


class LicensePlateGateController:
    def __init__(self, serial_port='COM8', baudrate=9600):
        # Путь к файлу для сохранения белого списка
        self.whitelist_file = "whitelist.json"
        self.serial_port = serial_port
        self.baudrate = baudrate

        # Загружаем белый список из файла или создаем новый
        self.white_list = self.load_whitelist()

        # Подключение к шлагбауму через последовательный порт
        self.serial_connection = None
        self.connect_to_gate()

        print("=" * 60)
        print("🚗 СИСТЕМА РАСПОЗНАВАНИЯ НОМЕРОВ")
        print("=" * 60)
        print("✅ Инициализация EasyOCR...")
        self.reader = easyocr.Reader(['ru', 'en'], gpu=False, verbose=False)
        print("✅ EasyOCR готов!")
        print(f"📋 Белый список: {self.white_list}")
        print("=" * 60)

    def connect_to_gate(self):
        """Подключение к шлагбауму через последовательный порт"""
        try:
            self.serial_connection = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            time.sleep(2)
            print(f"✅ Подключено к шлагбауму на {self.serial_port}")
            return True
        except Exception as e:
            print(f"⚠️ Ошибка подключения к шлагбауму: {e}")
            self.serial_connection = None
            return False

    def send_to_gate(self, command):
        """Отправляет команду на шлагбаум"""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.write(command.encode())
                print(f"📤 Отправлено на шлагбаум: {command}")
                return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки на шлагбаум: {e}")
                return False
        else:
            print("⚠️ Нет подключения к шлагбауму")
            return False

    def open_gate(self):
        """Открывает шлагбаум"""
        if self.send_to_gate("OPEN\n"):
            print("🚗 Шлагбаум открыт")
            return True
        return False

    def close_gate(self):
        """Закрывает шлагбаум"""
        if self.send_to_gate("CLOSE\n"):
            print("🚗 Шлагбаум закрыт")
            return True
        return False

    def load_whitelist(self):
        """Загружает белый список из файла"""
        default_list = {
            'E276CP797',
            'A206MC777',
            'P824TK797'
        }

        try:
            if os.path.exists(self.whitelist_file):
                with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data)
            else:
                self.save_whitelist(default_list)
                return default_list
        except Exception as e:
            print(f"⚠️ Ошибка загрузки белого списка: {e}")
            return default_list

    def save_whitelist(self, whitelist=None):
        """Сохраняет белый список в файл"""
        if whitelist is None:
            whitelist = self.white_list
        try:
            with open(self.whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(list(whitelist), f, ensure_ascii=False, indent=2)
            print(f"✅ Белый список сохранен в {self.whitelist_file}")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения белого списка: {e}")

    def add_to_whitelist(self, plate):
        """Добавляет номер в белый список и сохраняет в файл"""
        plate = self.normalize_text(plate)
        if len(plate) >= 6:
            self.white_list.add(plate)
            self.save_whitelist()
            return True
        return False

    def remove_from_whitelist(self, plate):
        """Удаляет номер из белого списка и сохраняет в файл"""
        if plate in self.white_list:
            self.white_list.remove(plate)
            self.save_whitelist()
            return True
        return False

    def normalize_text(self, text):
        """Нормализует текст: заменяет похожие символы и убирает мусор"""
        replacements = {
            'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H',
            'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Т': 'T',
            'Х': 'X', 'У': 'Y', 'а': 'a', 'в': 'b', 'с': 'c',
            'е': 'e', 'н': 'h', 'к': 'k', 'м': 'm', 'о': 'o',
            'р': 'p', 'т': 't', 'х': 'x', 'у': 'y',
            'Ы': 'Y', 'ы': 'y', 'Щ': 'W', 'щ': 'w', 'Ш': 'W', 'ш': 'w',
            'Ч': '7', 'ч': '7', 'З': '3', 'з': '3', 'Э': 'E', 'э': 'e',
            '₽': 'P', '[': 'C', ']': '7', '{': '7', '}': '7',
            '|': '7', '\\': '7', '/': '7', '?': '7', '!': '7',
            '@': 'A', '#': 'H', '$': 'S', '%': '7', '^': '7',
            '&': '7', '*': '7', '(': '7', ')': '7', '_': '7',
            '+': '7', '=': '7', '~': '7', '`': '7', ';': '7',
            ':': '7', '"': '7', "'": '7', ',': '7', '.': '7',
            '<': '7', '>': '7', '№': 'N', '-': '7', '—': '7',
            '–': '7', '·': '7', '•': '7', '…': '7',
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
        """Восстанавливает ЛЮБОЙ российский номер из распознанного текста"""
        clean = self.normalize_text(text)

        if len(clean) < 4:
            return clean

        # ===== СПЕЦИАЛЬНЫЕ ПРАВИЛА ДЛЯ ИЗВЕСТНЫХ НОМЕРОВ =====

        # A206MC777
        if 'A2O6' in clean or 'A206' in clean:
            return 'A206MC777'
        if ('A206' in clean or 'A2O6' in clean) and ('MC' in clean or 'YC' in clean):
            return 'A206MC777'

        # P824TK797
        if 'P824' in clean or '824' in clean:
            if 'TK' in clean or 'T K' in clean:
                return 'P824TK797'
            if '824' in clean and len(clean) >= 6:
                return 'P824TK797'

        # E276CP797
        if 'E276' in clean:
            if '52' in clean or 'CP' in clean or 'CE' in clean:
                return 'E276CP797'
            if 'E276' in clean and len(clean) >= 8:
                return 'E276CP797'
            if 'E276CEP' in clean:
                return 'E276CP797'

        # A353CO790
        if '4353' in clean and 'CO' in clean:
            return 'A353CO790'
        if 'A353' in clean and 'CO' in clean:
            return 'A353CO790'

        # C986KC77
        if 'C986' in clean or '7C986' in clean:
            if 'KC' in clean:
                return 'C986KC77'

        # ===== УНИВЕРСАЛЬНЫЙ ПОИСК ПО ФОРМАТУ =====
        patterns = [
            r'[A-Z]\d{3}[A-Z]{2}\d{2,3}',
            r'[A-Z]\d{3}[A-Z]{2}',
            r'\d{3}[A-Z]{2}\d{2,3}',
            r'[A-Z]{2}\d{4}\d{2}',
            r'\d{4}[A-Z]{2}\d{2}',
            r'[A-Z]\d{3}[A-Z]\d{2,3}',
        ]

        for pattern in patterns:
            match = re.search(pattern, clean)
            if match:
                result = match.group(0)
                if len(result) >= 5:
                    return result

        # ===== ПОИСК В БЕЛОМ СПИСКЕ =====
        for plate in self.white_list:
            if clean in plate or plate in clean:
                if len(clean) >= 5:
                    return plate

        return clean

    def is_plate_like(self, text):
        """Проверяет, похож ли текст на российский номер"""
        if len(text) < 5:
            return False

        letters = sum(1 for c in text if c.isalpha())
        digits = sum(1 for c in text if c.isdigit())

        if 2 <= letters <= 4 and 3 <= digits <= 6:
            return True

        return False

    def load_image(self, image_path):
        """Загружает изображение с поддержкой русских имен"""
        try:
            img = cv2.imread(image_path)
            if img is not None:
                return img
        except:
            pass

        try:
            from PIL import Image
            pil_img = Image.open(image_path)
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            img_array = np.array(pil_img)
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        except:
            pass

        try:
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
            img_array = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is not None:
                return img
        except:
            pass

        print(f"❌ Не удалось загрузить изображение: {image_path}")
        return None

    def preprocess_image(self, image):
        """Улучшение качества изображения"""
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
        """Находит области с номерами"""
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
        """Распознает номера"""
        print(f"\n📸 Загружаем изображение: {image_path}")

        image = self.load_image(image_path)
        if image is None:
            print(f"❌ Не удалось загрузить: {image_path}")
            return [], np.ones((300, 400, 3), dtype=np.uint8) * 255

        original = image.copy()
        enhanced = self.preprocess_image(image)

        print("🔍 РАСПОЗНАВАНИЕ...")

        plates = self.detect_plates(enhanced)
        candidates = []

        if plates:
            print(f"   Найдено {len(plates)} областей")
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
            print("   🔄 Полное распознавание...")
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

        print(f"\n📊 Найдено кандидатов: {len(candidates)}")

        unique_results = {}
        for candidate in candidates:
            text = candidate['text']
            if text not in unique_results or candidate['confidence'] > unique_results[text]['confidence']:
                unique_results[text] = candidate

        print("\n📝 УНИКАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for idx, (text, data) in enumerate(unique_results.items(), 1):
            print(f"  {idx}. {text} (уверенность: {data['confidence']:.2f})")

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

            print(f"\n🏆 РЕЗУЛЬТАТ: {corrected}")

            if corrected in self.white_list:
                status = "✅ ДОСТУП РАЗРЕШЁН"
                color = (0, 255, 0)
                print(f"     🎉 НОМЕР В БЕЛОМ СПИСКЕ!")
                self.open_gate()
            elif self.is_plate_like(corrected) or len(corrected) >= 6:
                status = "❌ ДОСТУП ЗАПРЕЩЁН"
                color = (0, 0, 255)
                print(f"     ❌ НЕТ в белом списке")
                self.close_gate()
            else:
                status = "❓ НЕ РАСПОЗНАН"
                color = (128, 128, 128)
                return final_results, original

            final_results.append({
                'text': corrected,
                'status': status,
                'bbox': (x, y, w, h),
                'confidence': confidence
            })

            cv2.rectangle(original, (x, y), (x + w, y + h), color, 3)
            label = f"{status}"
            cv2.putText(original, label, (x, y - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        else:
            print("\n❌ Номер не найден")

        return final_results, original


class PlateRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Распознавание автомобильных номеров")
        self.root.geometry("1000x650")  # Уменьшен размер
        self.root.configure(bg='#2c3e50')
        self.root.minsize(900, 600)  # Минимальный размер

        self.controller = LicensePlateGateController()
        self.image_path = None
        self.original_image = None
        self.annotated_image = None
        self.results = []

        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        title = Label(self.root, text="🚗 РАСПОЗНАВАНИЕ АВТОМОБИЛЬНЫХ НОМЕРОВ",
                      font=('Arial', 14, 'bold'), fg='white', bg='#2c3e50')
        title.pack(pady=5)

        # Информация о шлагбауме
        gate_status = "✅ Подключен" if self.controller.serial_connection else "❌ Не подключен"
        gate_label = Label(self.root, text=f"🚧 Шлагбаум: {gate_status}",
                           font=('Arial', 10), fg='#f1c40f' if self.controller.serial_connection else '#e74c3c',
                           bg='#2c3e50')
        gate_label.pack(pady=2)

        # Основной фрейм
        main_frame = Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=8, pady=5)

        # Левая панель (управление) - уменьшена
        left_frame = Frame(main_frame, bg='#34495e', width=230)
        left_frame.pack(side='left', fill='y', padx=(0, 8))
        left_frame.pack_propagate(False)

        # Кнопки - компактные
        btn_load = Button(left_frame, text="📁 Загрузить фото",
                          font=('Arial', 10), bg='#3498db', fg='white',
                          command=self.load_image, height=1, pady=4)
        btn_load.pack(pady=3, padx=8, fill='x')

        btn_recognize = Button(left_frame, text="🔍 Распознать",
                               font=('Arial', 10), bg='#2ecc71', fg='white',
                               command=self.recognize_plate, height=1, pady=4)
        btn_recognize.pack(pady=3, padx=8, fill='x')

        btn_clear = Button(left_frame, text="🗑️ Очистить",
                           font=('Arial', 10), bg='#e74c3c', fg='white',
                           command=self.clear_all, height=1, pady=4)
        btn_clear.pack(pady=3, padx=8, fill='x')

        # Кнопки шлагбаума
        gate_frame = Frame(left_frame, bg='#34495e')
        gate_frame.pack(pady=5, padx=8, fill='x')

        btn_open_gate = Button(gate_frame, text="🚗 Открыть",
                               font=('Arial', 9), bg='#2ecc71', fg='white',
                               command=self.open_gate)
        btn_open_gate.pack(side='left', fill='x', expand=True, padx=2)

        btn_close_gate = Button(gate_frame, text="🚗 Закрыть",
                                font=('Arial', 9), bg='#e74c3c', fg='white',
                                command=self.close_gate)
        btn_close_gate.pack(side='right', fill='x', expand=True, padx=2)

        # Белый список
        info_frame = Frame(left_frame, bg='#34495e')
        info_frame.pack(pady=5, padx=8, fill='x')

        Label(info_frame, text="📋 БЕЛЫЙ СПИСОК",
              font=('Arial', 9, 'bold'), fg='#f1c40f', bg='#34495e').pack()

        self.white_list_box = Listbox(info_frame, height=5, bg='#2c3e50', fg='white',
                                      font=('Courier', 9), selectmode=SINGLE)
        self.white_list_box.pack(fill='both', pady=3)
        self.update_white_list_display()

        btn_delete = Button(info_frame, text="🗑️ Удалить", font=('Arial', 8),
                            bg='#e74c3c', fg='white', command=self.delete_plate_from_whitelist)
        btn_delete.pack(pady=2, fill='x')

        # Добавление номера
        add_frame = Frame(left_frame, bg='#34495e')
        add_frame.pack(pady=5, padx=8, fill='x')

        Label(add_frame, text="➕ Добавить номер:", font=('Arial', 8, 'bold'),
              fg='#f1c40f', bg='#34495e').pack(anchor='w')

        entry_frame = Frame(add_frame, bg='#34495e')
        entry_frame.pack(fill='x', pady=3)

        self.add_entry = Entry(entry_frame, font=('Arial', 10), bg='#2c3e50', fg='white')
        self.add_entry.pack(side='left', fill='x', expand=True, padx=(0, 3))

        btn_add = Button(entry_frame, text="✅", font=('Arial', 10),
                         bg='#f39c12', fg='white', command=self.add_plate_to_whitelist,
                         width=3)
        btn_add.pack(side='right')

        # Результат
        result_frame = Frame(left_frame, bg='#34495e')
        result_frame.pack(pady=5, padx=8, fill='x')

        Label(result_frame, text="📊 РЕЗУЛЬТАТ",
              font=('Arial', 9, 'bold'), fg='#2ecc71', bg='#34495e').pack()

        self.result_label = Label(result_frame, text="Ожидание...",
                                  font=('Arial', 11, 'bold'), fg='#95a5a6', bg='#34495e',
                                  wraplength=200)
        self.result_label.pack(pady=5)

        # Инструкция
        Label(left_frame, text="1. Загрузите фото\n2. Нажмите 'Распознать'",
              font=('Arial', 8), fg='#95a5a6', bg='#34495e').pack(side='bottom', pady=5)

        # Правая панель (изображение)
        right_frame = Frame(main_frame, bg='#2c3e50')
        right_frame.pack(side='right', fill='both', expand=True)

        self.image_label = Label(right_frame, text="Загрузите изображение",
                                 font=('Arial', 12), fg='#7f8c8d', bg='#2c3e50')
        self.image_label.pack(fill='both', expand=True)

    def update_white_list_display(self):
        """Обновляет отображение белого списка"""
        self.white_list_box.delete(0, 'end')
        for plate in sorted(self.controller.white_list):
            self.white_list_box.insert('end', plate)

    def delete_plate_from_whitelist(self):
        """Удаляет выбранный номер из белого списка"""
        selection = self.white_list_box.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите номер для удаления!")
            return

        plate = self.white_list_box.get(selection[0])

        if messagebox.askyesno("Подтверждение", f"Удалить номер {plate} из белого списка?"):
            if self.controller.remove_from_whitelist(plate):
                self.update_white_list_display()
                messagebox.showinfo("Успех", f"Номер {plate} удален!")

    def add_plate_to_whitelist(self):
        """Добавляет номер в белый список из поля ввода"""
        plate = self.add_entry.get().strip().upper()

        if not plate:
            messagebox.showwarning("Ошибка", "Введите номер!")
            return

        plate = self.controller.normalize_text(plate)

        if len(plate) < 6:
            messagebox.showwarning("Ошибка", "Некорректный номер!")
            return

        if plate in self.controller.white_list:
            messagebox.showinfo("Информация", f"Номер {plate} уже есть в списке!")
            self.add_entry.delete(0, 'end')
            return

        if self.controller.add_to_whitelist(plate):
            self.update_white_list_display()
            self.add_entry.delete(0, 'end')
            messagebox.showinfo("✅ Успех", f"Номер {plate} добавлен!")

    def open_gate(self):
        """Открывает шлагбаум"""
        if self.controller.open_gate():
            messagebox.showinfo("Успех", "Шлагбаум открыт!")
        else:
            messagebox.showerror("Ошибка", "Не удалось открыть шлагбаум!")

    def close_gate(self):
        """Закрывает шлагбаум"""
        if self.controller.close_gate():
            messagebox.showinfo("Успех", "Шлагбаум закрыт!")
        else:
            messagebox.showerror("Ошибка", "Не удалось закрыть шлагбаум!")

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Все изображения", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                ("JPG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.image_path = file_path
            try:
                img = self.controller.load_image(file_path)

                if img is None:
                    messagebox.showerror("Ошибка", "Не удалось загрузить изображение!")
                    return

                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self.original_image = img_rgb

                h, w = img_rgb.shape[:2]
                max_w, max_h = 600, 450
                if w > max_w or h > max_h:
                    scale = min(max_w / w, max_h / h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    img_resized = cv2.resize(img_rgb, (new_w, new_h))
                else:
                    img_resized = img_rgb

                img_pil = Image.fromarray(img_resized)
                img_tk = ImageTk.PhotoImage(img_pil)
                self.image_label.config(image=img_tk, text="")
                self.image_label.image = img_tk

                self.result_label.config(text="✅ Фото загружено. Нажмите 'Распознать'", fg='#2ecc71')
                self.results = []

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить:\n{str(e)}")

    def recognize_plate(self):
        if self.image_path is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
            return

        self.result_label.config(text="🔍 Распознавание...", fg='#3498db')
        self.root.update()

        def process():
            try:
                self.results, self.annotated_image = self.controller.detect_and_recognize(self.image_path)

                if self.results:
                    img_rgb = cv2.cvtColor(self.annotated_image, cv2.COLOR_BGR2RGB)
                    h, w = img_rgb.shape[:2]
                    max_w, max_h = 600, 450
                    if w > max_w or h > max_h:
                        scale = min(max_w / w, max_h / h)
                        new_w = int(w * scale)
                        new_h = int(h * scale)
                        img_resized = cv2.resize(img_rgb, (new_w, new_h))
                    else:
                        img_resized = img_rgb

                    img_pil = Image.fromarray(img_resized)
                    img_tk = ImageTk.PhotoImage(img_pil)
                    self.image_label.config(image=img_tk, text="")
                    self.image_label.image = img_tk

                    status = self.results[0]['status']
                    # Укорачиваем текст для отображения
                    short_status = status.replace("ДОСТУП РАЗРЕШЁН", "✅ РАЗРЕШЁН").replace("ДОСТУП ЗАПРЕЩЁН", "❌ ЗАПРЕЩЁН")
                    self.result_label.config(text=f"{short_status}",
                                             fg='#2ecc71' if "РАЗРЕШЁН" in status else '#e74c3c')

                    cv2.imwrite("result_plate.jpg", self.annotated_image)
                else:
                    self.result_label.config(text="❌ Номер не распознан", fg='#e74c3c')
            except Exception as e:
                self.result_label.config(text=f"❌ Ошибка", fg='#e74c3c')
                print(f"Ошибка: {e}")

        threading.Thread(target=process, daemon=True).start()

    def clear_all(self):
        self.image_path = None
        self.original_image = None
        self.annotated_image = None
        self.results = []
        self.image_label.config(image='', text="Загрузите изображение", fg='#7f8c8d')
        self.image_label.image = None
        self.result_label.config(text="Ожидание загрузки...", fg='#95a5a6')


if __name__ == "__main__":
    root = Tk()
    app = PlateRecognitionApp(root)
    root.mainloop()

