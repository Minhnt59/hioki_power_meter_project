import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import os

# Nếu bạn để file này ở gui/control_panels.py, hãy import controller vào:
# from core.hioki_controller import HiokiPW3336Controller

class RemoteConsoleWindow:
    def __init__(self, parent_root, current_ip="192.168.1.10", current_port="3390", callback_on_close=None):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Power Meter - Remote Control Console")
        self.window.geometry("500x600")
        self.window.configure(bg="#F4F6F9")
        
        # Khóa tương tác với cửa sổ chính khi Popup này đang mở (Modal window)
        self.window.grab_set() 
        
        self.controller = None
        self.is_connected = False
        
        self.current_ip = current_ip
        self.current_port = current_port
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
        # 2. MEASUREMENT CHANNEL SELECTION
        # ==========================================
        ch_frame = ttk.LabelFrame(self.window, text="Measurement Channel", style="Console.TLabelframe")
        ch_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        inner_ch = tk.Frame(ch_frame, bg="#FFFFFF")
        inner_ch.pack(fill="both", expand=True, padx=10, pady=10)

        # Row 1: Channel selection
        tk.Label(inner_ch, text="Meas. Channel:", bg="#FFFFFF").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.cb_channel = ttk.Combobox(inner_ch, values=["CH1", "CH2", "CH3", "SUM"], width=10, state="readonly")
        self.cb_channel.set("CH1")
        self.cb_channel.grid(row=0, column=1, padx=5, pady=5, sticky="w")

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
        if not self.is_connected:
            # Thực hiện kết nối
            ip = self.ent_ip.get()
            port = int(self.ent_port.get())
            
            # Khởi tạo class điều khiển (Nếu chưa import file thì dùng socket trực tiếp tạm thời)
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(2.0)
                self.sock.connect((ip, port))
                
                self.is_connected = True
                self.lbl_status.config(text="● CONNECTED", fg="#22C55E")
                self.btn_connect.config(text="Disconnect", bg="#EF4444")
                self.btn_send.config(state="normal")
                
                self.append_response("[System] Connection established.\n")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Cannot connect to {ip}:{port}\nError: {e}")
        else:
            # Thực hiện ngắt kết nối
            try:
                self.sock.close()
            except:
                pass
            self.is_connected = False
            self.lbl_status.config(text="● DISCONNECTED", fg="#EF4444")
            self.btn_connect.config(text="Connect", bg="#2563EB")
            self.btn_send.config(state="disabled")
            self.append_response("[System] Connection closed.\n")

    def send_command(self):
        if not self.is_connected:
            return
            
        raw_cmd = self.ent_cmd.get().strip()
        if not raw_cmd:
            return
            
        # Thêm ký tự ngắt dòng CRLF chuẩn của HIOKI SCPI
        cmd_to_send = raw_cmd + "\r\n"
        
        try:
            self.sock.sendall(cmd_to_send.encode('ascii'))
            self.append_response(f"> {raw_cmd}\n")
            
            # Nếu lệnh chứa dấu hỏi (?), đây là lệnh truy vấn cần chờ đọc phản hồi
            if "?" in raw_cmd:
                response = self.sock.recv(4096).decode('ascii').strip()
                self.append_response(f"< {response}\n")
                
        except socket.timeout:
            self.append_response("< [Error] Timeout waiting for response.\n")
        except Exception as e:
            self.append_response(f"< [Error] Communication failed: {e}\n")
            self.toggle_connection() # Ngắt kết nối nếu lỗi mạng

    def append_response(self, text):
        """Hàm hỗ trợ ghi log vào khung Response"""
        self.txt_response.insert(tk.END, text)
        self.txt_response.see(tk.END) # Tự động cuộn xuống dòng mới nhất
    
    def on_close_clicked(self):
        """Hàm xử lý khi bấm nút Close hoặc bấm X đỏ"""
        # Nếu đã truyền hàm callback từ cửa sổ chính sang
        if self.callback_on_close:
            # Gói các dữ liệu cần truyền về vào 1 dictionary
            data_to_return = {
                "model": self.cb_model.get(),
                "ip": self.ent_ip.get(),
                "port": self.ent_port.get(),
                "channel": self.cb_channel.get()
            }
            # Gọi hàm callback, ném data về cho cửa sổ chính
            self.callback_on_close(data_to_return)
        
        # Đóng kết nối socket nếu đang mở
        if self.is_connected:
            try:
                self.sock.close()
            except:
                pass
                
        # Phá hủy cửa sổ con
        self.window.destroy()

# ==========================================
# DUT CONTROL PANEL
# ==========================================
class DutControlWindow:
    def __init__(self, parent_root):
        self.window = tk.Toplevel(parent_root)
        self.window.title("DUT - Server SSH Control Panel")
        self.window.geometry("600x680") # Tăng nhẹ chiều cao để chứa nút mới
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
        self.cb_model = ttk.Combobox(inner_conn, values=["O-RAN DU Server", "Generic Linux Server"], width=18, state="readonly")
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