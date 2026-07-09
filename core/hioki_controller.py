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
            
            idn = self.query("*IDN?")
            print(f"IDN response: {idn}")
            if "HIOKI" in idn:
                self.is_connected = True
                return True, f"Connected to {idn}"
            else:
                return False, "Thiết bị phản hồi nhưng không phải HIOKI."
        except Exception as e:
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
            return response
        except:
            return ""

    def setup_measure_items(self):
        """Cấu hình HIOKI chỉ trả về đúng U, I, P và WP của Kênh 1 (CH1)"""
        # Xóa các thiết lập cũ
        self.send_command("*CLS")
        # Yêu cầu xuất: Điện áp (U1), Dòng (I1), Công suất (P1), Điện năng (WP1)
        self.send_command(":DATA:ITEM U1,I1,P1,WP1")
        
    def start_integration(self):
        """Khởi động bộ đếm tích phân (Integration) trên phần cứng"""
        self.send_command(":INTEG:RES")
        self.send_command(":INTEG:STAT START")
        
    def stop_integration(self):
        """Dừng bộ đếm tích phân"""
        self.send_command(":INTEG:STAT STOP")
        
    def read_measurements(self):
        """Gửi lệnh :MEASure? để lấy mảng dữ liệu thực"""
        raw_data = self.query(":MEAS?")
        if not raw_data: return None
        
        try:
            # Máy đo trả về chuỗi CSV (VD: "48.05, 10.12, 485.7, 1.25")
            parts = raw_data.split(',')
            if len(parts) >= 3:
                return {
                    'U': float(parts[0]),
                    'I': float(parts[1]),
                    'P': float(parts[2]),
                    'WP': float(parts[3]) if len(parts) >= 4 else 0.0
                }
        except Exception as e:
            print(f"Lỗi phân tích dữ liệu SCPI: {e}")
        return None