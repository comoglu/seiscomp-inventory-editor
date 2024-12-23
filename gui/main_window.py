# gui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QSplitter, QStatusBar, QPushButton, QFileDialog,
                           QMessageBox, QLabel, QStyle, QAction, QTabWidget)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QIcon, QPalette, QColor
from pathlib import Path
import sys

from gui.widgets.tree_widget import TreeWidgetWithKeyboardNav
from gui.tabs.network_tab import NetworkTab
from gui.tabs.station_tab import StationTab
from gui.tabs.location_tab import LocationTab
from gui.tabs.sensor_tab import SensorTab
from gui.tabs.datalogger_tab import DataloggerTab
from gui.tabs.stream_tab import StreamTab

from core.xml_handler import XMLHandler
from core.inventory_model import InventoryModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.xml_handler = XMLHandler()
        self.inventory_model = InventoryModel(self.xml_handler)
        self.settings = QSettings('SeisCompEditor', 'InventoryEditor')
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.perform_autosave)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Initialize the main window user interface"""
        self.setWindowTitle('SeisComP Inventory Editor')
        self.setMinimumSize(1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Create left panel (tree view)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Add file controls
        file_controls = QWidget()
        file_layout = QHBoxLayout(file_controls)
        self.load_button = QPushButton('Load XML')
        self.load_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.save_button = QPushButton('Save XML')
        self.save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_button.setEnabled(False)
        file_layout.addWidget(self.load_button)
        file_layout.addWidget(self.save_button)
        left_layout.addWidget(file_controls)

        # Add tree widget
        self.tree_widget = TreeWidgetWithKeyboardNav()
        self.tree_widget.setHeaderLabel('Inventory Structure')
        left_layout.addWidget(self.tree_widget)

        # Create right panel (tabs)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Create and setup tabs
        self.setup_tabs()
        right_layout.addWidget(self.tab_widget)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # Add splitter to layout
        layout.addWidget(splitter)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add autosave indicator
        self.autosave_label = QLabel("AutoSave Ready")
        self.autosave_label.setStyleSheet("""
            QLabel {
                color: green;
                padding: 2px 5px;
                border: 1px solid green;
                border-radius: 3px;
            }
        """)
        self.status_bar.addPermanentWidget(self.autosave_label)

        # Connect signals
        self.load_button.clicked.connect(self.load_xml)
        self.save_button.clicked.connect(self.save_xml)
        self.tree_widget.elementSelected.connect(self.handle_element_selection)

        # Create menu bar
        self.create_menu_bar()

    def setup_tabs(self):
        """Initialize all tab widgets"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin: 2px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QTabBar::tab:selected {
                background-color: #e6f3ff;
            }
        """)

        # Create tabs
        self.network_tab = NetworkTab()
        self.station_tab = StationTab()
        self.location_tab = LocationTab()
        self.sensor_tab = SensorTab()
        self.datalogger_tab = DataloggerTab()
        self.stream_tab = StreamTab()

        # Set inventory model for all tabs
        self.network_tab.set_inventory_model(self.inventory_model)
        self.station_tab.set_inventory_model(self.inventory_model)
        self.location_tab.set_inventory_model(self.inventory_model)
        self.sensor_tab.set_inventory_model(self.inventory_model)
        self.datalogger_tab.set_inventory_model(self.inventory_model)
        self.stream_tab.set_inventory_model(self.inventory_model)

        # Add tabs
        self.tab_widget.addTab(self.network_tab, "Network")
        self.tab_widget.addTab(self.station_tab, "Station")
        self.tab_widget.addTab(self.location_tab, "Location")
        self.tab_widget.addTab(self.sensor_tab, "Sensor")
        self.tab_widget.addTab(self.datalogger_tab, "Datalogger")
        self.tab_widget.addTab(self.stream_tab, "Stream")

        # Connect update signals
        self.network_tab.networkUpdated.connect(self.handle_element_updated)
        self.station_tab.stationUpdated.connect(self.handle_element_updated)
        self.location_tab.locationUpdated.connect(self.handle_element_updated)
        self.sensor_tab.sensorUpdated.connect(self.handle_element_updated)
        self.datalogger_tab.dataloggerUpdated.connect(self.handle_element_updated)
        self.stream_tab.streamUpdated.connect(self.handle_element_updated)

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        
        # Open action
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_xml)
        file_menu.addAction(open_action)

        # Save action
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_xml)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu('Edit')

        # Expand/Collapse actions
        expand_action = QAction('Expand All', self)
        expand_action.setShortcut('F5')
        expand_action.triggered.connect(self.tree_widget.expandAll)
        edit_menu.addAction(expand_action)

        collapse_action = QAction('Collapse All', self)
        collapse_action.setShortcut('F6')
        collapse_action.triggered.connect(self.tree_widget.collapseAll)
        edit_menu.addAction(collapse_action)

        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # Keyboard shortcuts action
        shortcuts_action = QAction('Keyboard Shortcuts', self)
        shortcuts_action.setShortcut('F1')
        shortcuts_action.triggered.connect(self.show_shortcuts_help)
        help_menu.addAction(shortcuts_action)

    def show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        shortcuts_text = """
Keyboard Shortcuts:
------------------
Navigation:
↑/↓: Move between items
←/→: Collapse/Expand items
Enter: Select item
Home: Go to first item
End: Go to last item
Tab: Move between fields

Global:
Ctrl+O: Open file
Ctrl+S: Save file
Ctrl+Q: Quit
F5: Expand all
F6: Collapse all
F1: Show this help
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setText(shortcuts_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                font-family: monospace;
                min-width: 500px;
            }
        """)
        msg.exec_()

    def load_settings(self):
        """Load application settings"""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        window_state = self.settings.value('windowState')
        if window_state:
            self.restoreState(window_state)
            
        self.last_directory = self.settings.value('lastDirectory', str(Path.home()))

    def save_settings(self):
        """Save application settings"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        if hasattr(self, 'last_directory'):
            self.settings.setValue('lastDirectory', self.last_directory)

    def load_xml(self):
        """Load XML inventory file"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Load SeisComP Inventory",
                self.last_directory,
                "XML files (*.xml)"
            )

            if filename:
                self.last_directory = str(Path(filename).parent)
                success, message = self.xml_handler.load_file(filename)

                if success:
                    self.inventory_model.load_inventory()
                    self.tree_widget.populate_inventory(self.xml_handler)
                    self.save_button.setEnabled(True)
                    self.status_bar.showMessage(f"Loaded: {filename}", 5000)
                else:
                    QMessageBox.warning(self, "Load Error", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred:\n{str(e)}"
            )

    def save_xml(self):
        """Save XML inventory file"""
        try:
            success, message = self.xml_handler.save_file()

            if success:
                self.status_bar.showMessage("File saved successfully", 5000)
                self.autosave_label.setText("Changes Saved")
                self.autosave_label.setStyleSheet("""
                    QLabel {
                        color: green;
                        padding: 2px 5px;
                        border: 1px solid green;
                        border-radius: 3px;
                    }
                """)
            else:
                QMessageBox.critical(self, "Save Error", message)
                self.autosave_label.setText("Save Failed")
                self.autosave_label.setStyleSheet("""
                    QLabel {
                        color: red;
                        padding: 2px 5px;
                        border: 1px solid red;
                        border-radius: 3px;
                    }
                """)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred:\n{str(e)}"
            )

    def handle_element_selection(self, element_type: str, element):
        """Handle element selection in tree view"""
        # Select appropriate tab
        tab_map = {
            'network': (self.network_tab, 0),
            'station': (self.station_tab, 1),
            'location': (self.location_tab, 2),
            'sensor': (self.sensor_tab, 3),
            'datalogger': (self.datalogger_tab, 4),
            'stream': (self.stream_tab, 5)
        }

        if element_type in tab_map:
            tab, index = tab_map[element_type]
            self.tab_widget.setCurrentIndex(index)
            tab.set_current_element(element)

    def handle_element_updated(self):
        """Handle element updates"""
        # Refresh tree view while maintaining expansion state
        expanded_state = self.tree_widget.save_expanded_state()
        self.tree_widget.populate_inventory(self.xml_handler)
        self.tree_widget.restore_expanded_state(expanded_state)
        
        # Trigger autosave
        self.autosave_timer.start(1000)
        self.autosave_label.setText("Saving...")
        self.autosave_label.setStyleSheet("""
            QLabel {
                color: orange;
                padding: 2px 5px;
                border: 1px solid orange;
                border-radius: 3px;
            }
        """)

    def perform_autosave(self):
        """Perform autosave operation"""
        self.save_xml()
        self.autosave_timer.stop()

    def closeEvent(self, event):
        """Handle application close event"""
        if self.xml_handler.modified_elements:
            reply = QMessageBox.question(
                self,
                'Save Changes?',
                'There are unsaved changes. Do you want to save before closing?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self.save_xml()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        self.save_settings()
        event.accept()