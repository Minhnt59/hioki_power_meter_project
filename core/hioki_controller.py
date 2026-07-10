import socket
import time

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
        """Cấu hình HIOKI trả về dữ liệu của TẤT CẢ các kênh được truyền vào (dạng mảng)"""
        self.send_command("*CLS")
        self.active_channels = channels_list # Lưu lại mảng để lát nữa đọc dữ liệu
        
        items = []
        for ch in channels_list:
            ch_idx = ch.replace("CH", "") if ch != "SUM" else "sum"
            items.append(f"U{ch_idx},I{ch_idx},P{ch_idx},WP{ch_idx}")
            
        cmd = ":DATAout:ITEM " + ",".join(items)
        self.send_command(cmd)
        print(f"Đã cấu hình HIOKI đo đồng thời: {channels_list}")

    def read_measurements(self):
        """Đọc và bóc tách dữ liệu thành Dictionary theo từng kênh"""
        raw_data = self.query(":MEAS?")
        if not raw_data: return None
        
        try:
            parts = raw_data.split(',')
            result = {}
            idx = 0
            
            for ch in self.active_channels:
                if idx + 3 < len(parts):
                    result[ch] = {
                        'U': float(parts[idx]),
                        'I': float(parts[idx+1]),
                        'P': float(parts[idx+2]),
                        'WP': float(parts[idx+3]) if len(parts) > idx+3 else 0.0
                    }
                idx += 4 # Nhảy 4 giá trị để sang kênh tiếp theo
            return result
        except Exception as e:
            print(f"Lỗi phân tích dữ liệu SCPI: {e}")
            return None
        
    def start_integration(self):
        """Khởi động bộ đếm tích phân (Integration) trên phần cứng"""
        self.send_command(":INTEG:RES")
        self.send_command(":INTEG:STAT START")
        
    def stop_integration(self):
        """Dừng bộ đếm tích phân"""
        self.send_command(":INTEG:STAT STOP")
        
    # def read_measurements(self):
    #     """Gửi lệnh :MEASure? để lấy mảng dữ liệu thực"""
    #     raw_data = self.query(":MEAS?")
    #     if not raw_data: return None
        
    #     try:
    #         # Máy đo trả về chuỗi CSV (VD: "48.05, 10.12, 485.7, 1.25")
    #         parts = raw_data.split(',')
    #         if len(parts) >= 3:
    #             return {
    #                 'U': float(parts[0]),
    #                 'I': float(parts[1]),
    #                 'P': float(parts[2]),
    #                 'WP': float(parts[3]) if len(parts) >= 4 else 0.0
    #             }
    #     except Exception as e:
    #         print(f"Lỗi phân tích dữ liệu SCPI: {e}")
    #     return None