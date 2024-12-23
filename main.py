#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from gui.main_window import MainWindow

def setup_application_style(app):
    """Setup application-wide style and theme"""
    # Use Fusion style for a modern look
    app.setStyle('Fusion')
    
    # Setup color palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.Link, QColor(0, 120, 210))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)

def main():
    """Application entry point"""
    # Create application instance
    app = QApplication(sys.argv)
    
    # Setup application style
    setup_application_style(app)
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Critical Error",
            f"An unexpected error occurred:\n{str(e)}\n\nThe application will now close."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()