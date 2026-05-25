import subprocess
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MultiAgentAutoCodingLab.Executor")

def execute_workspace(workspace_dir, entry_file=None, timeout=10):
    """
    Executes the main entry file inside a workspace directory.
    If entry_file is not specified, scans for common main files (main.py, app.py, run.py, index.js, etc.).
    Returns: (success: bool, stdout: str, stderr: str, exit_code: int)
    """
    if not os.path.exists(workspace_dir):
        return False, "", f"Lỗi: Thư mục workspace không tồn tại: {workspace_dir}", -3

    # 1. Detect entry file if not provided
    if not entry_file:
        possible_entries = ["main.py", "app.py", "run.py", "index.js", "src/main.py", "src/app.py"]
        for entry in possible_entries:
            if os.path.exists(os.path.join(workspace_dir, entry)):
                entry_file = entry
                break
                
    # Fallback: find the first python or javascript file in the workspace
    if not entry_file:
        for root, dirs, files in os.walk(workspace_dir):
            for file in files:
                if file.endswith(".py") or file.endswith(".js"):
                    # Calculate path relative to workspace_dir
                    entry_file = os.path.relpath(os.path.join(root, file), workspace_dir)
                    break
            if entry_file:
                break
                
    if not entry_file:
        return (
            True,
            "Biên dịch thành công. Không tìm thấy file chạy chính (main.py, app.py...) để chạy thử nghiệm runtime. Đã bỏ qua chạy thử.",
            "",
            0
        )
        
    entry_path = os.path.join(workspace_dir, entry_file)
    ext = os.path.splitext(entry_file)[1].lower()
    
    try:
        # Determine execution command
        cmd = []
        if ext == ".py":
            cmd = [sys.executable, entry_path]
        elif ext == ".js":
            cmd = ["node", entry_path]
        else:
            return (
                True, 
                f"Biên dịch thành công. Không hỗ trợ thực thi file {entry_file} trên host của bạn. Đã bỏ qua chạy thử.", 
                "", 
                0
            )
            
        logger.info(f"Executing entry: {' '.join(cmd)} in Cwd: {workspace_dir}")
        
        # Run subprocess with Cwd set to workspace_dir (essential for local imports to work!)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workspace_dir
        )
        
        success = (result.returncode == 0)
        return success, result.stdout, result.stderr, result.returncode
        
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout if e.stdout else ""
        stderr = e.stderr if e.stderr else ""
        error_msg = f"Lỗi: Chương trình chạy vượt quá giới hạn thời gian ({timeout} giây) tại file '{entry_file}'. Nghi ngờ xảy ra vòng lặp vô hạn hoặc đợi nhập liệu."
        logger.warning(error_msg)
        return False, stdout, error_msg, -1
        
    except Exception as e:
        error_msg = f"Lỗi hệ thống khi khởi chạy tiến trình: {str(e)}"
        logger.error(error_msg)
        return False, "", error_msg, -2
