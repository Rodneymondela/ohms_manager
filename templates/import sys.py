import sys
import os

# Diagnostic prints (we can remove these later)
print("--- DIAGNOSTIC PRINTS (run.py) ---")
print(f"Current Working Directory (os.getcwd()): {os.getcwd()}")
print(f"sys.path: {sys.path}")
print(f"PYTHONPATH Environment Variable (os.environ.get('PYTHONPATH')): {os.environ.get('PYTHONPATH')}")
print("--- END DIAGNOSTIC PRINTS ---")

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)