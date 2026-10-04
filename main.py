import json
import os
from datetime import date

from kivy.app import App
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.core.window import Window


# =========================================================
# THEME
# =========================================================

BG = (0.965, 0.975, 0.98, 1)
CARD = (1, 1, 1, 1)

TEXT = (0.08, 0.15, 0.22, 1)
TEXT_LIGHT = (0.35, 0.43, 0.50, 1)

BLUE = (0.30, 0.62, 0.95, 1)
BLUE_LIGHT = (0.88, 0.94, 1, 1)

TEAL = (0.20, 0.70, 0.68, 1)

GREEN = (0.30, 0.75, 0.48, 1)
GREEN_LIGHT = (0.88, 0.97, 0.91, 1)

AMBER = (0.95, 0.68, 0.25, 1)

BORDER = (0.82, 0.87, 0.92, 1)

Window.clearcolor = BG


# =========================================================
# DATA
# =========================================================

# Overridden in LifeBackApp.build() with the app's private storage path
DATA_FILE = "life_back.json"


DEFAULT_TASKS = [
    {"name": "Complete my main task", "points": 30, "done": False, "xp_awarded": False},
    {"name": "Study / Work", "points": 20, "done": False, "xp_awarded": False},
    {"name": "Exercise", "points": 15, "done": False, "xp_awarded": False},
    {"name": "Limit phone time", "points": 20, "done": False, "xp_awarded": False},
    {"name": "Sleep on time", "points": 15, "done": False, "xp_awarded": False},
]


def create_default_data():
    return {
        "last_date": date.today().isoformat(),
        "tasks": [dict(task) for task in DEFAULT_TASKS],
        "streak": 0,
        "best_streak": 0,
        # Lifetime XP
        "xp": 0,
        "completed_days": [],
        "time_thieves": [],
        "history": [],
    }


def calculate_score(tasks):
    if not tasks:
        return 0

    total_points = sum(task.get("points", 0) for task in tasks)
    completed_points = sum(
        task.get("points", 0) for task in tasks if task.get("done", False)
    )

    if total_points <= 0:
        return 0

    return round((completed_points / total_points) * 100)


def calculate_completed_tasks(tasks):
    return sum(1 for task in tasks if task.get("done", False))


def calculate_time_for_day(data, day):
    total = 0
    for item in data.get("time_thieves", []):
        if item.get("date") == day:
            total += item.get("minutes", 0)
    return total


def format_time(minutes):
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours > 0 and remaining_minutes > 0:
        return f"{hours} hr {remaining_minutes} min"
    elif hours > 0:
        return f"{hours} hr"
    else:
        return f"{remaining_minutes} min"


def save_today_snapshot(data):
    today = date.today().isoformat()

    score = calculate_score(data.get("tasks", []))
    completed = calculate_completed_tasks(data.get("tasks", []))
    time_lost = calculate_time_for_day(data, today)

    history = data.setdefault("history", [])

    # Update today's existing snapshot
    for item in history:
        if item.get("date") == today:
            item["score"] = score
            item["completed"] = completed
            item["time_lost"] = time_lost
            return

    # Otherwise create one
    history.append(
        {
            "date": today,
            "score": score,
            "completed": completed,
            "time_lost": time_lost,
        }
    )


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print("Save error:", e)


def load_data():
    if not os.path.exists(DATA_FILE):
        data = create_default_data()
        save_data(data)
        return data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        print("Load error:", e)
        data = create_default_data()
        save_data(data)
        return data

    # -----------------------------------------------------
    # Safety defaults
    # -----------------------------------------------------

    data.setdefault("streak", 0)
    data.setdefault("best_streak", 0)
    data.setdefault("xp", 0)
    data.setdefault("completed_days", [])
    data.setdefault("time_thieves", [])
    data.setdefault("history", [])
    data.setdefault("tasks", [])

    # -----------------------------------------------------
    # Make sure old tasks have required fields
    # -----------------------------------------------------

    for task in data["tasks"]:
        task.setdefault("done", False)
        task.setdefault("points", 0)
        task.setdefault("xp_awarded", False)

    today = date.today().isoformat()
    last_date = data.get("last_date", today)

    # -----------------------------------------------------
    # New day
    # -----------------------------------------------------

    if last_date != today:

        try:
            last_day = date.fromisoformat(last_date)
            today_date = date.today()
            difference = (today_date - last_day).days
        except Exception:
            difference = 999

        # ---------------------------------------------
        # Archive previous day
        # ---------------------------------------------

        old_score = calculate_score(data.get("tasks", []))
        old_completed = calculate_completed_tasks(data.get("tasks", []))
        old_time = calculate_time_for_day(data, last_date)

        history = data.setdefault("history", [])

        already_saved = False

        for item in history:
            if item.get("date") == last_date:
                item["score"] = old_score
                item["completed"] = old_completed
                item["time_lost"] = old_time
                already_saved = True
                break

        if not already_saved:
            history.append(
                {
                    "date": last_date,
                    "score": old_score,
                    "completed": old_completed,
                    "time_lost": old_time,
                }
            )

        # ---------------------------------------------
        # Streak
        # ---------------------------------------------

        if old_score >= 100 and difference == 1:
            data["streak"] = data.get("streak", 0) + 1
        elif old_score >= 100 and difference > 1:
            data["streak"] = 1
        else:
            data["streak"] = 0

        if data["streak"] > data.get("best_streak", 0):
            data["best_streak"] = data["streak"]

        # ---------------------------------------------
        # Fresh tasks for today
        # ---------------------------------------------

        data["tasks"] = [dict(task) for task in DEFAULT_TASKS]
        data["last_date"] = today

        save_data(data)

    return data


# =========================================================
# UI HELPERS
# =========================================================

def label_text(text="", size=16, color=TEXT, bold=False):
    label = Label(
        text=text,
        color=color,
        font_size=dp(size),
        bold=bold,
        halign="left",
        valign="middle",
    )

    label.bind(
        size=lambda instance, value: setattr(instance, "text_size", value)
    )

    return label


class Card(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(110)

        with self.canvas.before:
            Color(*CARD)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(16)],
            )

            Color(*BORDER)
            self.border = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(16),
                ),
                width=1,
            )

        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

        self.border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(16),
        )


class ModernButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = BLUE
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.font_size = dp(15)
        self.size_hint_y = None
        self.height = dp(48)


class SmallButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = BLUE_LIGHT
        self.color = BLUE
        self.bold = True
        self.font_size = dp(14)
        self.size_hint_y = None
        self.height = dp(42)


def create_back_button():
    button = Button(
        text="< BACK",
        size_hint_y=None,
        height=dp(45),
        background_normal="",
        background_color=BLUE_LIGHT,
        color=BLUE,
        bold=True,
    )
    return button


# =========================================================
# HOME SCREEN
# =========================================================

class HomeScreen(Screen):

    def on_enter(self):
        self.build_screen()

    def build_screen(self):

        self.clear_widgets()

        data = self.manager.app_data

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(18), dp(15), dp(18), dp(15)],
            spacing=dp(12),
        )

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        title = label_text("Get Your Life Back", size=27, color=BLUE, bold=True)
        title.size_hint_y = None
        title.height = dp(45)
        root.add_widget(title)

        subtitle = label_text(
            "Take control, one day at a time.", size=14, color=TEXT_LIGHT
        )
        subtitle.size_hint_y = None
        subtitle.height = dp(30)
        root.add_widget(subtitle)

        # -------------------------------------------------
        # Score card
        # -------------------------------------------------

        score = calculate_score(data["tasks"])

        score_card = Card()

        score_title = label_text(
            "LIFE BACK SCORE", size=13, color=TEXT_LIGHT, bold=True
        )
        score_value = label_text(
            f"{score} / 100", size=27, color=BLUE, bold=True
        )

        score_card.add_widget(score_title)
        score_card.add_widget(score_value)
        root.add_widget(score_card)

        # -------------------------------------------------
        # Streak + XP
        # -------------------------------------------------

        stats = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(90))

        streak_card = Card()
        streak_card.padding = dp(12)

        streak_title = label_text("STREAK", size=12, color=TEXT_LIGHT, bold=True)
        streak_value = label_text(
            f"{data.get('streak', 0)} 🔥", size=21, color=TEAL, bold=True
        )

        streak_card.add_widget(streak_title)
        streak_card.add_widget(streak_value)

        xp_card = Card()
        xp_card.padding = dp(12)

        xp_title = label_text("TOTAL XP", size=12, color=TEXT_LIGHT, bold=True)
        xp_value = label_text(
            f"{data.get('xp', 0)} XP", size=21, color=BLUE, bold=True
        )

        xp_card.add_widget(xp_title)
        xp_card.add_widget(xp_value)

        stats.add_widget(streak_card)
        stats.add_widget(xp_card)
        root.add_widget(stats)

        # -------------------------------------------------
        # Missions title
        # -------------------------------------------------

        mission_title = label_text(
            "TODAY'S MISSIONS", size=15, color=TEXT, bold=True
        )
        mission_title.size_hint_y = None
        mission_title.height = dp(35)
        root.add_widget(mission_title)

        # -------------------------------------------------
        # Tasks
        # -------------------------------------------------

        scroll = ScrollView(do_scroll_x=False)

        task_box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
        )

        task_box.bind(minimum_height=task_box.setter("height"))

        for index, task in enumerate(data["tasks"]):

            row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(54))

            done = task.get("done", False)

            task_button = Button(
                text=("✓ " if done else "○ ") + task.get("name", "Task"),
                background_normal="",
                background_color=GREEN_LIGHT if done else CARD,
                color=GREEN if done else TEXT,
                halign="left",
                valign="middle",
                font_size=dp(14),
                bold=True,
            )

            task_button.bind(
                on_release=lambda button, i=index: self.toggle_task(i)
            )

            points = label_text(
                f"+{task.get('points', 0)}", size=14, color=BLUE, bold=True
            )
            points.size_hint_x = None
            points.width = dp(50)

            row.add_widget(task_button)
            row.add_widget(points)
            task_box.add_widget(row)

        scroll.add_widget(task_box)
        root.add_widget(scroll)

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------

        add_button = ModernButton(text="+ ADD MISSION")
        add_button.bind(on_release=self.show_add_task_popup)
        root.add_widget(add_button)

        time_button = ModernButton(text="⏱ TIME THIEVES")
        time_button.bind(
            on_release=lambda x: setattr(self.manager, "current", "time")
        )
        root.add_widget(time_button)

        progress_button = SmallButton(text="📊 VIEW PROGRESS")
        progress_button.bind(
            on_release=lambda x: setattr(self.manager, "current", "progress")
        )
        root.add_widget(progress_button)

        reset_button = SmallButton(text="↻ RESET / RECOVER")
        reset_button.bind(
            on_release=lambda x: setattr(self.manager, "current", "reset")
        )
        root.add_widget(reset_button)

        self.add_widget(root)

    # =====================================================
    # XP TASK TOGGLE
    # =====================================================

    def toggle_task(self, index):

        data = self.manager.app_data

        task = data["tasks"][index]

        # ---------------------------------------------
        # Completing task
        # ---------------------------------------------

        if not task.get("done", False):

            task["done"] = True

            # Award XP only once
            if not task.get("xp_awarded", False):

                points = task.get("points", 0)

                data["xp"] = data.get("xp", 0) + points

                task["xp_awarded"] = True

        # ---------------------------------------------
        # Unchecking task
        # ---------------------------------------------

        else:

            task["done"] = False

            # IMPORTANT:
            # XP is NOT removed.

        save_today_snapshot(data)
        save_data(data)
        self.build_screen()

    # =====================================================
    # ADD TASK
    # =====================================================

    def show_add_task_popup(self, *args):

        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10),
        )

        name_input = TextInput(
            hint_text="Mission name",
            multiline=False,
            size_hint_y=None,
            height=dp(45),
        )

        points_input = TextInput(
            hint_text="Points",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(45),
        )

        add_button = ModernButton(text="ADD")

        box.add_widget(name_input)
        box.add_widget(points_input)
        box.add_widget(add_button)

        popup = Popup(
            title="Add Mission",
            content=box,
            size_hint=(0.88, None),
            height=dp(260),
        )

        def add_task(*args):

            name = name_input.text.strip()

            try:
                points = int(points_input.text)
            except Exception:
                points = 10

            if not name:
                return

            data = self.manager.app_data

            data["tasks"].append(
                {
                    "name": name,
                    "points": points,
                    "done": False,
                    "xp_awarded": False,
                }
            )

            save_data(data)

            popup.dismiss()

            self.build_screen()

        add_button.bind(on_release=add_task)

        popup.open()


# =========================================================
# TIME SCREEN
# =========================================================

class TimeScreen(Screen):

    def on_enter(self):
        self.build_screen()

    def build_screen(self):

        self.clear_widgets()

        data = self.manager.app_data

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )

        back = create_back_button()
        back.bind(on_release=lambda x: setattr(self.manager, "current", "home"))
        root.add_widget(back)

        title = label_text("Time Thieves", size=27, color=BLUE, bold=True)
        title.size_hint_y = None
        title.height = dp(45)
        root.add_widget(title)

        subtitle = label_text(
            "Track where your time disappears.", size=14, color=TEXT_LIGHT
        )
        subtitle.size_hint_y = None
        subtitle.height = dp(35)
        root.add_widget(subtitle)

        # -------------------------------------------------
        # Today's total time lost
        # -------------------------------------------------

        today = date.today().isoformat()

        total_time = calculate_time_for_day(data, today)

        time_card = Card()
        time_card.height = dp(105)

        time_title = label_text(
            "TODAY'S TIME LOST", size=13, color=TEXT_LIGHT, bold=True
        )
        time_value = label_text(
            format_time(total_time), size=27, color=TEAL, bold=True
        )

        time_card.add_widget(time_title)
        time_card.add_widget(time_value)
        root.add_widget(time_card)

        scroll = ScrollView(do_scroll_x=False)

        box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
        )

        box.bind(minimum_height=box.setter("height"))

        entries = [
            item
            for item in data.get("time_thieves", [])
            if item.get("date") == today
        ]

        if not entries:

            empty = label_text(
                "No time thieves recorded today.", size=15, color=TEXT_LIGHT
            )
            empty.size_hint_y = None
            empty.height = dp(60)

            box.add_widget(empty)

        for item in entries:

            card = Card()
            card.height = dp(75)

            name = label_text(
                item.get("name", "Unknown"), size=15, color=TEXT, bold=True
            )

            minutes = label_text(
                f"{item.get('minutes', 0)} minutes", size=13, color=TEXT_LIGHT
            )

            card.add_widget(name)
            card.add_widget(minutes)

            box.add_widget(card)

        scroll.add_widget(box)
        root.add_widget(scroll)

        add_button = ModernButton(text="+ ADD TIME THIEF")
        add_button.bind(on_release=self.show_add_time_popup)
        root.add_widget(add_button)

        self.add_widget(root)

    def show_add_time_popup(self, *args):

        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10),
        )

        name_input = TextInput(
            hint_text="What stole your time?",
            multiline=False,
            size_hint_y=None,
            height=dp(45),
        )

        minutes_input = TextInput(
            hint_text="Minutes",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(45),
        )

        add_button = ModernButton(text="ADD")

        box.add_widget(name_input)
        box.add_widget(minutes_input)
        box.add_widget(add_button)

        popup = Popup(
            title="Add Time Thief",
            content=box,
            size_hint=(0.88, None),
            height=dp(260),
        )

        def add_time(*args):

            name = name_input.text.strip()

            try:
                minutes = int(minutes_input.text)
            except Exception:
                minutes = 0

            if not name or minutes <= 0:
                return

            data = self.manager.app_data

            data.setdefault("time_thieves", []).append(
                {
                    "date": date.today().isoformat(),
                    "name": name,
                    "minutes": minutes,
                }
            )

            save_today_snapshot(data)
            save_data(data)

            popup.dismiss()

            self.build_screen()

        add_button.bind(on_release=add_time)

        popup.open()


# =========================================================
# PROGRESS SCREEN
# =========================================================

class ProgressScreen(Screen):

    def on_enter(self):
        self.build_screen()

    def build_screen(self):

        self.clear_widgets()

        data = self.manager.app_data

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )

        back = create_back_button()
        back.bind(on_release=lambda x: setattr(self.manager, "current", "home"))
        root.add_widget(back)

        title = label_text("Your Progress", size=27, color=BLUE, bold=True)
        title.size_hint_y = None
        title.height = dp(45)
        root.add_widget(title)

        # -------------------------------------------------
        # XP CARD
        # -------------------------------------------------

        xp_card = Card()
        xp_card.height = dp(110)

        xp_title = label_text("LIFETIME XP", size=13, color=TEXT_LIGHT, bold=True)
        xp_value = label_text(
            f"{data.get('xp', 0)} XP", size=30, color=BLUE, bold=True
        )
        xp_subtitle = label_text(
            "XP never decreases when you uncheck a mission.",
            size=12,
            color=TEXT_LIGHT,
        )

        xp_card.add_widget(xp_title)
        xp_card.add_widget(xp_value)
        xp_card.add_widget(xp_subtitle)
        root.add_widget(xp_card)

        # -------------------------------------------------
        # Stats
        # -------------------------------------------------

        history = data.get("history", [])

        if history:
            scores = [item.get("score", 0) for item in history]
            average_score = round(sum(scores) / len(scores))
        else:
            average_score = 0

        today = date.today().isoformat()

        time_lost = calculate_time_for_day(data, today)

        missions = calculate_completed_tasks(data.get("tasks", []))

        stats = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(95))

        card1 = Card()
        card1.padding = dp(10)
        card1.add_widget(label_text("AVERAGE", 11, TEXT_LIGHT, True))
        card1.add_widget(label_text(f"{average_score}%", 20, BLUE, True))

        card2 = Card()
        card2.padding = dp(10)
        card2.add_widget(label_text("TIME LOST", 11, TEXT_LIGHT, True))
        card2.add_widget(label_text(f"{time_lost}m", 20, TEAL, True))

        card3 = Card()
        card3.padding = dp(10)
        card3.add_widget(label_text("MISSIONS", 11, TEXT_LIGHT, True))
        card3.add_widget(label_text(str(missions), 20, GREEN, True))

        stats.add_widget(card1)
        stats.add_widget(card2)
        stats.add_widget(card3)
        root.add_widget(stats)

        # -------------------------------------------------
        # History
        # -------------------------------------------------

        history_title = label_text("LAST 7 DAYS", size=15, color=TEXT, bold=True)
        history_title.size_hint_y = None
        history_title.height = dp(35)
        root.add_widget(history_title)

        scroll = ScrollView(do_scroll_x=False)

        history_box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
        )

        history_box.bind(minimum_height=history_box.setter("height"))

        recent_history = history[-7:]

        if not recent_history:

            empty = label_text(
                "Your history will appear here.", size=14, color=TEXT_LIGHT
            )
            empty.size_hint_y = None
            empty.height = dp(60)

            history_box.add_widget(empty)

        for item in reversed(recent_history):

            card = Card()
            card.height = dp(75)

            day = label_text(item.get("date", ""), size=13, color=TEXT_LIGHT)

            score = label_text(
                f"Score: {item.get('score', 0)} / 100",
                size=15,
                color=BLUE,
                bold=True,
            )

            time = label_text(
                f"Time lost: {item.get('time_lost', 0)} min",
                size=12,
                color=TEXT_LIGHT,
            )

            card.add_widget(day)
            card.add_widget(score)
            card.add_widget(time)

            history_box.add_widget(card)

        scroll.add_widget(history_box)
        root.add_widget(scroll)

        self.add_widget(root)


# =========================================================
# RESET SCREEN
# =========================================================

class ResetScreen(Screen):

    def on_enter(self):
        self.build_screen()

    def build_screen(self):

        self.clear_widgets()

        data = self.manager.app_data

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )

        back = create_back_button()
        back.bind(on_release=lambda x: setattr(self.manager, "current", "home"))
        root.add_widget(back)

        title = label_text("Reset & Recover", size=27, color=BLUE, bold=True)
        title.size_hint_y = None
        title.height = dp(45)
        root.add_widget(title)

        message = Card()
        message.height = dp(170)

        message.add_widget(
            label_text("You don't need a perfect day.", 18, TEXT, True)
        )
        message.add_widget(
            label_text("Start with one small win.", 15, TEXT_LIGHT)
        )
        message.add_widget(
            label_text(
                "Complete one mission, put the phone away, "
                "and get back on track.",
                14,
                TEXT_LIGHT,
            )
        )

        root.add_widget(message)

        streak_card = Card()
        streak_card.height = dp(100)

        streak_card.add_widget(
            label_text("CURRENT STREAK", 13, TEXT_LIGHT, True)
        )
        streak_card.add_widget(
            label_text(f"{data.get('streak', 0)} days 🔥", 24, TEAL, True)
        )

        root.add_widget(streak_card)

        best_card = Card()
        best_card.height = dp(100)

        best_card.add_widget(label_text("BEST STREAK", 13, TEXT_LIGHT, True))
        best_card.add_widget(
            label_text(f"{data.get('best_streak', 0)} days", 24, BLUE, True)
        )

        root.add_widget(best_card)

        root.add_widget(Widget())

        self.add_widget(root)


# =========================================================
# APP
# =========================================================

class LifeBackApp(App):

    def build(self):

        # Save data in the app's private, writable storage folder
        global DATA_FILE
        DATA_FILE = os.path.join(self.user_data_dir, "life_back.json")

        self.app_data = load_data()

        manager = ScreenManager()

        manager.app_data = self.app_data

        manager.add_widget(HomeScreen(name="home"))
        manager.add_widget(TimeScreen(name="time"))
        manager.add_widget(ProgressScreen(name="progress"))
        manager.add_widget(ResetScreen(name="reset"))

        return manager


if __name__ == "__main__":

    LifeBackApp().run()
