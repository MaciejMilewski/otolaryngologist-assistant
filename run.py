from app import create_app, db
import os

os.environ["FLASK_APP"] = "run.py"
os.environ["FLASK_ENV"] = "development"

app = create_app()
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

