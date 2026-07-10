import PyInstaller.__main__
import shutil
import os

def clean_old_builds():
    """Xóa các thư mục build và dist cũ để đảm bảo bản build mới luôn sạch sẽ"""
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"[*] Đang dọn dẹp thư mục {dir_name} cũ...")
            shutil.rmtree(dir_name)

def build_exe():
    print("[*] Bắt đầu đóng gói ứng dụng thành file .exe...")
    
    # Truyền các tham số y hệt như trên dòng lệnh CMD
    PyInstaller.__main__.run([
        'run.py',                                  # File chạy chính
        '--onefile',                                # Đóng gói thành 1 file duy nhất
        '--windowed',                               # Ẩn cửa sổ console (terminal)
        '--add-data=utils/chart.umd.min.js;utils',  # Đính kèm thư viện Chart.js
        '--name=PowerMeter_Dashboard',              # (Tùy chọn) Đổi tên file exe xuất ra
        '--clean'                                   # Xóa cache của PyInstaller trước khi build
    ])
    
    print("\n[*] ĐÓNG GÓI HOÀN TẤT! Hãy kiểm tra thư mục 'dist'.")

if __name__ == "__main__":
    clean_old_builds()
    build_exe()