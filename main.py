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
from kivymd.uix.button import MDRectangleFlatButton, MDIconButton
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


def fetch_transactions_by_cathegory(category):
    cursor.execute(f"SELECT * FROM Balance WHERE category = '{category}'")
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

    def __init__(self, **kwargs):
        super(Finances, self).__init__(**kwargs)
        Clock.schedule_once(self._add_widgets, 0.1)
        print(1)

    def _add_widgets(self, dt):
        self.balance = fetch_balance()[0]

    def on_resize(self, *args):
        self.ids.pie_chart.on_resize()

    def show_drop_down(self, *args):
        if self.ticket_holder.drop_down.dropped_down:
            self.ticket_holder.drop_down.toggle_drop_down()
        input_field = self.ids.input_field
        animation = Animation(pos=(input_field.pos[0], self.ticket_holder.drop_down.pos[1])
                              , t='out_cubic', duration=0.5)
        animation.start(self.ticket_holder.drop_down.main_button)

    def show_ticket(self, identifier):
        if self.ticket_holder is None:
            self.ticket_holder = TicketHolder((self.pos[0], self.pos[1] - self.size[1] /2), (self.size[0] * 0.5, self.size[1] /2))
            self.add_widget(self.ticket_holder)
        self.current_identifier = identifier
        if self.ticket_holder.drop_down.dropped_down:
            self.ticket_holder.drop_down.toggle_drop_down()
        self.show_drop_down()
        if self.current_identifier == 0:
            self.ticket_holder.input_amount.hint_text = "income"
        if self.current_identifier == 1:
            self.ticket_holder.input_amount.hint_text = "expense"

        Clock.schedule_once(self.show_drop_down, 0.1)
        animation = Animation(pos=(self.ticket_holder.pos[0], 0), t='in_cubic', duration=0.3)
        animation.start(self.ticket_holder)
        if self.ticket_holder.commit_button is not None:
            self.hide_commit_button()

    def inflate_items(self):
        if self.ticket_holder.drop_down.dropped_down:
            self.ticket_holder.drop_down.toggle_drop_down()
        if self.current_identifier == 0:
            self.ticket_holder.input_amount.hint_text = "income"
            self.ticket_holder.drop_down.inflate_items(finance_categories_income)
        if self.current_identifier == 1:
            self.ticket_holder.input_amount.hint_text = "expense"
            self.ticket_holder.drop_down.inflate_items(finance_categories_expense)

    def show_commit_button(self):
        app = MDApp.get_running_app()
        if self.ticket_holder.commit_button is None:
            self.ticket_holder.commit_button = MDIconButton(icon="chevron-double-up", size_hint=(1, 1), top=0, padding=10,
                                              pos= (self.pos[0] + self.ticket_holder.size[0] / 2, self.pos[1]),
                                              theme_icon_color="Custom", icon_color=app.theme_cls.primary_dark,
                                              on_release=app.root.commit_ticket)
            self.ticket_holder.add_widget(self.ticket_holder.commit_button)
        animation = Animation(pos=(self.ticket_holder.commit_button.pos[0], self.ids.input_field.size[1] - 5 * self.ticket_holder.input_name.size[1]),
                              t='out_cubic', duration=1)
        animation.start(self.ticket_holder.commit_button)

    def hide_commit_button(self, *args):
        commit_button = self.ticket_holder.commit_button
        animation = Animation(pos=(self.ticket_holder.commit_button.pos[0], - self.ticket_holder.commit_button.height - 10), t='out_cubic')
        animation.start(commit_button)

    def commit_ticket(self, *args):
        self.ids.pie_chart.set_last_progress_to0()
        now = datetime.now()
        self.transaction_category = self.ticket_holder.drop_down.selected.text
        if (self.ticket_holder.input_amount.text == "") or self.ticket_holder.input_amount.text.isalpha():
            self.ticket_holder.input_amount.helper_text = "amount is required"
            self.ticket_holder.input_amount.error = True
            self.is_valid = False
        elif self.current_identifier == 0:
            # to do : check for input acceptance
            self.transaction_value = float(self.ticket_holder.input_amount.text)
            self.balance += float(self.ticket_holder.input_amount.text)
            save_transaction(now, self.ticket_holder.input_amount.text, self.ticket_holder.drop_down.selected.text, False)
        elif self.current_identifier == 1:
            # to do : check for input acceptance
            self.transaction_value = - float(self.ticket_holder.input_amount.text)
            self.balance -= float(self.ticket_holder.input_amount.text)
            save_transaction(now, - float(self.ticket_holder.input_amount.text), self.ticket_holder.drop_down.selected.text, False)
        if self.is_valid:
            self.transaction_amount = float(self.ticket_holder.input_amount.text)
            animation = Animation(pos=(self.ticket_holder.commit_button.pos[0], self.ticket_holder.commit_button.pos[1] + 50), t='out_cubic')
            animation.bind(on_progress=self.commit_on_progress_callback)
            animation.start(self.ticket_holder.commit_button)
            self.animate_y(self.ticket_holder.input_amount, 50)
            self.animate_y(self.ticket_holder.input_name, 50)
            self.animate_y(self.ticket_holder.drop_down.selected, 50)
            animation.bind(on_complete=self.reset_input_display)
            save_transaction(now, self.balance, self.ticket_holder.drop_down.selected.text, True)

    def animate_y(self, item, amount):
        animation = Animation(pos=(item.pos[0], item.pos[1] + amount), t='out_cubic')
        animation.start(item)

    def update_balance_display(self, balance):
        self.balance_label.text = str(balance)

    def update_input_display(self, balance):
        self.ticket_holder.input_amount.text = str(balance)

    def update_pos(self, *args):
        relative_pos = self.ticket_holder.ids.input_field.pos
        self.ticket_holder.ids.input_amount.pos = relative_pos

    def commit_on_progress_callback(self, *args):
        progress = args[2]
        regressive_progress = 1 - progress
        input = self.ticket_holder.input_amount
        self.update_input_display("{:.2f}".format(self.transaction_amount * regressive_progress))
        self.update_balance_display("{:.2f}".format(self.balance - regressive_progress * float(input.text)))
        if self.transaction_value < 0:
            self.ids.pie_chart.update_pie(self.transaction_value, self.transaction_category, progress)

    def reset_input_display(self, *args):
        def delete_ticket_holder(*args):
            self.ticket_holder = None
        input = self.ticket_holder.input_amount
        name = self.ticket_holder.input_name
        self.animate_y(self.ticket_holder, -self.ticket_holder.height)
        self.animate_y(self.ticket_holder.drop_down.main_button, -self.ticket_holder.height)
        self.ticket_holder.drop_down.clear_items()
        Clock.schedule_once(delete_ticket_holder, 0.4)
        input.text = ""
        name.text = ""
        self.hide_commit_button()
        pass


class PieChart(MDFloatLayout):
    pie_slices = []
    pie_amount_dictionary = {}
    category_pie_dictionary = {}
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
        def button_category_on_release(category):
            def rotate_pie_chart (angle):
                for pie_category in self.category_pie_dictionary:
                    pie_slice = self.category_pie_dictionary.get(pie_category)
                    animation = Animation(angle_start=pie_slice.slice.angle_start+angle, t='in_cubic', duration=0.3)
                    animation &= Animation(angle_end=pie_slice.slice.angle_end+angle, t='in_cubic', duration=0.3)
                    animation.start(pie_slice.slice)

            def show_transactions(*args):
                app = MDApp.get_running_app()
                transactions = fetch_transactions_by_cathegory(category)
                transactions_widget = TransactionHolder((0, 0), (app.root.size[0] / 2, app.root.size[1]), transactions)
                scroll_view = TransactionScrollView((0,0), (app.root.size[0], app.root.size[1]/2), transactions)
                transactions_widget.add_widget(scroll_view)


            pie_slice = self.category_pie_dictionary.get(category)
            angle_to_center = pie_slice.slice.angle_start + (pie_slice.slice.angle_end - pie_slice.slice.angle_start) / 2
            angle_to_rotate = 180 - angle_to_center
            rotate_pie_chart(angle_to_rotate)
            Clock.schedule_once(show_transactions, 0.5)

        self.add_pie_slices_and_legend(button_category_on_release)

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
    input_amount = None
    input_name = None
    drop_down = None
    commit_button = None

    def __init__(self, pos, size, **kwargs):
        super(TicketHolder, self).__init__(**kwargs)
        self.pos = pos
        self.size = size
        self.clear_widgets(self.children)

        def inflate(*args):
            app = MDApp.get_running_app()
            self.input_amount = MDTextField(pos_hint={"center_x": .5, "center_y": 0.2}, size_hint=(0.9, None),
                                       hint_text="Amount", helper_text="input a valid amount",
                                       helper_text_mode="on_error", input_type='number')
            self.input_name = MDTextField(pos_hint={"center_x": .5, "center_y": 0.5}, size_hint=(0.9, None),
                                       hint_text="Name")
            self.drop_down = DropDownMenu("Category", self)
            self.add_widget(self.input_amount)
            self.add_widget(self.input_name)
            self.add_widget(self.drop_down)
            self.add_widget(Widget())
        inflate()
        print(self.children)

    def reset_amount_input(self):
        self.ticket_holder.input_amount.error = False
        if self.ticket_holder.input_amount.text.isalpha():
            self.ticket_holder.input_amount.helper_text = "input a number"
            self.ticket_holder.input_amount.text = ""
            self.ticket_holder.input_amount.error = True
            print(self.current_identifier)
            if self.current_identifier == 0:
                self.show_commit_button()
        self.pos = (self.pos[0], self.parent.height)
        self.is_valid = True


class TransactionHolder(MDBoxLayout):
    def __init__(self, pos, size, transactions, **kwargs):
        super(TransactionHolder, self).__init__(size_hint=(None, None), **kwargs)
        app = MDApp.get_running_app()
        self.pos = pos
        self.size = size
        print(self.pos)
        print(self.size)
        with self.canvas:
            Color(app.theme_cls.primary_dark)
            self.line = Line(points=[self.x, self.y, self.width, self.height], width=1)
            self.bind(pos = self.update_line,
                      size = self.update_line)

    def update_line(self, *args):
        self.line.points = [self.x, self.y, self.x + self.width, self.y, self.x + self.width, self.y + self.height]


class TransactionScrollView(ScrollView):
    def __init__(self, pos, size, transactions, **kwargs):
        super(TransactionScrollView, self).__init__(size_hint=(None, None), **kwargs)
        app = MDApp.get_running_app()
        self.pos = pos
        self.size = size
        self.transaction = transactions

        def inflate():
            stack_layout = MDStackLayout(size_hint=(1, 1), orientation='lr-tb')
            for transaction in transactions:
                transaction_view = TransactionView(transaction[3], datetime.fromtimestamp(transaction[1]), "transaction",
                                                   transaction[2])
                stack_layout.add_widget(transaction_view)
            self.add_widget(stack_layout)
            self.size = stack_layout.size
            print(self.pos)
            print(self.size)
        inflate()
        with self.canvas:
            Color(app.theme_cls.primary_dark)
            self.line = Line(points=[self.x, self.y, self.width, self.height], width=1)
            self.bind(pos=self.update_line,
                      size=self.update_line)

    def update_line(self, *args):
        self.line.points = [self.x, self.y, self.x + self.width, self.y, self.x + self.width, self.y + self.height]


class TransactionView(MDBoxLayout):
    def __init__(self, category, date, name, amount, **kwargs):
        super(TransactionView, self).__init__(**kwargs)
        self.category = category
        self.date = date
        self.name = name
        self.amount = amount

        def set_widget(dt):
            self.ids.date.text = (str)(self.date.day) + "." + (str)(self.date.month)
            self.ids.name.text = name
            self.ids.amount = amount
            self.width = self.parent.width
            self.height = self.parent.height

        Clock.schedule_once(set_widget, 0.1)


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

    def __init__(self, text, parent, **kwargs):
        super(DropDownMenu, self).__init__(**kwargs)
        app = MDApp.get_running_app()
        self.text = text
        self.size_hint = (1, None)
        self.pos_hint_y = None
        print(self.pos)
        #with self.canvas:
        #    Color(app.theme_cls.primary_dark)
        #    self.line = Line(points=[self.x, self.y, self.width, self.height], width=1)
        #    self.bind(pos = self.update_line,
        #              size = self.update_line)

        self.set_view()
        self.height = self.main_button.height
        Clock.schedule_once(app.root.show_drop_down, 0.5)

    def update_line(self, *args):
        self.line.points = [self.x, self.y, self.x + self.width, self.y, self.x + self.width, self.y + self.height]

    def set_view(self):
        main_button = MDRectangleFlatButton(text=self.text, pos_hint=(None, None), pos=self.pos)
        main_button.theme_text_color = "Custom"
        main_button.pos_hint = {"center_x": .5}
        main_button.pos[1] = self.pos[1] - self.height * 2
        main_button.on_release = self.toggle_drop_down
        self.main_button = main_button
        self.add_widget(self.main_button)
        self.bind(pos=self.update_pos)

    def update_pos(self, *args):
        ##self.main_button.pos = self.pos
        pass

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
        if self.parent.commit_button is not None:
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
                animation = Animation(pos=(self.pos[0], self.pos[1] - (item.height + dp(10)) * (index + 1)), t='out_cubic',
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
