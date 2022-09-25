from kivy.core.window import Window
from kivy.metrics import dp
##window_width = dp(360)
##window_height = dp(780)
##Window.size = (window_width, window_height)
##Window.top = -500
##Window.left = -1200
from kivy.graphics import Ellipse, Color
from kivy.lang.builder import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivy.properties import ObjectProperty
from kivy.animation import Animation
from datetime import datetime
from functools import partial
import sqlite3 as sl

connection = sl.connect("OrganizerApp.db")
cursor = connection.cursor()

finance_categories_income = ["wage", "gift", "independency", "other"]
finance_categories_expense = ["groceries", "pleasures", "rent and services", "other"]
finance_categories_expense_icon_map = {"groceries": "food-apple", "rent and services": "home", "pleasures": "tea",
                                       "other": "dots-square"}
finance_categories_expense_color_map = {"groceries": [0.97, 0.18, 0.53, 1], "pleasures": [0.43, 0.05, 0.7, 1],
                                        "rent and services": [0.21, 0.06, 0.68, 1], "other": [0.25, 0.65, 0.93, 1]}



def create_table_balance():
    ##cursor.execute("DROP TABLE IF EXISTS Balance")
    cursor.execute(f""" CREATE TABLE IF NOT EXISTS Balance (
    transaction_id integer PRIMARY KEY,
    date_timestamp real NOT NULL,
    amount real NOT NULL,
    category text NOT NULL
    )
    """)
    connection.commit()

    cursor.execute("SELECT * FROM Balance WHERE transaction_id = '-1'")
    total = cursor.fetchone()
    connection.commit()
    if not total:
        cursor.execute(
            f"INSERT INTO Balance VALUES('-1', '{datetime.now().timestamp()}', '0', 'other')")
        connection.commit()


def save_transaction(transaction_datetime, amount, category, is_total):
    datetime_timestamp = datetime.timestamp(transaction_datetime)
    if not is_total:
        cursor.execute(
            f"INSERT INTO Balance VALUES(NULL, '{datetime_timestamp}', '{amount}', '{category}')")
        connection.commit()
    if is_total:
        cursor.execute(
            f"UPDATE Balance "
            f"SET "
            f"amount = '{amount}', "
            f"date_timestamp = '{datetime_timestamp}' "
            f"WHERE "
            f"transaction_id = '-1'")
        connection.commit()


def fetch_balance():
    cursor.execute("SELECT amount FROM Balance WHERE transaction_id = '-1'")
    total = cursor.fetchone()
    connection.commit()
    return total


def fetch_transactions(is_expense):
    if is_expense:
        cursor.execute("SELECT * FROM Balance WHERE amount < '0'")
    else:
        cursor.execute("SELECT * FROM Balance WHERE amount < '0'")
    transactions = cursor.fetchall()
    connection.commit()
    return transactions


class Finances(MDFloatLayout):
    current_identifier = 0
    balance = 0
    transaction_amount = 0
    transaction_value = 0
    transaction_category = ""
    drop_down = ObjectProperty(None)
    balance_label = ObjectProperty(None)
    is_valid = True
    keyboard = None

    def __init__(self, **kwargs):
        super(Finances, self).__init__(**kwargs)
        Clock.schedule_once(self._add_widgets, 0.1)
        self.keyboard = Window.request_keyboard(self.keyboard_closed, self, 'text')

    def _add_widgets(self, dt):
        app = MDApp.get_running_app()
        self.balance = fetch_balance()[0]
        self.ids.input_field.bind(pos=self.update_pos)
        self.drop_down = DropDownMenu("Category")
        self.ids.drop_down_holder.add_widget(self.drop_down)

    def on_resize(self, *args):
        self.ids.pie_chart.on_resize()

    def keyboard_closed(self):
        pass
    def show_drop_down(self):
        if self.drop_down.dropped_down:
            self.drop_down.toggle_drop_down()
        input_field = self.ids.input_field
        animation = Animation(pos=(input_field.pos[0], self.ids.input_field.size[1] - 3 * self.ids.input_amount.size[1])
                              , t='out_cubic', duration=0.5)
        animation.start(self.drop_down.main_button)

    def show_ticket(self, identifier):
        app = MDApp.get_running_app()
        input_field = self.ids.input_field
        animation = Animation(pos=(input_field.pos[0], input_field.size[1] - 1 * self.ids.input_amount.size[1]),
                              t='out_cubic', duration=0.5)
        animation.start(self.ids.input_amount)
        animation = Animation(pos=(input_field.pos[0], input_field.size[1] - 2 * self.ids.input_amount.size[1]),
                              t='out_cubic', duration=0.5)
        animation.start(self.ids.input_name)
        animation = Animation(pos=(input_field.pos[0], self.ids.input_field.size[1] - 3 * self.ids.input_amount.size[1])
                              , t='out_cubic', duration=0.5)
        animation.start(self.drop_down)
        self.current_identifier = identifier
        if self.drop_down.dropped_down:
            self.drop_down.toggle_drop_down()
        self.show_drop_down()
        if self.current_identifier == 0:
            self.ids.input_amount.hint_text = "income"
        if self.current_identifier == 1:
            self.ids.input_amount.hint_text = "expense"

    def inflate_items(self):
        if self.drop_down.dropped_down:
            self.drop_down.toggle_drop_down()
        if self.current_identifier == 0:
            self.ids.input_amount.hint_text = "income"
            self.drop_down.inflate_items(finance_categories_income)
        if self.current_identifier == 1:
            self.ids.input_amount.hint_text = "expense"
            self.drop_down.inflate_items(finance_categories_expense)

    def show_commit_button(self):
        commit_button = self.ids.commit_button
        animation = Animation(pos=(commit_button.pos[0], self.ids.input_field.size[1] - 5 * self.ids.input_name.size[1]),
                              t='out_cubic', duration=1)
        animation.start(commit_button)

    def hide_commit_button(self):
        commit_button = self.ids.commit_button
        animation = Animation(pos=(self.ids.commit_button.pos[0], - self.ids.commit_button.height - 10), t='out_cubic')
        animation.start(commit_button)

    def reset_amount_input(self):
        self.ids.input_amount.error = False
        if self.ids.input_amount.text.isalpha():
            self.ids.input_amount.helper_text = "input a number"
            self.ids.input_amount.text = ""
            self.ids.input_amount.error = True
        self.pos = (self.pos[0], self.parent.height)
        self.is_valid = True

    def commit_ticket(self):
        self.ids.pie_chart.set_last_progress_to0()
        now = datetime.now()
        self.transaction_category = self.drop_down.selected.text
        if (self.ids.input_amount.text == "") or self.ids.input_amount.text.isalpha():
            self.ids.input_amount.helper_text = "amount is required"
            self.ids.input_amount.error = True
            self.is_valid = False
        elif self.current_identifier == 0:
            # to do : check for input acceptance
            self.transaction_value = float(self.ids.input_amount.text)
            self.balance += float(self.ids.input_amount.text)
            save_transaction(now, self.ids.input_amount.text, self.drop_down.selected.text, False)
        elif self.current_identifier == 1:
            # to do : check for input acceptance
            self.transaction_value = - float(self.ids.input_amount.text)
            self.balance -= float(self.ids.input_amount.text)
            save_transaction(now, - float(self.ids.input_amount.text), self.drop_down.selected.text, False)
        if self.is_valid:
            self.transaction_amount = float(self.ids.input_amount.text)
            animation = Animation(pos=(self.ids.commit_button.pos[0], self.ids.commit_button.pos[1] + 50), t='out_cubic')
            animation.bind(on_progress=self.commit_on_progress_callback)
            animation.start(self.ids.commit_button)
            self.animate_y(self.ids.input_amount, 50)
            self.animate_y(self.ids.input_name, 50)
            self.animate_y(self.drop_down.selected, 50)
            animation.bind(on_complete=self.reset_input_display)
            save_transaction(now, self.balance, self.drop_down.selected.text, True)

    def animate_y(self, item, amount):
        animation = Animation(pos=(item.pos[0], item.pos[1] + amount), t='out_cubic')
        animation.start(item)

    def update_balance_display(self, balance):
        self.balance_label.text = str(balance)

    def update_input_display(self, balance):
        self.ids.input_amount.text = str(balance)

    def update_pos(self, *args):
        relative_pos = self.ids.input_field.pos
        self.ids.input_amount.pos = relative_pos

    def commit_on_progress_callback(self, *args):
        progress = args[2]
        regressive_progress = 1 - progress
        input = self.ids.input_amount
        self.update_input_display("{:.2f}".format(self.transaction_amount * regressive_progress))
        self.update_balance_display("{:.2f}".format(self.balance - regressive_progress * float(input.text)))
        if self.transaction_value < 0:
            self.ids.pie_chart.update_pie(self.transaction_value, self.transaction_category, progress)

    def reset_input_display(self, *args):
        input = self.ids.input_amount
        name = self.ids.input_name
        self.animate_y(input, -50)
        self.animate_y(name, -50)
        self.drop_down.pos = (self.drop_down.pos[0], self.drop_down.pos[1] + 50)
        self.animate_y(self.drop_down, -50)
        self.drop_down.clear_items()
        self.show_drop_down()
        input.text = ""
        name.text = ""
        self.hide_commit_button()
        pass


class PieChart(MDFloatLayout):
    pie_slices = []
    pie_dictionary = {}
    total_expense = 0
    last_progress = 0
    radius_difference = dp(100)
    background_circle = None
    foreground_circle = None
    virgin = True

    def __init__(self, **kwargs):
        super(PieChart, self).__init__(**kwargs)
        Clock.schedule_once(self._add_widgets, 0.1)

    def _add_widgets(self, dt):
        app = MDApp.get_running_app()
        holder_widget = self.parent.parent
        self.size = (holder_widget.size[1] / 3, holder_widget.size[1] / 3)
        self.pos = (holder_widget.size[0] / 2 - self.size[0] / 2, holder_widget.size[1] * 0.55)
        transactions = fetch_transactions(True)
        current_angle = 0
        for category_name in finance_categories_expense:
            self.pie_dictionary.update({category_name: 0})
        if len(transactions) > 0:
            for transaction in transactions:
                self.pie_dictionary[transaction[3]] += transaction[2]
                self.total_expense += transaction[2]
        if self.background_circle is None:
            self.background_circle = PieSlice(self.pos, self.size, [1, 1, 1, 0.1],
                                              0, 360, "place_holder")
            self.add_widget(self.background_circle)
        if len(app.root.ids.legend.children) <= 0:
            app.root.ids.legend.add_widget(Widget())
        for key in self.pie_dictionary.keys():
            color = finance_categories_expense_color_map.get(key)
            if self.total_expense == 0:
                category_angle = 0.0001
            else:
                category_angle = self.pie_dictionary.get(key) / self.total_expense * 360
            pie_slice = PieSlice(self.pos, self.size, color,
                                 current_angle, current_angle + category_angle, key)
            self.add_widget(pie_slice)
            self.pie_slices.append(pie_slice)
            current_angle += category_angle
            new_button = MDIconButton()
            new_button.icon = finance_categories_expense_icon_map.get(key)
            new_button.theme_icon_color = "Custom"
            new_button.icon_color = color
            if len(app.root.ids.legend.children) <= len(finance_categories_expense) + 1:
                app.root.ids.legend.add_widget(new_button)
        if len(app.root.ids.legend.children) <= len(finance_categories_expense) + 1:
            app.root.ids.legend.add_widget(Widget())

        new_size = (self.size[0] - self.radius_difference, self.size[0] - self.radius_difference)
        new_pos = (0 + holder_widget.size[0] / 2 - (self.size[0] - self.radius_difference) / 2,
                   self.pos[1] + self.radius_difference / 2)
        if self.foreground_circle is None:
            self.foreground_circle = PieSlice(new_pos, new_size, app.theme_cls.bg_normal, 0, 360, "bg")
            self.add_widget(self.foreground_circle)
            app.root.balance_label = BalanceLabel()
            self.add_widget(app.root.balance_label)

    def on_resize(self):
        app = MDApp.get_running_app()
        holder_widget = self.parent.parent
        self.pos = (holder_widget.size[0] / 2 - self.size[0] / 2, holder_widget.size[1] * 0.55)
        self.size = (holder_widget.size[1] / 3, holder_widget.size[1] / 3)
        new_size = (self.size[0] - self.radius_difference, self.size[0] - self.radius_difference)
        new_pos = (holder_widget.size[0] / 2 - (self.size[0] - self.radius_difference) / 2,
                   self.pos[1] + self.radius_difference / 2)
        self.foreground_circle.on_resize(new_size, new_pos)
        self.background_circle.on_resize(self.size, self.pos)
        app.root.balance_label.place_widget(0.1)
        for pie_slice in self.pie_slices:
            pie_slice.on_resize(self.size, self.pos)

    def update_pie(self, value, category, progress):
        progress_delta = progress - self.last_progress
        self.last_progress = progress
        increment = value * progress_delta
        self.total_expense += increment
        if category in self.pie_dictionary:
            self.pie_dictionary[category] += increment
        else:
            self.pie_dictionary.update({category: increment})
        current_angle = 0
        for pie_slice in self.pie_slices:
            category_angle = 0.001
            if self.total_expense != 0:
                category_angle = self.pie_dictionary.get(pie_slice.category) / self.total_expense * 360
            pie_slice.slice.angle_start = current_angle
            pie_slice.slice.angle_end = current_angle + category_angle
            current_angle += category_angle

    def set_last_progress_to0(self):
        self.last_progress = 0


class PieSlice(FloatLayout):
    category = ""

    def __init__(self, pos, size, color, angle_start, angle_end, category, **kwargs):
        super(PieSlice, self).__init__(**kwargs)
        self.category = category
        with self.canvas.before:
            Color(*color)
            self.slice = Ellipse(pos=pos, size=size,
                                 angle_start=angle_start,
                                 angle_end=angle_end)

    def on_resize(self, size, pos):
        self.size = size
        self.slice.size = size
        self.pos = pos
        self.slice.pos = pos


class BalanceLabel(MDLabel):
    def __init__(self, **kwargs):
        super(BalanceLabel, self).__init__(**kwargs)
        Clock.schedule_once(self.place_widget, 0.1)

    def place_widget(self, dt):
        app = MDApp.get_running_app()
        self.width = self.parent.width
        self.height = self.parent.height
        self.pos = self.parent.pos
        self.text = (str)(app.root.balance)
        self.color = app.theme_cls.primary_dark


class DropDownMenu(MDFloatLayout):
    items = []
    text = ""
    selected = ObjectProperty(None)
    dropped_down = False
    main_button = ObjectProperty(None)

    def __init__(self, text, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs)

        self.text = text

        self.set_view()

    def set_view(self):
        main_button = MDRectangleFlatButton(text=self.text, top=self.top)
        main_button.theme_text_color = "Custom"
        main_button.pos_hint = {"center_x": .5}
        main_button.on_release = self.toggle_drop_down
        self.main_button = main_button
        self.add_widget(self.main_button)
        self.bind(pos=self.update_pos)

    def update_pos(self, *args):
        self.main_button.pos = self.pos

    def clear_items(self):
        for item in self.items:
            self.remove_widget(item)
        self.items.clear()

    def inflate_items(self, item_names):

        def set_selected(item):
            self.main_button.pos = (self.pos[0], - item.height - 10)
            for iterated_item in self.items:
                if iterated_item != item:
                    self.remove_widget(iterated_item)
            self.selected = item
            animation = Animation(pos=self.pos, t='in_back', duration=0.3)
            animation.start(item)
            app = MDApp
            app.get_running_app().root.show_commit_button()

        self.clear_items()

        for item_name in item_names:
            item = MDRectangleFlatButton(text=item_name, top=10)
            item.theme_text_color = "Custom"
            if item_name in finance_categories_expense_color_map:
                item.text_color = finance_categories_expense_color_map.get(item_name)
                item.line_color = finance_categories_expense_color_map.get(item_name)
            item.pos_hint = {"center_x": .5}
            item.on_release = partial(set_selected, item)
            self.items.append(item)
            self.add_widget(item)
        app = MDApp.get_running_app()
        app.root.hide_commit_button()
        app.root.show_drop_down()
        self.update_pos()

    def toggle_drop_down(self, *args):
        app = MDApp.get_running_app()

        def collapse():
            def check_for_hide(item, *args):
                if args[2] > 0.85:
                    hide_item(item)
            def hide_item(item):
                Animation.cancel(animation, item)
                item.pos = (self.pos[0], - self.pos[1] - item.height * 10 - dp(20))

            for index, item in enumerate(self.items):
                ##item.pos = self.pos
                animation = Animation(pos=(self.pos[0], self.pos[1]), t='in_back',
                                      duration=(0.3 + len(self.items)-index) / 10)
                animation.bind(on_progress=partial(check_for_hide, item))
                animation.start(item)
            self.main_button.text_color = app.theme_cls.primary_dark
            self.main_button.line_color = app.theme_cls.primary_dark

        def drop_down():
            app.root.inflate_items()
            for index, item in enumerate(self.items):
                item.pos = self.pos
                animation = Animation(pos=(self.pos[0], self.pos[1] - (item.height + 10) * (index + 1)), t='out_cubic',
                                      duration=0.3 - index/10)
                animation.start(item)
            self.main_button.text_color = "gray"
            self.main_button.line_color = "gray"
            pass

        if self.dropped_down:
            collapse()
            self.dropped_down = False
        elif not self.dropped_down:
            drop_down()
            self.dropped_down = True


class FinanceApp (MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Pink"
        return Builder.load_file("Finance.kv")

    def on_start(self):
        app = MDApp.get_running_app()
        create_table_balance()
        Window.bind(size=app.root.on_resize)
        Window.softinput_mode = "below_target"
        Window.release_all_keyboards()


if __name__ == '__main__':
    FinanceApp().run()
