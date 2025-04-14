# ライブラリのインポート
import tkinter as tk
from   tkinter import messagebox, font, filedialog
import os
import sys
import json
import pywinusb.hid as hid
from   datetime import datetime

class PreSetting():
    # 設定ファイルを取得するクラス
    def __init__(self, SETTING_FILE):
        self.setting = os.path.join(os.path.dirname(__file__), SETTING_FILE)

    # 設定データ（ベンダーＩＤ，デバイスＩＤ，リレー個数、デフォルトデータファイル名）を読み込む関数
    def read_settings(self):
        try:
            with open(self.setting, "r") as file:
                print("設定ファイルを読み込みました")
                return json.load(file)
        except FileNotFoundError:
            print("設定ファイルが見つかりません")
            return {"vender_id": "", "device_id": "", "quantity_relay": 0, "auto_load": ""}  # 初期値
        
    def check_settings(self):
        settings = self.read_settings()
        #print(f"settings = {settings}")
        if not all(key in settings for key in ["vender_id", "device_id", "quantity_relay", "auto_load"]):
            print("設定ファイルに必要なキーが不足しています")
            return False
    
        # 設定ファイルデータのチェックと設定
        if settings["vender_id"] == "" :
            settings["vender_id"] = "入力無し"
        else:
            check_string = settings["vender_id"]
            if check_string[:2] == "0x":
                settings["vender_id"] = int(check_string,16)
            else:
                try:
                    settings["vender_id"] = int(check_string)
                except ValueError:
                    settings["vender_id"] = "入力不正"

        if settings["device_id"] == "" :
            settings["device_id"] = "入力無し"
        else:
            check_string = settings["device_id"]
            if check_string[:2] == "0x":
                settings["device_id"] = int(check_string,16)
            else:
                try:
                    settings["device_id"] = int(check_string)
                except ValueError:
                    settings["device_id"] = "入力不正"

        if settings["quantity_relay"] == "" :
            settings["quantity_relay"] = 8  # デフォルト値を設定
            print("リレーの個数は8にデフォルト設定しました。") 
        else:
            try:
                settings["quantity_relay"] = int(settings["quantity_relay"])
                if settings["quantity_relay"] < 1 or settings["quantity_relay"] > 8:
                    settings["quantity_relay"] = 8  # デフォルト値を設定
                    print("リレーの個数を8にデフォルト設定しました。")
            except ValueError:
                settings["quantity_relay"] = 8  # デフォルト値を設定
                print("リレーの個数が8にデフォルト設定されました。") 
                
        return settings

class AutoLoadData():
    def __init__(self, auto_load_file, quantity_relay):
        self.load_file = os.path.join(os.path.dirname(__file__), auto_load_file)
        self.quantity_relay = quantity_relay
        
    def read_data(self):
        try:
            with open(self.load_file, 'r') as f:
                loaded_data = json.load(f)
                return loaded_data
        except FileNotFoundError:
            print('ファイルが見つかりません')
            return None  # ファイルが見つからない場合はNoneを返す
        except json.JSONDecodeError:
            print('ファイルの読み込みに失敗しました。ファイルが破損しているか、json形式で保存されていません。')
            return None
        except Exception as e:
            print(f'予期せぬエラーが発生しました: {e}')
            return None
        
    def load_data(self):
    # プログラム起動時にデフォルトファイルを読み込む処理
        if os.path.exists(self.load_file):
            filepath = os.path.join(os.getcwd(), self.load_file)
            loaded_data = self.read_data()
            if loaded_data:
                print(f"デフォルトファイル '{self.load_file}' を読み込みました。")
                return loaded_data
        
        # ファイルが存在しない場合のデフォルトデータを作成
        loaded_data = []
        for i in range(self.quantity_relay):
            loaded_data.append({"classifying": "名称", "timer_onoff": False, "start_hour": " 0","start_minute": " 0",  "end_hour": " 0","end_minute": " 0"})
        print(f"デフォルトファイル '{self.load_file}' は存在しません。")
        return loaded_data  # ファイルが存在しない場合はデフォルト値を返す
    
class USBRelayInterface:
# USB通信ロジック
    def __init__(self, vender_id, device_id):
        self.vender_id  = vender_id
        self.device_id  = device_id
        self.USB_device = None
    
    #デバイス情報を取得
    def get_filter(self):
        try:
            # 指定されたベンダーIDとデバイスIDをもつHIDデバイスをフィルター
            filter = hid.HidDeviceFilter(vendor_id=self.vender_id, product_id=self.device_id)
            # フィルターされたデバイスのリストを取得
            hid_device = filter.get_devices()
            # デバイスが見つからない場合のチェック
            if not hid_device:
                print("エラー: デバイスが見つかりません")
                return False
            # 取得したデバイスリストの最初のデバイスを選択
            self.USB_device = hid_device[0]
            print("デバイスが正常に取得されました:", self.USB_device)
            return self.USB_device
        except Exception as e:
            # 例外をキャッチしてエラーメッセージを出力
            print("エラーが発生しました:", str(e))
            return False 
   
    #デバイスを開く
    def open_device(self):
        if self.USB_device.is_active():
            if not self.USB_device.is_opened():
                self.USB_device.open()
                if not self.USB_device.is_active():
                    self.USB_device = None
                else:
                    for dev in self.USB_device.find_output_reports() + self.USB_device.find_feature_reports():
                        Usb_relay_device = dev
                    print("デバイスが正常にオープンされました。")
                    return Usb_relay_device
            else:
                print("既に開かれているデバイスを開こうとしました")
        else:
            print("アクティブではないデバイスを開こうとしました")
        return False

    #デバイスを閉じる
    def close_device(self):
        if self.USB_device is not None:
            if self.USB_device.is_active():
                if self.USB_device.is_opened():
                    self.USB_device.close()
                    return True
                else:
                    print("既に閉じられているデバイスを閉じようとしました")
            else:
                print("アクティブではないデバイスを閉じようとしました")
            return True
        else:
            print("デバイスが取得されていないため、クローズ処理をスキップしました")
            return False  

    # デバイスのステータスを参照して、全リレーのＯＮＯＦＦを8バイトのフラグにして返す
    def get_all_status(self):
        try:
            # デバイスの状態を確認
            if not self.USB_device:  # USB_deviceが未定義またはNoneの場合をチェック
                print("デバイスが正常にオープンされていません。")
                return False
            # 全リレーのステータスを取得
            last_row_status = Usb_relay_device.get()
            byte_value = last_row_status[8]  # 8番目がリレーの状態ステータス
            # 各ビットをチェックしてリストに格納　ビット(0)はリレー1(0)のステータス
            status_string = [(byte_value >> i) & 1 for i in range(8)]
            #print(f'get_all_status  status_string= {status_string}')
            return status_string
        except Exception as e:
            # エラー発生時はログを出力し、Falseを返す
            print(f"デバイスの状態確認でエラーが発生しました: {e}")
            return False

# リレーボードのクラス
class RelayBoard:
    def __init__(self,relay_number, On_off, timer_begin, classifying, timer_onoff, start_hour, start_minute, end_hour, end_minute):
        self.relay_number = relay_number                      # リレー番号 １～
        self.on_off       = On_off                            # リレーのＯＮ／ＯＦＦ状態　True:ＯＮ False:ＯＦＦ
        self.timer_begin  = timer_begin                       # タイマーの開始状態 True:タイマーが開始した False:タイマーが開始していない
        self.classifying  = tk.StringVar( value=classifying)  # リレーの分類・名称
        self.timer_onoff  = tk.BooleanVar(value=timer_onoff)  # タイマーの状態 True:設定済 False:未設定
        self.start_hour   = tk.StringVar( value=start_hour)   # タイマー開始時刻
        self.start_minute = tk.StringVar( value=start_minute) # タイマー開始分
        self.end_hour     = tk.StringVar( value=end_hour)     # タイマー終了時刻
        self.end_minute   = tk.StringVar( value=end_minute)   # タイマー終了分

    def clear_all(self):
        self.on_off       = False
        self.timer_begin  = False
        self.classifying.set("")
        self.timer_onoff.set(False)
        self.start_hour.set(" 0")
        self.start_minute.set(" 0")
        self.end_hour.set(" 0")
        self.end_minute.set(" 0")
        
    def check_hour_minute(self):
        global err_message
        #print(f"&&check_hour_minute {self.relay_number} : {self.start_hour.get()}:{self.start_minute.get()} ~ {self.end_hour.get()}:{self.end_minute.get()}")
        if self.start_hour.get() == ' 0' and self.start_minute.get() == ' 0' and self.end_hour.get() == ' 0' and self.end_minute.get() == ' 0':
            return 'タイマー時刻が設定されていません。'
        elif self.start_hour.get() == self.end_hour.get() and self.start_minute.get() == self.end_minute.get():
            return 'タイマー開始と終了に同じ時刻は設定できません。'
        elif (0 <= int(self.start_hour.get()) < 24 ) and (0 <= int(self.start_minute.get()) < 60 ) and \
             (0 <= int(self.end_hour.get())   < 24 ) and (0 <= int(self.end_minute.get())   < 60 ):
            return None
        else:
            return 'タイマー時刻にあり得ない数値が設定されています。'

    def relay_on(self,i):
        # 個別リレーのＯＮ
        if Usb_relay_device:
            instructions=[0, 0xFF, self.relay_number, 0, 0, 0, 0, 0, 1]
            Usb_relay_device.send(raw_data=instructions)
        Each_Relay[i].on_off = True
        root.show_relay_status(i)
        root.each_timer_status_update(i)        
        #print(f'relay {self.relay_number} on')

    def relay_off(self,i):
        #個別リレーのＯＦＦ
        if Usb_relay_device:
            instructions=[0, 0xFD, self.relay_number, 0, 0, 0, 0, 0, 1]
            Usb_relay_device.send(raw_data=instructions)
        Each_Relay[i].on_off = False
        root.show_relay_status(i)
        root.each_timer_status_update(i)
        #print(f'relay {self.relay_number} off')
        
    # タイマー処理(リレーのTIMERがONの時の処理)
    def relay_timer_decision(self,i):
        now = datetime.now()
        #print(f'##relay_timer<on> relay_id={i} relay_number={Each_Relay[i].relay_number}: {now.hour}:{now.minute} begin={Each_Relay[i].timer_begin} ')
        start_hour_int   = int(Each_Relay[i].start_hour.get())
        start_minute_int = int(Each_Relay[i].start_minute.get())
        end_hour_int     = int(Each_Relay[i].end_hour.get())
        end_minute_int   = int(Each_Relay[i].end_minute.get())
        #タイマーが開始されていないとき：０
        if (Each_Relay[i].timer_begin == False and 
            #開始時と開始分がカレント時、カレント分と等しい場合
            start_hour_int   == now.hour and 
            start_minute_int == now.minute):  
                Each_Relay[i].relay_on(i)
                USBRelayInterface.get_all_status()
                root.each_timer_status_update(i) 
                        
        #タイマーＯＦＦ時刻未到来のとき　：１ 
            #タイマーが開始していた場合(timer_beginがTrueの場合)         
        elif (Each_Relay[i].timer_begin and 
            #終了時と終了分がカレント時、カレント分と等しい場合
            end_hour_int   == now.hour and 
            end_minute_int == now.minute):
                Each_Relay[i].relay_off(i)
                USBRelayInterface.get_all_status()
                root.each_timer_status_update(i) 
    
    @staticmethod
    # デバイスのステータスを参照して、個別リレーのＯＮＯＦＦ状況をEach_Relay[i].on_offに反映する。
    def set_all_status():
        status_string = USBRelayInterface.get_all_status()
        if status_string:
            for i in range(QUANTITY_RELAY):
                if status_string[i] == 1:
                    Each_Relay[i].on_off = True
                else:
                    Each_Relay[i].on_off = False
        else:
            return False

    @staticmethod
    def on_all():
        # 全リレーをONにする
        if Usb_relay_device:
            instructions=[0, 0xFE, 0, 0, 0, 0, 0, 0, 1]
            Usb_relay_device.send(raw_data=instructions)
            RelayBoard.set_all_status()
        else:
            for i in range(QUANTITY_RELAY):
                Each_Relay[i].on_off = True
        root.show_all_relay_status()
        root.all_timer_status_update()
        #print('relay all on')
        
    @staticmethod
    def off_all():
        # 全リレーをOFFにする
        if Usb_relay_device:
            instructions=[0, 0xFC, 0, 0, 0, 0, 0, 0, 1]
            Usb_relay_device.send(raw_data=instructions)
            RelayBoard.set_all_status()
        else:
            for i in range(QUANTITY_RELAY):
                Each_Relay[i].on_off = False
        root.show_all_relay_status()
        root.all_timer_status_update()
        #print('relay all off')
     
class RelayControll:
    # メインウィンドウのクラス
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RELAY CONTROLLER")
        self.root.configure(bg="lightblue")
        height = QUANTITY_RELAY * 30 + 120
        self.root.geometry(f"635x{height}") # リレーの個数により高さを変更
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Arial", size=10)
        self.timer_status_infos    = [] 
        self.onoff_indicators      = []
        self.spinbox_start_hours   = []
        self.spinbox_start_minutes = []
        self.spinbox_end_hours     = []
        self.spinbox_end_minutes   = []
        self.relay_datas           = []
        self.y_offset              = 0
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # ウィンドウが閉じられたときの処理
        
            
    #========メニューの作成=========#
    # 読み込みイベントハンドラ
    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
        )
        if file_path:  # ユーザーがファイルを選択した場合
            try:
                with open(file_path, 'r') as f:
                    loaded_data = json.load(f)
                for i in range(QUANTITY_RELAY):
                    Each_Relay[i].classifying.set( loaded_data[i]["classifying"])
                    Each_Relay[i].timer_onoff.set( loaded_data[i]["timer_onoff"])
                    Each_Relay[i].start_hour.set(  loaded_data[i]["start_hour"])
                    Each_Relay[i].start_minute.set(loaded_data[i]["start_minute"])
                    Each_Relay[i].end_hour.set(    loaded_data[i]["end_hour"])
                    Each_Relay[i].end_minute.set(  loaded_data[i]["end_minute"])
                print(f"{file_path} からデータを読み込みました")
                self.Initial_display()
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                #show_error("エラーが発生しました。ファイルが正しく読み込まれない可能性があります。")
        
    # メニューのイベントハンドラ
    def save_file_dialog(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
        )
        if file_path:  # ユーザーがファイルを選択した場合
            data_to_save = []
            for i in range(QUANTITY_RELAY):
                data_to_save.append({
                    "classifying":  Each_Relay[i].classifying.get(),
                    "timer_onoff":  Each_Relay[i].timer_onoff.get(),
                    "start_hour":   Each_Relay[i].start_hour.get(),
                    "start_minute": Each_Relay[i].start_minute.get(),
                    "end_hour":     Each_Relay[i].end_hour.get(),
                    "end_minute":   Each_Relay[i].end_minute.get(),
                })
            with open(file_path, 'w') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            print(f"データを {file_path} に保存しました")

    # 設定メニューのイベントハンドラ
    def open_settings(self, settings):
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("設定")

        # ベンダーIDの設定
        vender_id_label = tk.Label(self.settings_window, text="ベンダーID:")
        vender_id_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        vender_id_entry = tk.Entry(self.settings_window)
        vender_id_entry.insert(0, settings["vender_id"])                    # 初期値を設定
        vender_id_entry.grid(row=0, column=1, padx=5, pady=5)

        # デバイスIDの設定
        device_id_label = tk.Label(self.settings_window, text="デバイスID:")
        device_id_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        device_id_entry = tk.Entry(self.settings_window)
        device_id_entry.insert(0, settings["device_id"])                    # 初期値を設定
        device_id_entry.grid(row=1, column=1, padx=5, pady=5)

        # リレーの個数の設定
        quantity_relay_label = tk.Label(self.settings_window, text="リレーの個数:")
        quantity_relay_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        quantity_relay_entry = tk.Entry(self.settings_window)
        quantity_relay_entry.insert(0, settings["quantity_relay"])          # 初期値を設定
        quantity_relay_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # デフォルトファイルの設定
        auto_load_label = tk.Label(self.settings_window, text="ﾃﾞﾌｫﾙﾄﾌｧｲﾙ名:")
        auto_load_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        auto_load_entry = tk.Entry(self.settings_window)
        auto_load_entry.insert(0, settings["auto_load"])                    # 初期値を設定
        auto_load_entry.grid(row=4, column=1, padx=5, pady=5)

        # 保存ボタン
        def set_settings():
            vender_id      = vender_id_entry.get()
            device_id      = device_id_entry.get()
            quantity_relay = quantity_relay_entry.get()
            auto_load      = auto_load_entry.get()
            data = {"vender_id": vender_id, "device_id": device_id, "quantity_relay": quantity_relay, "auto_load": auto_load }
            self.save_settings(data)
            print(f"ベンダーID: {vender_id}, デバイスID: {device_id}, リレー個数: {quantity_relay}, デフォルトファイル: {auto_load}")
            self.settings_window.destroy()

        save_button = tk.Button(self.settings_window, text="保存", command=lambda: set_settings())
        save_button.grid(row=6, column=0, columnspan=2, pady=10)

    def restart_program(self):
        #プログラムの再起動を行う関数
        # Pythonインタプリタの場合
        python = sys.executable
        os.execl(python, python, *sys.argv)
        # EXEの場合
        #executable = sys.executable  
        #os.execl(executable, executable, *sys.argv)

    # 設定データ（ベンダーＩＤ，デバイスＩＤ，リレー個数、デフォルトデータファイル名）を保存する関数
    def save_settings(self,data):
        print("設定ファイルを保存しました : ", data)
        with open(SETTING_FILE, "w") as file:
            json.dump(data, file)

        response = messagebox.askquestion(
            title="変更内容を反映",
            message="変更内容を反映するためにはこのプログラムの再起動が必要です。",
            icon="question"
        )

        if response == "yes":
            self.restart_program()
        else:
            messagebox.showinfo("キャンセル", "再起動はキャンセルされました。")
    
    def create_window_menu(self, settings):
        # メニューを作成
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        # ファイルメニューを作成
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="開く", command=lambda: self.open_file_dialog())
        self.filemenu.add_command(label="保存", command=lambda: self.save_file_dialog())
        self.filemenu.add_separator()
        self.filemenu.add_command(label="終了", command=root.on_closing)
        self.menubar.add_cascade(label="ファイル", menu=self.filemenu)
        # 設定メニューを開く
        self.menubar.add_command(label="設定", command=lambda: self.open_settings(settings))
    #========メニューの作成終わり=========#

    #========ヘッダーの作成=========# 
    def create_window_header(self):
        # ヘッダーを作成
        # プログラムタイトルと日時表示
        self.label = tk.Label(self.root, text=f"   {QUANTITY_RELAY}CH RELAY CONTROLLER   ", font=("Arial", 16), bg="SteelBlue", fg="white", relief="groove")
        self.label.place(x=120, y=0)
        self.label_current_time = tk.Label(self.root, text="", font=("Arial", 10), fg="Violet Red4", bg="lightblue")
        self.label_current_time.place(x=455, y=5)
        # 列タイトルの配置
        self.label1_1 = tk.Label(self.root, text="リレー  即 時                名           称                        タイマー SET   開始時：開始分～終了時：終了分", 
                            bg="turquoise",fg="navy", relief="groove")
        self.label1_1.place(x=5, y=30)

    def update_time(self):
        # 現在の日時分秒を取得し、表示
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.label_current_time.config(text=formatted_time)
        # 1秒後に再度この関数を呼び出す
        self.root.after(1000, self.update_time)
    #========ヘッダーの作成終わり=========#
    
    #========ＢＯＤＹの作成=========# 
    # 繰り返し処理でチャンネル数分の行を配置
    def create_window_relay(self,QUANTITY_RELAY):
        for i in range(QUANTITY_RELAY):
            self.y_offset = 54 + (30 * i)  # yの値を30ずつ増加
                
            # GUI部品を配置   
            relay_number = tk.Label(self.root, text=f"{i+1}：",bg="lightblue")
            relay_number.place(x=5, y=self.y_offset + 2)
            onoff_indicator = tk.Label(self.root, text="〇", bg="black", fg="white" )
            onoff_indicator.place(x=28, y=self.y_offset + 2)
            # エントリー項目の変数とクラス変数Each_Relay[i].classifyingをバインド
            entry_classifying = tk.Entry(self.root, width=30, font=("Arial", 10), textvariable=Each_Relay[i].classifying)
            entry_classifying.place(x=95, y=self.y_offset + 2)
            button_onoff = tk.Button(self.root, text="入/切", width=4, command=lambda idx=i: self.toggle_switch(idx), bg="cornsilk2")
            button_onoff.place(x=52, y=self.y_offset - 2)
            timer_status_info = tk.Label(self.root, text="未設定", bg="lightblue", fg="Orange Red4")
            timer_status_info.place(x=325, y=self.y_offset)
            # エントリー項目の変数とクラス変数Each_Relay[i].timer_onoffをバインド
            checkbox_timer = tk.Checkbutton(self.root, text="", variable=Each_Relay[i].timer_onoff, command=lambda idx=i: self.toggle_timer(idx), bg="lightblue")
            checkbox_timer.place(x=380, y=self.y_offset - 2)
            # エントリー項目の変数とクラス変数Each_Relay[i].start_hourをバインド
            spinbox_start_hour = tk.Spinbox(self.root, textvariable=Each_Relay[i].start_hour, from_=0, to=23, width=3, format='%2.0f', wrap=True, state='readonly')
            spinbox_start_hour.place(x=420, y=self.y_offset + 2)
            label_timer_s = tk.Label(self.root, text="：", bg="lightblue")
            label_timer_s.place(x=455, y=self.y_offset)
            # エントリー項目の変数とクラス変数Each_Relay[i].start_minuteをバインド
            spinbox_start_minute = tk.Spinbox(self.root, textvariable=Each_Relay[i].start_minute, from_=0, to=59, width=3, format='%2.0f', wrap=True, state='readonly')
            spinbox_start_minute.place(x=475, y=self.y_offset + 2)
            label_timer_kara = tk.Label(self.root, text="～", bg="lightblue")
            label_timer_kara.place(x=513, y=self.y_offset)   
            # エントリー項目の変数とクラス変数Each_Relay[i].end_hourをバインド
            spinbox_end_hour = tk.Spinbox(self.root, textvariable=Each_Relay[i].end_hour, from_=0, to=23, width=3, format='%2.0f', wrap=True, state='readonly')
            spinbox_end_hour.place(x=530, y=self.y_offset + 2)
            label_timer_e = tk.Label(self.root, text="：", bg="lightblue")
            label_timer_e.place(x=565, y=self.y_offset)
            # エントリー項目の変数とクラス変数Each_Relay[i].end_minuteをバインド
            spinbox_end_minute = tk.Spinbox(self.root, textvariable=Each_Relay[i].end_minute, from_=0, to=59, width=3, format='%2.0f', wrap=True, state='readonly')
            spinbox_end_minute.place(x=590, y=self.y_offset + 2)

            # Listに追加
            self.timer_status_infos.append(timer_status_info) 
            self.onoff_indicators.append(onoff_indicator) 
            self.spinbox_start_hours.append(spinbox_start_hour)
            self.spinbox_start_minutes.append(spinbox_start_minute)
            self.spinbox_end_hours.append(spinbox_end_hour)
            self.spinbox_end_minutes.append(spinbox_end_minute)      
    #========ＢＯＤＹの作成終わり=========#
    
    #========下行の作成=========# 
    # 下行のボタンとメッセージを配置
    def create_window_bottom(self):
        button_allon = tk.Button(self.root, text="全部入", width=6, command=RelayBoard.on_all, bg="light steel blue",fg="gray10")
        button_allon.place(x=25, y=self.y_offset + 30)
        button_alloff = tk.Button(self.root, text="全部切", width=6, command=RelayBoard.off_all, bg="light steel blue",fg="gray10")
        button_alloff.place(x=85, y=self.y_offset + 30)
        button_clear = tk.Button(self.root, text="画面クリア", width=10, command=self.all_clear, bg="light steel blue",fg="gray10")
        button_clear.place(x=145, y=self.y_offset + 30)

        if Usb_relay_device:
            program_message_color = "navy"
            # デバイスが正常に起動したとき、起動時の各リレーの機械的ONOFF状況を画面に反映する。
            RelayBoard.set_all_status()
            #show_all_relay_status()
        else:
            program_message_color = "red" 
            
        label10_1 = tk.Label(self.root, text=f"ベンダーID：{USB_CFG_VENDOR_ID}  デバイスID：{USB_CFG_DEVICE_ID}  {program_message}",bg="lightblue" ,fg=program_message_color)
        label10_1.place(x=6, y=self.y_offset + 60)
    #========下行の作成終わり=========# 

    #========画面イベントハンドラ=========# 
    # タイマーの状況を表示する関数
    def show_timer_status(self, i, info_text, fg_color):
        root.timer_status_infos[i]['text'] = info_text
        root.timer_status_infos[i].config( fg=fg_color) 
        
    # 全リレーの状況を画面に表示する関数
    def show_all_relay_status(self):
        for i in range(QUANTITY_RELAY):
            self.show_relay_status(i)

    # 個別リレーのＯＮ/ＯＦＦ状況を画面に表示する関数
    def show_relay_status(self,i):
        if Each_Relay[i].on_off:
            root.onoff_indicators[i].config(bg="yellow", fg="red")  # リレーがＯＮの時の表示
        else:
            root.onoff_indicators[i].config(bg="Black", fg="white") # リレーがＯＦＦの時の表示

    def set_disable_time(self,i):
        # タイマーをＯＮにしたらタイマー時刻の変更は不可とする
        root.spinbox_start_hours[i].config(state="disabled" )
        root.spinbox_start_minutes[i].config(state="disabled")
        root.spinbox_end_hours[i].config(state="disabled",)
        root.spinbox_end_minutes[i].config(state="disabled")
        
    def set_enable_time(self,i):
        # タイマー時刻の変更不可を解除する
        root.spinbox_start_hours[i].config(state="readonly")
        root.spinbox_start_minutes[i].config(state="readonly")
        root.spinbox_end_hours[i].config(state="readonly")
        root.spinbox_end_minutes[i].config(state="readonly")
        
    # 各リレーのタイマー状況を画面に表示する関数
    def each_timer_status_update(self,i):
        # タイマーの状況をセット
        if Each_Relay[i].timer_onoff.get() and Each_Relay[i].on_off:
            Each_Relay[i].timer_begin = True
            self.show_timer_status(i, "  開始", "red") 
        elif Each_Relay[i].timer_onoff.get() and not Each_Relay[i].on_off:
            Each_Relay[i].timer_begin = False
            self.show_timer_status(i, "待機中", "Orange Red4") 
        else:
            Each_Relay[i].timer_begin = False
            self.show_timer_status(i, "未設定", "green")
        #print(f"$$リレー{i+1} : タイマーON={Each_Relay[i].timer_onoff.get()} ON/OFF={Each_Relay[i].on_off} timer_begin={Each_Relay[i].timer_begin} status={root.timer_status_infos[i]['text']} " )
    # 全リレーの状況を画面に表示する関数
    def all_timer_status_update(self):
        for i in range(QUANTITY_RELAY):
            # リレーのＯＮＯＦＦ状況をリセット
            self.each_timer_status_update(i)  

    # タイマーのチェックボックスがクリックされた時の処理
    def toggle_timer(self,i):                                
        global err_message
        if Each_Relay[i].timer_onoff.get():                 # タイマーのチェックボックスをＯＮにした時
            err_message = Each_Relay[i].check_hour_minute() # 入力タイマー時刻のチェックを行う。
            if err_message:                                 # チェック結果にエラーメッセージがあれば
                Each_Relay[i].timer_onoff.set(False)        # チェックを外しタイマーをＯＦＦにする
                message = f"リレー{i+1} : {err_message}"     # エラーメッセージを作成
                self.show_error (message)                   # エラーポップアップ表示
                return                                      # エラーがあった場合はここで終了する
            
            self.each_timer_status_update(i)                # 各リレーの状況を画面に表示する 
            self.set_disable_time(i)                        # タイマーをＯＮにしたらタイマー時刻の変更は不可とする

        else:                                               # タイマーのチェックボックスをＯＦＦにした時
            self.each_timer_status_update(i)                # 各リレーの状況を画面に表示する            
            self.set_enable_time(i)                         # タイマー時刻の変更不可を解除する

    def toggle_switch(self,i):
        # 即時スイッチONOFFの切り替え
        if Each_Relay[i].on_off:                           # リレーがＯＮの時
            Each_Relay[i].relay_off(i)                     # 即時ＯＦＦの処理メソッド実行
            if RelayBoard.set_all_status() == False:       # 全リレーのＯＮＯＦＦ状況を設定(デバイスが有効の場合機械的にステータスを全部設定)
                Each_Relay[i].on_off = False               # デバイスが有効でない場合、ＯＮＯＦＦフラグをＯＦＦにする
        else:                                              # リレーがＯＦＦの時
            Each_Relay[i].relay_on(i)                      # 即時ＯＮの処理メソッド実行
            if RelayBoard.set_all_status() == False:       # 全リレーのＯＮＯＦＦ状況を設定(デバイスが有効の場合機械的にステータスを全部設定)
                Each_Relay[i].on_off = True                # デバイスが有効でない場合、ＯＮＯＦＦフラグをＯＮにする
        self.each_timer_status_update(i)                   # 各リレーの状況を画面に表示する 

    def all_clear(self):
        # 画面入力内容のクリア
        for i in range(QUANTITY_RELAY):
            Each_Relay[i].clear_all()
            # リレー時刻入力不可をリセット
            self.spinbox_start_hours[i].config(state="readonly")
            self.spinbox_start_minutes[i].config(state="readonly")
            self.spinbox_end_hours[i].config(state="readonly")
            self.spinbox_end_minutes[i].config(state="readonly")
            # リレーのＯＮＯＦＦ状況をリセット
            self.show_timer_status(i, "未設定", "green")
            
    def relay_timer_process(self):
        for i in range(QUANTITY_RELAY):
            # 各リレーのタイマーがＯＮの場合、時分のチェックを行う
            if Each_Relay[i].timer_onoff.get():  
                #print(f">>>>{i}.timer_onoff=", Each_Relay[i].timer_onoff.get())
                Each_Relay[i].relay_timer_decision(i)  # 各リレーの処理を実行

        # タイマー時刻の監視を60秒ごとに行う
        self.root.after(60000, self.relay_timer_process)
        # タイマー時刻の監視を6秒ごとに行う
        #root.after(6000, relay_timer_process)

    def Initial_display(self):
        self.show_all_relay_status()             # 全リレーの状況を画面に表示 
        for i in range(QUANTITY_RELAY):
            self.each_timer_status_update(i)     # 各タイマーの状況を画面に表示する
            if Each_Relay[i].timer_onoff.get():
                self.set_disable_time(i)         # タイマーをＯＮにしたらタイマー時刻の変更は不可とする
            else:
                self.set_enable_time(i)          # タイマー時刻の変更不可を解除する
        
    def run(self):
        self.root.mainloop()

    def on_closing(self):
        # ウィンドウ終了時に実行する処理
        USBRelayInterface.close_device()  # デバイスクローズ関数を呼び出す
        self.root.destroy()               # ウィンドウを閉じる
        
    # ポップアップを表示する関数
    def show_error(self,message):
        messagebox.showerror("エラー", message)
    #========画面イベントハンドラの終わり=========#
    
#========メイン処理=========#    
if __name__ == "__main__":
    
    # 外部設定ファイル名の定義
    SETTING_FILE = "settings.json"
    
    # 外部設定ファイルの読み込み       
    preset_file = PreSetting(SETTING_FILE)     # 設定ファイルのインスタンス化
    settings    = preset_file.check_settings() # 設定ファイルのチェック
    #print(f"ベンダーID: {settings["vender_id"]}\nデバイスID: {settings["device_id"]}\nリレー個数: {settings["quantity_relay"]}\n自動読み込み: {settings["auto_load"]}")
    # 設定ファイルの定数の設定 
    USB_CFG_VENDOR_ID = settings["vender_id"]
    USB_CFG_DEVICE_ID = settings["device_id"]
    QUANTITY_RELAY    = settings["quantity_relay"]
    AUTO_LOAD         = settings["auto_load"]
    
    # オートロード・データファイルの読み込み
    auto_loaded       = AutoLoadData(AUTO_LOAD,QUANTITY_RELAY)
    loaded_data       = auto_loaded.load_data()
    
    # HID情報の取得
    USBRelayInterface = USBRelayInterface(USB_CFG_VENDOR_ID, USB_CFG_DEVICE_ID)
    get_Hid_USBRelay  = USBRelayInterface.get_filter()

    # デバイスのオープン
    if get_Hid_USBRelay:
        Usb_relay_device      = USBRelayInterface.open_device()
        if Usb_relay_device:
            program_message   = "デバイスが正常にオープンされました。" 
        else:
            program_message   = "デバイスをＯＰＥＮできないためコントロール不可"
            Usb_relay_device  = None
    else:
        program_message       = "デバイスが不明のため、コントロール不可"
        Usb_relay_device      = None
        
    # tkオブジェクトの作成
    root = RelayControll()

    # 繰り返し処理でチャンネル数分のリレーオブジェクトを生成
    Each_Relay = []                            # リレーオブジェクトのリスト
    for i in range(QUANTITY_RELAY):
        # リレーオブジェクトの個別生成（クラス変数は画面の生成処理でバインドする
        Each_Relay.append(RelayBoard(i+1, False, False, 
                                    loaded_data[i]['classifying'], 
                                    loaded_data[i]['timer_onoff'], 
                                    loaded_data[i]['start_hour'], 
                                    loaded_data[i]['start_minute'], 
                                    loaded_data[i]['end_hour'], 
                                    loaded_data[i]['end_minute']
                                    )
                        )
        
    # GUIの初期化と画面生成
    root.create_window_menu(settings)         # メニューの作成
    root.create_window_header()               # ヘッダーの作成
    root.create_window_relay(QUANTITY_RELAY)  # リレーの行を配置
    root.create_window_bottom()               # 下行のボタンとメッセージを配置
    
    # 初期画面表示処理
    root.Initial_display()
    
    # カレント日時分秒の表示
    root.update_time()
    
    # タイマー処理の呼び出し
    root.relay_timer_process()
    
    # イベントループ開始
    root.run()
