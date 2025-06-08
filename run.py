from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # The create_app factory now handles instance path creation.
    # os.makedirs(app.instance_path, exist_ok=True) # More concise way if needed here
    app.run(debug=True)
