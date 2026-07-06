# HIOKI PW3336 ETSI Power Measurement
hioki_power_meter_project/
│
├── core/                           
│   ├── __init__.py
│   ├── hioki_controller.py         # Class giao tiếp máy đo HIOKI
│   ├── etsi_profiles.py            # Cấu hình tham số chuẩn ETSI
│   └── data_logger.py              # Xử lý tính toán và ghi log
│
├── gui/                            
│   ├── __init__.py
│   ├── main_window.py              # Giao diện chính (Bảng LED, Nút bấm)
│   ├── control_panels.py           # Các popup phụ (DUT, SCPI, Batch)
│   └── styles.py                   # Quản lý màu sắc, fonts, style
│
├── data/                           
│   ├── reports/                    # Nơi lưu file Excel/CSV xuất ra
│   └── logs/                       # Nơi lưu file log lỗi hệ thống
│
├── assets/                         
│   ├── icon.ico                    # Icon ứng dụng
│   └── images/                     # Ảnh, logo
│
├── utils/                          
│   ├── __init__.py
│   ├── excel_exporter.py           # Module xuất báo cáo Excel
│   └── helpers.py                  # Các hàm tiện ích dùng chung
│
├── tests/                          
│   ├── test_connection.py          
│   └── test_scpi_commands.py       
│
├── .gitignore                      
├── requirements.txt                
├── README.md                       
└── run.py                          # File chạy chính của ứng dụng