app:
	poetry run streamlit run app/streamlit_app.py

data-update:
	poetry run python scripts/update_latest_gameweeks.py --gameweeks 1
