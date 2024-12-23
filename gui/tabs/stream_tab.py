# gui/tabs/stream_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel, QComboBox)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
import re
from typing import Optional, Dict, List
from xml.etree import ElementTree as ET

class StreamTab(QWidget):
    """Tab for editing stream information"""
    
    streamUpdated = pyqtSignal()  # Signal when stream is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element = None
        self.inventory_model = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create main form group
        stream_group = QGroupBox("Stream/Channel Information")
        stream_layout = QFormLayout()
        
        # Create input fields with validation
        self.stream_code = ValidationLineEdit(required=True, parent=self)
        self.stream_start = ValidationLineEdit(
            validator='datetime',
            parent=self
        )
        self.stream_end = ValidationLineEdit(
            validator='datetime',
            parent=self
        )
        self.stream_depth = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) if x else True,
            parent=self
        )
        self.stream_azimuth = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) and 0 <= float(x) <= 360 if x else True,
            parent=self
        )
        self.stream_dip = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) and -90 <= float(x) <= 90 if x else True,
            parent=self
        )
        self.stream_gain = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) if x else True,
            parent=self
        )
        self.stream_sampleRate = ValidationLineEdit(
            validator=lambda x: re.match(r'^\d*\.?\d*$', x) if x else True,
            parent=self
        )
        self.stream_gainFrequency = ValidationLineEdit(
            validator=lambda x: re.match(r'^\d*\.?\d*$', x) if x else True,
            parent=self
        )
        self.stream_gainUnit = ValidationLineEdit(parent=self)
        
        # Create sensor and datalogger combo boxes
        self.sensor_combo = QComboBox(self)
        self.datalogger_combo = QComboBox(self)
        
        # Add tooltips
        self.stream_code.setToolTip("Stream code (required)")
        self.stream_start.setToolTip("Start date/time (YYYY-MM-DD HH:MM:SS)")
        self.stream_end.setToolTip("End date/time (YYYY-MM-DD HH:MM:SS)")
        self.stream_depth.setToolTip("Depth in meters below surface (positive down)")
        self.stream_azimuth.setToolTip("Azimuth in degrees (0-360)")
        self.stream_dip.setToolTip("Dip in degrees (-90 to 90)")
        self.stream_gain.setToolTip("Gain value")
        self.stream_sampleRate.setToolTip("Sample rate in Hz")
        self.stream_gainFrequency.setToolTip("Gain frequency in Hz")
        self.stream_gainUnit.setToolTip("Gain unit")
        
        # Add fields to layout
        stream_layout.addRow("Code:", self.stream_code)
        stream_layout.addRow("Start Time:", self.stream_start)
        stream_layout.addRow("End Time:", self.stream_end)
        stream_layout.addRow("Depth (m):", self.stream_depth)
        stream_layout.addRow("Azimuth (°):", self.stream_azimuth)
        stream_layout.addRow("Dip (°):", self.stream_dip)
        stream_layout.addRow("Gain:", self.stream_gain)
        stream_layout.addRow("Sample Rate (Hz):", self.stream_sampleRate)
        stream_layout.addRow("Gain Frequency (Hz):", self.stream_gainFrequency)
        stream_layout.addRow("Gain Unit:", self.stream_gainUnit)
        stream_layout.addRow("Sensor:", self.sensor_combo)
        stream_layout.addRow("Datalogger:", self.datalogger_combo)
        
        stream_group.setLayout(stream_layout)
        layout.addWidget(stream_group)
        
        # Add update button
        self.update_button = QPushButton("Update Stream")
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.update_button.clicked.connect(self.update_stream)
        layout.addWidget(self.update_button)
        
        # Add status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
    def set_inventory_model(self, model):
        """Set the inventory model reference"""
        self.inventory_model = model
        self.populate_combos()
        
    def populate_combos(self):
        """Populate sensor and datalogger combo boxes"""
        if not self.inventory_model:
            return
            
        # Clear existing items
        self.sensor_combo.clear()
        self.datalogger_combo.clear()
        
        # Add empty option
        self.sensor_combo.addItem("Select Sensor...", None)
        self.datalogger_combo.addItem("Select Datalogger...", None)
        
        # Add sensors
        sensors = self.inventory_model.get_sensors()
        for sensor in sensors:
            name = sensor.get('name', 'Unknown')
            serial = self.inventory_model.get_element_text(sensor, 'serialNumber')
            if serial:
                self.sensor_combo.addItem(f"{name} ({serial})", serial)
            
        # Add dataloggers
        dataloggers = self.inventory_model.get_dataloggers()
        for datalogger in dataloggers:
            name = datalogger.get('name', 'Unknown')
            serial = self.inventory_model.get_element_text(datalogger, 'serialNumber')
            if serial:
                self.datalogger_combo.addItem(f"{name} ({serial})", serial)
                
    def set_current_element(self, element: Optional[ET.Element]):
        """Set current stream element and populate fields"""
        self.current_element = element
        if element is None:
            return
            
        # Get stream data
        data = self.inventory_model.get_stream_data(element)
        
        # Populate fields
        self.stream_code.setText(data.code)
        self.stream_start.setText(data.start)
        self.stream_end.setText(data.end)
        self.stream_depth.setText(data.depth)
        self.stream_azimuth.setText(data.azimuth)
        self.stream_dip.setText(data.dip)
        self.stream_gain.setText(data.gain)
        self.stream_sampleRate.setText(data.sampleRate)
        self.stream_gainFrequency.setText(data.gainFrequency)
        self.stream_gainUnit.setText(data.gainUnit)
        
        # Set combo box selections
        self.set_sensor_selection(data.sensor_serialnumber)
        self.set_datalogger_selection(data.datalogger_serialnumber)
        
        self.status_label.setText("")
        
    def set_sensor_selection(self, serial: str):
        """Set sensor combo box selection"""
        index = self.sensor_combo.findData(serial)
        if index >= 0:
            self.sensor_combo.setCurrentIndex(index)
            
    def set_datalogger_selection(self, serial: str):
        """Set datalogger combo box selection"""
        index = self.datalogger_combo.findData(serial)
        if index >= 0:
            self.datalogger_combo.setCurrentIndex(index)
            
    def validate_datetime(self, text: str) -> bool:
        """Validate datetime string format"""
        if not text:  # Empty is valid
            return True
            
        # Basic datetime format validation
        datetime_pattern = r'^\d{4}-\d{2}-\d{2}(?:\s\d{2}:\d{2}:\d{2})?$'
        if not re.match(datetime_pattern, text):
            return False
            
        try:
            parts = text.split()
            date_parts = parts[0].split('-')
            
            year = int(date_parts[0])
            month = int(date_parts[1])
            day = int(date_parts[2])
            
            if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
                return False
                
            if len(parts) > 1:
                time_parts = parts[1].split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2])
                
                if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                    return False
                    
            return True
            
        except (ValueError, IndexError):
            return False
            
    def get_current_data(self) -> Dict[str, str]:
        """Get current field values"""
        return {
            'code': self.stream_code.text(),
            'start': self.stream_start.text(),
            'end': self.stream_end.text(),
            'depth': self.stream_depth.text(),
            'azimuth': self.stream_azimuth.text(),
            'dip': self.stream_dip.text(),
            'gain': self.stream_gain.text(),
            'sampleRate': self.stream_sampleRate.text(),
            'gainFrequency': self.stream_gainFrequency.text(),
            'gainUnit': self.stream_gainUnit.text(),
            'sensor_serialnumber': self.sensor_combo.currentData(),
            'datalogger_serialnumber': self.datalogger_combo.currentData()
        }
        
    def validate_all(self) -> bool:
        """Validate all input fields"""
        return all([
            self.stream_code.validate(),
            self.stream_start.validate(),
            self.stream_end.validate(),
            self.validate_numeric_field(self.stream_depth),
            self.validate_numeric_field(self.stream_azimuth, 0, 360),
            self.validate_numeric_field(self.stream_dip, -90, 90),
            self.validate_numeric_field(self.stream_gain),
            self.validate_numeric_field(self.stream_sampleRate, min_val=0),
            self.validate_numeric_field(self.stream_gainFrequency, min_val=0)
        ])
        
    def validate_numeric_field(self, field: ValidationLineEdit, 
                             min_val: float = None, max_val: float = None) -> bool:
        """Validate numeric field with optional range"""
        if not field.text():
            return True
            
        try:
            value = float(field.text())
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False
            return True
        except ValueError:
            return False
            
    def update_stream(self):
        """Update stream data"""
        if not self.current_element or not self.inventory_model:
            return
            
        if not self.validate_all():
            self.status_label.setText("Please correct the invalid fields")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            return
            
        try:
            data = self.get_current_data()
            if self.inventory_model.update_stream(self.current_element, data):
                self.status_label.setText("Stream updated successfully")
                self.status_label.setStyleSheet("QLabel { color: #5cb85c; }")
                self.streamUpdated.emit()
            else:
                self.status_label.setText("No changes to update")
                self.status_label.setStyleSheet("QLabel { color: #666; }")
                
        except Exception as e:
            self.status_label.setText(f"Error updating stream: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            
    def handle_editing_finished(self):
        """Called when editing is finished in any field"""
        if self.current_element:
            self.update_stream()