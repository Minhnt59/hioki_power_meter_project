from core.hioki_controller import HiokiPW3336Controller
# Sau này bạn có thể import thêm: from core.ssh_controller import DUServerController

class DeviceManager:

    # Singleton Pattern
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)
            # Nơi lưu trữ tất cả các thiết bị kết nối của hệ thống
            cls._instance.hioki = None
            cls._instance.du_server = None # Chuẩn bị sẵn cho tương lai
        return cls._instance

    # ==========================================
    # QUẢN LÝ THIẾT BỊ HIOKI
    # ==========================================
    def connect_hioki(self, ip, port):
        """Mở kết nối tới Hioki. Nếu đang có kết nối cũ thì tự động ngắt."""
        if self.is_hioki_connected():
            self.hioki.disconnect()
            
        self.hioki = HiokiPW3336Controller(ip, int(port))
        success, msg = self.hioki.connect()
        return success, msg

    def disconnect_hioki(self):
        if self.hioki:
            self.hioki.disconnect()

    def get_hioki(self):
        return self.hioki

    def is_hioki_connected(self):
        return self.hioki is not None and self.hioki.is_connected

    # ==========================================
    # QUẢN LÝ THIẾT BỊ DU SERVER (Ví dụ mở rộng)
    # ==========================================
    # def connect_du_server(self, ip, user, pwd):
    #     self.du_server = DUServerController(ip, user, pwd)
    #     ...