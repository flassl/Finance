from kivy.core.window import Window
from kivy.metrics import dp
##window_width = dp(360)
##window_height = dp(780)
##Window.size = (window_width, window_height)
##Window.top = -500
##Window.left = -1200
from kivy.graphics import Ellipse, Color, Line
from kivy.lang.builder import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivymd.uix.stacklayout import MDStackLayout
from kivymd.app import MDApp
from kivymd.uix.button import MDRectangleFlatButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
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
finance_categories_expense_icon_map = {"groceries": "cart-outline", "rent and services": "home", "pleasures": "glass-wine",
                                       "other": "dots-square"}
finance_categories_expense_color_map = {"groceries": [0.97, 0.18, 0.53, 1], "pleasures": [0.6, 0.2, 0.9, 1],
                                        "rent and services": [0.25, 0.24, 1, 1], "other": [0.25, 0.65, 0.93, 1],
                                        "income": [0.1, 0.65, 0.4, 1]}

item_height = dp(40)


def create_table_balance():
    ##cursor.execute("DROP TABLE IF EXISTS Balance")
    cursor.execute(f""" CREATE TABLE IF NOT EXISTS Balance (
    transaction_id integer PRIMARY KEY,
    date_timestamp real NOT NULL,
    amount real NOT NULL,
    category text NOT NULL,
    name text
    )
    """)
    connection.commit()

    cursor.execute("SELECT * FROM Balance WHERE transaction_id = '-1'")
    total = cursor.fetchone()
    connection.commit()
    if not total:
        cursor.execute(
            f"INSERT INTO Balance VALUES('-1', '{datetime.now().timestamp()}', '0', 'balance', 'balance')")
        connection.commit()


def save_transaction(transaction_datetime, amount, category, is_total, name):
    datetime_timestamp = datetime.timestamp(transaction_datetime)
    if not is_total:
        cursor.execute(
            f"INSERT INTO Balance VALUES(NULL, '{datetime_timestamp}', '{amount}', '{category}', '{name}')")
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
    cursor.execute("SELECT amount FROM Balance WHERE transaction_id = '-1' ORDER BY date_timestamp DESC")
    total = cursor.fetchone()
    connection.commit()
    return total


def fetch_total_expense():
    cursor.execute("SELECT amount FROM Balance WHERE amount < '0' AND transaction_id != '-1' ORDER BY date_timestamp DESC")
    transactions = cursor.fetchall()
    total = 0
    for transaction in transactions:
        total += transaction[0]
    return total


def fetch_transactions(is_expense):
    if is_expense:
        cursor.execute("SELECT * FROM Balance WHERE amount < '0' AND transaction_id != '-1' ORDER BY date_timestamp DESC")
    else:
        cursor.execute("SELECT * FROM Balance WHERE amount > '0' AND transaction_id != '-1' ORDER BY date_timestamp DESC")
    transactions = cursor.fetchall()
    connection.commit()
    return transactions


def fetch_all_transactions():
    cursor.execute("SELECT * FROM Balance WHERE transaction_id != '-1' ORDER BY date_timestamp DESC")
    transactions = cursor.fetchall()
    connection.commit()
    return transactions


def fetch_transactions_by_category(category):
    cursor.execute(f"SELECT * FROM Balance WHERE category = '{category}' ORDER BY date_timestamp DESC")
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
    showed_widget = None
    ticket_holder = None
    transaction_holder = None

    def __init__(self, **kwargs):
        super(Finances, self).__init__(**kwargs)
        Clock.schedule_once(self._add_widgets, 0.1)

    def _add_widgets(self, dt):
        self.balance = fetch_balance()[0]
        self.ticket_holder = self.ids.ticket_holder

    def on_resize(self, *args):
        self.ids.pie_chart.on_resize()

    def show_ticket(self, identifier):
        self.ids.pie_chart.rotate_pie_chart(-self.ids.pie_chart.category_pie_dictionary.get("groceries").slice.angle_start)
        self.ticket_holder.input_amount.text = ""
        self.ticket_holder.input_name.text = ""
        if self.ids.pie_chart.active_transactions is not None:
            self.ids.pie_chart.hide_transactions()
        self.current_identifier = identifier
        if self.ticket_holder.drop_down.dropped_down:
            self.ticket_holder.drop_down.toggle_drop_down()
        if self.current_identifier == 0:
            self.ticket_holder.input_amount.hint_text = "income"
            self.ticket_holder.current_identifier = 0
        if self.current_identifier == 1:
            hint_text = "expense"
            self.ticket_holder.current_identifier = 1
        if self.current_identifier == 0:
            self.ticket_holder.input_amount.hint_text = "income"
        if self.current_identifier == 1:
            self.ticket_holder.input_amount.hint_text = "expense"

        def show_input_fields(dt):
            input_amount = self.ticket_holder.input_amount
            input_name = self.ticket_holder.input_name
            item_size = input_amount.size[1]
            animation = Animation(pos=(self.ticket_holder.pos[0], self.ticket_holder.size[1] - item_size), t='in_out_circ', duration=0.3)
            animation.start(self.ticket_holder.input_amount)
            animation2 = Animation(pos=(self.ticket_holder.pos[0], self.ticket_holder.size[1] - item_size * 2),
                                  t='in_out_circ', duration=0.3)
            animation2.start(input_name)
        self.ticket_holder.hide_commit_button()
        if self.current_identifier == 1:
            Clock.schedule_once(self.ticket_holder.show_drop_down, 0.6)
        if self.current_identifier == 0:
            self.ticket_holder.hide_drop_down()
        Clock.schedule_once(show_input_fields, 0.3)
        self.showed_widget = self.ticket_holder

    def update_balance_display(self, balance):
        self.balance_label.text = str(balance)


class PieChart(MDFloatLayout):
    pie_slices = []
    pie_amount_dictionary = {}
    category_pie_dictionary = {}
    total_expense = 0
    last_progress = 0
    radius_difference = dp(100)
    background_circle = None
    foreground_circle = None
    active_transactions = None
    virgin = True

    def __init__(self, **kwargs):
        super(PieChart, self).__init__(**kwargs)
        Clock.schedule_once(self._add_widgets, 0.1)

    def rotate_pie_chart(self, angle):
        for pie_category in self.category_pie_dictionary:
            pie_slice = self.category_pie_dictionary.get(pie_category)
            animation = Animation(angle_start=pie_slice.slice.angle_start + angle, t='in_cubic', duration=0.3)
            animation &= Animation(angle_end=pie_slice.slice.angle_end + angle, t='in_cubic', duration=0.3)
            animation.start(pie_slice.slice)

    def _add_widgets(self, dt):
        def button_category_on_release(category):

            def show_transactions(*args):
                app = MDApp.get_running_app()
                transactions_widget_width = app.root.width * 0.5
                transactions_widget_height = app.root.height * 0.4
                animation = Animation(pos=(app.root.width/2-transactions_widget_width / 2,
                                           (app.root.height/2 - transactions_widget_height)/2),
                                      t='in_out_circ', duration=0.3)
                animation.start(app.root.ids.transaction_holder)
                self.active_transactions = app.root.ids.transaction_holder

            app = MDApp.get_running_app()
            pie_slice = self.category_pie_dictionary.get(category)
            angle_to_center = pie_slice.slice.angle_start + (pie_slice.slice.angle_end - pie_slice.slice.angle_start) / 2
            angle_to_rotate = 180 - angle_to_center
            self.rotate_pie_chart(angle_to_rotate)
            if app.root.showed_widget is not None:
                app.root.ticket_holder.reset_input_display()
            if self.active_transactions is not None:
                self.hide_transactions()
            app.root.ids.transaction_holder.category = category
            app.root.ids.transaction_holder.fill_transactions()
            Clock.schedule_once(show_transactions, 0.4)

        self.add_pie_slices_and_legend(button_category_on_release)

    def hide_transactions(self):
        app = MDApp.get_running_app()
        transactions_widget_width = app.root.width * 0.5
        transactions_widget_height = app.root.height * 0.4
        animation = Animation(pos=(app.root.width/2-transactions_widget_width / 2, - app.root.height / 2),
                              t='in_out_circ', duration=0.3)
        animation.start(self.active_transactions)

    def add_pie_slices_and_legend(self, button_category_on_release):
        app = MDApp.get_running_app()
        holder_widget = self.parent.parent
        self.size = (holder_widget.size[1] / 3, holder_widget.size[1] / 3)
        self.pos = (holder_widget.size[0] / 2 - self.size[0] / 2, holder_widget.size[1] * 0.55)
        transactions = fetch_transactions(True)
        current_angle = 0
        for category_name in finance_categories_expense:
            self.pie_amount_dictionary.update({category_name: 0})
        if len(transactions) > 0:
            for transaction in transactions:
                if transaction[3] != "balance":
                    self.pie_amount_dictionary[transaction[3]] += transaction[2]
                    self.total_expense += transaction[2]
        if self.background_circle is None:
            self.background_circle = PieSlice(self.pos, self.size, [1, 1, 1, 0.1],
                                              0, 360, "place_holder")
            self.add_widget(self.background_circle)
        if len(app.root.ids.legend.children) <= 0:
            app.root.ids.legend.add_widget(Widget())
        for key in self.pie_amount_dictionary.keys():
            color = finance_categories_expense_color_map.get(key)
            if self.total_expense == 0:
                category_angle = 0.0001
            else:
                category_angle = self.pie_amount_dictionary.get(key) / self.total_expense * 360
            pie_slice = PieSlice(self.pos, self.size, color,
                                 current_angle, current_angle + category_angle, key)
            self.add_widget(pie_slice)
            self.pie_slices.append(pie_slice)
            self.category_pie_dictionary.update({key: pie_slice})
            current_angle += category_angle
            new_button = MDIconButton()
            new_button.icon = finance_categories_expense_icon_map.get(key)
            new_button.theme_icon_color = "Custom"
            new_button.icon_color = color
            new_button.on_release = partial(button_category_on_release, key)
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
        if category in self.pie_amount_dictionary:
            self.pie_amount_dictionary[category] += increment
        else:
            self.pie_amount_dictionary.update({category: increment})
        current_angle = 0
        for pie_slice in self.pie_slices:
            category_angle = 0.001
            if self.total_expense != 0:
                category_angle = self.pie_amount_dictionary.get(pie_slice.category) / self.total_expense * 360
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


class TicketHolder(MDBoxLayout):
    current_identifier = 0
    input_amount = ObjectProperty(None)
    input_name = ObjectProperty(None)
    drop_down = ObjectProperty(None)
    commit_button = ObjectProperty(None)
    transaction_category = None
    is_valid = True
    balance = 0
    transaction_amount = 0
    transaction_value = 0

    def __init__(self, **kwargs):
        super(TicketHolder, self).__init__(**kwargs)

    def show_drop_down(self, *args):
        app = MDApp.get_running_app()
        if self.drop_down.dropped_down:
            self.drop_down.toggle_drop_down()
        animation = Animation(pos=(self.pos[0], app.root.size[1] / 2 - self.input_amount.size[1] * 2
                                   - self.drop_down.size[1]), t='in_out_circ', duration=0.3)
        animation.start(self.drop_down.main_button)

    def hide_drop_down(self):
        animation = Animation(pos=(self.pos[0], 0 - self.drop_down.size[1] - dp(10)), t='in_out_circ', duration=0.3)
        animation.start(self.drop_down.main_button)

    def show_commit_button(self):
        app = MDApp.get_running_app()
        animation = Animation(pos=(self.commit_button.pos[0], app.root.height/2 - self.drop_down.size[1] - dp(10)
                                   - self.input_amount.height * 2 - self.commit_button.height),
                              t='in_out_circ', duration=0.3)
        animation.start(self.commit_button)

    def hide_commit_button(self, *args):
        commit_button = self.commit_button
        animation = Animation(
            pos=(commit_button.pos[0], - commit_button.height - dp(10)),
            t='in_out_circ', duration=0.3)
        animation.start(commit_button)

    def commit_ticket(self, *args):
        app = MDApp.get_running_app()
        app.root.ids.pie_chart.set_last_progress_to0()
        now = datetime.now()
        if self.current_identifier == 1:
            self.transaction_category = self.drop_down.selected.text
        else:
            self.transaction_category = "income"
        if (self.input_amount.text == "") or self.input_amount.text.isalpha():
            self.input_amount.helper_text = "amount is required"
            self.input_amount.error = True
            self.is_valid = False
        elif self.current_identifier == 0:
            # to do : check for input acceptance
            self.transaction_value = float(self.input_amount.text)
            self.balance += float(self.input_amount.text)
            save_transaction(now, float(self.input_amount.text), self.transaction_category, False, self.input_name.text)
        elif self.current_identifier == 1:
            # to do : check for input acceptance
            self.transaction_value = - float(self.input_amount.text)
            self.balance -= float(self.input_amount.text)
            save_transaction(now, - float(self.input_amount.text), self.drop_down.selected.text, False, self.input_name.text)
        if self.is_valid:
            self.transaction_amount = float(self.input_amount.text)
            animation = Animation(pos=(self.commit_button.pos[0], self.commit_button.pos[1] + 50), t='out_cubic')
            animation.bind(on_progress=self.commit_on_progress_callback)
            animation.start(self.commit_button)
            ##self.animate_y(self.ticket_holder.ids.input_amount, 50)
            ##self.animate_y(self.ticket_holder.ids.input_name, 50)
            if self.current_identifier == 1:
                self.animate_y(self.drop_down.selected, dp(30))
            self.animate_y(self.input_amount, dp(30))
            self.animate_y(self.input_name, dp(30))
            animation.bind(on_complete=self.reset_input_display)
            save_transaction(now, self.balance, self.transaction_category, True, "balance")

    def commit_on_progress_callback(self, *args):
        app = MDApp.get_running_app()
        progress = args[2]
        regressive_progress = 1 - progress
        input = self.input_amount
        self.update_input_display("{:.2f}".format(self.transaction_amount * regressive_progress))
        app.root.update_balance_display("{:.2f}".format(self.balance - regressive_progress * float(input.text)))
        if self.transaction_value < 0:
            app.root.ids.pie_chart.update_pie(self.transaction_value, self.transaction_category, progress)

    def reset_input_display(self, *args):
        input = self.input_amount
        name = self.input_name
        main_button = self.drop_down.main_button
        item_size = main_button.size[1]
        animation = Animation(pos=(input.pos[0], -item_size - dp(10)), t='in_out_circ', duration=0.3)
        animation.start(input)
        animation.start(name)
        animation.start(main_button)
        self.drop_down.clear_items()
        input.text = ""
        name.text = ""
        self.hide_commit_button()
        self.showed_widget = None

    def inflate_items(self):
        if self.drop_down.dropped_down:
            self.drop_down.toggle_drop_down()
        if self.current_identifier == 0:
            self.input_amount.hint_text = "income"
            self.drop_down.inflate_items(finance_categories_income)
        if self.current_identifier == 1:
            self.input_amount.hint_text = "expense"
            self.drop_down.inflate_items(finance_categories_expense)

    def update_input_display(self, balance):
        self.input_amount.text = str(balance)

    def animate_y(self, item, amount):
        animation = Animation(pos=(item.pos[0], item.pos[1] + amount), t='out_cubic')
        animation.start(item)

    def reset_amount_input(self):
        self.is_valid = True
        self.input_amount.error = False
        if self.input_amount.text.isalpha():
            self.input_amount.helper_text = "input a number"
            self.input_amount.text = ""
            self.input_amount.error = True
            self.is_valid = False
        if (self.current_identifier == 0) and self.is_valid and self.input_amount.text != "":
            self.show_commit_button()
        ##self.pos = (self.pos[0], self.parent.height)
        self.is_valid = True


class TransactionHolder(MDBoxLayout):
    category = ""
    transactions = []
    stack_layout = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(TransactionHolder, self).__init__(size_hint=(None, None), **kwargs)
        self.pos = (self.pos[0], - self.height * 4)

    def fill_transactions(self):
        self.transactions = fetch_transactions_by_category(self.category)
        print(self.transactions)
        def setup_widget(*args):
            transactions_total_value = 0
            for transaction in self.transactions:
                transactions_total_value += transaction[2]

            color = finance_categories_expense_color_map.get(self.category)
            if transactions_total_value != 0:
                percentage_string = str(round((transactions_total_value / fetch_total_expense()) * 100))
                self.ids.category_expense_percentage_label.text = percentage_string + "%"
            else:
                self.ids.category_expense_percentage_label.text = "No expense"
            self.ids.category_expense_percentage_label.color = color
            self.ids.category_expense_label.text = str(transactions_total_value)
            self.ids.category_expense_label.color = color
            self.ids.scroll_view.size = self.size
            self.ids.scroll_view.bar_color = [0, 0, 0, 0]
            self.ids.scroll_view.bar_inactive_color = [0, 0, 0, 0]
            self.stack_layout.size = (self.size[0], len(self.transactions) * (item_height + dp(7)))
            self.stack_layout.clear_widgets(self.stack_layout.children)
            for transaction in self.transactions:
                transaction_view = TransactionView(transaction[3], transaction[4],
                                                   transaction[2], color)
                self.stack_layout.add_widget(transaction_view)

        Clock.schedule_once(setup_widget, 0.4)


class TransactionView(MDBoxLayout):
    def __init__(self, category, name, amount, color, **kwargs):
        super(TransactionView, self).__init__(**kwargs)

        def setup_widget():
            self.category = category
            self.name = name
            self.amount = amount
            self.height = item_height
            self.ids.name.text = name
            self.ids.name.color = color
            self.ids.amount.text = str(amount)
            self.ids.amount.color = color

        setup_widget()


class BalanceLabel(MDFlatButton):
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

    def show_total_transactions(self):
        app = MDApp.get_running_app()

        def inflate_transactions(*args):

            pie_chart = app.root.ids.pie_chart
            transaction_holder = app.root.ids.transaction_holder
            pie_chart.rotate_pie_chart(-pie_chart.category_pie_dictionary.get("groceries").slice.angle_start)
            transaction_holder.stack_layout.clear_widgets(transaction_holder.stack_layout.children)
            transactions = fetch_all_transactions()
            total_expense = 0
            total_income = 0
            transaction_holder.stack_layout.size = (transaction_holder.size[0], len(transactions) * (item_height + dp(7)))
            for transaction in transactions:
                if transaction[2] > 0:
                    total_income += transaction[2]
                else:
                    total_expense += transaction[2]
                text = transaction[4]
                color = None
                if transaction[2] > 0:
                    color = finance_categories_expense_color_map.get("income")
                else:
                    color = app.theme_cls.primary_dark
                if transaction[4] == "":
                    text = transaction[3]
                transaction_view = TransactionView(transaction[3], text,
                                                   transaction[2], color)
                transaction_holder.stack_layout.add_widget(transaction_view)
            if abs(total_income) > abs(total_expense):
                transaction_holder.ids.category_expense_percentage_label.text = str(total_expense)
                transaction_holder.ids.category_expense_label.text = str(total_income)
                transaction_holder.ids.category_expense_percentage_label.color = app.theme_cls.primary_dark
                transaction_holder.ids.category_expense_label.color = finance_categories_expense_color_map.get("income")
            else:
                transaction_holder.ids.category_expense_percentage_label.text = str(total_income)
                transaction_holder.ids.category_expense_label.text = str(total_expense)
                transaction_holder.ids.category_expense_percentage_label.color = finance_categories_expense_color_map.get("income")
                transaction_holder.ids.category_expense_label.color = app.theme_cls.primary_dark


            transaction_holder.ids.scroll_view.size = self.size
            transaction_holder.ids.scroll_view.bar_color = [0, 0, 0, 0]
            transaction_holder.ids.scroll_view.bar_inactive_color = [0, 0, 0, 0]

        def show_transactions(*args):
            animation = Animation(pos=(app.root.width / 2 - app.root.ids.transaction_holder.width / 2,
                                       (app.root.height / 2 - app.root.ids.transaction_holder.height) / 2),
                                  t='in_out_circ', duration=0.3)
            animation.start(app.root.ids.transaction_holder)
            app.root.ids.pie_chart.active_transactions = app.root.ids.transaction_holder

        if app.root.showed_widget is not None:
            app.root.ticket_holder.reset_input_display()
        if app.root.ids.pie_chart.active_transactions is not None:
            app.root.ids.pie_chart.hide_transactions()
        Clock.schedule_once(inflate_transactions, 0.3)
        Clock.schedule_once(show_transactions, 0.4)


class DropDownMenu(MDFloatLayout):
    items = []
    selected = ObjectProperty(None)
    dropped_down = False
    main_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs)

        def resize(dt):
            self.size = self.main_button.size
        Clock.schedule_once(resize, 0.1)

    def clear_items(self):
        for item in self.items:
            self.remove_widget(item)
        self.items.clear()

    def inflate_items(self, item_names):

        def set_selected(item):
            app = MDApp.get_running_app()
            self.main_button.pos = (self.pos[0], - item.height - 10)
            for iterated_item in self.items:
                if iterated_item != item:
                    self.remove_widget(iterated_item)
            self.selected = item
            animation = Animation(pos=(self.pos[0], app.root.size[1] / 2 - app.root.ticket_holder.input_amount.size[1] * 2
                                  - app.root.ticket_holder.drop_down.size[1]), t='in_out_circ', duration=0.3)
            animation.start(item)
            app = MDApp
            app.get_running_app().root.ticket_holder.show_commit_button()

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
        app.root.ticket_holder.hide_commit_button()
        app.root.ticket_holder.show_drop_down()

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
                animation = Animation(pos=(self.pos[0], self.pos[1]), t='in_out_circ',
                                      duration=(0.3 + len(self.items)-index) / 10)
                animation.bind(on_progress=partial(check_for_hide, item))
                animation.start(item)
            self.main_button.text_color = app.theme_cls.primary_dark
            self.main_button.line_color = app.theme_cls.primary_dark

        def drop_down():
            app.root.ticket_holder.inflate_items()
            for index, item in enumerate(self.items):
                #alpha animation
                item.pos = self.pos
                animation = Animation(pos=(self.pos[0], self.main_button.pos[1] - (item.height + dp(10)) * (index + 1)), t='in_out_circ',
                                      duration=(0.3 + index * 0.1))
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
        return Builder.load_file("FinanceLayout.kv")

    def on_start(self):
        app = MDApp.get_running_app()
        create_table_balance()
        Window.bind(size=app.root.on_resize)
        Window.softinput_mode = "below_target"
        Window.release_all_keyboards()


if __name__ == '__main__':
    FinanceApp().run()


##canvas.before:
##        Color:
##            rgba: app.theme_cls.primary_dark
##        Line:
##            width: 1
##            rectangle: (self.x, self.y, self.width, self.height)
