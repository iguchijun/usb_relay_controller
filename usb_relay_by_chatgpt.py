# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
from pywinusb import hid

SETTINGS_FILE = "settings.json"

class USBRelayController:
    def __init__(self, vendor_id=0x16c0, product_id=0x05df):
        self.device = None
        self.relay_state = 0x00  # 8bitでリレーのON/OFFを記録
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.open_device()

    def open_device(self):
        try:
            all_devices = hid.HidDeviceFilter(vendor_id=self.vendor_id, product_id=self.product_id).get_devices()
            if all_devices:
                self.device = all_devices[0]
                self.device.open()
                return True
        except Exception as e:
            print(f"USB接続エラー: {e}")
        return False

    def set_relay(self, idx, state):
        if not self.device or not (0 <= idx < 8):
            return
        if state:
            self.relay_state |= (1 << idx)
        else:
            self.relay_state &= ~(1 << idx)
        self._send_state()

    def set_all_relays(self, state, relay_count=8):
        if not self.device:
            return
        self.relay_state = 0xFF if state else 0x00
        self._send_state()
            
    def _send_state(self):
        try:
            out_report = self.device.find_output_reports()[0]
            buffer = [0x00] * out_report.report_length
            buffer[1] = self.relay_state
            out_report.set_raw_data(buffer)
            out_report.send()
        except Exception as e:
            print(f"リレー送信エラー: {e}")

class SettingsWindow(tk.Toplevel):
    def __init__(self, master, on_save_callback):
        super().__init__(master)
        self.title("設定画面")
        self.geometry("300x220")
        self.resizable(False, False)
        self.on_save_callback = on_save_callback

        tk.Label(self, text="ベンダーID").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.vendor_id_entry = tk.Entry(self)
        self.vendor_id_entry.grid(row=0, column=1)

        tk.Label(self, text="デバイスID").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.device_id_entry = tk.Entry(self)
        self.device_id_entry.grid(row=1, column=1)

        tk.Label(self, text="リレー個数").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.relay_count_entry = tk.Entry(self)
        self.relay_count_entry.grid(row=2, column=1)

        tk.Label(self, text="デフォルトファイル名").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.default_file_entry = tk.Entry(self)
        self.default_file_entry.grid(row=3, column=1)

        self.save_btn = tk.Button(self, text="保存", command=self.save_settings)
        self.save_btn.grid(row=5, column=0, columnspan=2, pady=15)

        self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.vendor_id_entry.insert(0, settings.get("vendor_id", ""))
                self.device_id_entry.insert(0, settings.get("device_id", ""))
                self.relay_count_entry.insert(0, settings.get("relay_count", 8))
                self.default_file_entry.insert(0, settings.get("default_file", ""))

    def save_settings(self):
        settings = {
            "vendor_id": self.vendor_id_entry.get(),
            "device_id": self.device_id_entry.get(),
            "relay_count": int(self.relay_count_entry.get()) if self.relay_count_entry.get().isdigit() else 8,
            "default_file": self.default_file_entry.get()
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("保存完了", "変更内容を反映するためには、このプログラムの再起動が必要です。")
        self.on_save_callback(settings)
        self.destroy()

class RelayControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8CH RELAY CONTROLLER")
        self.settings = self.load_settings()
        self.relay_count = self.settings.get("relay_count", 8)

        self.relay_states = [False] * self.relay_count
        self.indicators = []
        self.toggle_buttons = []

        self.name_entries = []
        self.timer_vars = []
        self.start_hours = []
        self.start_mins = []
        self.end_hours = []
        self.end_mins = []
        self.status_labels = []  # タイマーステータス表示追加
        
        self.create_menu()
        self.create_header()
        self.create_relay_controls()
        self.create_footer()
        self.update_time()
        self.load_default_file_if_exists()  #  デフォルトファイルの自動読み込み
        self.check_timer_events()
        self.relay_controller = None
        self.try_connect_device()


    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="開く", command=self.load_data_file)
        file_menu.add_command(label="保存", command=self.save_data_file)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit)
        menubar.add_cascade(label="ファイル", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="設定", command=self.open_settings)
        menubar.add_cascade(label="設定", menu=settings_menu)

        self.root.config(menu=menubar)

    def create_header(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)

        self.title_label = tk.Label(top_frame, text="8CH RELAY CONTROLLER", font=("Helvetica", 16))
        self.title_label.pack(side=tk.LEFT, padx=10)

        self.time_label = tk.Label(top_frame, text="", font=("Helvetica", 12))
        self.time_label.pack(side=tk.RIGHT, padx=10)

    def create_relay_controls(self):
        if hasattr(self, "relay_frame"):
            self.relay_frame.destroy()

        self.relay_states = [False] * self.relay_count
        self.indicators.clear()
        self.toggle_buttons.clear()
        self.name_entries.clear()
        self.timer_vars.clear()
        self.start_hours.clear()
        self.start_mins.clear()
        self.end_hours.clear()
        self.end_mins.clear()
        self.status_labels.clear()

        self.relay_frame = tk.Frame(self.root)
        self.relay_frame.pack(padx=10, pady=5)

        for i in range(self.relay_count):
            row = tk.Frame(self.relay_frame)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=f"{i+1}:").pack(side=tk.LEFT)

            indicator = tk.Label(row, text="●", fg="gray")
            indicator.pack(side=tk.LEFT)
            self.indicators.append(indicator)

            toggle_btn = tk.Button(row, text="入切", command=lambda idx=i: self.toggle_relay(idx))
            toggle_btn.pack(side=tk.LEFT)
            self.toggle_buttons.append(toggle_btn)

            name_entry = tk.Entry(row, width=20)
            name_entry.pack(side=tk.LEFT)
            self.name_entries.append(name_entry)

            #tk.Label(row, text="未設定", fg="green").pack(side=tk.LEFT)
            status_label = tk.Label(row, text="未設定", fg="green")
            status_label.pack(side=tk.LEFT)
            self.status_labels.append(status_label)
            
            timer_var = tk.BooleanVar()
            #timer_check = tk.Checkbutton(row, variable=timer_var)
            timer_check = tk.Checkbutton(row, variable=timer_var, command=lambda idx=i: self.update_timer_status(idx))
            timer_check.pack(side=tk.LEFT)
            self.timer_vars.append(timer_var)

            sh = ttk.Spinbox(row, from_=0, to=23, width=2)
            sh.set(0)
            sh.pack(side=tk.LEFT)
            self.start_hours.append(sh)

            ttk.Label(row, text=":").pack(side=tk.LEFT)

            sm = ttk.Spinbox(row, from_=0, to=59, width=2)
            sm.set(0)
            sm.pack(side=tk.LEFT)
            self.start_mins.append(sm)

            ttk.Label(row, text="～").pack(side=tk.LEFT)

            eh = ttk.Spinbox(row, from_=0, to=23, width=2)
            eh.set(0)
            eh.pack(side=tk.LEFT)
            self.end_hours.append(eh)

            ttk.Label(row, text=":").pack(side=tk.LEFT)

            em = ttk.Spinbox(row, from_=0, to=59, width=2)
            em.set(0)
            em.pack(side=tk.LEFT)
            self.end_mins.append(em)

    def create_footer(self):
        bottom = tk.Frame(self.root)
        bottom.pack(pady=10)

        tk.Button(bottom, text="全部入", command=self.turn_all_on).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom, text="全部切", command=self.turn_all_off).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom, text="画面クリア", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        vendor = self.settings.get("vendor_id", "----")
        device = self.settings.get("device_id", "----")
        self.status_label = tk.Label(
            self.root,
            text=f"ベンダーID：{vendor}　デバイスID：{device}　デバイスは未接続です。",
            fg="navy"
        )
        self.status_label.pack(pady=5)

    def update_time(self):
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self.update_time)

    def update_timer_status(self, idx):
        if not self.timer_vars[idx].get():
            self.status_labels[idx].config(text="未設定", fg="green")
            # 入力を再び可能にする
            self.start_hours[idx].config(state="normal")
            self.start_mins[idx].config(state="normal")
            self.end_hours[idx].config(state="normal")
            self.end_mins[idx].config(state="normal")
        else:
            # ▼ エラーチェックを追加
            start_hour = int(self.start_hours[idx].get())
            start_min = int(self.start_mins[idx].get())
            end_hour = int(self.end_hours[idx].get())
            end_min = int(self.end_mins[idx].get())

            if start_hour == 0 and start_min == 0 and end_hour == 0 and end_min == 0:
                messagebox.showwarning("エラー", "タイマー時刻が設定されていません。")
                self.timer_vars[idx].set(False)
                self.status_labels[idx].config(text="未設定", fg="green")
                return

            if start_hour == end_hour and start_min == end_min:
                messagebox.showwarning("エラー", "タイマー開始と終了に同じ時刻は設定できません。")
                self.timer_vars[idx].set(False)
                self.status_labels[idx].config(text="未設定", fg="green")
                return

            # 入力を不可にする
            self.start_hours[idx].config(state="disabled")
            self.start_mins[idx].config(state="disabled")
            self.end_hours[idx].config(state="disabled")
            self.end_mins[idx].config(state="disabled")

            if self.relay_states[idx]:
                self.status_labels[idx].config(text="開始", fg="red")
            else:
                self.status_labels[idx].config(text="待機中", fg="orange")


    def check_timer_events(self):
        now = datetime.now()
        now_hour = now.hour
        now_minute = now.minute

        for idx in range(self.relay_count):
            if not self.timer_vars[idx].get():
                self.status_labels[idx].config(text="未設定", fg="green")
                continue

            start_hour = int(self.start_hours[idx].get())
            start_min = int(self.start_mins[idx].get())
            end_hour = int(self.end_hours[idx].get())
            end_min = int(self.end_mins[idx].get())

            if now_hour == start_hour and now_minute == start_min:
                if not self.relay_states[idx]:
                    self.relay_states[idx] = True
                    self.update_relay_indicator(idx)
                    self.update_timer_status(idx)
            elif now_hour == end_hour and now_minute == end_min:
                if self.relay_states[idx]:
                    self.relay_states[idx] = False
                    self.update_relay_indicator(idx)
                    self.update_timer_status(idx)

        self.root.after(60000, self.check_timer_events)

    def toggle_relay(self, idx):
        self.relay_states[idx] = not self.relay_states[idx]
        if self.relay_controller:
            self.relay_controller.set_relay(idx, self.relay_states[idx])
        self.update_relay_indicator(idx)
        self.update_timer_status(idx)

    def update_relay_indicator(self, idx):
        self.indicators[idx].config(fg="red" if self.relay_states[idx] else "gray")

    def turn_all_on(self):
        for idx in range(self.relay_count):
            self.relay_states[idx] = True
            self.update_relay_indicator(idx)
            self.update_timer_status(idx)
        if self.relay_controller:
            self.relay_controller.set_all_relays(True, self.relay_count)

    def turn_all_off(self):
        for idx in range(self.relay_count):
            self.relay_states[idx] = False
            self.update_relay_indicator(idx)
            self.update_timer_status(idx)
        if self.relay_controller:
            self.relay_controller.set_all_relays(False, self.relay_count)

    def clear_all(self):
        for i in range(self.relay_count):
            self.name_entries[i].delete(0, tk.END)
            self.timer_vars[i].set(False)
            self.start_hours[i].delete(0, tk.END)
            self.start_hours[i].insert(0, 0)
            self.start_mins[i].delete(0, tk.END)
            self.start_mins[i].insert(0, 0)
            self.end_hours[i].delete(0, tk.END)
            self.end_hours[i].insert(0, 0)
            self.end_mins[i].delete(0, tk.END)
            self.end_mins[i].insert(0, 0)
            self.relay_states[i] = False
            self.update_relay_indicator(i)

    def save_data_file(self):
        data = []
        for i in range(self.relay_count):
            relay_info = {
                "name": self.name_entries[i].get(),
                "timer_set": self.timer_vars[i].get(),
                "start_hour": int(self.start_hours[i].get()),
                "start_min": int(self.start_mins[i].get()),
                "end_hour": int(self.end_hours[i].get()),
                "end_min": int(self.end_mins[i].get())
            }
            data.append(relay_info)

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("保存完了", "リレーデータを保存しました。")

    def load_data_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for i, relay in enumerate(data):
                if i < self.relay_count:
                    self.name_entries[i].delete(0, tk.END)
                    self.name_entries[i].insert(0, relay.get("name", ""))
                    self.timer_vars[i].set(relay.get("timer_set", False))
                    self.start_hours[i].delete(0, tk.END)
                    self.start_hours[i].insert(0, relay.get("start_hour", 0))
                    self.start_mins[i].delete(0, tk.END)
                    self.start_mins[i].insert(0, relay.get("start_min", 0))
                    self.end_hours[i].delete(0, tk.END)
                    self.end_hours[i].insert(0, relay.get("end_hour", 0))
                    self.end_mins[i].delete(0, tk.END)
                    self.end_mins[i].insert(0, relay.get("end_min", 0))
            messagebox.showinfo("読込完了", "リレーデータを読み込みました。")

    def open_settings(self):
        SettingsWindow(self.root, self.apply_settings)

    def apply_settings(self, new_settings):
        self.settings = new_settings
        self.relay_count = self.settings.get("relay_count", 8)
        self.create_relay_controls()
        self.create_footer()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def load_default_file_if_exists(self):
        default_file = self.settings.get("default_file", "")
        if default_file and os.path.exists(default_file):
            try:
                with open(default_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for i, relay in enumerate(data):
                    if i < self.relay_count:
                        self.name_entries[i].delete(0, tk.END)
                        self.name_entries[i].insert(0, relay.get("name", ""))
                        self.timer_vars[i].set(relay.get("timer_set", False))
                        self.start_hours[i].delete(0, tk.END)
                        self.start_hours[i].insert(0, relay.get("start_hour", 0))
                        self.start_mins[i].delete(0, tk.END)
                        self.start_mins[i].insert(0, relay.get("start_min", 0))
                        self.end_hours[i].delete(0, tk.END)
                        self.end_hours[i].insert(0, relay.get("end_hour", 0))
                        self.end_mins[i].delete(0, tk.END)
                        self.end_mins[i].insert(0, relay.get("end_min", 0))
                        self.update_timer_status(i)
                print("デフォルトファイルを読み込みました。")
            except Exception as e:
                print(f"デフォルトファイルの読み込みに失敗しました: {e}")

    def try_connect_device(self):
        try:
            vendor = int(self.settings.get("vendor_id", "0"), 0)
            product = int(self.settings.get("device_id", "0"), 0)
            self.relay_controller = USBRelayController(vendor, product)
            if self.relay_controller.device:
                self.status_label.config(
                    text=f"ベンダーID：{vendor}　デバイスID：{product}　デバイスは正常にオープンしました。",
                    fg="navy"
                )
            else:
                self.status_label.config(
                    text=f"ベンダーID：{vendor}　デバイスID：{product}　デバイスをOPENできないためコントロール不可",
                    fg="red"
                )
        except ValueError:
            self.status_label.config(text="ベンダーID／デバイスID 入力不正", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = RelayControlApp(root)
    root.mainloop()