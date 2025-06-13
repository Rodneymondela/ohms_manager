import sys
import os

print("--- DIAGNOSTIC PRINTS (run.py) ---")
print(f"Current Working Directory (os.getcwd()): {os.getcwd()}")
print(f"sys.path: {sys.path}")
print(f"PYTHONPATH Environment Variable (os.environ.get('PYTHONPATH')): {os.environ.get('PYTHONPATH')}")
print("--- END DIAGNOSTIC PRINTS ---")

from app import create_app
# import os # This import is now at the top

app = create_app()

if __name__ == '__main__':
    # The create_app factory now handles instance path creation.
    # os.makedirs(app.instance_path, exist_ok=True) # More concise way if needed here
    app.run(debug=True)
