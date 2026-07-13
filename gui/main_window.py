# File: gui/main_window.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import random
from datetime import datetime
import time
from datetime import datetime

# Import Module điều khiển máy đo từ thư mục core
from core.hioki_controller import HiokiPW3336Controller
from utils.html_exporter import HTMLExporter
from tkinter import filedialog
from gui.control_panels import DutControlWindow, RemoteConsoleWindow, BatchConfigWindow, CalculationWindow
from core.device_manager import DeviceManager

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.devices = DeviceManager()
        self.root.title(f"VHT - BS Power Consumption Measurement Tool (ETSI ES 202 706-1) \tver.{self.get_version_info()}")
        self.root.geometry("1100x850")
        
        # Biến trạng thái hệ thống
        self.is_measuring = False
        self.controller = None
        self.data_logs = []
        self.start_time = 0
        
        # Bảng màu
        self.colors = {
            "bg_app": "#E5E7EB", "bg_card": "#FFFFFF", "primary": "#1E3A8A", 
            "border": "#D1D5DB", "led_bg": "#050505", "led_red": "#FF0000", 
            "led_label": "#9CA3AF", "status_on": "#22C55E", "status_off": "#EF4444"
        }

        self.root.configure(bg=self.colors["bg_app"])
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TLabelframe', background=self.colors["bg_card"], bordercolor=self.colors["border"])
        style.configure('Modern.TLabelframe.Label', font=("Helvetica", 10, "bold"), foreground=self.colors["primary"], background=self.colors["bg_card"])
        style.configure("Modern.Treeview", font=("Helvetica", 10), rowheight=30)
        style.configure("Modern.Treeview.Heading", font=("Helvetica", 10, "bold"), background="#F3F4F6")

    def build_ui(self):
        # --- HEADER ---
        header_frame = tk.Frame(self.root, bg=self.colors["primary"], height=50)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="POWER CONSUMPTION MEASUREMENT - ETSI ES 202 706-1", 
                 font=("Arial", 14, "bold"), bg=self.colors["primary"], fg="white").pack(side="left", padx=20, pady=10)

        # --- CONFIGURATION CONTAINER ---
        config_container = tk.Frame(self.root, bg=self.colors["bg_app"])
        config_container.pack(fill="x", padx=10, pady=10)
        
        # DUT
        frame_dut = ttk.LabelFrame(config_container, text="DUT CONFIG", style='Modern.TLabelframe')
        frame_dut.pack(side="left", fill="both", expand=True, padx=(0, 5), ipady=5)
        dut_form = tk.Frame(frame_dut, bg=self.colors["bg_card"])
        dut_form.pack(side="left", padx=5)
        
        self.ent_serial = self.create_input_row(dut_form, "Serial:", "RRU8888_SN01", 0)
        self.ent_max_pwr = self.create_input_row(dut_form, "Max Power (W):", "1000.0", 1)
        
        dut_ctrl = tk.Frame(frame_dut, bg=self.colors["bg_card"])
        dut_ctrl.pack(side="right", fill="y", padx=10, pady=5)
        self.lbl_dut_status = tk.Label(dut_ctrl, text="● STOPPED", font=("Helvetica", 10, "bold"), fg=self.colors["status_off"], bg=self.colors["bg_card"])
        self.lbl_dut_status.pack(pady=(5, 10))
        tk.Button(dut_ctrl, text="Connection", font=("Arial", 9), bg="#F3F4F6", command=self.open_dut_control).pack()

        # POWER METER
        frame_meter = ttk.LabelFrame(config_container, text="METER CONFIG", style='Modern.TLabelframe')
        frame_meter.pack(side="left", fill="both", expand=True, padx=5, ipady=5)
        meter_form = tk.Frame(frame_meter, bg=self.colors["bg_card"])
        meter_form.pack(side="left", padx=5)
        
        tk.Label(meter_form, text="Model:", bg=self.colors["bg_card"], font=("Helvetica", 9)).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.cb_model = ttk.Combobox(meter_form, values=["Hioki pw3336"], width=13)
        self.cb_model.set("Hioki pw3336")
        self.cb_model.grid(row=0, column=1, padx=5, pady=3)

        self.ent_ip = self.create_input_row(meter_form, "IP Address:", "10.6.6.94", 1)
        self.ent_port = self.create_input_row(meter_form, "Port:", "3300", 2)
        
        meter_ctrl = tk.Frame(frame_meter, bg=self.colors["bg_card"])
        meter_ctrl.pack(side="right", fill="y", padx=10, pady=5)
        self.lbl_meter_status = tk.Label(meter_ctrl, text="● DISCONNECTED", font=("Helvetica", 10, "bold"), fg=self.colors["status_off"], bg=self.colors["bg_card"])
        self.lbl_meter_status.pack(pady=(5, 10))
        tk.Button(meter_ctrl, text="Connection", font=("Arial", 9), bg="#F3F4F6", command=self.open_meter_remote).pack()
        self.var_sim_mode = tk.BooleanVar(value=False) # Mặc định bật chế độ giả lập để test
        tk.Checkbutton(meter_ctrl, text="Simulation Mode", variable=self.var_sim_mode, bg=self.colors["bg_card"], font=("Arial", 8, "italic")).pack()
        
        # MEASUREMENT INFO
        frame_test = ttk.LabelFrame(config_container, text="MEASUREMENT SETTINGS", style='Modern.TLabelframe')
        frame_test.pack(side="left", fill="both", expand=True, padx=(5, 0), ipady=5)
        test_form = tk.Frame(frame_test, bg=self.colors["bg_card"])
        test_form.pack(side="left", padx=5)
        
        # tk.Label(test_form, text="Bài đo:", bg=self.colors["bg_card"], font=("Helvetica", 9)).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        # self.cb_profile = ttk.Combobox(test_form, values=["Full Load", "Busy Hour Load", "Medium Load", "Low Load"], width=13)
        # self.cb_profile.set("Full Load")
        # self.cb_profile.grid(row=0, column=1, padx=5, pady=3)
        
        # # Thêm sự kiện: Khi chọn Combobox sẽ tự động đổi thời gian tương ứng
        # self.cb_profile.bind("<<ComboboxSelected>>", self.on_profile_selected)
        
        # self.ent_duration = self.create_input_row(test_form, "Time (s):", "3600", 1)
        self.ent_sample = self.create_input_row(test_form, "Sample (s):", "1.0", 0)

        test_ctrl = tk.Frame(frame_test, bg=self.colors["bg_card"])
        test_ctrl.pack(side="right", fill="y", padx=10, pady=5)
      
        # 1. Nút Batch Config
        tk.Button(test_ctrl, text="⚙ Testcases", font=("Arial", 9, "bold"), bg="#DBEAFE", fg=self.colors["primary"], height=2, command=self.open_batch_config).pack(pady=(0, 5), fill="x")   
        # 2. Nút Calculation (MỚI)
        tk.Button(test_ctrl, text="🧮 Calculation", font=("Arial", 9, "bold"), bg="#FEF3C7", fg="#B45309", height=1, command=self.open_calculation).pack(fill="x")
        # --- DASHBOARD & LED BẢNG ---
        dashboard_frame = tk.Frame(self.root, bg=self.colors["led_bg"], bd=5, relief="ridge")
        dashboard_frame.pack(fill="x", padx=10, pady=5)
        
        toolbar = tk.Frame(dashboard_frame, bg="#1F1F1F")
        toolbar.pack(fill="x")
        self.btn_start = tk.Button(toolbar, text="▶ START", font=("Arial", 10, "bold"), bg="#22C55E", fg="white", command=self.start_measurement)
        self.btn_start.pack(side="left", padx=10, pady=5)
        self.btn_stop = tk.Button(toolbar, text="⏹ STOP", font=("Arial", 10, "bold"), bg="#EF4444", fg="white", state="disabled", command=self.stop_measurement)
        self.btn_stop.pack(side="left")

        # === COMBOBOX CHỌN CHANNEL ===
        # tk.Label(toolbar, text="Channel:", bg=self.colors["bg_card"], font=("Arial", 9, "bold")).pack(side="left", padx=(20, 5))
        self.cb_channel = ttk.Combobox(toolbar, values=["CH1", "CH2", "CH3", "SUM"], width=10, state="readonly")
        self.cb_channel.set("CH1")
        self.cb_channel.pack(side="left", padx=10, pady=5)
        
        self.cb_channel.bind("<<ComboboxSelected>>", self.on_channel_changed)

        # === LABEL HIỂN THỊ TÊN BÀI ĐANG ĐO ===
        self.lbl_current_test = tk.Label(toolbar, text="TEST: NONE", font=("Arial", 11, "bold"), bg="#1F1F1F", fg="#60A5FA")
        self.lbl_current_test.pack(side="left", padx=30, pady=5)
        
        self.lbl_eval = tk.Label(toolbar, text="EVALUATION: N/A", font=("Courier New", 12, "bold"), bg="#1F1F1F", fg="yellow")
        self.lbl_eval.pack(side="left", padx=30, pady=5)

        # === BUTTON EXPORT REPORT ===
        self.btn_export = tk.Button(toolbar, text="EXPORT REPORT", font=("Arial", 10, "bold"), bg="#374151", fg="white", relief="flat", width=15, command=self.export_html_report)
        self.btn_export.pack(side="right", padx=10, pady=5)

        # === ĐỒNG HỒ ĐẾM NGƯỢC ===
        self.lbl_countdown = tk.Label(toolbar, text="⏳ 00:00:00", font=("Courier New", 14, "bold"), bg="#1F1F1F", fg="#38BDF8")
        self.lbl_countdown.pack(side="right", padx=20, pady=5)

        led_container = tk.Frame(dashboard_frame, bg=self.colors["led_bg"], padx=10, pady=10)
        led_container.pack(fill="x")
        self.lbl_ch_volt, self.lbl_volt = self.create_hardware_led_row(led_container, "CH1", "DC", "VOLTAGE", "00.00", "V")
        self.lbl_ch_curr, self.lbl_curr = self.create_hardware_led_row(led_container, "CH1", "DC", "CURRENT", "00.00", "A")
        self.lbl_ch_pwr, self.lbl_pwr  = self.create_hardware_led_row(led_container, "CH1", "DC", "POWER", "000.00", "W")
        _, self.lbl_avg  = self.create_hardware_led_row(led_container, "AVG", "INT", "P-AVG", "000.00", "W")

        # --- STATUS BAR (CẦN KHAI BÁO TRƯỚC TREEVIEW)---
        self.status_bar = tk.Frame(self.root, bg=self.colors["primary"], height=30)
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.pack_propagate(False)

        tk.Label(self.status_bar, text="Ready", font=("Arial", 9), bg=self.colors["primary"], fg="white").pack(side="left", padx=10)

        # -----------------

        # --- DATA LOGGING TREEVIEW ---
        table_container = tk.Frame(self.root, bg=self.colors["bg_card"])
        table_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tuple columns
        columns = ("stt", "sys_time", "meas_time", "channel", "volt", "curr", "inst_power", "avg_power", "eval")
        
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", style="Modern.Treeview")
        
        # Headers và widths đã có đủ 9 phần tử tương ứng với columns
        headers = ["STT", "System Time", "Elapsed (s)", "Channel", "Voltage (V)", "Current (A)", "P Inst (W)", "P Avg (W)", "Status"]
        
        # Điều chỉnh độ rộng cột Channel (80) để dồn không gian cho các cột số liệu
        widths = [50, 150, 100, 80, 100, 100, 120, 120, 100] 
        
        for col, text, width in zip(columns, headers, widths):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")
            
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # Kích hoạt chạy đồng hồ thời gian thực ngay khi mở App
        self.lbl_realtime = tk.Label(self.status_bar, text=" --:--:--", font=("Arial", 16, "bold"), bg=self.colors["primary"], fg="white")
        self.lbl_realtime.pack(side="right", padx=20)
        self.update_realtime_clock()

    # --- CÁC FUNCTION TRONG BUILTIN-UI ---
    def open_dut_control(self):
        DutControlWindow(self.root)

    def open_meter_remote(self):
        # Lấy IP và Port hiện tại từ giao diện chính để truyền sang Console
        current_ip = self.ent_ip.get()
        current_port = self.ent_port.get()
        
        # Mở popup
        RemoteConsoleWindow(
            parent_root=self.root, 
            current_ip=current_ip, 
            current_port=current_port,
            callback_on_close=self.update_meter_config_from_console
        )
    
    def update_meter_config_from_console(self, data):
        # 1. Cập nhật Textbox IP, Port
        self.ent_ip.delete(0, tk.END)
        self.ent_ip.insert(0, data["ip"])
        self.ent_port.delete(0, tk.END)
        self.ent_port.insert(0, data["port"])
        
        # 2. XỬ LÝ VÀ LƯU DANH SÁCH KÊNH (CHANNELS)
        selected_channels = data.get("channels", ["CH1"])
        self.measured_channels = selected_channels 
        
        # 3. COMBOBOX CHỈ LÀM NHIỆM VỤ ĐỔ CHUỖI ĐƠN LẺ ĐỂ VIEW LED
        self.cb_channel.config(values=self.measured_channels)
        self.cb_channel.set(self.measured_channels[0])  

        self.on_channel_changed()

        # 4. CẬP NHẬT TRẠNG THÁI UI
        if self.devices.is_hioki_connected():
            self.lbl_meter_status.config(text="● CONNECTED", fg=self.colors["status_on"])
        else:
            if not self.var_sim_mode.get():
                self.lbl_meter_status.config(text="● DISCONNECTED", fg=self.colors["status_off"])
            else:
                self.lbl_meter_status.config(text="● SIMULATING", fg="#F59E0B")

    def open_batch_config(self):
        initial_config = getattr(self, 'full_batch_config', None)
        BatchConfigWindow(self.root, initial_config=initial_config, callback_on_ok=self.apply_batch_plan)

    def apply_batch_plan(self, full_config):
        """Hàm nhận kết quả từ cửa sổ Batch Config"""
        # 2. Lưu lại toàn bộ trạng thái (cả cái check và uncheck)
        self.full_batch_config = full_config
        self.batch_plan = [item for item in full_config if item["checked"]]
        
        if self.batch_plan:
            msg = "Đã nhận danh sách chạy tự động:\n"
            for item in self.batch_plan:
                msg += f"- {item['name']}: {item['duration']}s\n"
            messagebox.showinfo("Batch Ready", msg)

    def on_profile_selected(self, event=None):
        """Khi user chọn bằng tay trên Combo Box, tự động tìm thời gian tương ứng trong Batch để điền vào"""
        selected_name = self.cb_profile.get()
        # Kiểm tra xem có cấu hình batch lưu sẵn không
        if hasattr(self, 'batch_plan') and self.batch_plan:
            for test in self.batch_plan:
                if test['name'] == selected_name:
                    self.ent_duration.delete(0, tk.END)
                    self.ent_duration.insert(0, test['duration'])
                    break

    def open_calculation(self):
        CalculationWindow(self.root)

    def update_realtime_clock(self):
        """Cập nhật đồng hồ hệ thống mỗi giây ở Status Bar"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_realtime.config(text=f"{now}")
        # Lặp lại hàm này sau 1000ms (1 giây)
        self.root.after(1000, self.update_realtime_clock)

    def update_countdown(self):
        """Chạy đồng hồ đếm ngược độc lập với chu kỳ lấy mẫu"""
        if self.is_measuring and self.remaining_time >= 0:
            mins, secs = divmod(self.remaining_time, 60)
            hours, mins = divmod(mins, 60)
            
            # Định dạng chuỗi hiển thị HH:MM:SS
            time_str = f"⏳ {int(hours):02d}:{int(mins):02d}:{int(secs):02d}"
            self.lbl_countdown.config(text=time_str)
            
            self.remaining_time -= 1
            self.root.after(1000, self.update_countdown)
        elif not self.is_measuring:
            self.lbl_countdown.config(text="⏳ 00:00:00")
    
    def on_channel_changed(self, event=None):
        selected_ch = self.cb_channel.get()
        self.lbl_ch_volt.config(text=selected_ch)
        self.lbl_ch_curr.config(text=selected_ch)
        self.lbl_ch_pwr.config(text=selected_ch)

    # ==========================================
    # CORE LOGIC & EVENT HANDLERS
    # ==========================================
    def start_measurement(self):
        if not hasattr(self, 'batch_plan') or not self.batch_plan:
            messagebox.showwarning("Chưa cấu hình", "Chưa chọn testcase!")
            return
        # Khởi tạo kho lưu trữ tổng cho toàn bộ Batch
        self.all_batch_results = []

        self.current_batch_index = 0
        self.run_next_batch_test()

    def run_next_batch_test(self):
        if self.current_batch_index < len(self.batch_plan):
            current_test = self.batch_plan[self.current_batch_index]
            
            # Cập nhật thông số ẩn và Label trạng thái
            self.current_profile_name = current_test['name']
            self.duration = int(current_test['duration'])
            self.lbl_current_test.config(text=f"TEST: {self.current_profile_name.upper()}")
            
            ready = messagebox.askokcancel(
                "Cấu hình Base Station",
                f"Bước {self.current_batch_index + 1}/{len(self.batch_plan)}: Chuẩn bị đo bài [{self.current_profile_name}]\n\n"
                f"Thời gian đo: {self.duration} giây.\n"
                f"Thực hiện cấu hình DUT thủ công.\n\n"
                f"Sau khi hoàn tất cấu hình, bấm OK để bắt đầu đo."
            )
            
            if ready:
                self.connect_and_measure()
            else:
                self.stop_measurement()
                messagebox.showinfo("Đã Hủy", "Quá trình đo đã bị hủy bỏ bởi người dùng.")
        else:
            self.stop_measurement()
            self.lbl_current_test.config(text="TEST: NONE")
            messagebox.showinfo("Hoàn tất", "Hoàn thành đo!")

    def connect_and_measure(self):
        if self.devices.is_hioki_connected():
            self.devices.get_hioki().start_integration()
            self.start_routine()
            # return
       
        ip = self.ent_ip.get()
        port = int(self.ent_port.get())
        
        try:
            self.sample_rate = float(self.ent_sample.get())
            self.max_power = float(self.ent_max_pwr.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập đúng định dạng số!")
            return

        if self.var_sim_mode.get():
            self.lbl_meter_status.config(text="● SIMULATING", fg="#F59E0B")
            self.start_routine()
        else:
            success, msg = self.devices.connect_hioki(ip, port)
            if success:
                self.lbl_meter_status.config(text="● CONNECTED", fg=self.colors["status_on"])
                # Lấy mảng kênh đã lưu thay vì Combobox
                channels_to_measure = getattr(self, 'measured_channels', ["CH1"])
                self.devices.get_hioki().setup_measure_items(channels_to_measure)
                self.devices.get_hioki().start_integration()
                self.start_routine()
            else:
                self.lbl_meter_status.config(text="● FAILED", fg=self.colors["status_off"])
                messagebox.showerror("Lỗi", msg)
            # self.controller = HiokiPW3336Controller(ip, port)
            # success, msg = self.controller.connect()
            # if success:
            #     self.lbl_meter_status.config(text="● CONNECTED", fg=self.colors["status_on"])
            #     self.controller.setup_measure_items()
            #     self.controller.setup_measure_items()
            #     self.controller.start_integration()
            #     self.start_routine()
            # else:
            #     self.lbl_meter_status.config(text="● FAILED", fg=self.colors["status_off"])
            #     messagebox.showerror("Lỗi Kết Nối", msg)

    def start_routine(self):
        """Hàm phụ trợ dọn dẹp UI và kích hoạt luồng chạy"""
        self.is_measuring = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.data_logs.clear()
        self.start_time = time.time()
        # --- KÍCH HOẠT ĐẾM NGƯỢC ---
        self.remaining_time = self.duration
        self.update_countdown()
        
        threading.Thread(target=self.measurement_worker, daemon=True).start()

    def stop_measurement(self):
        self.is_measuring = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.devices.get_hioki().stop_integration()
        
        # if self.controller:
        #     self.controller.disconnect()
        #     self.lbl_meter_status.config(text="● DISCONNECTED", fg=self.colors["status_off"])

    # def measurement_worker(self):       
        
    #     sample_count = 0
    #     current_profile = getattr(self, 'current_profile_name', 'Unknown')
        
    #     # Lấy danh sách các kênh đang cần đo (mặc định CH1 nếu mảng trống)
    #     measured_channels = getattr(self, 'measured_channels', ['CH1'])
        
    #     # Biến đệm riêng cho chế độ mô phỏng (Tính P_avg độc lập cho từng kênh)
    #     sim_total_power = {ch: 0.0 for ch in measured_channels}
    #     sim_tick_count = {ch: 0 for ch in measured_channels}
        
    #     while self.is_measuring:
    #         elapsed = time.time() - self.start_time
    #         if elapsed > self.duration:
    #             self.is_measuring = False
    #             self.root.after(0, self.on_test_finished)
    #             break

    #         data_dict = {}
    #         hours = elapsed / 3600.0
            
    #         # ==================================================
    #         # 1. ĐỌC DỮ LIỆU TỪ MÁY ĐO THẬT (QUA DEVICE MANAGER)
    #         # ==================================================
    #         if not self.var_sim_mode.get() and self.devices.is_hioki_connected():
    #             hioki = self.devices.get_hioki()
    #             if not hioki or not hioki.is_connected:
    #                 self.root.after(0, lambda: messagebox.showerror("Lỗi", "Mất kết nối với máy đo HIOKI!"))
    #                 self.is_measuring = False
    #                 break

    #             data_dict = hioki.read_measurements()
    #         # ==================================================
    #         # 2. CHẾ ĐỘ GIẢ LẬP 
    #         # ==================================================
    #         else:
    #             for ch in measured_channels:
    #                 volt = random.uniform(-48.2, -47.8) 
                    
    #                 if ch == "CH1":
    #                     # Giả lập BBU: Tiêu thụ điện ổn định, ít phụ thuộc vào tải
    #                     curr = random.uniform(3.5, 4.0)
                        
    #                 elif ch == "CH2":
    #                     # Giả lập RRU: Dao động mạnh theo kịch bản bài đo (Profile)
    #                     if current_profile == "Full Load": curr = random.uniform(14.5, 15.5)
    #                     elif current_profile == "Busy Hour Load": curr = random.uniform(10.0, 11.0)
    #                     elif current_profile == "Medium Load": curr = random.uniform(7.0, 7.8)
    #                     else: curr = random.uniform(2.0, 2.5)
                        
    #                 else:
    #                     # Kênh dự phòng (CH3) nếu có
    #                     curr = random.uniform(1.0, 1.5)
                    
    #                 # Thêm chút nhiễu ngẫu nhiên hệ thống cho tự nhiên
    #                 curr += random.uniform(-0.1, 0.1) 
                    
    #                 p = abs(volt * curr)
    #                 sim_tick_count[ch] += 1
    #                 sim_total_power[ch] += p
                    
    #                 data_dict[ch] = {'U': abs(volt), 'I': curr, 'P': p}

    #         # ==================================================
    #         # 3. XỬ LÝ VÀ ĐẨY DỮ LIỆU LÊN GIAO DIỆN
    #         # ==================================================
    #         if data_dict:
    #             # 1. Đọc và chuyển đổi kênh Combobox thành số nguyên (1 hoặc 2)
    #             selected_text = self.cb_channel.get().strip().upper()
    #             viewed_ch_int = 1 if "1" in selected_text else 2
                
    #             # 2. Đọc max_power 1 lần ở ngoài vòng lặp cho tối ưu
    #             try:
    #                 current_max_pwr = float(self.ent_max_pwr.get())
    #             except ValueError:
    #                 current_max_pwr = 1000.0

    #             # 3. Đọc trạng thái Simulation 1 lần
    #             is_sim_mode = self.var_sim_mode.get()

    #             for ch_name, vals in data_dict.items():
    #                 sample_count += 1
    #                 u, i, p, ptav = vals.get('U', 0), vals.get('I', 0), vals.get('P', 0), vals.get('PTAV', 0)
                    
    #                 # Tính Công suất trung bình (P_Avg)
    #                 if not is_sim_mode and ptav < 1e6:
    #                     p_avg = ptav
    #                     # wp = vals.get('PTAV', p)
    #                     # p_avg = (wp / hours) if hours > 0 else p
    #                 else:
    #                     p_avg = sim_total_power[ch_name] / sim_tick_count[ch_name]
                        
    #                 # Đánh giá PASS/FAIL dựa trên current_max_pwr đã đọc ở trên
    #                 eval_status = "PASS" if p <= current_max_pwr else "FAIL"
                    
    #                 # Gói thành Record 9 phần tử
    #                 record = (sample_count, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), int(elapsed), 
    #                         ch_name, f"{u:.2f}", f"{i:.2f}", f"{p:.2f}", f"{p_avg:.2f}", eval_status)
                    
    #                 # SỬA Ở ĐÂY: So sánh int với int (VD: 1 == 1)
    #                 is_viewed = (ch_name == viewed_ch_int)
                    
    #                 # Bắn qua UI (Main Thread)
    #                 self.root.after(0, self.update_dashboard, record, is_viewed)

    #         time.sleep(self.sample_rate)
    def measurement_worker(self):       
        import random
        import time
        import csv
        import os
        from datetime import datetime

        # 1. KHÓA CHỐNG TRÙNG LUỒNG
        if getattr(self, '_is_worker_running', False):
            return
        self._is_worker_running = True
        
        current_profile = getattr(self, 'current_profile_name', 'Unknown')
        measured_channels = getattr(self, 'measured_channels', ['CH1'])
        
        sim_total_power = {ch: 0.0 for ch in measured_channels}
        sim_tick_count = {ch: 0 for ch in measured_channels}
        
        # 2. CHỐT CHÍNH XÁC SỐ LƯỢNG MẪU
        total_cycles = int(self.duration / self.sample_rate)
        if total_cycles <= 0: total_cycles = 1

        cycle_count = 0  
        self.start_time = time.time()
        
        # ==================================================
        # KHỞI TẠO FILE CSV BACKUP CHỐNG CRASH
        # ==================================================
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        csv_filename = datetime.now().strftime(f"logs/BackupLog_{self.ent_serial.get()}_%Y%m%d_%H%M%S.csv")
        try:
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Ghi dòng tiêu đề
                writer.writerow(['STT', 'System Time', 'Elapsed (s)', 'Channel', 'Voltage (V)', 'Current (A)', 'Power (W)', 'P Avg (W)', 'Status'])
        except Exception as e:
            print(f"Không thể tạo file CSV backup: {e}")

        # Mốc thời gian chuẩn bị cho chu kỳ tiếp theo (bù trừ sai số)
        next_tick = self.start_time + self.sample_rate
        
        while self.is_measuring and cycle_count < total_cycles:
            cycle_count += 1
            
            elapsed = int(cycle_count * self.sample_rate)
            hours = elapsed / 3600.0

            data_dict = {}
            
            # ==================================================
            # 1. ĐỌC DỮ LIỆU TỪ MÁY ĐO THẬT (QUA DEVICE MANAGER)
            # ==================================================
            if not self.var_sim_mode.get() and self.devices.is_hioki_connected():
                hioki = self.devices.get_hioki()
                if not hioki or not hioki.is_connected:
                    self.root.after(0, lambda: messagebox.showerror("Lỗi", "Mất kết nối với máy đo HIOKI!"))
                    self.is_measuring = False
                    break

                data_dict = hioki.read_measurements()
            # ==================================================
            # 2. CHẾ ĐỘ GIẢ LẬP 
            # ==================================================
            else:
                for ch in measured_channels:
                    volt = random.uniform(-48.2, -47.8) 
                    
                    if ch == "CH1":
                        curr = random.uniform(3.5, 4.0)
                    elif ch == "CH2":
                        if current_profile == "Full Load": curr = random.uniform(14.5, 15.5)
                        elif current_profile == "Busy Hour Load": curr = random.uniform(10.0, 11.0)
                        elif current_profile == "Medium Load": curr = random.uniform(7.0, 7.8)
                        else: curr = random.uniform(2.0, 2.5)
                    else:
                        curr = random.uniform(1.0, 1.5)
                    
                    curr += random.uniform(-0.1, 0.1) 
                    
                    p = abs(volt * curr)
                    sim_tick_count[ch] += 1
                    sim_total_power[ch] += p
                    
                    data_dict[ch] = {'U': abs(volt), 'I': curr, 'P': p}

            # ==================================================
            # 3. XỬ LÝ VÀ ĐẨY DỮ LIỆU LÊN GIAO DIỆN + GHI FILE CSV
            # ==================================================
            if data_dict:
                selected_text = self.cb_channel.get().strip().upper()
                viewed_ch_int = 1 if "1" in selected_text else 2
                
                try:
                    current_max_pwr = float(self.ent_max_pwr.get())
                except ValueError:
                    current_max_pwr = 1000.0

                is_sim_mode = self.var_sim_mode.get()
                sys_time_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                for ch_name, vals in data_dict.items():
                    u, i, p, ptav = vals.get('U', 0), vals.get('I', 0), vals.get('P', 0), vals.get('PTAV', 0)
                    
                    if not is_sim_mode and ptav < 1e6:
                        p_avg = ptav
                    else:
                        if sim_tick_count[ch_name] > 0:
                            p_avg = sim_total_power[ch_name] / sim_tick_count[ch_name]
                        else:
                            p_avg = 0

                    eval_status = "PASS" if p <= current_max_pwr else "FAIL"
                    
                    # Gói thành Record 9 phần tử
                    record = (cycle_count, sys_time_str, elapsed, 
                              ch_name, f"{u:.2f}", f"{i:.2f}", f"{p:.2f}", f"{p_avg:.2f}", eval_status)
                    
                    # --- GHI REAL-TIME VÀO FILE CSV ---
                    try:
                        with open(csv_filename, mode='a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(record)
                    except Exception as e:
                        pass # Bỏ qua lỗi nếu có file đang bị kẹt để không làm treo tool
                    
                    # Bóc tách số từ ch_name (vd: "CH1" -> 1) để so sánh an toàn
                    try:
                        ch_name_int = int(str(ch_name).replace("CH", ""))
                    except:
                        ch_name_int = ch_name

                    is_viewed = (ch_name_int == viewed_ch_int)
                    
                    self.root.after(0, self.update_dashboard, record, is_viewed)

            # ==================================================
            # 4. BÙ TRỪ THỜI GIAN
            # ==================================================
            now = time.time()
            sleep_duration = next_tick - now
            
            if sleep_duration > 0:
                time.sleep(sleep_duration)
                
            next_tick += self.sample_rate

        # --- KẾT THÚC BÀI ĐO ---
        self.is_measuring = False
        self._is_worker_running = False
        self.root.after(0, self.on_test_finished)

    def on_test_finished(self):
        # 1. LƯU DỮ LIỆU CỦA BÀI VỪA ĐO VÀO KHO
        if hasattr(self, 'data_logs') and self.data_logs:
            self.all_batch_results.append({
                "test_name": self.current_profile_name,
                "max_power": float(self.ent_max_pwr.get()),
                "logs": list(self.data_logs) 
            })

        # Ngắt kết nối thiết bị sau mỗi bài
        # if self.controller:
        #     self.controller.stop_integration()
        #     self.controller.disconnect()
            
        # (Tùy chọn): Tại đây có thể chèn dòng code gọi tính năng Auto-Export báo cáo 
        # file_path = f"report_{self.batch_plan[self.current_batch_index]['name']}.html"
        # self.export_html_report(auto_save_path=file_path)
        
        
        self.current_batch_index += 1
        self.run_next_batch_test()    

    def update_dashboard(self, record, is_viewed=True):
        """Cập nhật dữ liệu hiển thị (Chạy trên Main Thread)"""
        # Giải nén 9 phần tử (Đã thêm biến 'channel' vào vị trí số 4)
        stt, sys_time, elapsed, channel, u, i, p, p_avg, status = record
        
        # 1. LUÔN LUÔN LƯU DỮ LIỆU: Cập nhật vào Data table và Memory
        # (Chèn vào vị trí 0 để dữ liệu mới nhất luôn hiển thị trên cùng)
        self.tree.insert("", 0, values=record)
        self.data_logs.append(record)
        
        # 2. CHỈ HIỂN THỊ LÊN LED NẾU ĐÚNG KÊNH ĐANG ĐƯỢC TICK CHỌN TRÊN COMBOBOX
        if is_viewed:
            # Update LED đỏ
            self.lbl_volt.config(text=f"{float(u):05.2f}")
            self.lbl_curr.config(text=f"{float(i):05.2f}")
            self.lbl_pwr.config(text=f"{float(p):06.2f}")
            self.lbl_avg.config(text=f"{float(p_avg):06.2f}")
            
            # Update Evaluation
            color = "#22C55E" if status == "PASS" else "#EF4444"
            self.lbl_eval.config(text=f"EVALUATION: {status}", fg=color)

    def on_closing(self):
        """Hàm dọn dẹp khi đóng cửa sổ phần mềm"""
        self.is_measuring = False
        if self.controller:
            self.controller.disconnect()
        self.root.destroy()

    # --- HÀM UI HELPERS ---
    def create_input_row(self, parent, label_text, default_val, row_idx):
        tk.Label(parent, text=label_text, bg=self.colors["bg_card"], font=("Helvetica", 9)).grid(row=row_idx, column=0, padx=5, pady=3, sticky="w")
        entry = ttk.Entry(parent, width=15)
        entry.insert(0, default_val)
        entry.grid(row=row_idx, column=1, padx=5, pady=3)
        return entry # Trả về đối tượng Entry để lấy value sau này

    def create_hardware_led_row(self, parent, channel, mode, label, value, unit):
        row_frame = tk.Frame(parent, bg=self.colors["led_bg"], highlightbackground="#222222", highlightthickness=1)
        row_frame.pack(fill="x", pady=2)

        left_panel = tk.Frame(row_frame, bg=self.colors["led_bg"], width=200)
        left_panel.pack(side="left", fill="y", padx=10, pady=5)
        
        # Gán nhãn kênh vào một biến để có thể return
        lbl_channel = tk.Label(left_panel, text=channel, font=("Arial", 11, "bold"), fg="white", bg="#333333", relief="raised", bd=2, width=5)
        lbl_channel.pack(side="left", padx=(0, 10))
        
        tk.Label(left_panel, text=mode, font=("Arial", 9, "bold"), fg=self.colors["led_red"], bg=self.colors["led_bg"]).pack(side="left", padx=5)
        tk.Label(left_panel, text=label, font=("Arial", 11, "bold"), fg=self.colors["led_label"], bg=self.colors["led_bg"], width=10, anchor="w").pack(side="left", padx=5)

        tk.Label(row_frame, text=unit, font=("Arial", 16, "bold"), fg=self.colors["led_red"], bg=self.colors["led_bg"], width=3, anchor="w").pack(side="right", padx=15)
        lbl_value = tk.Label(row_frame, text=value, font=("Courier New", 36, "bold"), fg=self.colors["led_red"], bg=self.colors["led_bg"], anchor="e")
        lbl_value.pack(side="right", expand=True, fill="x", padx=10)

        # TRẢ VỀ CẢ 2 NHÃN BẰNG TUPLE
        return lbl_channel, lbl_value
    
    # def export_html_report(self):
    #     from tkinter import filedialog, messagebox
    #     from datetime import datetime
        
    #     if not hasattr(self, 'data_logs') or not self.data_logs:
    #         messagebox.showwarning("Trống", "Không có dữ liệu để xuất báo cáo!")
    #         return

    #     file_path = filedialog.asksaveasfilename(
    #         defaultextension=".html",
    #         filetypes=[("HTML files", "*.html")],
    #         title="Lưu báo cáo HTML"
    #     )
        
    #     if not file_path:
    #         return

    #     logs = self.data_logs
        
    #     # 1. BÓC TÁCH DỮ LIỆU THEO TỪNG KÊNH
    #     channels_data = {}
    #     for row in logs:
    #         # row format: (stt, sys_time, elapsed, channel, u, i, p, p_avg, status)
    #         elapsed = int(row[2])
    #         ch = row[3]
    #         u = float(row[4])
    #         i = float(row[5])
    #         p = float(row[6])
            
    #         if ch not in channels_data:
    #             channels_data[ch] = {'elapsed': [], 'p': [], 'logs': []}
                
    #         channels_data[ch]['elapsed'].append(elapsed)
    #         channels_data[ch]['p'].append(p)
    #         channels_data[ch]['logs'].append(row)

    #     # 2. XÂY DỰNG KHỐI HTML SUMMARY CHO TỪNG KÊNH
    #     summary_html_blocks = ""
    #     for ch, cdata in channels_data.items():
    #         p_list = cdata['p']
    #         max_p = max(p_list) if p_list else 0
    #         min_p = min(p_list) if p_list else 0
    #         avg_p = sum(p_list) / len(p_list) if p_list else 0
            
    #         summary_html_blocks += f"""
    #         <div class="summary-card">
    #             <h3>Thống kê Kênh {ch}</h3>
    #             <p>Max Power: <span class="highlight">{max_p:.2f} W</span></p>
    #             <p>Min Power: <span class="highlight">{min_p:.2f} W</span></p>
    #             <p>Avg Power: <span class="highlight">{avg_p:.2f} W</span></p>
    #             <p>Số mẫu đo: <span class="highlight">{len(p_list)}</span></p>
    #         </div>
    #         """

    #     # 3. CHUẨN BỊ DATASET CHO CHART.JS (MỖI KÊNH 1 ĐƯỜNG ĐỒ THỊ)
    #     datasets_js = []
    #     colors = ["#EF4444", "#3B82F6", "#10B981", "#F59E0B"] # Bảng màu cho các đường (Đỏ, Xanh dương, Xanh lá, Vàng)
        
    #     for idx, (ch, cdata) in enumerate(channels_data.items()):
    #         color = colors[idx % len(colors)]
    #         datasets_js.append(f"""
    #             {{
    #                 label: 'Công suất {ch} (W)',
    #                 data: {cdata['p']},
    #                 borderColor: '{color}',
    #                 backgroundColor: '{color}22',
    #                 borderWidth: 2,
    #                 fill: true,
    #                 tension: 0.2,
    #                 pointRadius: 0,
    #                 pointHoverRadius: 4
    #             }}
    #         """)
            
    #     chart_datasets_string = ",\n".join(datasets_js)
    #     # Lấy trục thời gian (Elapsed) của kênh đầu tiên làm mốc chuẩn cho toàn bộ biểu đồ
    #     chart_labels_string = str(channels_data[list(channels_data.keys())[0]]['elapsed'])

    #     # 4. TẠO CÁC DÒNG CHO BẢNG DỮ LIỆU CHI TIẾT
    #     table_rows = ""
    #     for row in logs:
    #         # Gán class màu sắc dựa trên kết quả EVAL (PASS/FAIL)
    #         tr_class = "status-pass" if row[8] == "PASS" else "status-fail"
    #         table_rows += f"""
    #         <tr class="{tr_class}">
    #             <td>{row[0]}</td>
    #             <td>{row[1]}</td>
    #             <td>{row[2]}</td>
    #             <td><b>{row[3]}</b></td>
    #             <td>{row[4]}</td>
    #             <td>{row[5]}</td>
    #             <td>{row[6]}</td>
    #             <td>{row[7]}</td>
    #             <td>{row[8]}</td>
    #         </tr>
    #         """

    #     # 5. RÁP THÀNH MÃ HTML HOÀN CHỈNH
    #     html_content = f"""
    #     <!DOCTYPE html>
    #     <html lang="en">
    #     <head>
    #         <meta charset="UTF-8">
    #         <meta name="viewport" content="width=device-width, initial-scale=1.0">
    #         <title>Power Consumption Report</title>
    #         <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    #         <style>
    #             body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F3F4F6; margin: 0; padding: 20px; color: #1F2937; }}
    #             .container {{ max-width: 1200px; margin: auto; background: #FFFFFF; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    #             h1 {{ text-align: center; color: #111827; border-bottom: 2px solid #E5E7EB; padding-bottom: 10px; }}
                
    #             .summary-container {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; justify-content: center; }}
    #             .summary-card {{ flex: 1; min-width: 200px; background: #F8FAFC; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; text-align: center; }}
    #             .summary-card h3 {{ margin-top: 0; color: #3B82F6; }}
    #             .summary-card p {{ margin: 10px 0; font-size: 14px; font-weight: 500; }}
    #             .highlight {{ font-size: 18px; font-weight: bold; color: #0F172A; }}
                
    #             .chart-container {{ width: 100%; height: 400px; margin: 30px 0; }}
                
    #             table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
    #             th, td {{ border: 1px solid #E5E7EB; padding: 10px; text-align: center; }}
    #             th {{ background-color: #F9FAFB; color: #374151; font-weight: bold; }}
    #             .status-pass td {{ background-color: #DCFCE7; color: #166534; }}
    #             .status-fail td {{ background-color: #FEE2E2; color: #991B1B; }}
    #         </style>
    #     </head>
    #     <body>
    #         <div class="container">
    #             <h1>BÁO CÁO TIÊU THỤ ĐIỆN NĂNG (MULTI-CHANNEL)</h1>
    #             <p style="text-align: center; color: #6B7280;">Ngày xuất báo cáo: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
                
    #             <div class="summary-container">
    #                 {summary_html_blocks}
    #             </div>

    #             <div class="chart-container">
    #                 <canvas id="powerChart"></canvas>
    #             </div>

    #             <h3>Dữ liệu chi tiết</h3>
    #             <table>
    #                 <thead>
    #                     <tr>
    #                         <th>STT</th>
    #                         <th>Thời gian</th>
    #                         <th>Elapsed (s)</th>
    #                         <th>Kênh (CH)</th>
    #                         <th>Điện áp (V)</th>
    #                         <th>Dòng điện (A)</th>
    #                         <th>Công suất (W)</th>
    #                         <th>P. Trung bình (W)</th>
    #                         <th>Trạng thái</th>
    #                     </tr>
    #                 </thead>
    #                 <tbody>
    #                     {table_rows}
    #                 </tbody>
    #             </table>
    #         </div>

    #         <script>
    #             const ctx = document.getElementById('powerChart').getContext('2d');
    #             new Chart(ctx, {{
    #                 type: 'line',
    #                 data: {{
    #                     labels: {chart_labels_string},
    #                     datasets: [
    #                         {chart_datasets_string}
    #                     ]
    #                 }},
    #                 options: {{
    #                     responsive: true,
    #                     maintainAspectRatio: false,
    #                     interaction: {{ mode: 'index', intersect: false }},
    #                     scales: {{
    #                         x: {{ title: {{ display: true, text: 'Thời gian đo (s)', font: {{weight: 'bold'}} }} }},
    #                         y: {{ title: {{ display: true, text: 'Công suất tiêu thụ (W)', font: {{weight: 'bold'}} }} }}
    #                     }}
    #                 }}
    #             }});
    #         </script>
    #     </body>
    #     </html>
    #     """

    #     try:
    #         with open(file_path, "w", encoding="utf-8") as f:
    #             f.write(html_content)
    #         messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công tại:\n{file_path}")
    #     except Exception as e:
    #         messagebox.showerror("Lỗi file", f"Không thể lưu file báo cáo:\n{e}")

    def export_html_report(self):
        from tkinter import filedialog, messagebox
        from datetime import datetime
        
        # Kiểm tra xem có dữ liệu trong kho tổng hoặc data_logs đang hiển thị không
        if not hasattr(self, 'all_batch_results') or not self.all_batch_results:
            if not self.data_logs:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất báo cáo!")
                return
            else:
                # Nếu chạy lẻ tẻ (chưa có trong all_batch_results) thì tự động bọc lại
                self.all_batch_results = [{
                    "test_name": getattr(self, 'current_profile_name', 'Manual Test'),
                    "max_power": float(self.ent_max_pwr.get()),
                    "logs": list(self.data_logs)
                }]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".html", 
            filetypes=[("HTML Report", "*.html")],
            initialfile=f"{self.ent_serial.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        
        if not file_path:
            return

        summary_data = []
        detailed_data = []
        overall_pass = True

        # QUÉT QUA TỪNG BÀI ĐO TRONG BATCH
        for result in self.all_batch_results:
            t_name = result["test_name"]
            m_power = result["max_power"]
            raw_logs = result["logs"]
            
            if len(raw_logs) == 0: continue
            
            # 1. BÓC TÁCH DỮ LIỆU THEO TỪNG CHANNEL
            logs_by_channel = {}
            for row in raw_logs:
                ch = row[3]  # Lấy Channel ở vị trí index 3
                if ch not in logs_by_channel:
                    logs_by_channel[ch] = []
                logs_by_channel[ch].append(row)

            # 2. XỬ LÝ TỪNG CHANNEL THÀNH MỘT MỤC BÁO CÁO RIÊNG BIỆT
            for ch, logs in logs_by_channel.items():
                # Tạo tên bài đo ghép với tên kênh (VD: "Full Load - CH1")
                t_name_ch = f"{t_name} ({ch})"
                
                total = len(logs)
                
                # Đếm Pass/Fail (Trạng thái giờ nằm ở ô số 8)
                pass_count = sum(1 for row in logs if row[8] == "PASS")
                fail_count = total - pass_count
                
                if fail_count > 0:
                    overall_pass = False
                
                # P_avg cuối cùng nằm ở ô số 7
                final_p_avg = logs[-1][7]

                # Dữ liệu cho Bảng tóm tắt (Summary)
                summary_data.append({
                    "test_name": t_name_ch,
                    "total": total,
                    "pass_count": pass_count,
                    "fail_count": fail_count,
                    "max_power": m_power,
                    "final_p_avg": final_p_avg,
                    "verdict": "PASS" if fail_count == 0 else "FAIL"
                })
                
                # Dữ liệu cho Bảng chi tiết & Biểu đồ Chart.js (Đã cập nhật Index)
                chart_labels = [row[2] for row in logs]
                chart_data = [float(row[6]) for row in logs]  # Power (index 6)
                chart_limit = [m_power] * total

                chart_volt = [float(row[4]) for row in logs]  # Voltage (index 4)
                chart_curr = [float(row[5]) for row in logs]  # Current (index 5)
                
                detailed_data.append({
                    "test_name": t_name_ch,
                    "total": total,
                    "fail_count": fail_count,
                    "chart_labels": chart_labels,
                    "chart_data": chart_data,
                    "chart_limit": chart_limit,
                    "chart_volt": chart_volt,   
                    "chart_curr": chart_curr,   
                    "table_data": logs
                })

        # Dữ liệu Header của Report (Lấy sys_time ở index 1)
        first_log = self.all_batch_results[0]["logs"]
        last_log = self.all_batch_results[-1]["logs"]
        
        general_info = {
            "Serial Number": self.ent_serial.get(),
            "Product Type": "RRU gNodeB",
            "Test Standard": "ETSI ES 202 706-1",
            "Start Time": first_log[0][1] if first_log else "N/A",
            "End Time": last_log[-1][1] if last_log else "N/A",
            "Overall Result": "PASS" if overall_pass else "FAIL"
        }

        # Gọi file HTMLExporter của bạn
        from utils.html_exporter import HTMLExporter
        exporter = HTMLExporter()
        exporter.export_report(file_path, general_info, summary_data, detailed_data)
        
        messagebox.showinfo("Thành công", f"Đã xuất báo cáo Batch HTML thành công:\n{file_path}")


    def get_version_info(self):
        # 1. TỰ ĐỘNG ĐỌC VERSION TỪ FILE VERSION.TXT
        version = "0.0.0"
        try:
            # PyInstaller khi chạy exe sẽ giải nén vào thư mục tạm có tên trong sys._MEIPASS
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
                
            version_path = os.path.join(base_path, 'version.txt')
            
            if os.path.exists(version_path):
                with open(version_path, 'r') as f:
                    version = f.read().strip()
        except Exception as e:
            print(f"Không thể đọc version: {e}")
        
        return version
            