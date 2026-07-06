# File: tests/test_connection.py
import unittest
from unittest.mock import patch, MagicMock
import socket

# Import class cần test từ core
from core.hioki_controller import HiokiPW3336Controller

class TestHiokiConnection(unittest.TestCase):
    def setUp(self):
        # Thiết lập thông số mặc định trước mỗi bài test
        self.ip = "192.168.1.10"
        self.port = 3390
        self.controller = HiokiPW3336Controller(self.ip, self.port, timeout=1.0)

    @patch('core.hioki_controller.socket.socket')
    def test_connect_success(self, mock_socket_class):
        """Test trường hợp kết nối thành công tới máy đo"""
        # Tạo một Mock Socket (Giả lập card mạng)
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value = mock_sock_instance
        
        # Giả lập thiết bị trả về chuỗi IDN khi phần mềm gọi lệnh *IDN?
        mock_sock_instance.recv.return_value = b'HIOKI,PW3336,123456789,V1.00\r\n'

        success, msg = self.controller.connect()

        self.assertTrue(success)
        self.assertTrue(self.controller.is_connected)
        self.assertIn("HIOKI", msg)
        
        # Đảm bảo phần mềm thực sự gọi hàm connect tới đúng IP và Port
        mock_sock_instance.connect.assert_called_with((self.ip, self.port))

    @patch('core.hioki_controller.socket.socket')
    def test_connect_timeout(self, mock_socket_class):
        """Test trường hợp IP bị sai hoặc cáp mạng chưa cắm (Timeout)"""
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value = mock_sock_instance
        
        # Ép hàm connect tung ra lỗi Timeout
        mock_sock_instance.connect.side_effect = socket.timeout

        success, msg = self.controller.connect()

        self.assertFalse(success)
        self.assertFalse(self.controller.is_connected)
        self.assertIn("Timeout", msg)

    @patch('core.hioki_controller.socket.socket')
    def test_disconnect(self, mock_socket_class):
        """Test tính năng ngắt kết nối an toàn"""
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value = mock_sock_instance
        
        # Ép cho trạng thái đang kết nối
        self.controller.sock = mock_sock_instance
        self.controller.is_connected = True
        
        self.controller.disconnect()
        
        mock_sock_instance.close.assert_called_once()
        self.assertFalse(self.controller.is_connected)
        self.assertIsNone(self.controller.sock)

if __name__ == '__main__':
    unittest.main()