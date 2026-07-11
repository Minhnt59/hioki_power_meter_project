import PyInstaller.__main__
import shutil
import os

VERSION_FILE = 'version.txt'

def get_and_update_version():
    """Đọc version hiện tại, tự động tăng số Patch lên 1 và lưu lại."""
    # Nếu chưa có file version.txt, tạo mặc định là 1.0.0
    if not os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'w') as f:
            f.write("1.0.0")
        return "1.0.0"

    # Đọc version cũ
    with open(VERSION_FILE, 'r') as f:
        current_version = f.read().strip()

    try:
        # Tách version thành 3 phần: Major.Minor.Patch (VD: 1.0.5 -> ['1', '0', '5'])
        parts = current_version.split('.')
        major, minor, patch = parts[0], parts[1], parts[2]
        
        # Tăng số patch lên 1
        new_patch = int(patch) + 1
        new_version = f"{major}.{minor}.{new_patch}"
        
        # Lưu version mới lại vào file
        with open(VERSION_FILE, 'w') as f:
            f.write(new_version)
            
        print(f"[*] Nâng cấp Version: {current_version}  --->  {new_version}")
        return new_version
    except Exception as e:
        print(f"[!] File version.txt sai định dạng. Trở về mặc định 1.0.0")
        return "1.0.0"
    
def clean_old_builds():
    """Xóa các thư mục build và dist cũ để đảm bảo bản build mới luôn sạch sẽ"""
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"[*] Đang dọn dẹp thư mục {dir_name} cũ...")
            shutil.rmtree(dir_name)

def build_exe(version):
    print("[*] Bắt đầu đóng gói ứng dụng thành file .exe...")
    
    exe_name = f"VHT_PowerConsumption_Measurement_v{version}"

    PyInstaller.__main__.run([
        'run.py',                                  # File chạy chính
        '--onefile',                                # Đóng gói thành 1 file duy nhất
        '--windowed',                               # Ẩn cửa sổ console (terminal)
        '--add-data=utils/chart.umd.min.js;utils',  # Đính kèm thư viện Chart.js
        '--add-data=version.txt;.',                 # Đính kèm luôn file version.txt vào exe
        f'--name={exe_name}',                        # Đổi tên file exe xuất ra
        '--clean'                                   # Xóa cache của PyInstaller trước khi build
    ])
    
    print("\n[*] ĐÓNG GÓI HOÀN TẤT! Hãy kiểm tra thư mục 'dist'.")

if __name__ == "__main__":
    new_ver = get_and_update_version()
    clean_old_builds()
    build_exe(new_ver)