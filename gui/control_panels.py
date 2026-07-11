import tkinter as tk
import socket
import os
from tkinter import ttk, messagebox, filedialog
from core.device_manager import DeviceManager

class RemoteConsoleWindow:
    def __init__(self, parent_root, current_ip="10.6.6.94", current_port="3300", callback_on_close=None):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Power Meter - Remote Control Console")
        self.window.geometry("600x550")
        self.window.configure(bg="#F4F6F9")
        
        # Khóa tương tác với cửa sổ chính khi Popup này đang 
        # mở (Modal window)
        self.window.grab_set() 
        
        self.controller = None
        self.is_connected = False
        
        self.current_ip = current_ip
        self.current_port = current_port
        self.devices = DeviceManager()
        self.callback_on_close = callback_on_close
        
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Console.TLabelframe", background="#FFFFFF", bordercolor="#D1D5DB")
        style.configure("Console.TLabelframe.Label", font=("Arial", 10, "bold"), foreground="#1E3A8A", background="#FFFFFF")
        style.configure("TCombobox", padding=3)

    def build_ui(self):
        # ==========================================
        # 1. KHUNG CẤU HÌNH KẾT NỐI (CONNECTION)
        # ==========================================
        conn_frame = ttk.LabelFrame(self.window, text="Connection Settings", style="Console.TLabelframe")
        conn_frame.pack(fill="x", padx=15, pady=10, ipady=5)
        
        # Inner frame for white background
        inner_conn = tk.Frame(conn_frame, bg="#FFFFFF")
        inner_conn.pack(fill="both", expand=True, padx=10, pady=5)

        # Row 1: Model & Connection Type
        tk.Label(inner_conn, text="Model:", bg="#FFFFFF", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.cb_model = ttk.Combobox(inner_conn, values=["HIOKI PW3336"], width=15, state="readonly")
        self.cb_model.set("HIOKI PW3336")
        self.cb_model.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(inner_conn, text="Type:", bg="#FFFFFF", anchor="e").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.cb_type = ttk.Combobox(inner_conn, values=["TCPIP"], width=10, state="readonly")
        self.cb_type.set("TCPIP")
        self.cb_type.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Row 2: IP & Port
        tk.Label(inner_conn, text="IP Address:", bg="#FFFFFF", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_ip = ttk.Entry(inner_conn, width=18)
        self.ent_ip.insert(0, self.current_ip)
        self.ent_ip.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(inner_conn, text="Port:", bg="#FFFFFF", anchor="e").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.ent_port = ttk.Entry(inner_conn, width=12)
        self.ent_port.insert(0, self.current_port)
        self.ent_port.grid(row=1, column=3, padx=5, pady=5, sticky="w")        

        # Row 3: Connect Button & Status
        self.btn_connect = tk.Button(inner_conn, text="Connect", font=("Arial", 9, "bold"), bg="#2563EB", fg="white", relief="flat", width=12, command=self.toggle_connection)
        self.btn_connect.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        self.lbl_status = tk.Label(inner_conn, text="● DISCONNECTED", font=("Arial", 9, "bold"), fg="#EF4444", bg="#FFFFFF")
        self.lbl_status.grid(row=2, column=2, columnspan=2, padx=5, pady=10, sticky="w")

        # ==========================================
        # 2. CẤU HÌNH KÊNH ĐO (MEASUREMENT CHANNELS)
        # ==========================================
        ch_frame = ttk.LabelFrame(self.window, text="Measurement Channels", style="Console.TLabelframe")
        ch_frame.pack(fill="x", padx=15, pady=5)
        
        inner_ch = tk.Frame(ch_frame, bg="#FFFFFF")
        inner_ch.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.var_ch1 = tk.BooleanVar(value=True)  # Mặc định tick kênh 1
        self.var_ch2 = tk.BooleanVar(value=False)
        self.var_ch3 = tk.BooleanVar(value=False)
        
        tk.Checkbutton(inner_ch, text="CH1", variable=self.var_ch1, bg="#FFFFFF", font=("Arial", 9, "bold")).pack(side="left", padx=15)
        tk.Checkbutton(inner_ch, text="CH2", variable=self.var_ch2, bg="#FFFFFF", font=("Arial", 9, "bold")).pack(side="left", padx=15)
        tk.Checkbutton(inner_ch, text="CH3", variable=self.var_ch3, bg="#FFFFFF", font=("Arial", 9, "bold")).pack(side="left", padx=15)

        # ==========================================
        # 3. KHUNG CMD SCPI
        # ==========================================
        cmd_frame = ttk.LabelFrame(self.window, text="SCPI Command Terminal", style="Console.TLabelframe")
        cmd_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        inner_cmd = tk.Frame(cmd_frame, bg="#FFFFFF")
        inner_cmd.pack(fill="both", expand=True, padx=10, pady=10)

        # Command Input
        tk.Label(inner_cmd, text="Command:", bg="#FFFFFF", font=("Arial", 9, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_cmd = ttk.Entry(inner_cmd, width=40, font=("Courier New", 10))
        self.ent_cmd.insert(0, "*IDN?") # Lệnh nhận diện mặc định để test
        self.ent_cmd.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        self.btn_send = tk.Button(inner_cmd, text="SEND ↵", font=("Arial", 9, "bold"), bg="#10B981", fg="white", relief="flat", command=self.send_command, state="disabled")
        self.btn_send.grid(row=1, column=2, padx=10, pady=5)

        # Response Output
        tk.Label(inner_cmd, text="Response:", bg="#FFFFFF").grid(row=2, column=0, padx=5, pady=(15,5), sticky="ne")
        
        # Dùng Text widget thay vì Entry để hiển thị nhiều dòng nếu dữ liệu trả về dài
        self.txt_response = tk.Text(inner_cmd, width=40, height=8, font=("Courier New", 10), bg="#F8FAFC", relief="solid", bd=1)
        self.txt_response.grid(row=2, column=1, columnspan=2, padx=5, pady=(15,5), sticky="w")
        
        # Cho phép gõ Enter ở khung Command để gửi lệnh
        self.window.bind('<Return>', lambda event: self.send_command() if self.is_connected else None)

        # ==========================================
        # 2. CLOSE BUTTON
        # ==========================================
        bottom_frame = tk.Frame(self.window, bg="#F4F6F9")
        bottom_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        # Tạo nút Close
        btn_close = tk.Button(bottom_frame, text="Apply Config & Close", font=("Arial", 10, "bold"), bg="#6B7280", fg="white", relief="flat", height=2, command=self.on_close_clicked)
        btn_close.pack(fill="x")

    # ==========================================
    # CÁC HÀM XỬ LÝ LOGIC
    # ==========================================
    def toggle_connection(self):
        if not self.devices.is_hioki_connected():
            ip = self.ent_ip.get()
            port = self.ent_port.get()
            
            success, msg = self.devices.connect_hioki(ip, port)
            
            if success:
                self.btn_connect.config(text="Disconnect", bg="#EF4444")
                self.lbl_status.config(text="● CONNECTED", fg="#22C55E")
                self.append_response(f"Connected: {msg}")
                self.btn_send.config(state="normal")
            else:
                messagebox.showerror("Lỗi", msg)
        else:
            self.devices.disconnect_hioki()
            self.btn_connect.config(text="Connect", bg="#10B981")
            self.lbl_status.config(text="● DISCONNECTED", fg="#EF4444")
            self.btn_send.config(state="disabled")
            self.append_response("Disconnected.")


    def send_command(self, event=None):
        hioki = self.devices.get_hioki()
        if not hioki or not hioki.is_connected:
            messagebox.showwarning("Chưa kết nối", "Vui lòng kết nối máy đo trước!")
            return

        # Xóa nội dung cũ trước
        self.txt_response.delete(1.0, tk.END) 
            
        cmd = self.ent_cmd.get().strip()
        if not cmd: return
        self.append_response(f"> {cmd}")
        self.ent_cmd.delete(0, tk.END)
        
        if "?" in cmd:
            self.append_response(f"< {hioki.query(cmd)}\n")
        else:
            hioki.send_command(cmd)

    def append_response(self, text, clear_first=True):
        # Chèn nội dung mới (thêm \n để mỗi log nằm trên 1 dòng)
        self.txt_response.insert(tk.END, text + "\n") 
        self.txt_response.see(tk.END) # Tự động cuộn xuống dòng mới nhất
    
    def on_close_clicked(self):
        selected_channels = []
        if self.var_ch1.get(): selected_channels.append("CH1")
        if self.var_ch2.get(): selected_channels.append("CH2")
        if self.var_ch3.get(): selected_channels.append("CH3")

        if not selected_channels:
            messagebox.showwarning("Cảnh báo", "Chọn ít nhất 1 kênh đo!")
            return
        
        # 1. Đọc và gom dữ liệu vào biến TRƯỚC khi cửa sổ bị hủy
        data_to_return = {
            "model": self.cb_model.get(),
            "ip": self.ent_ip.get(),
            "port": self.ent_port.get(),
            "channels": selected_channels,
            "controller": getattr(self, 'controller', None),
            "is_connected": self.is_connected
        }
                
        cb = self.callback_on_close
        self.window.grab_release()
        self.window.destroy()

        if cb:
            cb(data_to_return)

# ==========================================
# DUT CONTROL PANEL
# ==========================================
class DutControlWindow:
    def __init__(self, parent_root):
        self.window = tk.Toplevel(parent_root)
        self.window.title("DUT - Server SSH Control Panel")
        self.window.geometry("600x680")
        self.window.configure(bg="#F4F6F9")
        
        self.window.grab_set()
        self.is_connected = False
        
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Console.TLabelframe", background="#FFFFFF", bordercolor="#D1D5DB")
        style.configure("Console.TLabelframe.Label", font=("Arial", 10, "bold"), foreground="#1E3A8A", background="#FFFFFF")

    def build_ui(self):
        # ==========================================
        # 1. KHUNG CẤU HÌNH KẾT NỐI (SSH CONNECTION)
        # ==========================================
        conn_frame = ttk.LabelFrame(self.window, text="SSH Connection Settings", style="Console.TLabelframe")
        conn_frame.pack(fill="x", padx=15, pady=10, ipady=5)
        
        inner_conn = tk.Frame(conn_frame, bg="#FFFFFF")
        inner_conn.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(inner_conn, text="Server Model:", bg="#FFFFFF", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.cb_model = ttk.Combobox(inner_conn, values=["O-RAN DU Server"], width=18, state="readonly")
        self.cb_model.set("O-RAN DU Server")
        self.cb_model.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(inner_conn, text="Protocol:", bg="#FFFFFF", anchor="e").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.cb_type = ttk.Combobox(inner_conn, values=["SSH", "Telnet"], width=10, state="readonly")
        self.cb_type.set("SSH")
        self.cb_type.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        tk.Label(inner_conn, text="IP Address:", bg="#FFFFFF", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_ip = ttk.Entry(inner_conn, width=21)
        self.ent_ip.insert(0, "192.168.1.100")
        self.ent_ip.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(inner_conn, text="Port:", bg="#FFFFFF", anchor="e").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.ent_port = ttk.Entry(inner_conn, width=13)
        self.ent_port.insert(0, "22")
        self.ent_port.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        tk.Label(inner_conn, text="Username:", bg="#FFFFFF", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.ent_user = ttk.Entry(inner_conn, width=21)
        self.ent_user.insert(0, "root")
        self.ent_user.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        tk.Label(inner_conn, text="Password:", bg="#FFFFFF", anchor="e").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.ent_pass = ttk.Entry(inner_conn, width=13, show="*")
        self.ent_pass.insert(0, "admin123")
        self.ent_pass.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        self.btn_connect = tk.Button(inner_conn, text="Test Connection", font=("Arial", 9, "bold"), bg="#2563EB", fg="white", relief="flat", width=15, command=self.test_connection)
        self.btn_connect.grid(row=3, column=1, padx=5, pady=10, sticky="w")

        self.lbl_status = tk.Label(inner_conn, text="● DISCONNECTED", font=("Arial", 9, "bold"), fg="#EF4444", bg="#FFFFFF")
        self.lbl_status.grid(row=3, column=2, columnspan=2, padx=5, pady=10, sticky="w")

        # ==========================================
        # 2. KHUNG KỊCH BẢN CẤU HÌNH (PROVISIONING SCRIPT)
        # ==========================================
        script_frame = ttk.LabelFrame(self.window, text="Pre-Test Configuration Script (Bash/CLI)", style="Console.TLabelframe")
        script_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        inner_script = tk.Frame(script_frame, bg="#FFFFFF")
        inner_script.pack(fill="both", expand=True, padx=10, pady=10)

        # Toolbar trên cùng
        toolbar = tk.Frame(inner_script, bg="#FFFFFF")
        toolbar.pack(fill="x", pady=(0, 5))
        
        tk.Label(toolbar, text="Nhập lệnh thủ công hoặc tải từ file:", bg="#FFFFFF", font=("Arial", 9, "italic"), fg="#6B7280").pack(side="left")
        
        btn_load = tk.Button(toolbar, text="📂 Load Script File", font=("Arial", 9, "bold"), bg="#F3F4F6", fg="#1F2937", relief="solid", bd=1, command=self.load_script_file)
        btn_load.pack(side="right")

        # Textbox soạn thảo
        self.txt_script = tk.Text(inner_script, width=40, height=12, font=("Courier New", 10), bg="#1E1E1E", fg="#D4D4D4", relief="solid", bd=1, insertbackground="white")
        demo_script = "# Setup Profile cho DU Server\necho 'Starting DU setup for ETSI Power Test...'\nsystemctl stop lte-service\nsleep 2\nsystemctl start nr-service --profile=full_load\necho 'Setup completed.'"
        self.txt_script.insert(tk.END, demo_script)
        
        scrollbar = ttk.Scrollbar(inner_script, orient="vertical", command=self.txt_script.yview)
        self.txt_script.configure(yscrollcommand=scrollbar.set)
        
        self.txt_script.pack(side="left", fill="both", expand=True, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # --- BỘ NÚT HÀNH ĐỘNG MỚI (RUN VÀ SAVE) ---
        action_frame = tk.Frame(self.window, bg="#F4F6F9")
        action_frame.pack(fill="x", padx=15, pady=(5, 15))

        # Nút Thực thi (Màu xanh dương)
        btn_run = tk.Button(action_frame, text="▶ Run Script Now", font=("Arial", 10, "bold"), bg="#3B82F6", fg="white", relief="flat", height=2, command=self.run_script)
        btn_run.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Nút Lưu lại (Màu xanh lá)
        btn_save = tk.Button(action_frame, text="Apply & Save Config", font=("Arial", 10, "bold"), bg="#10B981", fg="white", relief="flat", height=2, command=self.save_and_close)
        btn_save.pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ==========================================
    # CÁC HÀM XỬ LÝ LOGIC
    # ==========================================
    def test_connection(self):
        ip = self.ent_ip.get()
        user = self.ent_user.get()
        if not ip or not user:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đủ IP và Username!")
            return
            
        self.is_connected = True
        self.lbl_status.config(text="● CONNECTED (Mock)", fg="#22C55E")
        self.btn_connect.config(text="Re-connect", bg="#6B7280")
        messagebox.showinfo("SSH Login", f"Đăng nhập thành công vào {user}@{ip} (Mockup).")

    def load_script_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file Kịch bản (Script)",
            filetypes=[("Bash/Shell Script", "*.sh"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.txt_script.delete(1.0, tk.END)
                self.txt_script.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Lỗi đọc file", f"Không thể đọc file.\nChi tiết: {e}")

    def run_script(self):
        """Hàm thực thi chạy nháp Script (Dry Run / Manual Execute)"""
        if not self.is_connected:
            messagebox.showerror("Lỗi kết nối", "Kiểm tra kết nối!")
            return
            
        script_content = self.txt_script.get(1.0, tk.END).strip()
        if not script_content:
            messagebox.showwarning("Trống", "Khung soạn thảo hiện không có lệnh nào để chạy.")
            return
            
        # Tương lai: Chỗ này sẽ gọi paramiko (SSH_Client) để thực thi tuần tự các lệnh
        # Tạm thời: Hiển thị thông báo Mock-up
        messagebox.showinfo("Đang thực thi", f"Đã gửi script tới thiết bị {self.ent_ip.get()}!\n\n(Test)")

    def save_and_close(self):
        saved_script = self.txt_script.get(1.0, tk.END).strip()
        if saved_script:
            messagebox.showinfo("Đã lưu cấu hình", "Đã lưu script!")
            self.window.destroy()
        else:
            messagebox.showwarning("Cảnh báo", "Bạn chưa nhập kịch bản nào!")

# ==========================================
# BATCH CONTROL PANEL
# ==========================================
class BatchConfigWindow:
    def __init__(self, parent_root, initial_config=None, callback_on_ok=None):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Batch Configuration (Multi-tests)")
        self.window.geometry("550x380")
        self.window.configure(bg="#F4F6F9")
        self.window.grab_set()
        
        self.initial_config = initial_config
        self.callback_on_ok = callback_on_ok
        
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Batch.TLabelframe", background="#FFFFFF")
        style.configure("Batch.TLabelframe.Label", font=("Arial", 10, "bold"), foreground="#1E3A8A", background="#FFFFFF")

    def build_ui(self):
        # KHUNG 1: TESTCASE SELECTION
        test_frame = ttk.LabelFrame(self.window, text="TESTCASE SELECTION", style="Batch.TLabelframe")
        test_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        inner_frame = tk.Frame(test_frame, bg="#FFFFFF")
        inner_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tiêu đề cột
        tk.Label(inner_frame, text="Select", bg="#FFFFFF", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(inner_frame, text="Test Profile", bg="#FFFFFF", font=("Arial", 9, "bold"), anchor="w").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Label(inner_frame, text="Duration (s)", bg="#FFFFFF", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(inner_frame, text="ETSI Guideline", bg="#FFFFFF", font=("Arial", 9, "bold")).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # KNạp cấu hình
        if self.initial_config:
            self.tests = self.initial_config
        
        else:
            self.tests = [
                {"name": "Full Load", "default_time": "3600", "guide": "> 1 hr"},
                {"name": "Load 70%", "default_time": "3600", "guide": ""},
                {"name": "Busy Hour Load", "default_time": "28800", "guide": "8 hrs"},
                {"name": "Medium Load", "default_time": "36000", "guide": "10 hrs"},
                {"name": "Low Load", "default_time": "21600", "guide": "6 hrs"}
            ]
        
        self.vars_check = []
        self.entries_time = []
        self.labels_name = []
        self.labels_guide = []

        # Render các dòng
        for i, test in enumerate(self.tests, start=1):
            var_chk = tk.BooleanVar(value=test.get("checked", True))
            self.vars_check.append(var_chk)
            
            # Checkbox gọi hàm toggle khi click
            chk = tk.Checkbutton(inner_frame, variable=var_chk, bg="#FFFFFF", command=lambda idx=i-1: self.toggle_row_state(idx))
            chk.grid(row=i, column=0, padx=5, pady=5)
            
            lbl_name = tk.Label(inner_frame, text=test["name"], bg="#FFFFFF")
            lbl_name.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            self.labels_name.append(lbl_name)  # <--- ĐẢM BẢO CÓ DÒNG NÀY
            
            ent_time = ttk.Entry(inner_frame, width=10, justify="center")
            duration_value = test.get("duration", test.get("default_time", "3600"))
            ent_time.insert(0, duration_value)
            ent_time.grid(row=i, column=2, padx=5, pady=5)
            self.entries_time.append(ent_time) # <--- ĐẢM BẢO CÓ DÒNG NÀY
            
            lbl_guide = tk.Label(inner_frame, text=f"({test.get('guide', '')})", bg="#FFFFFF", font=("Arial", 9, "italic"))
            lbl_guide.grid(row=i, column=3, padx=5, pady=5, sticky="w")
            self.labels_guide.append(lbl_guide) # <--- ĐÂY LÀ DÒNG BẠN ĐANG BỊ THIẾU
            
            # Cập nhật màu sắc/trạng thái ngay từ lúc mở form
            self.toggle_row_state(i-1)

        # NÚT HÀNH ĐỘNG
        btn_frame = tk.Frame(self.window, bg="#F4F6F9")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        btn_close = tk.Button(btn_frame, text="Close", font=("Arial", 9), bg="#9CA3AF", fg="white", relief="flat", width=10, command=self.window.destroy)
        btn_close.pack(side="right", padx=5)
        
        btn_ok = tk.Button(btn_frame, text="OK", font=("Arial", 9, "bold"), bg="#10B981", fg="white", relief="flat", width=10, command=self.on_ok_clicked)
        btn_ok.pack(side="right", padx=5)
    
    def toggle_row_state(self, index):
        """Làm mờ chữ và khóa ô nhập liệu nếu bị bỏ check"""
        is_checked = self.vars_check[index].get()
        if is_checked:
            self.labels_name[index].config(fg="#000000")       # Chữ đen
            self.labels_guide[index].config(fg="#6B7280")      # Chữ xám đậm
            self.entries_time[index].config(state="normal")    # Mở khóa ô text
        else:
            self.labels_name[index].config(fg="#D1D5DB")       # Chữ xám nhạt (mờ)
            self.labels_guide[index].config(fg="#D1D5DB")      # Chữ xám nhạt
            self.entries_time[index].config(state="disabled")  # Khóa ô text

    def on_ok_clicked(self):
        full_config = []
        has_checked = False
        
        for i, test in enumerate(self.tests):
            checked = self.vars_check[i].get()
            if checked: has_checked = True
            
            full_config.append({
                "name": test["name"],
                "duration": self.entries_time[i].get(),
                "guide": test.get("guide", ""),
                "checked": checked
            })
        
        if not has_checked:
            messagebox.showwarning("Cảnh báo", "Bạn phải chọn ít nhất 1 bài đo!")
            return
            
        if self.callback_on_ok:
            self.callback_on_ok(full_config)
        self.window.destroy()

# ==========================================
# CALCULATION RESULTS WINDOW
# ==========================================
class CalculationWindow:
    def __init__(self, parent_root):
        self.window = tk.Toplevel(parent_root)
        self.window.title("ETSI ES 202 706-1 | Calculation Results")
        self.window.geometry("650x600") # Tăng nhẹ chiều cao để chứa công thức
        self.window.configure(bg="#F4F6F9")
        self.window.grab_set()
        
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Calc.TLabelframe", background="#FFFFFF", bordercolor="#D1D5DB")
        style.configure("Calc.TLabelframe.Label", font=("Arial", 10, "bold"), foreground="#1E3A8A", background="#FFFFFF")

    def build_ui(self):
        # 1. LỰA CHỌN MÔ HÌNH TRẠM GỐC (BS MODEL)
        model_frame = ttk.LabelFrame(self.window, text="1. BS Model Selection", style="Calc.TLabelframe")
        model_frame.pack(fill="x", padx=15, pady=10, ipady=5)
        
        inner_model = tk.Frame(model_frame, bg="#FFFFFF")
        inner_model.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.var_bs_model = tk.StringVar(value="Integrated")
        tk.Radiobutton(inner_model, text="Integrated BS", variable=self.var_bs_model, value="Integrated", bg="#FFFFFF", command=self.toggle_inputs).pack(side="left", padx=20)
        tk.Radiobutton(inner_model, text="Distributed BS", variable=self.var_bs_model, value="Distributed", bg="#FFFFFF", command=self.toggle_inputs).pack(side="left", padx=20)

        # 2. KHUNG NHẬP GIÁ TRỊ (CHAPTER 7.2.1 - 7.3.3)
        input_frame = ttk.LabelFrame(self.window, text="2. Input Measured Power (Watts)", style="Calc.TLabelframe")
        input_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.inner_input = tk.Frame(input_frame, bg="#FFFFFF")
        self.inner_input.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Khởi tạo các khung nhập liệu ẩn/hiện
        self.create_integrated_inputs()
        self.create_distributed_inputs()
        

        # 3. KẾT QUẢ TÍNH TOÁN CÓ KÈM CÔNG THỨC
        res_frame = ttk.LabelFrame(self.window, text="3. Calculation Results (ETSI Chapter 7)", style="Calc.TLabelframe")
        res_frame.pack(fill="x", padx=15, pady=10, ipady=5)
        
        inner_res = tk.Frame(res_frame, bg="#FFFFFF")
        inner_res.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- Phần tính Công suất Trung bình ---
        # Label hiển thị công thức P_avg (Sẽ thay đổi động theo mô hình BS)
        self.lbl_formula_avg = tk.Label(inner_res, text="Formula:", bg="#FFFFFF", fg="#6B7280", font=("Arial", 9, "italic"))
        self.lbl_formula_avg.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="w")

        tk.Label(inner_res, text="Average Power Consumption (W):", bg="#FFFFFF", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=(0, 5), sticky="e")
        self.lbl_avg_power = tk.Label(inner_res, text="0.00", font=("Arial", 12, "bold"), fg="#2563EB", bg="#FFFFFF")
        self.lbl_avg_power.grid(row=1, column=1, padx=10, pady=(0, 5), sticky="w")
        
        # --- Phần tính Điện năng Tiêu thụ hàng ngày ---
        # Label hiển thị công thức E_daily (Cố định)
        tk.Label(inner_res, text="Formula (7.2.2 / 7.3.2): E_daily = (P_avg × 24) / 1000", bg="#FFFFFF", fg="#6B7280", font=("Arial", 9, "italic")).grid(row=2, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")

        tk.Label(inner_res, text="Daily Energy Consumption (kWh):", bg="#FFFFFF", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=10, pady=(0, 5), sticky="e")
        self.lbl_daily_energy = tk.Label(inner_res, text="0.00", font=("Arial", 12, "bold"), fg="#10B981", bg="#FFFFFF")
        self.lbl_daily_energy.grid(row=3, column=1, padx=10, pady=(0, 5), sticky="w")
        
        # Gọi toggle_inputs ở đây để khởi tạo đúng công thức ngay từ đầu
        self.toggle_inputs()

        # Nút tính toán
        btn_calc = tk.Button(self.window, text="Calculate", font=("Arial", 10, "bold"), bg="#3B82F6", fg="white", relief="flat", height=2, command=self.perform_calculation)
        btn_calc.pack(fill="x", padx=15, pady=(0, 15))

    def create_integrated_inputs(self):
        self.frame_int = tk.Frame(self.inner_input, bg="#FFFFFF")
        
        # Hàng 1: P_bh
        tk.Label(self.frame_int, text="P_bh (Busy Hour):", bg="#FFFFFF").grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.ent_int_bh = ttk.Entry(self.frame_int, width=20)
        self.ent_int_bh.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # Hàng 2: P_med
        tk.Label(self.frame_int, text="P_med (Medium):", bg="#FFFFFF").grid(row=1, column=0, padx=5, pady=10, sticky="e")
        self.ent_int_med = ttk.Entry(self.frame_int, width=20)
        self.ent_int_med.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        
        # Hàng 3: P_low
        tk.Label(self.frame_int, text="P_low (Low Load):", bg="#FFFFFF").grid(row=2, column=0, padx=5, pady=10, sticky="e")
        self.ent_int_low = ttk.Entry(self.frame_int, width=20)
        self.ent_int_low.grid(row=2, column=1, padx=5, pady=10, sticky="w")

    def create_distributed_inputs(self):
        self.frame_dist = tk.Frame(self.inner_input, bg="#FFFFFF")
        
        # Central Part
        tk.Label(self.frame_dist, text="Central Part (BBU)", font=("Arial", 9, "bold"), bg="#FFFFFF").grid(row=0, column=0, columnspan=2, pady=(0,5))
        tk.Label(self.frame_dist, text="P_central_bh:", bg="#FFFFFF").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_c_bh = ttk.Entry(self.frame_dist, width=12)
        self.ent_c_bh.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(self.frame_dist, text="P_central_med:", bg="#FFFFFF").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.ent_c_med = ttk.Entry(self.frame_dist, width=12)
        self.ent_c_med.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(self.frame_dist, text="P_central_low:", bg="#FFFFFF").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.ent_c_low = ttk.Entry(self.frame_dist, width=12)
        self.ent_c_low.grid(row=3, column=1, padx=5, pady=5)
        
        # Remote Part
        tk.Label(self.frame_dist, text="Remote Part (RRU/Active Antenna)", font=("Arial", 9, "bold"), bg="#FFFFFF").grid(row=0, column=2, columnspan=2, pady=(0,5), padx=(20,0))
        tk.Label(self.frame_dist, text="P_remote_bh:", bg="#FFFFFF").grid(row=1, column=2, padx=(20,5), pady=5, sticky="e")
        self.ent_r_bh = ttk.Entry(self.frame_dist, width=12)
        self.ent_r_bh.grid(row=1, column=3, padx=5, pady=5)
        
        tk.Label(self.frame_dist, text="P_remote_med:", bg="#FFFFFF").grid(row=2, column=2, padx=(20,5), pady=5, sticky="e")
        self.ent_r_med = ttk.Entry(self.frame_dist, width=12)
        self.ent_r_med.grid(row=2, column=3, padx=5, pady=5)
        
        tk.Label(self.frame_dist, text="P_remote_low:", bg="#FFFFFF").grid(row=3, column=2, padx=(20,5), pady=5, sticky="e")
        self.ent_r_low = ttk.Entry(self.frame_dist, width=12)
        self.ent_r_low.grid(row=3, column=3, padx=5, pady=5)
        
        # Quantity
        tk.Label(self.frame_dist, text="Number of Remote Parts:", bg="#FFFFFF").grid(row=4, column=2, padx=(20,5), pady=15, sticky="e")
        self.ent_r_qty = ttk.Entry(self.frame_dist, width=12)
        self.ent_r_qty.insert(0, "1")
        self.ent_r_qty.grid(row=4, column=3, padx=5, pady=15)

    def toggle_inputs(self):
        """Hàm ẩn/hiện form nhập liệu và CẬP NHẬT CÔNG THỨC tương ứng"""
        if self.var_bs_model.get() == "Integrated":
            self.frame_dist.pack_forget()
            self.frame_int.pack(fill="both", expand=True)
            # Cập nhật công thức Integrated
            self.lbl_formula_avg.config(text="Formula (7.2.1): P_avg = (P_bh × 8 + P_med × 10 + P_low × 6) / 24")
        else:
            self.frame_int.pack_forget()
            self.frame_dist.pack(fill="both", expand=True)
            # Cập nhật công thức Distributed
            self.lbl_formula_avg.config(text="Formula (7.3.1): P_avg = P_central_avg + (P_remote_avg × Qty)")

    def perform_calculation(self):
        try:
            p_avg = 0.0
            if self.var_bs_model.get() == "Integrated":
                p_bh = float(self.ent_int_bh.get() or 0)
                p_med = float(self.ent_int_med.get() or 0)
                p_low = float(self.ent_int_low.get() or 0)
                
                # Formula 7.2.1
                p_avg = (p_bh * 8 + p_med * 10 + p_low * 6) / 24
            else:
                # Central
                p_c_bh = float(self.ent_c_bh.get() or 0)
                p_c_med = float(self.ent_c_med.get() or 0)
                p_c_low = float(self.ent_c_low.get() or 0)
                p_c_avg = (p_c_bh * 8 + p_c_med * 10 + p_c_low * 6) / 24
                
                # Remote
                p_r_bh = float(self.ent_r_bh.get() or 0)
                p_r_med = float(self.ent_r_med.get() or 0)
                p_r_low = float(self.ent_r_low.get() or 0)
                p_r_avg = (p_r_bh * 8 + p_r_med * 10 + p_r_low * 6) / 24
                
                qty = int(self.ent_r_qty.get() or 1)
                
                # Formula 7.3.1
                p_avg = p_c_avg + (p_r_avg * qty)
            
            # Formula 7.2.2 / 7.3.2
            daily_energy = (p_avg * 24) / 1000  # kWh
            
            self.lbl_avg_power.config(text=f"{p_avg:.2f}")
            self.lbl_daily_energy.config(text=f"{daily_energy:.2f}")
            
        except ValueError:
            messagebox.showerror("Lỗi dữ liệu", "Vui lòng nhập các giá trị Công suất (W) dưới dạng số hợp lệ!")