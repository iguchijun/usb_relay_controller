import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
import threading
import json
import pywinusb.hid as hid

class RelayControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8CH Relay Controller")
        self.settings_file = "settings.json"  # 設定ファイル名
        self.data_file = "relay_data.json"  # データファイル名
        self.relay_data = []  # リレーのデータ保存
        self.relay_count = 8  # リレー個数 (デフォルト値)

        # リレー行の初期化
        self.relay_rows = []  # ここで初期化

        # 設定ファイルをロード
        self.load_settings()

        # デフォルトファイルの自動読み込み
        self.load_default_file()

        # メニューの設定
        self.create_menu()

        # メイン画面のウィジェットを作成
        self.create_widgets()

        # タイマー監視スレッドの開始
        self.start_timer_monitor()

    
    def load_default_file(self):
        """デフォルトファイルを自動読み込み"""
        try:
            with open(self.data_file, "r") as file:
                relay_data = json.load(file)
                for row, data in zip(self.relay_rows, relay_data):
                    row["name"].delete(0, tk.END)
                    row["name"].insert(0, data["name"])
                    row["timer_set"].set(data["timer_set"])
                    row["start_hour"].delete(0, tk.END)
                    row["start_hour"].insert(0, data["start_hour"])
                    row["start_minute"].delete(0, tk.END)
                    row["start_minute"].insert(0, data["start_minute"])
                    row["end_hour"].delete(0, tk.END)
                    row["end_hour"].insert(0, data["end_hour"])
                    row["end_minute"].delete(0, tk.END)
                    row["end_minute"].insert(0, data["end_minute"])
        except FileNotFoundError:
            print("デフォルトファイルが見つかりませんでした。")
        """デフォルトファイルを自動読み込み"""
        try:
            with open(self.data_file, "r") as file:
                relay_data = json.load(file)
                for row, data in zip(self.relay_rows, relay_data):
                    row["name"].delete(0, tk.END)
                    row["name"].insert(0, data["name"])
                    row["timer_set"].set(data["timer_set"])
                    row["start_hour"].delete(0, tk.END)
                    row["start_hour"].insert(0, data["start_hour"])
                    row["start_minute"].delete(0, tk.END)
                    row["start_minute"].insert(0, data["start_minute"])
                    row["end_hour"].delete(0, tk.END)
                    row["end_hour"].insert(0, data["end_hour"])
                    row["end_minute"].delete(0, tk.END)
                    row["end_minute"].insert(0, data["end_minute"])
        except FileNotFoundError:
            print("デフォルトファイルが見つかりませんでした。")
            
    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="開く", command=self.load_relay_data)
        file_menu.add_command(label="保存", command=self.save_relay_data)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit)
        menubar.add_cascade(label="ファイル", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="設定", command=self.open_settings)
        menubar.add_cascade(label="設定", menu=settings_menu)

        self.root.config(menu=menubar)
 
    def create_widgets(self):
        # カレント日時の表示
        self.current_time_label = tk.Label(self.root, text="", font=("Helvetica", 14))
        self.current_time_label.pack(pady=10)
        self.update_current_time()

        self.relay_rows = []
        for i in range(self.relay_count):
            row = {}
            frame = tk.Frame(self.root)
            frame.pack(fill=tk.X)

            # インジケータ
            indicator_label = tk.Label(frame, text="OFF", fg="red")
            indicator_label.pack(side=tk.LEFT, padx=5)
            row["indicator"] = indicator_label

            # 即時スイッチ
            toggle_button = tk.Button(frame, text="入切", command=lambda r=row: self.toggle_relay(r))
            toggle_button.pack(side=tk.LEFT, padx=5)
            row["toggle_button"] = toggle_button

            # 名称入力
            name_entry = tk.Entry(frame)
            name_entry.insert(0, f"リレー{i+1}")
            name_entry.pack(side=tk.LEFT, padx=5)
            row["name"] = name_entry

            # タイマー設定
            timer_var = tk.BooleanVar()
            timer_set = tk.Checkbutton(frame, text="セット", variable=timer_var)
            timer_set.pack(side=tk.LEFT)
            row["timer_set"] = timer_var

            start_hour = tk.Spinbox(frame, from_=0, to=23, width=2)
            start_hour.pack(side=tk.LEFT)
            row["start_hour"] = start_hour

            start_minute = tk.Spinbox(frame, from_=0, to=59, width=2)
            start_minute.pack(side=tk.LEFT)
            row["start_minute"] = start_minute

            end_hour = tk.Spinbox(frame, from_=0, to=23, width=2)
            end_hour.pack(side=tk.LEFT)
            row["end_hour"] = end_hour

            end_minute = tk.Spinbox(frame, from_=0, to=59, width=2)
            end_minute.pack(side=tk.LEFT)
            row["end_minute"] = end_minute

            # タイマーステータス表示
            status_label = tk.Label(frame, text="未設定", fg="green")
            status_label.pack(side=tk.LEFT, padx=5)
            row["status_label"] = status_label

            self.relay_rows.append(row)
            

        # 全部ONボタン
        all_on_button = tk.Button(self.root, text="全部ON", command=self.turn_all_on)
        all_on_button.pack(side=tk.LEFT, padx=5)

        # 全部OFFボタン
        all_off_button = tk.Button(self.root, text="全部OFF", command=self.turn_all_off)
        all_off_button.pack(side=tk.LEFT, padx=5)

        # 画面クリアボタン
        clear_button = tk.Button(self.root, text="画面クリア", command=self.clear_screen)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # ベンダーIDとデバイスIDの表示
        self.device_info_label = tk.Label(self.root, text="ベンダーID: 未設定 デバイスID: 未設定", fg="navy")
        self.device_info_label.pack(pady=10)                    
        
        
    def update_device_info(self, vendor_id, device_id):
        """ベンダーIDとデバイスIDを更新"""
        if vendor_id and device_id:
            self.device_info_label.config(text=f"ベンダーID: {vendor_id} デバイスID: {device_id}", fg="navy")
        else:
            self.device_info_label.config(text="ベンダーID: 未設定 デバイスID: 未設定", fg="red")

    def update_current_time(self):
        """現在の日時を更新"""
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.root.after(1000, self.update_current_time)

    def start_timer_monitor(self):
        def timer_task():
            while True:
                current_time = datetime.datetime.now().time()
                for row in self.relay_rows:
                    timer_set = row["timer_set"].get()
                    start_time = datetime.time(int(row["start_hour"].get()), int(row["start_minute"].get()))
                    end_time = datetime.time(int(row["end_hour"].get()), int(row["end_minute"].get()))

                    if timer_set:
                        if start_time <= current_time <= end_time:
                            row["indicator"].config(text="ON", fg="green")
                        else:
                            row["indicator"].config(text="OFF", fg="red")

                threading.Event().wait(60)

        threading.Thread(target=timer_task, daemon=True).start()

    def load_settings(self):
        try:
            with open(self.settings_file, "r") as file:
                settings = json.load(file)
                self.relay_count = settings.get("relay_count", 8)
        except FileNotFoundError:
            messagebox.showwarning("警告", "設定ファイルが見つかりませんでした。デフォルト設定を使用します。")

    def save_relay_data(self):
        relay_data = []
        for row in self.relay_rows:
            relay_data.append({
                "name": row["name"].get(),
                "timer_set": row["timer_set"].get(),
                "start_hour": row["start_hour"].get(),
                "start_minute": row["start_minute"].get(),
                "end_hour": row["end_hour"].get(),
                "end_minute": row["end_minute"].get(),
            })
        with open(self.data_file, "w") as file:
            json.dump(relay_data, file)
        messagebox.showinfo("保存成功", "データを保存しました。")

    def load_relay_data(self):
        try:
            with open(self.data_file, "r") as file:
                relay_data = json.load(file)
                for row, data in zip(self.relay_rows, relay_data):
                    row["name"].delete(0, tk.END)
                    row["name"].insert(0, data["name"])
                    row["timer_set"].set(data["timer_set"])
                    row["start_hour"].delete(0, tk.END)
                    row["start_hour"].insert(0, data["start_hour"])
                    row["start_minute"].delete(0, tk.END)
                    row["start_minute"].insert(0, data["start_minute"])
                    row["end_hour"].delete(0, tk.END)
                    row["end_hour"].insert(0, data["end_hour"])
                    row["end_minute"].delete(0, tk.END)
                    row["end_minute"].insert(0, data["end_minute"])
                messagebox.showinfo("読み込み成功", "データを読み込みました。")
        except FileNotFoundError:
            messagebox.showwarning("警告", "データファイルが見つかりませんでした。")

    def open_settings(self):
        def save_settings():
            settings = {
                "relay_count": int(relay_count_entry.get())
            }
            with open(self.settings_file, "w") as file:
                json.dump(settings, file)
            messagebox.showinfo("保存成功", "設定を保存しました。\nプログラムを再起動してください。")
            settings_window.destroy()

        settings_window = tk.Toplevel(self.root)
        settings_window.title("設定画面")

        tk.Label(settings_window, text="リレー個数").grid(row=0, column=0, padx=5, pady=5)
        relay_count_entry = tk.Entry(settings_window)
        relay_count_entry.insert(0, str(self.relay_count))
        relay_count_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(settings_window, text="保存", command=save_settings).grid(row=1, column=0, columnspan=2, pady=10)

    def toggle_relay(self, row):
        """即時スイッチのON/OFF切り替え"""
        current_status = row["indicator"].cget("text")
        if current_status == "OFF":
            row["indicator"].config(text="ON", fg="green")
        else:
            row["indicator"].config(text="OFF", fg="red")
        self.update_timer_status(row)

    def update_timer_status(self, row):
        """タイマーステータスの更新"""
        if row["timer_set"].get():
            start_hour = int(row["start_hour"].get())
            start_minute = int(row["start_minute"].get())
            end_hour = int(row["end_hour"].get())
            end_minute = int(row["end_minute"].get())

            # エラーチェック
            if (start_hour == end_hour and start_minute == end_minute) or (start_hour == 0 and start_minute == 0 and end_hour == 0 and end_minute == 0):
                messagebox.showerror("エラー", "タイマー時刻が無効です。")
                row["timer_set"].set(False)
                row["status_label"].config(text="未設定", fg="green")
                return

            row["status_label"].config(text="待機中", fg="orange")
        else:
            row["status_label"].config(text="未設定", fg="green")

    def turn_all_on(self):
        """全リレーをONにする"""
        for row in self.relay_rows:
            row["indicator"].config(text="ON", fg="green")
            row["status_label"].config(text="開始", fg="red")

    def turn_all_off(self):
        """全リレーをOFFにする"""
        for row in self.relay_rows:
            row["indicator"].config(text="OFF", fg="red")
            row["status_label"].config(text="未設定", fg="green")

    def clear_screen(self):
        """画面をクリアする"""
        for row in self.relay_rows:
            row["name"].delete(0, tk.END)
            row["name"].insert(0, "")
            row["timer_set"].set(False)
            row["start_hour"].delete(0, tk.END)
            row["start_hour"].insert(0, "0")
            row["start_minute"].delete(0, tk.END)
            row["start_minute"].insert(0, "0")
            row["end_hour"].delete(0, tk.END)
            row["end_hour"].insert(0, "0")
            row["end_minute"].delete(0, tk.END)
            row["end_minute"].insert(0, "0")
            row["indicator"].config(text="OFF", fg="red")
            row["status_label"].config(text="未設定", fg="green")

if __name__ == "__main__":
    root = tk.Tk()
    app = RelayControllerApp(root)
    root.mainloop()