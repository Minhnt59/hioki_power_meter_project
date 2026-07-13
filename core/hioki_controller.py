import socket
import time
import re

class HiokiPW3336Controller:
    def __init__(self, ip, port=3300, timeout=5.0):
        self.ip = ip
        self.port = int(port)
        self.timeout = timeout
        self.sock = None
        self.is_connected = False
        self.num_meas_channels = 1  # Số kênh đo của máy Hioki PW3336
        self.current_channel = 1  # Mặc định là kênh 1

    def connect(self):
        """Mở kết nối TCP/IP tới máy đo và xác thực IDN"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.ip, self.port))
            
            self.is_connected = True

            self.send_command("*CLS")
            idn = self.query("*IDN?")
            print(f"IDN response: {idn}")
            if "HIOKI" in idn:
                return True, f"Connected to {idn}"
            else:
                # Nếu không phải Hioki, đóng socket và set lại cờ False
                self.disconnect() 
                return False, f"Thiết bị phản hồi nhưng không phải HIOKI. (Response: {idn})"
            
        except Exception as e:
            self.is_connected = False
            return False, f"Lỗi kết nối: {e}"

    def disconnect(self):
        """Đóng kết nối an toàn"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.is_connected = False

    def send_command(self, cmd):
        """Gửi lệnh SCPI (Có kèm ký tự ngắt dòng chuẩn CRLF)"""
        if not self.is_connected: return False
        try:
            self.sock.sendall((cmd + "\r\n").encode('ascii'))
            print(f"[PW3336]: ➡️ {cmd}")
            return True
        except:
            self.is_connected = False
            return False

    def query(self, cmd):
        """Gửi lệnh và chờ đọc kết quả trả về"""
        if not self.send_command(cmd): return ""

        time.sleep(1)
        try:
            response = self.sock.recv(4096).decode('ascii').strip()
            print(f"[PW3336]: ⬅️ {cmd}")
            return response
        except:
            return ""

    def setup_measure_items(self, channels_list):
        self.send_command("*CLS")
        self.active_channels = channels_list # Lưu lại mảng để lát nữa đọc dữ liệu

        self.send_command(":MEAS:ITEM:ALLC")     # Xóa toàn bộ các thiết lập output hiện tại
        self.send_command(":HEAD 1")     # Header ON lên
        # Cấu hình output U,I,P, PTAV cho các kênh đo được chọn
        for ch in channels_list:
            self.send_command(f":MEAS:ITEM:U:{ch} 1")
            self.send_command(f":MEAS:ITEM:I:{ch} 1")
            self.send_command(f":MEAS:ITEM:P:{ch} 1")
            self.send_command(f":MEAS:ITEM:PTAV:{ch} 1")

        # items = []
        # for ch in channels_list:
        #     ch_idx = ch.replace("CH", "") if ch != "SUM" else "sum"
        #     items.append(f"U{ch_idx},I{ch_idx},P{ch_idx},WP{ch_idx}")
            
        # cmd = ":DATAout:ITEM " + ",".join(items)
        # self.send_command(cmd)
        # print(f"Đã cấu hình HIOKI đo đồng thời: {channels_list}")

    def read_measurements(self):
        """Đọc và bóc tách dữ liệu thành Dictionary theo từng kênh"""
        raw_data = self.query(":MEAS?")
        if not raw_data: return None
        
        try:
            # 1. XỬ LÝ LỖI DÍNH CHUỖI (\r\n)
            # Nếu buffer nhận về nhiều dòng dính nhau, ta tách ra và chỉ lấy dòng cuối cùng (dữ liệu mới nhất)
            lines = raw_data.strip().split('\n')
            latest_data = lines[-1].strip()
            
            # 2. XỬ LÝ LỖI HEADER (VD: 'U1 +048.02E+0;I1 +02.390E+0')
            # Đổi hết dấu ';' thành ',' để chuẩn hóa việc tách chuỗi
            parts = latest_data.replace(';', ',').split(',')
            
            floats = []
            for p in parts:
                p = p.strip()
                if not p: continue
                
                # Nếu chuỗi có chứa chữ (VD: 'U1 +048.02E+0'), cắt bằng dấu cách và lấy phần tử cuối cùng
                val_str = p.split(' ')[-1]
                
                # Ép kiểu thành số thực (float)
                floats.append(float(val_str))
                
            # 3. ĐÓNG GÓI VÀO DICTIONARY THEO KÊNH
            result = {}
            idx = 0
            for ch in self.active_channels:
                if idx + 3 < len(floats):
                    result[ch] = {
                        'U': floats[idx],
                        'I': floats[idx+1],
                        'P': floats[idx+2],
                        'PTAV': floats[idx+3] if len(floats) > idx+3 else floats[idx+2]
                    }
                idx += 4
                
            return result
            
        except Exception as e:
            print(f"Lỗi phân tích dữ liệu SCPI: {e} | Chuỗi gốc: {raw_data}")
            return None
        
    def start_integration(self):
        self.stop_integration()
        self.send_command(":INTEG:RES")  # Reset
        time.sleep(1)
        self.send_command(":INTEG:STAT START") # Enable integration
        time.sleep(1)
        
    def stop_integration(self):
        """Dừng bộ đếm tích phân"""
        self.send_command(":INTEG:STAT STOP")
        