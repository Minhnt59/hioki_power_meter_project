import socket
import time

class HiokiPW3336Controller:
    """
    Class điều khiển máy đo công suất HIOKI PW3336 qua mạng LAN (Raw Socket)
    """
    def __init__(self, ip_address, port=3390, timeout=3.0):
        self.ip = ip_address
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.is_connected = False

    def connect(self):
        """Khởi tạo kết nối Socket tới máy đo"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.ip, self.port))
            self.is_connected = True
            
            # Xóa bộ đệm lỗi và kiểm tra kết nối bằng lệnh nhận diện
            self.send_command("*CLS") 
            idn = self.query("*IDN?")
            return True, f"Đã kết nối thành công: {idn}"
        except socket.timeout:
            self.is_connected = False
            return False, "Lỗi: Timeout khi kết nối. Vui lòng kiểm tra lại IP/Port."
        except Exception as e:
            self.is_connected = False
            return False, f"Lỗi kết nối: {str(e)}"

    def disconnect(self):
        """Đóng kết nối"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
        self.is_connected = False

    def send_command(self, cmd):
        """Gửi lệnh thiết lập (Không chờ phản hồi)"""
        if not self.is_connected:
            return False
        try:
            # Máy đo Hioki yêu cầu kết thúc chuỗi lệnh bằng CRLF (\r\n)
            self.sock.sendall((cmd + "\r\n").encode('ascii'))
            return True
        except Exception as e:
            print(f"Lỗi gửi lệnh: {e}")
            self.is_connected = False
            return False

    def query(self, cmd, buffer_size=4096):
        """Gửi lệnh truy vấn và đọc dữ liệu trả về"""
        if not self.send_command(cmd):
            return None
        try:
            response = self.sock.recv(buffer_size).decode('ascii').strip()
            return response
        except socket.timeout:
            print("Lỗi: Timeout khi chờ dữ liệu trả về.")
            return None
        except Exception as e:
            print(f"Lỗi nhận dữ liệu: {e}")
            self.is_connected = False
            return None

    # ==========================================
    # CÁC HÀM ĐIỀU KHIỂN CHỨC NĂNG CỤ THỂ (SCPI)
    # ==========================================

    def setup_measure_items(self):
        """
        Cấu hình các tham số cần đọc (Điện áp, Dòng điện, Công suất Tác dụng).
        Với ETSI 202 706-1 của RRU thường đo nguồn DC.
        """
        # Đặt cấu hình đầu ra của lệnh :MEAS? chỉ trả về U, I, P
        cmd = ":MEASURE:ITEM U,I,P"
        return self.send_command(cmd)

    def read_measurements(self):
        """
        Đọc giá trị đo tức thời
        Trả về dictionary: {'U': float, 'I': float, 'P': float}
        """
        response = self.query(":MEASURE?")
        if response:
            try:
                # Dữ liệu Hioki trả về dạng CSV: "48.05,14.20,682.31"
                data = response.split(",")
                if len(data) >= 3:
                    return {
                        'U': float(data[0]),
                        'I': float(data[1]),
                        'P': float(data[2])
                    }
            except ValueError:
                print(f"Lỗi parse dữ liệu từ chuỗi: {response}")
        return None

    def start_integration(self):
        """Bắt đầu tính toán tích phân (Dùng cho đo Công suất trung bình / Điện năng)"""
        self.send_command(":INTEGRATE:RESET") # Reset bộ đếm trước khi đo
        time.sleep(0.5)
        return self.send_command(":INTEGRATE:STATE START")

    def stop_integration(self):
        """Dừng tính toán tích phân"""
        return self.send_command(":INTEGRATE:STATE STOP")

    def read_integration(self):
        """
        Đọc thời gian đã chạy và Công suất trung bình/Điện năng tích lũy.
        (Cần cấu hình ITEM chứa TIME và WP/W trước đó).
        """
        # Tạm thời truy vấn điện năng tác dụng (WP) và thời gian (TIME)
        # Tùy thuộc vào lệnh SCPI cụ thể của PW3336
        pass