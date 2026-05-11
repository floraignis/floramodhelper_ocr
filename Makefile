install:
	pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
	pip install -r requirements.txt

run:
	gunicorn -w 1 --timeout 120 -b 0.0.0.0:8080 server:app
