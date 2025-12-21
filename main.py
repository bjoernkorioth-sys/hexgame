# main.py
from app import App
from menu_screen import MenuScreen

if __name__ == "__main__":
    app = App()
    app.run(MenuScreen(app))
