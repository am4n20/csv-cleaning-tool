import subprocess
import time
import sys
import os
import webbrowser

def main():
    print("==========================================")
    print("   CSV CLEANING TOOL - LOCAL LAUNCHER")
    print("==========================================")

    # 1. Install Dependencies
    print("\n[1/3] Ensuring dependencies are installed...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError:
        print("Error installing requirements. Please check requirements.txt")
        sys.exit(1)

    # 2. Start Backend
    print("\n[2/3] Starting Backend (FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--reload"],
        cwd=os.getcwd()
    )

    # Give backend a moment to start
    time.sleep(3)

    # 3. Start Frontend
    print("\n[3/3] Starting Frontend (Streamlit)...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py"],
        cwd=os.getcwd()
    )

    print("\n==========================================")
    print("   APPLICATION RUNNING")
    print("   Backend:  http://localhost:8000")
    print("   Frontend: http://localhost:8501")
    print("==========================================")
    print("Press Ctrl+C to stop the application.")

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if backend_process.poll() is not None:
                print("Backend stopped unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("Frontend stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping application...")
    finally:
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
