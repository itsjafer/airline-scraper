
build: requirements.txt
		pip install -r requirements.txt
		playwright install
		playwright install-deps