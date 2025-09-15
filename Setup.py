# setup.py - راه‌اندازی خودکار پلتفرم ChabokTool
import os
import subprocess
import sys
from pathlib import Path

print("🚀 خوش آمدید به راه‌اندازی پلتفرم ChabokTool")
print("=" * 50)

def check_python():
    """بررسی Python"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor} آماده است")
        return True
    else:
        print("❌ Python 3.8+ مورد نیاز است")
        return False

def create_backend_structure():
    """ایجاد ساختار backend"""
    print("\n📁 ایجاد ساختار فایل‌ها...")
    
    backend_dir = Path("backend")
    backend_dir.mkdir(exist_ok=True)
    
    # ایجاد پوشه‌های مورد نیاز
    folders = [
        "platform_api",
        "accounts", 
        "modules",
        "payments",
        "licenses",
        "core",
        "templates",
        "static"
    ]
    
    for folder in folders:
        folder_path = backend_dir / folder
        folder_path.mkdir(exist_ok=True)
        
        # ایجاد فایل __init__.py برای هر پوشه
        if folder != "templates" and folder != "static":
            init_file = folder_path / "__init__.py"
            init_file.touch()
    
    print("✅ ساختار فایل‌ها ایجاد شد")

def create_requirements():
    """ایجاد فایل requirements.txt"""
    requirements_content = """Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
python-decouple==3.8
pillow==10.0.1
requests==2.31.0"""
    
    requirements_file = Path("backend") / "requirements.txt"
    requirements_file.write_text(requirements_content)
    print("✅ فایل requirements.txt ایجاد شد")

def main():
    """اجرای اصلی"""
    if not check_python():
        input("برای خروج Enter بزنید...")
        return
    
    create_backend_structure()
    create_requirements()
    
    print("\n🎉 راه‌اندازی اولیه تمام شد!")
    print("🔄 مرحله بعد: ایجاد فایل‌های Django")
    print("\nبرای ادامه، فایل create_django.py را اجرا کنید")
    
    input("\nبرای خروج Enter بزنید...")

if __name__ == "__main__":
    main()