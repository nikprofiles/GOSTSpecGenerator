"""
Точка входа приложения — Генератор спецификаций ГОСТ 21.110-2013.
"""

import sys
import os

# Добавляем корень проекта в sys.path для корректного импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GOSTSpecGenerator")
    app.setOrganizationName("GOSTSpecGenerator")

    # Стиль
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
