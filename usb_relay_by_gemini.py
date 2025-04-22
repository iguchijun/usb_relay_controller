import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import threading
import time
import json
import os
import re

# ダミーのUSBリレー制御関数
def dummy_set_relay(relay_num, on_off):
    """
    USBリレーを制御するダミー関数。
    実際にはpywinusb.hidを使用して制御する。
    """
    print(f"リレー{relay_num}を{'ON' if on_off else 'OFF'}に設定 (ダミー)")

def dummy_get_relay_status():
    """
    USBリレーの状態を取得するダミー関数。
    実際にはpywinusb.hidを使用して状態を取得する。
    """
    # ランダムなON/OFF状態を返す（実際にはデバイスから取得）
    import random
    return [random.choice([True, False]) for _ in range(8)]

class RelayTimer:
    def __init__(self, master, relay_num):
        self.master = master
        self.relay_num = relay_num
        self.name_var = tk.StringVar()
        self.timer_set_var = tk.BooleanVar()
        self.start_hour_var = tk.IntVar(value=0)
        self.start_minute_var = tk.IntVar(value=0)
        self.end_hour_var = tk.IntVar(value=0)
        self.end_minute_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="未設定")
        self.is_on = False  # リレーのON/OFF状態を保持

        self.create_widgets()

    def create_widgets(self):
        # リレー番号ラベル
        tk.Label(self.master, text=f"{self.relay_num}:").grid(row=self.relay_num + 3, column=0, sticky="w")

        # ON/OFFインジケーター（ダミー）
        self.indicator_label = tk.Label(self.master, text="〇", fg="black")
        self.indicator_label.grid(row=self.relay_num + 3, column=1, sticky="w")

        # 入/切ボタン
        on_off_button = tk.Button(self.master, text="入/切", command=self.toggle_relay)
        on_off_button.grid(row=self.relay_num + 3, column=2, sticky="w")

        # 名称入力欄
        name_entry = tk.Entry(self.master, textvariable=self.name_var)
        name_entry.grid(row=self.relay_num + 3, column=4, sticky="w")

        # タイマーステータス表示
        self.status_label = tk.Label(self.master, textvariable=self.status_var)
        self.status_label.grid(row=self.relay_num + 3, column=17, sticky="w")

        # タイマー設定チェックボックス
        timer_check = tk.Checkbutton(self.master, text="タイマー", variable=self.timer_set_var, command=self.toggle_timer_settings)
        timer_check.grid(row=self.relay_num + 3, column=20, sticky="w")

        # 開始時、開始分、終了時、終了分スピンボックス
        start_hour_spinbox = tk.Spinbox(self.master, from_=0, to=23, width=3, textvariable=self.start_hour_var, state="disabled")
        start_hour_spinbox.grid(row=self.relay_num + 3, column=22, sticky="w")
        start_minute_spinbox = tk.Spinbox(self.master, from_=0, to=59, width=3, textvariable=self.start_minute_var, state="disabled")
        start_minute_spinbox.grid(row=self.relay_num + 3, column=23, sticky="w")
        end_hour_spinbox = tk.Spinbox(self.master, from_=0, to=23, width=3, textvariable=self.end_hour_var, state="disabled")
        end_hour_spinbox.grid(row=self.relay_num + 3, column=25, sticky="w")
        end_minute_spinbox = tk.Spinbox(self.master, from_=0, to=59, width=3, textvariable=self.end_minute_var, state="disabled")
        end_minute_spinbox.grid(row=self.relay_num + 3, column=26, sticky="w")

        self.start_hour_spinbox = start_hour_spinbox
        self.start_minute_spinbox = start_minute_spinbox
        self.end_hour_spinbox = end_hour_spinbox
        self.end_minute_spinbox = end_minute_spinbox

    def toggle_relay(self):
        """
        リレーのON/OFFを切り替える。
        """
        self.is_on = not self.is_on
        dummy_set_relay(self.relay_num, self.is_on)  # ダミー関数
        self.update_indicator()
        self.update_timer_status()

    def update_indicator(self):
        """
        リレーのON/OFFインジケーターを更新する。
        """
        if self.is_on:
            self.indicator_label.config(fg="green")  # ONの時明るく
        else:
            self.indicator_label.config(fg="black")  # OFFの時暗く

    def toggle_timer_settings(self):
        """
        タイマー設定の有効/無効を切り替える。
        """
        is_enabled = self.timer_set_var.get()
        states = "normal" if is_enabled else "disabled"
        self.start_hour_spinbox.config(state=states)
        self.start_minute_spinbox.config(state=states)
        self.end_hour_spinbox.config(state=states)
        self.end_minute_spinbox.config(state=states)

        if is_enabled:
            self.validate_timer_settings()
        else:
            self.status_var.set("未設定")
            self.status_label.config(fg="green")

    def validate_timer_settings(self):
        """
        タイマー設定時刻のチェックを行う。
        """
        start_hour = self.start_hour_var.get()
        start_minute = self.start_minute_var.get()
        end_hour = self.end_hour_var.get()
        end_minute = self.end_minute_var.get()

        if start_hour == 0 and start_minute == 0 and end_hour == 0 and end_minute == 0:
            messagebox.showerror("エラー", "タイマー時刻が設定されていません。")
            self.timer_set_var.set(False)
            self.toggle_timer_settings()
            return

        if start_hour == end_hour and start_minute == end_minute:
            messagebox.showerror("エラー", "タイマー開始と終了に同じ時刻は設定できません。")
            self.timer_set_var.set(False)
            self.toggle_timer_settings()
            return

        if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59 and 0 <= end_hour <= 23 and 0 <= end_minute <= 59):
            messagebox.showerror("エラー", "タイマー時刻にあり得ない数値が設定されています。")
            self.timer_set_var.set(False)
            self.toggle_timer_settings()
            return

        self.start_timer_monitoring()
        self.update_timer_status()

    def start_timer_monitoring(self):
        """
        タイマー監視を開始する。
        """
        threading.Thread(target=self.monitor_timer, daemon=True).start()

    def monitor_timer(self):
        """
        タイマーを監視し、設定時刻になったらリレーをON/OFFする。
        """
        while self.timer_set_var.get():
            now = datetime.datetime.now()
            if now.hour == self.start_hour_var.get() and now.minute == self.start_minute_var.get():
                if not self.is_on:
                    self.toggle_relay()  # ONにする
            elif now.hour == self.end_hour_var.get() and now.minute == self.end_minute_var.get():
                if self.is_on:
                    self.toggle_relay()  # OFFにする
            self.update_timer_status()
            time.sleep(60)  # 60秒ごとに監視

    def update_timer_status(self):
        """
        タイマーステータスを更新する。
        """
        if not self.timer_set_var.get():
            self.status_var.set("未設定")
            self.status_label.config(fg="green")
        elif self.is_on:
            self.status_var.set("開始")
            self.status_label.config(fg="red")
        else:
            self.status_var.set("待機中")
            self.status_label.config(fg="brown")

class RelayApp:
    def __init__(self, master):
        self.master = master
        master.title("8CH RELAY CONTROLLER")  # タイトルを設定 [cite: 2]

        self.vendor_id = tk.StringVar()
        self.device_id = tk.StringVar()
        self.num_relays = 8  # デフォルト値 [cite: 1]
        self.default_file_name = tk.StringVar()
        self.relays = []
        self.current_time_var = tk.StringVar()
        self.message_var = tk.StringVar()

        self.create_menu()
        self.create_widgets()
        self.load_settings()
        self.load_default_data()
        self.update_time()
        self.update_relay_status_all()  # プログラム開始時にリレー状態を取得

    def create_menu(self):
        """
        メニューバーを作成する。 [cite: 4]
        """
        menu_bar = tk.Menu(self.master)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="開く", command=self.load_data)
        file_menu.add_command(label="保存", command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.master.destroy)
        menu_bar.add_cascade(label="ファイル", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="設定", command=self.show_settings)
        menu_bar.add_cascade(label="設定", menu=settings_menu)

        self.master.config(menu=menu_bar)

    def create_widgets(self):
        """
        画面のウィジェットを作成する。 [cite: 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        """
        # タイトルラベル
        tk.Label(self.master, text="8CH RELAY CONTROLLER").grid(row=2, column=4, columnspan=10)

        # 現在時刻表示ラベル
        tk.Label(self.master, textvariable=self.current_time_var).grid(row=2, column=26, columnspan=3)

        # リレー設定ラベル
        tk.Label(self.master, text="リレー即時").grid(row=4, column=0, sticky="w")
        tk.Label(self.master, text="名　　称").grid(row=4, column=4, sticky="w")
        tk.Label(self.master, text="タイマー　開始時：開始分～終了時：終了分").grid(row=4, column=20, columnspan=7, sticky="w")

        # リレーごとの行を作成
        for i in range(self.num_relays):
            relay_timer = RelayTimer(self.master, i + 1)
            self.relays.append(relay_timer)

        # 全部ON/OFF、クリアボタン
        tk.Button(self.master, text="全部入", command=self.all_on).grid(row=13, column=1)
        tk.Button(self.master, text="全部切", command=self.all_off).grid(row=13, column=5)
        tk.Button(self.master, text="画面クリア", command=self.clear_all).grid(row=13, column=9)

        # メッセージ表示欄
        self.message_label = tk.Label(self.master, textvariable=self.message_var, fg="navy")
        self.message_label.grid(row=14, column=0, columnspan=30, sticky="w")

    def update_time(self):
        """
        現在時刻を1秒ごとに更新する。 [cite: 11]
        """
        now = datetime.datetime.now()
        self.current_time_var.set(now.strftime("%Y/%m/%d %H:%M:%S"))
        self.master.after(1000, self.update_time)

    def update_relay_status_all(self):
        """
        全てのリレーのON/OFF状態を更新する。
        """
        relay_statuses = dummy_get_relay_status()  # ダミー関数
        for i, relay in enumerate(self.relays):
            relay.is_on = relay_statuses[i]
            relay.update_indicator()
            relay.update_timer_status()

    def all_on(self):
        """
        全てのリレーをONにする。 [cite: 10]
        """
        for relay in self.relays:
            if not relay.is_on:
                relay.toggle_relay()

    def all_off(self):
        """
        全てのリレーをOFFにする。 [cite: 10, 11]
        """
        for relay in self.relays:
            if relay.is_on:
                relay.toggle_relay()

    def clear_all(self):
        """
        全てのリレーの設定をクリアする。 [cite: 10, 11]
        """
        for relay in self.relays:
            relay.name_var.set("")
            relay.timer_set_var.set(False)
            relay.start_hour_var.set(0)
            relay.start_minute_var.set(0)
            relay.end_hour_var.set(0)
            relay.end_minute_var.set(0)
            relay.status_var.set("未設定")
            relay.status_label.config(fg="green")
            relay.toggle_timer_settings()  # スピンボックスの状態を更新

    def load_data(self):
        """
        ファイルからリレーデータを読み込む。 [cite: 1, 2]
        """
        file_path = filedialog.askopenfilename(title="データファイルを開く")
        if file_path:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.load_relay_data(data)
            except FileNotFoundError:
                messagebox.showerror("エラー", "ファイルが見つかりません。")
            except json.JSONDecodeError:
                messagebox.showerror("エラー", "ファイルが破損しています。")

    def save_data(self):
        """
        リレーデータをファイルに保存する。 [cite: 1, 2]
        """
        file_path = filedialog.asksaveasfilename(title="データファイルを保存", defaultextension=".json")
        if file_path:
            data = self.get_relay_data()
            try:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました: {e}")

    def load_default_data(self):
        """
        デフォルトファイルからデータを読み込む。 [cite: 1]
        """
        if self.default_file_name.get():
            try:
                with open(self.default_file_name.get(), "r") as f:
                    data = json.load(f)
                    self.load_relay_data(data)
                    self.message_var.set(f"デフォルトファイル '{self.default_file_name.get()}' を読み込みました。")
            except FileNotFoundError:
                print(f"デフォルトファイル '{self.default_file_name.get()}' が見つかりません。")  # エラーは表示するが続行
            except json.JSONDecodeError:
                print(f"デフォルトファイル '{self.default_file_name.get()}' が破損しています。")  # エラーは表示するが続行

    def load_relay_data(self, data):
        """
        ファイルから読み込んだリレーデータを画面に反映する。
        """
        for i, relay_data in enumerate(data):
            if i < len(self.relays):
                relay = self.relays[i]
                relay.name_var.set(relay_data.get("name", ""))
                relay.timer_set_var.set(relay_data.get("timer_set", False))
                relay.start_hour_var.set(relay_data.get("start_hour", 0))
                relay.start_minute_var.set(relay_data.get("start_minute", 0))
                relay.end_hour_var.set(relay_data.get("end_hour", 0))
                relay.end_minute_var.set(relay_data.get("end_minute", 0))
                relay.toggle_timer_settings()  # スピンボックスの状態を更新
                if relay.timer_set_var.get():
                    relay.start_timer_monitoring()
                    relay.update_timer_status()

    def get_relay_data(self):
        """
        画面のリレーデータを取得する。
        """
        data = []
        for relay in self.relays:
            data.append({
                "name": relay.name_var.get(),
                "timer_set": relay.timer_set_var.get(),
                "start_hour": relay.start_hour_var.get(),
                "start_minute": relay.start_minute_var.get(),
                "end_hour": relay.end_hour_var.get(),
                "end_minute": relay.end_minute_var.get()
            })
        return data

    def show_settings(self):
        """
        設定画面を表示する。
        """
        settings_window = tk.Toplevel(self.master)
        settings_window.title("設定")
        settings_window.geometry("300x200")  # サイズを指定

        tk.Label(settings_window, text="ベンダーID").grid(row=0, column=0, sticky="w")
        tk.Entry(settings_window, textvariable=self.vendor_id).grid(row=0, column=1)
        tk.Label(settings_window, text="デバイスID").grid(row=1, column=0, sticky="w")
        tk.Entry(settings_window, textvariable=self.device_id).grid(row=1, column=1)
        tk.Label(settings_window, text="リレー個数").grid(row=2, column=0, sticky="w")
        tk.Entry(settings_window, textvariable=tk.StringVar(value=str(self.num_relays))).grid(row=2, column=1)  # StringVarを使用
        tk.Label(settings_window, text="デフォルトファイル名").grid(row=3, column=0, sticky="w")
        tk.Entry(settings_window, textvariable=self.default_file_name).grid(row=3, column=1)

        def save_settings():
            """
            設定を保存する。
            """
            try:
                # リレー個数を整数に変換
                num_relays = int(settings_window.nametowidget(settings_window.winfo_children()[4]).get())  # 直接ウィジェットから取得
                if 1 <= num_relays <= 8:
                    self.num_relays = num_relays
                    self.recreate_relay_rows()  # リレー行を再生成
                else:
                    messagebox.showerror("エラー", "リレー個数は1～8の範囲で指定してください。")
                    return

                messagebox.showinfo("情報", "変更内容を反映するためには、このプログラムの再起動が必要です。")
                settings_window.destroy()
            except ValueError:
                messagebox.showerror("エラー", "リレー個数に有効な数値を入力してください。")

        tk.Button(settings_window, text="保存", command=save_settings).grid(row=4, column=1)

    def load_settings(self):
        """
        設定ファイルから設定を読み込む。
        """
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.vendor_id.set(settings.get("vendor_id", ""))
                self.device_id.set(settings.get("device_id", ""))
                self.num_relays = settings.get("num_relays", 8)
                self.default_file_name.set(settings.get("default_file_name", ""))
        except FileNotFoundError:
            print("設定ファイルが見つかりません。デフォルト値を使用します。")
        except json.JSONDecodeError:
            print("設定ファイルが破損しています。デフォルト値を使用します。")
        self.recreate_relay_rows()  # リレー行を再生成

    def save_settings(self):
        """
        設定をファイルに保存する。
        """
        settings = {
            "vendor_id": self.vendor_id.get(),
            "device_id": self.device_id.get(),
            "num_relays": self.num_relays,
            "default_file_name": self.default_file_name.get()
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")

    def recreate_relay_rows(self):
        """
        リレーの行を再生成する（リレー個数が変更された場合に使用）。
        """

        # 既存のリレー行を削除
        for relay in self.relays:
            for widget in relay.master.grid_slaves():
                if int(widget.grid_info()["row"]) > 4 and int(widget.grid_info()["row"]) < 13:
                    widget.destroy()

        self.relays = []
        # 新しいリレー行を作成
        for i in range(self.num_relays):
            relay_timer = RelayTimer(self.master, i + 1)
            self.relays.append(relay_timer)

        # ボタンを再配置
        tk.Button(self.master, text="全部入", command=self.all_on).grid(row=13, column=1)
        tk.Button(self.master, text="全部切", command=self.all_off).grid(row=13, column=5)
        tk.Button(self.master, text="画面クリア", command=self.clear_all).grid(row=13, column=9)
        self.message_label.grid(row=14, column=0, columnspan=30, sticky="w")

    def set_message(self, message, color="navy"):
        """
        メッセージを表示する。
        """
        self.message_var.set(message)
        self.message_label.config(fg=color)

def main():
    root = tk.Tk()
    app = RelayApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
