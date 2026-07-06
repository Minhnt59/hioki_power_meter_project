# File: tests/test_scpi_commands.py
import unittest
from unittest.mock import patch

from core.hioki_controller import HiokiPW3336Controller

class TestSCPICommands(unittest.TestCase):
    def setUp(self):
        self.controller = HiokiPW3336Controller("localhost")
        # Giả vờ như đã kết nối thành công để bỏ qua check socket
        self.controller.is_connected = True 

    @patch.object(HiokiPW3336Controller, 'query')
    def test_read_measurements_valid_data(self, mock_query):
        """Test đọc dữ liệu chuẩn (U, I, P) từ máy đo"""
        # Giả lập máy đo trả về chuỗi: 48.05V, 14.20A, 682.31W
        mock_query.return_value = "48.05,14.20,682.31"
        
        data = self.controller.read_measurements()
        
        self.assertIsNotNone(data)
        self.assertEqual(data['U'], 48.05)
        self.assertEqual(data['I'], 14.20)
        self.assertEqual(data['P'], 682.31)
        
        # Đảm bảo phần mềm đã gửi đúng lệnh truy vấn ":MEASURE?"
        mock_query.assert_called_with(":MEASURE?")

    @patch.object(HiokiPW3336Controller, 'query')
    def test_read_measurements_invalid_format(self, mock_query):
        """Test phần mềm không bị Crash khi máy đo trả về rác hoặc thiếu số"""
        # Trả về chuỗi không phải số
        mock_query.return_value = "ERROR,NO_DATA"
        data = self.controller.read_measurements()
        self.assertIsNone(data)

        # Trả về chuỗi thiếu tham số (chỉ có U và I, không có P)
        mock_query.return_value = "48.05,14.20"
        data2 = self.controller.read_measurements()
        self.assertIsNone(data2)

    @patch.object(HiokiPW3336Controller, 'send_command')
    def test_start_integration(self, mock_send):
        """Test gửi lệnh bắt đầu bài đo ETSI (Tích phân công suất)"""
        mock_send.return_value = True
        
        result = self.controller.start_integration()
        
        self.assertTrue(result)
        # Kiểm tra xem nó có gọi lệnh RESET trước khi START không
        mock_send.assert_any_call(":INTEGRATE:RESET")
        mock_send.assert_called_with(":INTEGRATE:STATE START")

if __name__ == '__main__':
    unittest.main()