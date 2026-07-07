# File: gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

# Import Module điều khiển máy đo từ thư mục core
from core.hioki_controller import HiokiPW3336Controller
from utils.html_exporter import HTMLExporter
from tkinter import filedialog
from gui.control_panels import DutControlWindow, RemoteConsoleWindow

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("ETSI ES 202 706-1 | RRU Power Measurement")
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
        self.ent_max_pwr = self.create_input_row(dut_form, "Max Power (W):", "1500.0", 1)
        
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

        self.ent_ip = self.create_input_row(meter_form, "IP Address:", "192.168.1.10", 1)
        self.ent_port = self.create_input_row(meter_form, "Port:", "3390", 2)
        
        meter_ctrl = tk.Frame(frame_meter, bg=self.colors["bg_card"])
        meter_ctrl.pack(side="right", fill="y", padx=10, pady=5)
        self.lbl_meter_status = tk.Label(meter_ctrl, text="● DISCONNECTED", font=("Helvetica", 10, "bold"), fg=self.colors["status_off"], bg=self.colors["bg_card"])
        self.lbl_meter_status.pack(pady=(5, 10))
        tk.Button(meter_ctrl, text="Connection", font=("Arial", 9), bg="#F3F4F6", command=self.open_meter_remote).pack()
        self.var_sim_mode = tk.BooleanVar(value=True) # Mặc định bật chế độ giả lập để test
        tk.Checkbutton(meter_ctrl, text="Simulation Mode", variable=self.var_sim_mode, bg=self.colors["bg_card"], font=("Arial", 8, "italic")).pack()
        
        # MEASUREMENT INFO
        frame_test = ttk.LabelFrame(config_container, text="MEASUREMENT SETTINGS", style='Modern.TLabelframe')
        frame_test.pack(side="left", fill="both", expand=True, padx=(5, 0), ipady=5)
        test_form = tk.Frame(frame_test, bg=self.colors["bg_card"])
        test_form.pack(side="left", padx=5)
        
        tk.Label(test_form, text="Bài đo:", bg=self.colors["bg_card"], font=("Helvetica", 9)).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.cb_profile = ttk.Combobox(test_form, values=["Full Load", "Busy 70%", "Busy 50%", "Low Load"], width=13)
        self.cb_profile.set("Full Load")
        self.cb_profile.grid(row=0, column=1, padx=5, pady=3)
        
        self.ent_duration = self.create_input_row(test_form, "Time (s):", "3600", 1)
        self.ent_sample = self.create_input_row(test_form, "Sample (s):", "1.0", 2)

        test_ctrl = tk.Frame(frame_test, bg=self.colors["bg_card"])
        test_ctrl.pack(side="right", fill="y", padx=10, pady=5)
      
        tk.Button(test_ctrl, text="⚙ Batch Config\n(Multi-tests)", font=("Arial", 9, "bold"), bg="#DBEAFE", fg=self.colors["primary"], height=3, command=self.open_batch_config).pack(pady=5)
        # --- DASHBOARD & LED BẢNG ---
        dashboard_frame = tk.Frame(self.root, bg=self.colors["led_bg"], bd=5, relief="ridge")
        dashboard_frame.pack(fill="x", padx=10, pady=5)
        
        toolbar = tk.Frame(dashboard_frame, bg="#1F1F1F")
        toolbar.pack(fill="x")
        self.btn_start = tk.Button(toolbar, text="▶ START", font=("Arial", 10, "bold"), bg="#22C55E", fg="white", command=self.start_measurement)
        self.btn_start.pack(side="left", padx=10, pady=5)
        self.btn_stop = tk.Button(toolbar, text="⏹ STOP", font=("Arial", 10, "bold"), bg="#EF4444", fg="white", state="disabled", command=self.stop_measurement)
        self.btn_stop.pack(side="left")
        
        self.lbl_eval = tk.Label(toolbar, text="EVALUATION: N/A", font=("Courier New", 12, "bold"), bg="#1F1F1F", fg="yellow")
        self.lbl_eval.pack(side="left", padx=30, pady=5)

        self.btn_export = tk.Button(toolbar, text="EXPORT REPORT", font=("Arial", 10, "bold"), bg="#374151", fg="white", relief="flat", width=15, command=self.export_html_report)
        self.btn_export.pack(side="right", padx=10, pady=5)

        # 1. Thêm đồng hồ đếm ngược
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

        # 2. Label hiển thị đồng hồ thời gian thực
        self.lbl_realtime = tk.Label(self.status_bar, text="System Time: --:--:--", font=("Arial", 16, "bold"), bg=self.colors["primary"], fg="white")
        self.lbl_realtime.pack(side="right", padx=20)

        # --- DATA LOGGING TREEVIEW ---
        table_container = tk.Frame(self.root, bg=self.colors["bg_card"])
        table_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("stt", "sys_time", "meas_time", "volt", "curr", "inst_power", "avg_power", "eval")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", style="Modern.Treeview")
        headers = ["STT", "System Time", "Elapsed (s)", "Voltage (V)", "Current (A)", "P Inst (W)", "P Avg (W)", "Status"]
        widths = [50, 150, 100, 100, 100, 120, 120, 100]
        for col, text, width in zip(columns, headers, widths):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")
            
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # Kích hoạt chạy đồng hồ thời gian thực ngay khi mở App
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
        # 1. Cập nhật IP
        self.ent_ip.delete(0, tk.END)
        self.ent_ip.insert(0, data["ip"])
        
        # 2. Cập nhật Port
        self.ent_port.delete(0, tk.END)
        self.ent_port.insert(0, data["port"])
        
        # 3. Cập nhật Channel trên Bảng LED
        selected_ch = data["channel"]
        if selected_ch != "SUM":
            self.lbl_ch_volt.config(text=selected_ch)
            self.lbl_ch_curr.config(text=selected_ch)
            self.lbl_ch_pwr.config(text=selected_ch)
            
        print(f"[UI Updated] Thiết lập máy đo: {data['model']} | {data['ip']}:{data['port']} | Kênh: {selected_ch}")


    def open_batch_config(self):
        messagebox.showinfo("Batch Configuration", "Tự động chạy lần lượt các testcase theo ETSI ES 202 706-1:\n1. Full Load (4h)\n2. Busy 70% (8h)\n3. Busy 50% (8h)\n(Tính năng chưa phát triển)")
    
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

    # ==========================================
    # CORE LOGIC & EVENT HANDLERS
    # ==========================================
    def start_measurement(self):
        ip = self.ent_ip.get()
        port = int(self.ent_port.get())
        
        try:
            self.duration = int(self.ent_duration.get())
            self.sample_rate = float(self.ent_sample.get())
            self.max_power = float(self.ent_max_pwr.get())
        except ValueError:
            messagebox.showerror("Input Error", "Vui lòng nhập đúng số!")
            return

        # KIỂM TRA CHẾ ĐỘ MÔ PHỎNG
        if self.var_sim_mode.get():
            self.lbl_meter_status.config(text="● SIMULATING", fg="#F59E0B") # Màu cam báo hiệu đang chạy giả lập
            self.start_routine()
        else:
            # Chạy thật: Kết nối thiết bị
            self.controller = HiokiPW3336Controller(ip, port)
            success, msg = self.controller.connect()
            
            if success:
                self.lbl_meter_status.config(text="● CONNECTED", fg=self.colors["status_on"])
                self.controller.setup_measure_items()
                self.start_routine()
            else:
                self.lbl_meter_status.config(text="● FAILED", fg=self.colors["status_off"])
                messagebox.showerror("Connection Error", msg)

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
        
        if self.controller:
            self.controller.disconnect()
            self.lbl_meter_status.config(text="● DISCONNECTED", fg=self.colors["status_off"])

    def measurement_worker(self):
        import random # Thêm thư viện random
        sample_count = 0
        total_power = 0.0
        
        # Đọc tên bài đo từ Combobox để giả lập cho giống thật
        current_profile = self.cb_profile.get() 
        
        while self.is_measuring:
            elapsed = time.time() - self.start_time
            if elapsed > self.duration:
                self.root.after(0, self.stop_measurement)
                self.root.after(0, lambda: messagebox.showinfo("Hoàn thành", "Đã kết thúc thời gian thử nghiệm."))
                break

            data = None
            if not self.var_sim_mode.get() and self.controller:
                data = self.controller.read_measurements() # Đọc máy thật
            else:
                # --- GIẢ LẬP DỮ LIỆU THEO TẢI ETSI ---
                volt = random.uniform(-48.2, -47.8) # Điện áp DC trạm viễn thông luôn quanh -48V
                
                if current_profile == "Full Load":
                    curr = random.uniform(14.5, 15.5)
                elif current_profile == "Busy 70%":
                    curr = random.uniform(10.0, 11.0)
                elif current_profile == "Busy 50%":
                    curr = random.uniform(7.0, 7.8)
                else: # Low Load
                    curr = random.uniform(2.0, 2.5)
                    
                data = {'U': abs(volt), 'I': curr, 'P': abs(volt * curr)}

            if data:
                sample_count += 1
                u, i, p = data['U'], data['I'], data['P']
                
                total_power += p
                p_avg = total_power / sample_count
                eval_status = "PASS" if p <= self.max_power else "FAIL"
                
                record = (sample_count, datetime.now().strftime("%H:%M:%S"), int(elapsed), 
                          f"{u:.2f}", f"{i:.2f}", f"{p:.2f}", f"{p_avg:.2f}", eval_status)
                self.root.after(0, self.update_dashboard, record)

            time.sleep(self.sample_rate)

    def update_dashboard(self, record):
        """Cập nhật dữ liệu hiển thị (Chạy trên Main Thread)"""
        stt, sys_time, elapsed, u, i, p, p_avg, status = record
        
        # Update LED đỏ
        self.lbl_volt.config(text=f"{float(u):05.2f}")
        self.lbl_curr.config(text=f"{float(i):05.2f}")
        self.lbl_pwr.config(text=f"{float(p):06.2f}")
        self.lbl_avg.config(text=f"{float(p_avg):06.2f}")
        
        # Update Evaluation
        color = "#22C55E" if status == "PASS" else "#EF4444"
        self.lbl_eval.config(text=f"EVALUATION: {status}", fg=color)
        
        # Update Data table
        self.tree.insert("", 0, values=record)
        self.data_logs.append(record)

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
        lbl_channel = tk.Label(left_panel, text=channel, font=("Arial", 11, "bold"), fg="white", bg="#333333", relief="raised", bd=2, width=4)
        lbl_channel.pack(side="left", padx=(0, 10))
        
        tk.Label(left_panel, text=mode, font=("Arial", 9, "bold"), fg=self.colors["led_red"], bg=self.colors["led_bg"]).pack(side="left", padx=5)
        tk.Label(left_panel, text=label, font=("Arial", 11, "bold"), fg=self.colors["led_label"], bg=self.colors["led_bg"], width=10, anchor="w").pack(side="left", padx=5)

        tk.Label(row_frame, text=unit, font=("Arial", 16, "bold"), fg=self.colors["led_red"], bg=self.colors["led_bg"], width=3, anchor="w").pack(side="right", padx=15)
        lbl_value = tk.Label(row_frame, text=value, font=("Courier New", 36, "bold"), fg=self.colors["led_red"], bg=self.colors["led_bg"], anchor="e")
        lbl_value.pack(side="right", expand=True, fill="x", padx=10)

        # TRẢ VỀ CẢ 2 NHÃN BẰNG TUPLE
        return lbl_channel, lbl_value

    def export_html_report(self):
        if not self.data_logs:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất báo cáo!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".html", 
            filetypes=[("HTML Report", "*.html")],
            initialfile=f"{self.ent_serial.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        
        if not file_path:
            return

        # 1. Chuẩn bị Dữ liệu Thông tin chung
        overall_pass = all(row[7] == "PASS" for row in self.data_logs)
        general_info = {
            "Serial Number": self.ent_serial.get(),
            "Product Type": "RRU gNodeB",
            "Test Standard": "ETSI ES 202 706-1",
            "Start Time": self.data_logs[0][1] if self.data_logs else "N/A",
            "End Time": self.data_logs[-1][1] if self.data_logs else "N/A",
            "Overall Result": "PASS" if overall_pass else "FAIL"
        }

        # 2. Chuẩn bị Dữ liệu Tóm tắt
        test_name = self.cb_profile.get()
        max_limit = float(self.ent_max_pwr.get())
        total = len(self.data_logs)
        pass_count = sum(1 for row in self.data_logs if row[7] == "PASS")
        fail_count = total - pass_count

        summary_data = [
            {
                "test_name": test_name,
                "total": total,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "max_power": max_limit,
                "verdict": "PASS" if fail_count == 0 else "FAIL"
            }
        ]

        # 3. Chuẩn bị Dữ liệu Chi tiết & Biểu đồ
        chart_labels = [row[2] for row in self.data_logs] # Trục X: Thời gian đo (s)
        chart_data = [float(row[5]) for row in self.data_logs] # Trục Y: Công suất P
        chart_limit = [max_limit] * total # Đường kẻ ngang đỏ giới hạn

        detailed_data = [
            {
                "test_name": test_name,
                "total": total,
                "fail_count": fail_count,
                "chart_labels": chart_labels,
                "chart_data": chart_data,
                "chart_limit": chart_limit,
                "table_data": self.data_logs
            }
        ]

        # 4. Xuất file
        exporter = HTMLExporter()
        exporter.export_report(file_path, general_info, summary_data, detailed_data)
        
        messagebox.showinfo("Thành công", f"Đã xuất báo cáo HTML thành công:\n{file_path}")