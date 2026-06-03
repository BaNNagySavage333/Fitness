# -*- coding: utf-8 -*-
"""
Счетчик калорий и программа для похудения
==========================================

Настольное приложение на Python + Tkinter.

Возможности:
    * Профиль пользователя (имя, возраст, пол, рост, вес, целевой вес, активность)
    * Расчет ИМТ (BMI), суточной нормы калорий (TDEE) и рекомендуемого дефицита
    * Дневник питания: завтрак / обед / ужин / перекусы
    * Подсчет калорий, белков, жиров и углеводов за день
    * Прогресс похудения и график изменения веса (matplotlib)
    * История по дням
    * Экспорт данных в CSV и JSON

Все данные хранятся в локальном файле data.json (создается автоматически).

Зависимости (помимо стандартной библиотеки):
    pip install matplotlib

Автор: учебный проект.
Лицензия: MIT
"""

import os
import sys
import json
import csv
import base64
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# matplotlib встраивается прямо в окно Tkinter
import matplotlib
matplotlib.use("TkAgg")  # backend для Tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------------------------------------------------------------------------
#  Базовые настройки и пути
# ---------------------------------------------------------------------------

def get_base_dir() -> str:
    """Возвращает каталог, рядом с которым хранится data.json.

    При сборке в EXE (PyInstaller) __file__ указывает во временную папку,
    поэтому используем каталог исполняемого файла.
    """
    if getattr(sys, "frozen", False):           # запущено как .exe
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
DATA_FILE = os.path.join(BASE_DIR, "data.json")
ICON_ICO = os.path.join(BASE_DIR, "icon.ico")
ICON_PNG = os.path.join(BASE_DIR, "icon.png")

# Маленькая иконка в base64 — используется как запасной вариант,
# если файлы icon.ico / icon.png отсутствуют.
ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAACZklEQVR4nO1bO04DMRAdPidAoqGl"
    "JxKRKDgMlJyCFOEUtFwCitQUSEEKPS1NJK4A1UjZzXo9Hs8bO7v7uo2y43lvxmN7bRNNmDBqHGl"
    "fvHq8/rN0xAJfT5/JfJJeqJF0CFIxjqUGD4k8kdzfqEqHRrwLfdnQmwFDIE/UzyMowFDIM0J8xDV"
    "gqOjsGzVE//zyvPG8/d6a2G3Xgz0BSpNvE2/DQohdEarqAjHy0v+koCoBSqDRBbzS/3V1svfb3cN"
    "Zko3crsDd4DTLSiK6iJeGiwA1EmfAa0DN5ImAAmyW6yTyL8+/4v9azQmIQAJslmuEWQjMBWDyP7c"
    "3ye9KssAy+kSGRdAq6ixCe1hc3b81nmeLuUl7JvOANnlN9CW4eP9oPOeIwPOA0c8EswUoWfAs2s4"
    "SoIZqn+uDWoAayDNyfJlqgLVBq+HJy7ZKgFjKtYcrC8RsaruBaQbMFnNobdgs1+ZZAKsBllmAyCh"
    "GsgChCKOjv9t+KAs07UNHAYvIIaNP5DAM5hBAkydy+iTGRKSLJA/iDNePojEhPIkzXAVglCAawjQ"
    "VLu1AaSQL0DcGI9cBu+33zUVSMWWApTF0FiBmmyoBPFI9FVqfIPsCCIFQaw3YzpClCMiFllqAGEE"
    "rESTkc9rJ3hiROpcaQel7WvK8MQLZGepCKqEUmxq4nxBhQpKu4wmzM0LejufWl84uQJR/UAothEV"
    "hhZ4THMW+QAyoiRACLmeFtd0CQTp6VpiBOjSJnNTE0HVxwv2TWG0LqWAN0NzAqhkhPr1FcCgi9PE"
    "QEyx9j0ADSQDFw+ChZYPU39HfHJ0wdvwDl+QLSIyN5X4AAAAASUVORK5CYII="
)

# Цветовая палитра приложения (зелёная «здоровая» тема)
COLORS = {
    "bg":        "#eef3ee",   # общий фон
    "card":      "#ffffff",   # карточки / панели
    "primary":   "#2e7d32",   # основной зелёный
    "primary_d": "#1b5e20",   # тёмный зелёный
    "accent":    "#43a047",   # акцент
    "text":      "#1f2d27",   # основной текст
    "muted":     "#6b7d72",   # приглушённый текст
    "danger":    "#e53935",   # удаление / предупреждение
    "track":     "#d7e3d8",   # фон прогресс-бара
}

# Виды приёмов пищи: внутренний ключ -> подпись для интерфейса
MEAL_TYPES = {
    "breakfast": "Завтрак",
    "lunch":     "Обед",
    "dinner":    "Ужин",
    "snacks":    "Перекусы",
}

# Уровни физической активности и коэффициенты для TDEE
ACTIVITY_LEVELS = {
    "Минимальная (сидячий образ жизни)": 1.2,
    "Низкая (1–3 тренировки в неделю)":  1.375,
    "Средняя (3–5 тренировок в неделю)": 1.55,
    "Высокая (6–7 тренировок в неделю)": 1.725,
    "Очень высокая (физ. работа)":       1.9,
}

# Встроенная база продуктов. Значения указаны НА 100 ГРАММ продукта.
# По выбранному продукту и весу порции приложение само считает калории и Б/Ж/У.
# Ключи: "calories" (ккал), "protein" (белки, г), "fat" (жиры, г),
# "carbs" (углеводы, г).
DEFAULT_PRODUCTS = {
    "Куриная грудка (отварная)":   {"calories": 165, "protein": 31.0, "fat": 3.6,  "carbs": 0.0},
    "Куриное бедро (отварное)":    {"calories": 211, "protein": 26.0, "fat": 11.0, "carbs": 0.0},
    "Индейка (филе)":              {"calories": 114, "protein": 24.0, "fat": 1.0,  "carbs": 0.0},
    "Говядина (отварная)":         {"calories": 250, "protein": 26.0, "fat": 15.0, "carbs": 0.0},
    "Свинина (нежирная)":          {"calories": 242, "protein": 27.0, "fat": 14.0, "carbs": 0.0},
    "Лосось":                      {"calories": 208, "protein": 20.0, "fat": 13.0, "carbs": 0.0},
    "Тунец (в собств. соку)":      {"calories": 116, "protein": 25.0, "fat": 1.0,  "carbs": 0.0},
    "Яйцо куриное":                {"calories": 157, "protein": 12.7, "fat": 11.5, "carbs": 0.7},
    "Творог 5%":                   {"calories": 121, "protein": 17.0, "fat": 5.0,  "carbs": 1.8},
    "Творог 9%":                   {"calories": 159, "protein": 16.7, "fat": 9.0,  "carbs": 2.0},
    "Сыр твёрдый":                 {"calories": 364, "protein": 25.0, "fat": 30.0, "carbs": 0.0},
    "Молоко 2.5%":                 {"calories": 52,  "protein": 2.9,  "fat": 2.5,  "carbs": 4.8},
    "Кефир 1%":                    {"calories": 40,  "protein": 3.0,  "fat": 1.0,  "carbs": 4.0},
    "Йогурт натуральный":          {"calories": 60,  "protein": 3.5,  "fat": 3.3,  "carbs": 4.7},
    "Овсянка (сухая)":             {"calories": 366, "protein": 12.0, "fat": 7.0,  "carbs": 62.0},
    "Гречка (сухая)":              {"calories": 343, "protein": 13.0, "fat": 3.4,  "carbs": 62.0},
    "Рис белый (сухой)":           {"calories": 344, "protein": 7.0,  "fat": 1.0,  "carbs": 78.0},
    "Рис бурый (сухой)":           {"calories": 337, "protein": 7.4,  "fat": 1.8,  "carbs": 72.0},
    "Макароны (сухие)":            {"calories": 350, "protein": 12.0, "fat": 1.5,  "carbs": 71.0},
    "Картофель (отварной)":        {"calories": 82,  "protein": 2.0,  "fat": 0.4,  "carbs": 17.0},
    "Хлеб белый":                  {"calories": 265, "protein": 8.0,  "fat": 3.2,  "carbs": 49.0},
    "Хлеб ржаной":                 {"calories": 250, "protein": 6.6,  "fat": 1.2,  "carbs": 34.0},
    "Банан":                       {"calories": 89,  "protein": 1.1,  "fat": 0.3,  "carbs": 22.8},
    "Яблоко":                      {"calories": 52,  "protein": 0.3,  "fat": 0.2,  "carbs": 13.8},
    "Апельсин":                    {"calories": 47,  "protein": 0.9,  "fat": 0.1,  "carbs": 11.8},
    "Огурец":                      {"calories": 15,  "protein": 0.8,  "fat": 0.1,  "carbs": 2.8},
    "Помидор":                     {"calories": 18,  "protein": 0.9,  "fat": 0.2,  "carbs": 3.9},
    "Морковь":                     {"calories": 41,  "protein": 0.9,  "fat": 0.2,  "carbs": 9.6},
    "Брокколи":                    {"calories": 34,  "protein": 2.8,  "fat": 0.4,  "carbs": 6.6},
    "Авокадо":                     {"calories": 160, "protein": 2.0,  "fat": 15.0, "carbs": 9.0},
    "Грецкий орех":                {"calories": 654, "protein": 15.0, "fat": 65.0, "carbs": 14.0},
    "Миндаль":                     {"calories": 579, "protein": 21.0, "fat": 50.0, "carbs": 22.0},
    "Масло сливочное":             {"calories": 717, "protein": 0.9,  "fat": 81.0, "carbs": 0.1},
    "Масло оливковое":             {"calories": 884, "protein": 0.0,  "fat": 100.0,"carbs": 0.0},
    "Сахар":                       {"calories": 387, "protein": 0.0,  "fat": 0.0,  "carbs": 100.0},
    "Мёд":                         {"calories": 304, "protein": 0.3,  "fat": 0.0,  "carbs": 82.0},
}


# ---------------------------------------------------------------------------
#  Расчётный модуль (формулы)
# ---------------------------------------------------------------------------

class Calculator:
    """Набор статических методов для медицинских/диетических расчётов."""

    @staticmethod
    def bmi(weight_kg: float, height_cm: float) -> float:
        """Индекс массы тела: вес(кг) / рост(м)^2."""
        if height_cm <= 0:
            return 0.0
        height_m = height_cm / 100.0
        return weight_kg / (height_m * height_m)

    @staticmethod
    def bmi_category(bmi: float) -> str:
        """Текстовая интерпретация ИМТ по классификации ВОЗ."""
        if bmi <= 0:
            return "—"
        if bmi < 18.5:
            return "Недостаточный вес"
        if bmi < 25:
            return "Нормальный вес"
        if bmi < 30:
            return "Избыточный вес"
        if bmi < 35:
            return "Ожирение I степени"
        if bmi < 40:
            return "Ожирение II степени"
        return "Ожирение III степени"

    @staticmethod
    def bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
        """Базовый обмен веществ по формуле Миффлина–Сан Жеора."""
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        if gender == "Мужской":
            return base + 5
        return base - 161  # женский (и значение по умолчанию)

    @staticmethod
    def tdee(bmr_value: float, activity_factor: float) -> float:
        """Суточная норма калорий = BMR * коэффициент активности."""
        return bmr_value * activity_factor

    @staticmethod
    def recommended_deficit(tdee_value: float) -> dict:
        """Рекомендуемый дефицит для безопасного похудения.

        Используем дефицит ~500 ккал/сутки (примерно 0.5 кг/неделю),
        но не опускаем целевую калорийность ниже 1200 ккал.
        """
        deficit = 500
        target = tdee_value - deficit
        if target < 1200:
            target = 1200
            deficit = max(0, tdee_value - target)
        return {"deficit": deficit, "target_calories": target}


# ---------------------------------------------------------------------------
#  Работа с данными (JSON)
# ---------------------------------------------------------------------------

class DataManager:
    """Загрузка, сохранение и доступ к данным приложения (data.json)."""

    def __init__(self, path: str = DATA_FILE):
        self.path = path
        self.data = self._default_data()
        self.load()

    # --- структура по умолчанию -------------------------------------------
    @staticmethod
    def _default_data() -> dict:
        return {
            "user": {
                "name": "",
                "age": 0,
                "gender": "Мужской",
                "height": 0.0,        # см
                "weight": 0.0,        # кг — текущий вес
                "target_weight": 0.0, # кг — целевой вес
                "activity": "Низкая (1–3 тренировки в неделю)",
            },
            # база продуктов (значения на 100 г) — встроенная + добавленная пользователем
            "products": dict(DEFAULT_PRODUCTS),
            # history[ГГГГ-ММ-ДД] = {"weight": float|None, "meals": {...}}
            "history": {},
        }

    # --- загрузка / сохранение --------------------------------------------
    def load(self):
        """Читает data.json. Если файла нет или он повреждён — создаёт новый."""
        if not os.path.exists(self.path):
            self.save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # аккуратно объединяем со структурой по умолчанию
            self.data = self._default_data()
            self.data["user"].update(loaded.get("user", {}))
            # база продуктов: встроенные + сохранённые пользователем
            self.data["products"] = dict(DEFAULT_PRODUCTS)
            self.data["products"].update(loaded.get("products", {}))
            self.data["history"] = loaded.get("history", {})
        except (json.JSONDecodeError, OSError):
            # повреждённый файл — начинаем с чистой структуры
            self.data = self._default_data()
            self.save()

    def save(self):
        """Сохраняет данные в data.json (с отступами и кириллицей)."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные:\n{e}")

    # --- пользователь ------------------------------------------------------
    def get_user(self) -> dict:
        return self.data["user"]

    def update_user(self, **kwargs):
        self.data["user"].update(kwargs)
        self.save()

    # --- база продуктов ----------------------------------------------------
    def get_products(self) -> dict:
        """Все известные продукты (значения на 100 г)."""
        return self.data.setdefault("products", {})

    def get_product(self, name: str):
        """Ищет продукт по названию (без учёта регистра). None — если нет."""
        name = (name or "").strip()
        if not name:
            return None
        products = self.get_products()
        if name in products:
            return products[name]
        low = name.lower()
        for key, value in products.items():
            if key.lower() == low:
                return value
        return None

    def add_product(self, name: str, per_100g: dict):
        """Сохраняет/обновляет продукт (значения на 100 г) в базе."""
        name = (name or "").strip()
        if not name:
            return
        self.get_products()[name] = per_100g
        self.save()

    # --- дни / приёмы пищи -------------------------------------------------
    def ensure_day(self, date_str: str) -> dict:
        """Гарантирует наличие записи дня с корректной структурой."""
        day = self.data["history"].get(date_str)
        if day is None:
            day = {"weight": None, "meals": {k: [] for k in MEAL_TYPES}}
            self.data["history"][date_str] = day
        # на случай старых/неполных данных — добиваем недостающие ключи
        day.setdefault("weight", None)
        day.setdefault("meals", {})
        for k in MEAL_TYPES:
            day["meals"].setdefault(k, [])
        return day

    def get_day(self, date_str: str) -> dict:
        return self.ensure_day(date_str)

    def add_meal_item(self, date_str: str, meal: str, item: dict):
        day = self.ensure_day(date_str)
        day["meals"][meal].append(item)
        self.save()

    def remove_meal_item(self, date_str: str, meal: str, index: int):
        day = self.ensure_day(date_str)
        items = day["meals"].get(meal, [])
        if 0 <= index < len(items):
            items.pop(index)
            self.save()

    def set_weight(self, date_str: str, weight: float):
        """Записывает вес за день и обновляет текущий вес в профиле."""
        day = self.ensure_day(date_str)
        day["weight"] = weight
        self.data["user"]["weight"] = weight
        self.save()

    # --- агрегаты ----------------------------------------------------------
    def day_totals(self, date_str: str) -> dict:
        """Суммарные калории/Б/Ж/У за день."""
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        day = self.data["history"].get(date_str)
        if not day:
            return totals
        for meal in MEAL_TYPES:
            for item in day.get("meals", {}).get(meal, []):
                totals["calories"] += item.get("calories", 0)
                totals["protein"] += item.get("protein", 0)
                totals["fat"] += item.get("fat", 0)
                totals["carbs"] += item.get("carbs", 0)
        return totals

    def sorted_dates(self) -> list:
        """Список дат истории, отсортированный по возрастанию."""
        return sorted(self.data["history"].keys())

    def weight_series(self):
        """Возвращает (даты, веса) только для дней, где вес указан."""
        dates, weights = [], []
        for d in self.sorted_dates():
            w = self.data["history"][d].get("weight")
            if w is not None:
                dates.append(d)
                weights.append(w)
        return dates, weights


# ---------------------------------------------------------------------------
#  Вспомогательные функции
# ---------------------------------------------------------------------------

def today_str() -> str:
    """Сегодняшняя дата в формате ГГГГ-ММ-ДД."""
    return datetime.date.today().isoformat()


def parse_float(value: str, field: str) -> float:
    """Преобразует строку в число с понятной ошибкой."""
    value = (value or "").strip().replace(",", ".")
    if value == "":
        return 0.0
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Поле «{field}» должно быть числом.")


def parse_int(value: str, field: str) -> int:
    return int(round(parse_float(value, field)))


def valid_date(date_str: str) -> bool:
    """Проверяет корректность даты ГГГГ-ММ-ДД."""
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
#  Главное приложение
# ---------------------------------------------------------------------------

class CalorieApp(tk.Tk):
    """Главное окно приложения со вкладками."""

    def __init__(self):
        super().__init__()
        self.dm = DataManager()
        self.current_date = tk.StringVar(value=today_str())

        self.title("Счетчик калорий и программа для похудения")
        self.geometry("960x680")
        self.minsize(820, 600)
        self.configure(bg=COLORS["bg"])

        self._set_icon()
        self._init_style()
        self._build_menu()
        self._build_ui()

        # первичная отрисовка
        self.refresh_profile_view()
        self.refresh_diary()
        self.refresh_progress()
        self.refresh_history()

    # --- иконка окна -------------------------------------------------------
    def _set_icon(self):
        """Пытается установить иконку из .ico, .png или из встроенного base64."""
        # 1) Windows .ico
        try:
            if os.path.exists(ICON_ICO):
                self.iconbitmap(ICON_ICO)
                return
        except tk.TclError:
            pass
        # 2) PNG-файл или встроенная картинка (кроссплатформенно)
        try:
            if os.path.exists(ICON_PNG):
                self._icon_img = tk.PhotoImage(file=ICON_PNG)
            else:
                self._icon_img = tk.PhotoImage(data=ICON_BASE64)
            self.iconphoto(True, self._icon_img)
        except tk.TclError:
            pass  # иконка не критична

    # --- стили ttk ---------------------------------------------------------
    def _init_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")  # тема, которую удобно перекрашивать
        except tk.TclError:
            pass

        base_font = ("Segoe UI", 10)
        style.configure(".", background=COLORS["bg"], foreground=COLORS["text"],
                        font=base_font)

        # Notebook (вкладки)
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10),
                        font=("Segoe UI", 10, "bold"),
                        background=COLORS["track"], foreground=COLORS["muted"])
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["primary"])],
                  foreground=[("selected", "#ffffff")])

        # Карточки / фреймы
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Card.TLabel", background=COLORS["card"],
                        foreground=COLORS["text"])
        style.configure("Title.TLabel", background=COLORS["bg"],
                        foreground=COLORS["primary_d"],
                        font=("Segoe UI", 16, "bold"))
        style.configure("CardTitle.TLabel", background=COLORS["card"],
                        foreground=COLORS["primary_d"],
                        font=("Segoe UI", 13, "bold"))
        style.configure("Muted.TLabel", background=COLORS["card"],
                        foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("Stat.TLabel", background=COLORS["card"],
                        foreground=COLORS["primary"],
                        font=("Segoe UI", 18, "bold"))

        # Кнопки
        style.configure("TButton", padding=(12, 7), font=("Segoe UI", 10, "bold"),
                        background=COLORS["primary"], foreground="#ffffff",
                        borderwidth=0)
        style.map("TButton",
                  background=[("active", COLORS["primary_d"]),
                              ("disabled", COLORS["track"])])
        style.configure("Accent.TButton", background=COLORS["accent"])
        style.map("Accent.TButton", background=[("active", COLORS["primary"])])
        style.configure("Danger.TButton", background=COLORS["danger"])
        style.map("Danger.TButton", background=[("active", "#b71c1c")])

        # Поля ввода
        style.configure("TEntry", padding=5, fieldbackground="#ffffff")
        style.configure("TCombobox", padding=4, fieldbackground="#ffffff")

        # Таблицы
        style.configure("Treeview", rowheight=26, fieldbackground=COLORS["card"],
                        background=COLORS["card"], font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background=COLORS["primary"], foreground="#ffffff")
        style.map("Treeview.Heading",
                  background=[("active", COLORS["primary_d"])])

        # Прогресс-бар
        style.configure("green.Horizontal.TProgressbar",
                        troughcolor=COLORS["track"], background=COLORS["accent"],
                        thickness=22)

    # --- меню --------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Экспорт в CSV…", command=self.export_csv)
        filemenu.add_command(label="Экспорт в JSON…", command=self.export_json)
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="О программе", command=self._about)
        menubar.add_cascade(label="Справка", menu=helpmenu)

        self.config(menu=menubar)

    def _about(self):
        messagebox.showinfo(
            "О программе",
            "Счетчик калорий и программа для похудения\n\n"
            "Учебный проект на Python + Tkinter.\n"
            "Данные хранятся локально в data.json.\n\n"
            "Лицензия: MIT")

    # --- построение интерфейса --------------------------------------------
    def _build_ui(self):
        header = ttk.Label(self, text="🥗  Счетчик калорий и программа для похудения",
                           style="Title.TLabel")
        header.pack(side="top", anchor="w", padx=16, pady=(14, 8))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.tab_profile = ttk.Frame(self.notebook)
        self.tab_diary = ttk.Frame(self.notebook)
        self.tab_progress = ttk.Frame(self.notebook)
        self.tab_history = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_profile, text="👤  Профиль")
        self.notebook.add(self.tab_diary, text="🍽  Дневник питания")
        self.notebook.add(self.tab_progress, text="📉  Прогресс")
        self.notebook.add(self.tab_history, text="📅  История")

        self._build_profile_tab()
        self._build_diary_tab()
        self._build_progress_tab()
        self._build_history_tab()

        # при переключении вкладок обновляем зависимые данные
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, _event=None):
        tab = self.notebook.tab(self.notebook.select(), "text")
        if "Прогресс" in tab:
            self.refresh_progress()
        elif "История" in tab:
            self.refresh_history()
        elif "Профиль" in tab:
            self.refresh_profile_view()

    # ==================================================================
    #  ВКЛАДКА 1: ПРОФИЛЬ
    # ==================================================================
    def _build_profile_tab(self):
        outer = ttk.Frame(self.tab_profile)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.columnconfigure(0, weight=1, uniform="col")
        outer.columnconfigure(1, weight=1, uniform="col")
        outer.rowconfigure(0, weight=1)

        # --- левая карточка: ввод данных ---
        form = ttk.Frame(outer, style="Card.TFrame", padding=18)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        for i in range(2):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text="Данные пользователя",
                  style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2,
                                                 sticky="w", pady=(0, 12))

        self.v_name = tk.StringVar()
        self.v_age = tk.StringVar()
        self.v_gender = tk.StringVar(value="Мужской")
        self.v_height = tk.StringVar()
        self.v_weight = tk.StringVar()
        self.v_target = tk.StringVar()
        self.v_activity = tk.StringVar()

        self._form_row(form, 1, "Имя:", self.v_name)
        self._form_row(form, 2, "Возраст (лет):", self.v_age)

        ttk.Label(form, text="Пол:", style="Card.TLabel").grid(
            row=3, column=0, sticky="w", pady=6)
        gender_cb = ttk.Combobox(form, textvariable=self.v_gender,
                                 values=["Мужской", "Женский"],
                                 state="readonly")
        gender_cb.grid(row=3, column=1, sticky="ew", pady=6)

        self._form_row(form, 4, "Рост (см):", self.v_height)
        self._form_row(form, 5, "Текущий вес (кг):", self.v_weight)
        self._form_row(form, 6, "Целевой вес (кг):", self.v_target)

        ttk.Label(form, text="Активность:", style="Card.TLabel").grid(
            row=7, column=0, sticky="w", pady=6)
        act_cb = ttk.Combobox(form, textvariable=self.v_activity,
                              values=list(ACTIVITY_LEVELS.keys()),
                              state="readonly")
        act_cb.grid(row=7, column=1, sticky="ew", pady=6)

        ttk.Button(form, text="💾  Сохранить и рассчитать",
                   command=self.save_profile).grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=(16, 0))

        # --- правая карточка: результаты расчёта ---
        result = ttk.Frame(outer, style="Card.TFrame", padding=18)
        result.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        result.columnconfigure(0, weight=1)

        ttk.Label(result, text="Результаты расчёта",
                  style="CardTitle.TLabel").grid(row=0, column=0, sticky="w",
                                                 pady=(0, 12))

        self.lbl_bmi = ttk.Label(result, text="—", style="Stat.TLabel")
        self.lbl_bmi.grid(row=1, column=0, sticky="w")
        ttk.Label(result, text="Индекс массы тела (ИМТ)",
                  style="Muted.TLabel").grid(row=2, column=0, sticky="w",
                                             pady=(0, 10))
        self.lbl_bmi_cat = ttk.Label(result, text="", style="Card.TLabel")
        self.lbl_bmi_cat.grid(row=3, column=0, sticky="w", pady=(0, 14))

        self.lbl_tdee = ttk.Label(result, text="—", style="Stat.TLabel")
        self.lbl_tdee.grid(row=4, column=0, sticky="w")
        ttk.Label(result, text="Суточная норма калорий (TDEE)",
                  style="Muted.TLabel").grid(row=5, column=0, sticky="w",
                                             pady=(0, 14))

        self.lbl_target_cal = ttk.Label(result, text="—", style="Stat.TLabel")
        self.lbl_target_cal.grid(row=6, column=0, sticky="w")
        ttk.Label(result, text="Норма для похудения (с дефицитом)",
                  style="Muted.TLabel").grid(row=7, column=0, sticky="w",
                                             pady=(0, 14))

        self.lbl_deficit = ttk.Label(result, text="", style="Card.TLabel")
        self.lbl_deficit.grid(row=8, column=0, sticky="w")

    def _form_row(self, parent, row, label, var):
        """Создаёт строку «подпись + поле ввода»."""
        ttk.Label(parent, text=label, style="Card.TLabel").grid(
            row=row, column=0, sticky="w", pady=6)
        ttk.Entry(parent, textvariable=var).grid(
            row=row, column=1, sticky="ew", pady=6)

    def refresh_profile_view(self):
        """Заполняет поля профиля из данных и пересчитывает показатели."""
        u = self.dm.get_user()
        self.v_name.set(u.get("name", ""))
        self.v_age.set(str(u.get("age", "")) if u.get("age") else "")
        self.v_gender.set(u.get("gender", "Мужской"))
        self.v_height.set(str(u.get("height", "")) if u.get("height") else "")
        self.v_weight.set(str(u.get("weight", "")) if u.get("weight") else "")
        self.v_target.set(str(u.get("target_weight", "")) if u.get("target_weight") else "")
        self.v_activity.set(u.get("activity", list(ACTIVITY_LEVELS.keys())[1]))
        self._update_calculations()

    def save_profile(self):
        """Проверяет ввод, сохраняет профиль и пересчитывает показатели."""
        try:
            name = self.v_name.get().strip()
            age = parse_int(self.v_age.get(), "Возраст")
            gender = self.v_gender.get()
            height = parse_float(self.v_height.get(), "Рост")
            weight = parse_float(self.v_weight.get(), "Текущий вес")
            target = parse_float(self.v_target.get(), "Целевой вес")
            activity = self.v_activity.get() or list(ACTIVITY_LEVELS.keys())[1]
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return

        if not name:
            messagebox.showwarning("Внимание", "Укажите имя пользователя.")
            return
        if age <= 0 or height <= 0 or weight <= 0:
            messagebox.showwarning(
                "Внимание", "Возраст, рост и вес должны быть больше нуля.")
            return

        self.dm.update_user(name=name, age=age, gender=gender, height=height,
                            weight=weight, target_weight=target,
                            activity=activity)
        # фиксируем текущий вес в истории сегодняшнего дня
        self.dm.set_weight(today_str(), weight)

        self._update_calculations()
        self.refresh_progress()
        self.refresh_history()
        messagebox.showinfo("Готово", "Профиль сохранён, показатели обновлены.")

    def _update_calculations(self):
        """Обновляет ИМТ, TDEE и рекомендуемую калорийность на экране."""
        u = self.dm.get_user()
        weight = u.get("weight", 0) or 0
        height = u.get("height", 0) or 0
        age = u.get("age", 0) or 0
        gender = u.get("gender", "Мужской")
        activity_factor = ACTIVITY_LEVELS.get(u.get("activity"), 1.375)

        bmi = Calculator.bmi(weight, height)
        if bmi > 0:
            self.lbl_bmi.config(text=f"{bmi:.1f}")
            self.lbl_bmi_cat.config(text=Calculator.bmi_category(bmi))
        else:
            self.lbl_bmi.config(text="—")
            self.lbl_bmi_cat.config(text="")

        if weight > 0 and height > 0 and age > 0:
            bmr = Calculator.bmr(gender, weight, height, age)
            tdee = Calculator.tdee(bmr, activity_factor)
            rec = Calculator.recommended_deficit(tdee)
            self.lbl_tdee.config(text=f"{tdee:.0f} ккал")
            self.lbl_target_cal.config(text=f"{rec['target_calories']:.0f} ккал")
            self.lbl_deficit.config(
                text=f"Рекомендуемый дефицит: {rec['deficit']:.0f} ккал/сутки")
        else:
            self.lbl_tdee.config(text="—")
            self.lbl_target_cal.config(text="—")
            self.lbl_deficit.config(text="")

    # ==================================================================
    #  ВКЛАДКА 2: ДНЕВНИК ПИТАНИЯ
    # ==================================================================
    def _build_diary_tab(self):
        outer = ttk.Frame(self.tab_diary)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        # --- верхняя панель: дата и вес за день ---
        top = ttk.Frame(outer, style="Card.TFrame", padding=12)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text="Дата (ГГГГ-ММ-ДД):",
                  style="Card.TLabel").pack(side="left")
        date_entry = ttk.Entry(top, textvariable=self.current_date, width=14)
        date_entry.pack(side="left", padx=6)
        ttk.Button(top, text="Сегодня", style="Accent.TButton",
                   command=self._set_today).pack(side="left")
        ttk.Button(top, text="Показать", command=self.refresh_diary).pack(
            side="left", padx=6)

        ttk.Label(top, text="    Вес за день (кг):",
                  style="Card.TLabel").pack(side="left")
        self.v_day_weight = tk.StringVar()
        ttk.Entry(top, textvariable=self.v_day_weight, width=8).pack(
            side="left", padx=6)
        ttk.Button(top, text="Записать вес", style="Accent.TButton",
                   command=self._save_day_weight).pack(side="left")

        # --- панель добавления продукта ---
        add = ttk.Frame(outer, style="Card.TFrame", padding=12)
        add.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        for i in range(8):
            add.columnconfigure(i, weight=1)

        ttk.Label(add, text="Добавить продукт",
                  style="CardTitle.TLabel").grid(row=0, column=0, columnspan=8,
                                                 sticky="w", pady=(0, 8))

        self.v_meal = tk.StringVar(value="Завтрак")
        self.v_food = tk.StringVar()
        self.v_grams = tk.StringVar()
        self.v_cal = tk.StringVar()
        self.v_prot = tk.StringVar()
        self.v_fat = tk.StringVar()
        self.v_carb = tk.StringVar()

        # авто-пересчёт калорий и Б/Ж/У при изменении продукта или граммовки
        self.v_food.trace_add("write", self._recalc_nutrition)
        self.v_grams.trace_add("write", self._recalc_nutrition)

        self._labeled(add, 1, 0, "Приём пищи")
        ttk.Combobox(add, textvariable=self.v_meal,
                     values=list(MEAL_TYPES.values()),
                     state="readonly", width=12).grid(row=2, column=0,
                                                       sticky="ew", padx=4)
        self._labeled(add, 1, 1, "Продукт")
        # выпадающий список продуктов из базы (можно и вписать своё название)
        self.food_combo = ttk.Combobox(add, textvariable=self.v_food)
        self.food_combo.grid(row=2, column=1, columnspan=2, sticky="ew", padx=4)
        self.food_combo.bind("<<ComboboxSelected>>", self._recalc_nutrition)
        self._labeled(add, 1, 3, "Граммы")
        ttk.Entry(add, textvariable=self.v_grams, width=8).grid(row=2, column=3,
                                                                sticky="ew",
                                                                padx=4)
        self._labeled(add, 1, 4, "Ккал")
        ttk.Entry(add, textvariable=self.v_cal, width=8).grid(row=2, column=4,
                                                              sticky="ew", padx=4)
        self._labeled(add, 1, 5, "Белки")
        ttk.Entry(add, textvariable=self.v_prot, width=7).grid(row=2, column=5,
                                                               sticky="ew", padx=4)
        self._labeled(add, 1, 6, "Жиры")
        ttk.Entry(add, textvariable=self.v_fat, width=7).grid(row=2, column=6,
                                                              sticky="ew", padx=4)
        self._labeled(add, 1, 7, "Углеводы")
        ttk.Entry(add, textvariable=self.v_carb, width=7).grid(row=2, column=7,
                                                               sticky="ew", padx=4)

        ttk.Button(add, text="➕  Добавить", command=self.add_food).grid(
            row=3, column=0, columnspan=8, sticky="e", pady=(10, 0))
        # строка состояния авто-расчёта (обновляется при выборе продукта)
        self.lbl_auto = ttk.Label(
            add,
            text="Выберите продукт из списка — калории и Б/Ж/У посчитаются "
                 "автоматически по граммам. Нет в списке — впишите вручную "
                 "(продукт сохранится в базу).",
            style="Muted.TLabel")
        self.lbl_auto.grid(row=4, column=0, columnspan=8, sticky="w",
                           pady=(6, 0))

        # заполняем выпадающий список названиями продуктов из базы
        self._refresh_food_values()

        # --- таблица продуктов за день ---
        table_frame = ttk.Frame(outer, style="Card.TFrame", padding=8)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("meal", "food", "grams", "cal", "prot", "fat", "carb")
        headers = ("Приём пищи", "Продукт", "Граммы", "Ккал",
                   "Белки", "Жиры", "Углеводы")
        self.diary_tree = ttk.Treeview(table_frame, columns=cols,
                                       show="headings", selectmode="browse")
        for c, h in zip(cols, headers):
            self.diary_tree.heading(c, text=h)
            width = 140 if c in ("meal", "food") else 80
            self.diary_tree.column(c, width=width,
                                   anchor="w" if c in ("meal", "food") else "center")
        self.diary_tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(table_frame, orient="vertical",
                               command=self.diary_tree.yview)
        self.diary_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        # зебра-окраска строк
        self.diary_tree.tag_configure("odd", background="#f4f8f4")
        self.diary_tree.tag_configure("even", background="#ffffff")

        # карта iid -> (meal_key, index) для удаления
        self.diary_index = {}

        # --- нижняя панель: итоги и удаление ---
        bottom = ttk.Frame(outer, style="Card.TFrame", padding=12)
        bottom.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.lbl_totals = ttk.Label(
            bottom, text="Итого за день: 0 ккал | Б: 0 | Ж: 0 | У: 0",
            style="CardTitle.TLabel")
        self.lbl_totals.pack(side="left")
        ttk.Button(bottom, text="🗑  Удалить выбранное", style="Danger.TButton",
                   command=self.delete_food).pack(side="right")

    def _labeled(self, parent, row, col, text):
        ttk.Label(parent, text=text, style="Muted.TLabel").grid(
            row=row, column=col, sticky="w", padx=4)

    def _set_today(self):
        self.current_date.set(today_str())
        self.refresh_diary()

    def _refresh_food_values(self):
        """Обновляет список названий продуктов в выпадающем списке."""
        names = sorted(self.dm.get_products().keys(), key=str.lower)
        self.food_combo["values"] = names

    def _recalc_nutrition(self, *args):
        """Автоматически считает калории и Б/Ж/У по продукту и граммам.

        Срабатывает при выборе продукта или изменении веса порции.
        Если продукт есть в базе и указан вес — заполняет поля калорий,
        белков, жиров и углеводов. Если продукта нет в базе — поля не трогаем
        (пользователь вводит значения вручную, и продукт сохранится при добавлении).
        """
        # метод может вызваться до полного построения интерфейса
        if not hasattr(self, "lbl_auto"):
            return

        name = self.v_food.get().strip()
        product = self.dm.get_product(name)

        if product is None:
            if name:
                self.lbl_auto.config(
                    text="Продукта нет в базе — впишите Ккал и Б/Ж/У вручную "
                         "(он сохранится для будущих расчётов).")
            else:
                self.lbl_auto.config(
                    text="Выберите продукт из списка — калории и Б/Ж/У "
                         "посчитаются автоматически по граммам.")
            return

        # продукт найден — пробуем посчитать по граммам
        try:
            grams = parse_float(self.v_grams.get(), "Граммы")
        except ValueError:
            grams = 0.0

        if grams <= 0:
            self.lbl_auto.config(
                text=f"«{name}» найден в базе. Укажите граммы — посчитаю "
                     f"автоматически (на 100 г: {product['calories']:g} ккал, "
                     f"Б {product['protein']:g} / Ж {product['fat']:g} / "
                     f"У {product['carbs']:g}).")
            return

        factor = grams / 100.0
        self.v_cal.set(f"{product['calories'] * factor:.0f}")
        self.v_prot.set(f"{product['protein'] * factor:.1f}")
        self.v_fat.set(f"{product['fat'] * factor:.1f}")
        self.v_carb.set(f"{product['carbs'] * factor:.1f}")
        self.lbl_auto.config(
            text=f"✓ Посчитано автоматически для {grams:g} г продукта «{name}».")

    def _save_day_weight(self):
        date_str = self.current_date.get().strip()
        if not valid_date(date_str):
            messagebox.showerror("Ошибка", "Неверный формат даты (нужно ГГГГ-ММ-ДД).")
            return
        try:
            w = parse_float(self.v_day_weight.get(), "Вес за день")
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return
        if w <= 0:
            messagebox.showwarning("Внимание", "Вес должен быть больше нуля.")
            return
        self.dm.set_weight(date_str, w)
        self.refresh_profile_view()
        self.refresh_progress()
        self.refresh_history()
        messagebox.showinfo("Готово", f"Вес {w} кг сохранён за {date_str}.")

    def add_food(self):
        """Добавляет продукт в выбранный приём пищи за текущую дату."""
        date_str = self.current_date.get().strip()
        if not valid_date(date_str):
            messagebox.showerror("Ошибка", "Неверный формат даты (нужно ГГГГ-ММ-ДД).")
            return

        food = self.v_food.get().strip()
        if not food:
            messagebox.showwarning("Внимание", "Введите название продукта.")
            return
        try:
            item = {
                "name": food,
                "grams": parse_float(self.v_grams.get(), "Граммы"),
                "calories": parse_float(self.v_cal.get(), "Ккал"),
                "protein": parse_float(self.v_prot.get(), "Белки"),
                "fat": parse_float(self.v_fat.get(), "Жиры"),
                "carbs": parse_float(self.v_carb.get(), "Углеводы"),
            }
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return

        # подпись приёма пищи -> внутренний ключ
        meal_key = next((k for k, v in MEAL_TYPES.items()
                         if v == self.v_meal.get()), "breakfast")
        self.dm.add_meal_item(date_str, meal_key, item)

        # если продукта ещё нет в базе — сохраняем его значения на 100 г,
        # чтобы в следующий раз расчёт шёл автоматически
        if self.dm.get_product(food) is None and item["grams"] > 0:
            factor = 100.0 / item["grams"]
            self.dm.add_product(food, {
                "calories": round(item["calories"] * factor, 1),
                "protein": round(item["protein"] * factor, 1),
                "fat": round(item["fat"] * factor, 1),
                "carbs": round(item["carbs"] * factor, 1),
            })
            self._refresh_food_values()

        # очищаем поля продукта (приём пищи оставляем)
        for var in (self.v_food, self.v_grams, self.v_cal,
                    self.v_prot, self.v_fat, self.v_carb):
            var.set("")
        self.refresh_diary()

    def delete_food(self):
        """Удаляет выбранную строку из дневника."""
        sel = self.diary_tree.selection()
        if not sel:
            messagebox.showinfo("Удаление", "Выберите строку для удаления.")
            return
        iid = sel[0]
        ref = self.diary_index.get(iid)
        if not ref:
            return
        meal_key, index = ref
        if messagebox.askyesno("Удаление", "Удалить выбранный продукт?"):
            self.dm.remove_meal_item(self.current_date.get().strip(),
                                     meal_key, index)
            self.refresh_diary()

    def refresh_diary(self):
        """Перерисовывает таблицу продуктов и итоги за выбранный день."""
        date_str = self.current_date.get().strip()
        # очистка таблицы
        for row in self.diary_tree.get_children():
            self.diary_tree.delete(row)
        self.diary_index.clear()

        if not valid_date(date_str):
            return

        day = self.dm.get_day(date_str)
        # вес за день в поле ввода
        w = day.get("weight")
        self.v_day_weight.set(str(w) if w else "")

        counter = 0
        for meal_key, meal_label in MEAL_TYPES.items():
            for idx, item in enumerate(day["meals"].get(meal_key, [])):
                tag = "even" if counter % 2 == 0 else "odd"
                iid = self.diary_tree.insert(
                    "", "end",
                    values=(meal_label, item.get("name", ""),
                            f"{item.get('grams', 0):g}",
                            f"{item.get('calories', 0):g}",
                            f"{item.get('protein', 0):g}",
                            f"{item.get('fat', 0):g}",
                            f"{item.get('carbs', 0):g}"),
                    tags=(tag,))
                self.diary_index[iid] = (meal_key, idx)
                counter += 1

        t = self.dm.day_totals(date_str)
        self.lbl_totals.config(
            text=(f"Итого за день: {t['calories']:.0f} ккал  |  "
                  f"Б: {t['protein']:.1f} г  |  "
                  f"Ж: {t['fat']:.1f} г  |  "
                  f"У: {t['carbs']:.1f} г"))

    # ==================================================================
    #  ВКЛАДКА 3: ПРОГРЕСС
    # ==================================================================
    def _build_progress_tab(self):
        outer = ttk.Frame(self.tab_progress)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        # карточки со статистикой
        stats = ttk.Frame(outer)
        stats.grid(row=0, column=0, sticky="ew")
        for i in range(3):
            stats.columnconfigure(i, weight=1, uniform="s")

        self.card_cur, self.lbl_cur = self._stat_card(
            stats, 0, "Текущий вес")
        self.card_goal, self.lbl_goal = self._stat_card(
            stats, 1, "Целевой вес")
        self.card_left, self.lbl_left = self._stat_card(
            stats, 2, "Осталось сбросить")

        # прогресс-бар
        prog = ttk.Frame(outer, style="Card.TFrame", padding=14)
        prog.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        prog.columnconfigure(0, weight=1)
        ttk.Label(prog, text="Прогресс похудения",
                  style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(
            prog, style="green.Horizontal.TProgressbar",
            maximum=100, value=0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(8, 4))
        self.lbl_progress = ttk.Label(prog, text="", style="Muted.TLabel")
        self.lbl_progress.grid(row=2, column=0, sticky="w")

        # график веса
        chart = ttk.Frame(outer, style="Card.TFrame", padding=10)
        chart.grid(row=2, column=0, sticky="nsew")
        chart.columnconfigure(0, weight=1)
        chart.rowconfigure(1, weight=1)
        ttk.Label(chart, text="График изменения веса",
                  style="CardTitle.TLabel").grid(row=0, column=0, sticky="w",
                                                 pady=(0, 6))

        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.figure.patch.set_facecolor(COLORS["card"])
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    def _stat_card(self, parent, col, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0 if col == 0 else 6, 0 if col == 2 else 6))
        value = ttk.Label(card, text="—", style="Stat.TLabel")
        value.pack(anchor="w")
        ttk.Label(card, text=title, style="Muted.TLabel").pack(anchor="w")
        return card, value

    def refresh_progress(self):
        """Обновляет карточки, прогресс-бар и график веса."""
        u = self.dm.get_user()
        current = u.get("weight", 0) or 0
        goal = u.get("target_weight", 0) or 0

        self.lbl_cur.config(text=f"{current:g} кг" if current else "—")
        self.lbl_goal.config(text=f"{goal:g} кг" if goal else "—")

        remaining = max(0.0, current - goal)
        self.lbl_left.config(text=f"{remaining:g} кг" if current and goal else "—")

        # стартовый вес — первый записанный в истории (или текущий)
        dates, weights = self.dm.weight_series()
        start_weight = weights[0] if weights else current

        # вычисляем процент выполнения цели
        percent = 0.0
        if start_weight and goal and start_weight > goal:
            done = start_weight - current
            total = start_weight - goal
            percent = max(0.0, min(100.0, (done / total) * 100.0))
        self.progress_bar.config(value=percent)

        if current and goal:
            if current <= goal:
                self.lbl_progress.config(text="🎉 Цель достигнута! Поздравляем!")
            else:
                self.lbl_progress.config(
                    text=f"Выполнено {percent:.0f}% пути. "
                         f"Стартовый вес: {start_weight:g} кг.")
        else:
            self.lbl_progress.config(
                text="Заполните текущий и целевой вес в профиле.")

        self._draw_weight_chart(dates, weights, goal)

    def _draw_weight_chart(self, dates, weights, goal):
        """Рисует график веса по дням средствами matplotlib."""
        self.ax.clear()
        self.ax.set_facecolor(COLORS["card"])

        if len(weights) >= 1:
            x = list(range(len(weights)))
            self.ax.plot(x, weights, marker="o", color=COLORS["primary"],
                         linewidth=2, markersize=5, label="Вес")
            # линия целевого веса
            if goal:
                self.ax.axhline(goal, color=COLORS["danger"], linestyle="--",
                                linewidth=1.5, label="Цель")
            # подписи дат (короткие)
            labels = [d[5:] for d in dates]  # ММ-ДД
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            self.ax.set_ylabel("Вес, кг")
            self.ax.legend(loc="best", fontsize=8)
            self.ax.grid(True, alpha=0.3)
        else:
            self.ax.text(0.5, 0.5, "Нет данных о весе.\n"
                                   "Запишите вес в дневнике или профиле.",
                         ha="center", va="center", color=COLORS["muted"],
                         fontsize=11, transform=self.ax.transAxes)
            self.ax.set_xticks([])
            self.ax.set_yticks([])

        self.figure.tight_layout()
        self.canvas.draw()

    # ==================================================================
    #  ВКЛАДКА 4: ИСТОРИЯ
    # ==================================================================
    def _build_history_tab(self):
        outer = ttk.Frame(self.tab_history)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        bar = ttk.Frame(outer, style="Card.TFrame", padding=10)
        bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(bar, text="История по дням",
                  style="CardTitle.TLabel").pack(side="left")
        ttk.Button(bar, text="⬇  Экспорт CSV", style="Accent.TButton",
                   command=self.export_csv).pack(side="right", padx=4)
        ttk.Button(bar, text="⬇  Экспорт JSON", style="Accent.TButton",
                   command=self.export_json).pack(side="right", padx=4)
        ttk.Button(bar, text="🔄  Обновить",
                   command=self.refresh_history).pack(side="right", padx=4)

        table_frame = ttk.Frame(outer, style="Card.TFrame", padding=8)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("date", "weight", "cal", "prot", "fat", "carb")
        headers = ("Дата", "Вес (кг)", "Калории", "Белки", "Жиры", "Углеводы")
        self.hist_tree = ttk.Treeview(table_frame, columns=cols,
                                      show="headings")
        for c, h in zip(cols, headers):
            self.hist_tree.heading(c, text=h)
            self.hist_tree.column(c, width=110, anchor="center")
        self.hist_tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(table_frame, orient="vertical",
                               command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        self.hist_tree.tag_configure("odd", background="#f4f8f4")
        self.hist_tree.tag_configure("even", background="#ffffff")

        # двойной клик по дню — открыть его в дневнике
        self.hist_tree.bind("<Double-1>", self._open_day_from_history)

    def _open_day_from_history(self, _event=None):
        sel = self.hist_tree.selection()
        if not sel:
            return
        date_str = self.hist_tree.item(sel[0], "values")[0]
        self.current_date.set(date_str)
        self.refresh_diary()
        self.notebook.select(self.tab_diary)

    def refresh_history(self):
        """Перерисовывает таблицу истории по дням."""
        for row in self.hist_tree.get_children():
            self.hist_tree.delete(row)
        for i, date_str in enumerate(self.dm.sorted_dates()):
            day = self.dm.get_day(date_str)
            t = self.dm.day_totals(date_str)
            w = day.get("weight")
            tag = "even" if i % 2 == 0 else "odd"
            self.hist_tree.insert(
                "", "end",
                values=(date_str,
                        f"{w:g}" if w else "—",
                        f"{t['calories']:.0f}",
                        f"{t['protein']:.1f}",
                        f"{t['fat']:.1f}",
                        f"{t['carbs']:.1f}"),
                tags=(tag,))

    # ==================================================================
    #  ЭКСПОРТ ДАННЫХ
    # ==================================================================
    def export_json(self):
        """Сохраняет все данные приложения в выбранный JSON-файл."""
        path = filedialog.asksaveasfilename(
            title="Сохранить как JSON",
            defaultextension=".json",
            filetypes=[("JSON-файлы", "*.json"), ("Все файлы", "*.*")],
            initialfile="export.json")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.dm.data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Экспорт", f"Данные сохранены в:\n{path}")
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def export_csv(self):
        """Экспортирует подробный отчёт по всем приёмам пищи в CSV."""
        path = filedialog.asksaveasfilename(
            title="Сохранить как CSV",
            defaultextension=".csv",
            filetypes=[("CSV-файлы", "*.csv"), ("Все файлы", "*.*")],
            initialfile="export.csv")
        if not path:
            return
        try:
            # utf-8-sig — чтобы Excel корректно открыл кириллицу
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Дата", "Вес за день (кг)", "Приём пищи",
                                 "Продукт", "Граммы", "Калории",
                                 "Белки", "Жиры", "Углеводы"])
                for date_str in self.dm.sorted_dates():
                    day = self.dm.get_day(date_str)
                    weight = day.get("weight")
                    has_items = False
                    for meal_key, meal_label in MEAL_TYPES.items():
                        for item in day["meals"].get(meal_key, []):
                            has_items = True
                            writer.writerow([
                                date_str,
                                weight if weight else "",
                                meal_label,
                                item.get("name", ""),
                                item.get("grams", 0),
                                item.get("calories", 0),
                                item.get("protein", 0),
                                item.get("fat", 0),
                                item.get("carbs", 0),
                            ])
                    # день без продуктов, но с весом — тоже строкой
                    if not has_items and weight:
                        writer.writerow([date_str, weight, "", "",
                                         "", "", "", "", ""])
                    # итоговая строка по дню
                    t = self.dm.day_totals(date_str)
                    writer.writerow([date_str, "", "ИТОГО ЗА ДЕНЬ", "", "",
                                     f"{t['calories']:.0f}",
                                     f"{t['protein']:.1f}",
                                     f"{t['fat']:.1f}",
                                     f"{t['carbs']:.1f}"])
            messagebox.showinfo("Экспорт", f"Данные сохранены в:\n{path}")
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")


# ---------------------------------------------------------------------------
#  Точка входа
# ---------------------------------------------------------------------------

def main():
    app = CalorieApp()
    app.mainloop()


if __name__ == "__main__":
    main()
