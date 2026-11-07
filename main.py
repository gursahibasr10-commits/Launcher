import os
import re
import sys
import subprocess

try:
    import winreg
except ImportError:  # Non-Windows platforms fallback for development/testing.
    winreg = None

from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QPushButton,
    QGraphicsOpacityEffect,
)
from PyQt6.QtGui import QPixmap, QFont, QIcon


# ---------------------------------------------------------
# STEAM LIBRARY SCANNER
# ---------------------------------------------------------
def get_steam_path():
    """Locates the main Steam installation path from the Windows Registry."""
    if winreg is None:
        return "C:/Program Files (x86)/Steam"

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "SteamPath")
        return path.replace("\\", "/")
    except Exception:
        return "C:/Program Files (x86)/Steam"


def get_installed_games():
    """Scans local Steam manifest files to find installed games and assets."""
    steam_path = get_steam_path()
    apps_path = f"{steam_path}/steamapps"
    games = []

    if not os.path.exists(apps_path):
        return [
            {"appid": "730", "name": "Counter-Strike 2"},
            {"appid": "1091500", "name": "Cyberpunk 2077"},
            {"appid": "1151640", "name": "Horizon Zero Dawn"},
        ]

    for file in os.listdir(apps_path):
        if file.endswith(".acf"):
            try:
                with open(
                    os.path.join(apps_path, file),
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as f:
                    content = f.read()
                    appid_match = re.search(r'"appid"\s+"(\d+)"', content)
                    name_match = re.search(r'"name"\s+"([^"]+)"', content)

                    if not appid_match or not name_match:
                        continue

                    appid = appid_match.group(1)
                    name = name_match.group(1)

                    hero_path = f"{steam_path}/appcache/librarycache/{appid}_library_hero.jpg"
                    grid_path = f"{steam_path}/appcache/librarycache/{appid}_library_600x900.jpg"

                    if not os.path.exists(hero_path):
                        hero_path = f"https://steamstatic.com{appid}/library_hero.jpg"
                    if not os.path.exists(grid_path):
                        grid_path = f"https://steamstatic.com{appid}/library_600x900.jpg"

                    games.append({
                        "appid": appid,
                        "name": name,
                        "hero": hero_path,
                        "grid": grid_path,
                    })
            except Exception:
                continue

    return games


# ---------------------------------------------------------
# UI PAGES
# ---------------------------------------------------------
class WelcomePage(QWidget):
    """The PS5 Profile Selector / Login Screen."""

    def __init__(self, on_login_callback):
        super().__init__()
        self.setStyleSheet("background-color: #080c14;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Welcome Back to PlayStation")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Who's using this controller?")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: #8a93a1; margin-bottom: 50px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        profile_btn = QPushButton("🎮\n\nScotty Kenzo")
        profile_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        profile_btn.setFixedSize(180, 180)
        profile_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #161c26;
                color: white;
                border: 3px solid #2a3547;
                border-radius: 90px;
            }
            QPushButton:hover {
                border: 3px solid #0066ff;
                background-color: #1f293a;
            }
            """
        )
        profile_btn.clicked.connect(on_login_callback)
        layout.addWidget(profile_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class DashboardPage(QWidget):
    """The Main PS5 dashboard with theme changes and bottom-scrolling games."""

    def __init__(self, games):
        super().__init__()
        self.games = games
        self.init_ui()

    def init_ui(self):
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setStyleSheet("background-color: #050a12;")

        self.opacity_effect = QGraphicsOpacityEffect(self.bg_label)
        self.bg_label.setGraphicsEffect(self.opacity_effect)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)

        self.meta_layout = QVBoxLayout()
        self.game_title = QLabel("Select a Game")
        self.game_title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        self.game_title.setStyleSheet("color: white; background: transparent;")

        self.play_btn = QPushButton("▶ Launch Game")
        self.play_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.play_btn.setFixedSize(180, 50)
        self.play_btn.setStyleSheet(
            """
            QPushButton { background-color: white; color: black; border-radius: 25px; }
            QPushButton:hover { background-color: #0066ff; color: white; }
            """
        )
        self.play_btn.hide()
        self.play_btn.clicked.connect(self.launch_game)

        self.meta_layout.addWidget(self.game_title)
        self.meta_layout.addWidget(self.play_btn)
        self.meta_layout.addStretch()
        main_layout.addLayout(self.meta_layout)

        self.games_shelf = QListWidget()
        self.games_shelf.setViewMode(QListWidget.ViewMode.IconMode)
        self.games_shelf.setOrientation(Qt.Orientation.Horizontal)
        self.games_shelf.setMovement(QListWidget.Movement.Static)
        self.games_shelf.setFixedSize(1150, 180)
        self.games_shelf.setSpacing(20)
        self.games_shelf.setStyleSheet(
            """
            QListWidget { background: transparent; border: none; }
            QListWidget::item { background-color: #1a2230; border-radius: 12px; color: white; padding: 5px; }
            QListWidget::item:selected { border: 3px solid #0066ff; background-color: #253146; }
            """
        )
        self.games_shelf.setIconSize(QSize(100, 130))
        self.games_shelf.currentItemChanged.connect(self.on_game_selected)

        for game in self.games:
            item = QListWidgetItem(game["name"])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if os.path.exists(game["grid"]):
                item.setIcon(QIcon(game["grid"]))
            else:
                item.setIcon(QIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogIconView)))
            self.games_shelf.addItem(item)

        main_layout.addWidget(self.games_shelf, alignment=Qt.AlignmentFlag.AlignHCenter)

    def resizeEvent(self, event):
        """Ensures the background wallpaper scales perfectly dynamically."""
        self.bg_label.resize(self.size())
        super().resizeEvent(event)

    def on_game_selected(self, current, previous):
        """Triggered when user navigates or selects a game card at the bottom."""
        if not current:
            return

        index = self.games_shelf.row(current)
        game = self.games[index]

        self.game_title.setText(game["name"])
        self.play_btn.show()
        self.active_appid = game["appid"]

        if os.path.exists(game["hero"]):
            pixmap = QPixmap(game["hero"])
        else:
            pixmap = QPixmap()

        self.bg_label.setPixmap(pixmap)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.2)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()

    def launch_game(self):
        """Launches the selected game directly via Steam protocol."""
        if hasattr(self, "active_appid"):
            subprocess.Popen(f"start steam://run/{self.active_appid}", shell=True)


# ---------------------------------------------------------
# APPLICATION ROOT WINDOW
# ---------------------------------------------------------
class PS5Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom PlayStation 5 Launcher")
        self.resize(1280, 720)

        self.installed_games = get_installed_games()

        self.page_controller = QStackedWidget()
        self.setCentralWidget(self.page_controller)

        self.welcome_screen = WelcomePage(on_login_callback=self.go_to_dashboard)
        self.dashboard_screen = DashboardPage(self.installed_games)

        self.page_controller.addWidget(self.welcome_screen)
        self.page_controller.addWidget(self.dashboard_screen)

        self.page_controller.setCurrentWidget(self.welcome_screen)

    def go_to_dashboard(self):
        self.page_controller.setCurrentWidget(self.dashboard_screen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PS5Launcher()
    window.show()
    sys.exit(app.exec())


# ---------------------------------------------------------
# NOTE:
# This app is designed for Windows because it reads Steam metadata from
# the Windows registry and launches Steam URIs using the `start` command.
# ---------------------------------------------------------
"""
The original code was incomplete; this version completes the missing app logic
and adds a safe fallback for non-Windows environments.
"""
