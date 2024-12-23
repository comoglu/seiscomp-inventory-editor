# gui/tabs/sensor_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel, QLineEdit, QComboBox)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
from typing import Optional, Dict
from xml.etree import ElementTree as ET
import re
from core.datetime_validation import DateTimeValidator

class SensorTab(QWidget):
    """Tab for editing sensor information"""
    
    sensorUpdated = pyqtSignal()  # Signal when sensor is updated
    
    # Common sensor types for dropdown
    SENSOR_TYPES = [
        "Accelerometer",
        "Broadband",
        "Electric-Field",
        "Geophone",
        "High-Gain",
        "Low-Gain",
        "Magnetic-Field",
        "Rotational",
        "Short-Period",
        "Temperature",
        "Water-Level",
        "Other"
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element = None
        self.inventory_model = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create main form group
        sensor_group = QGroupBox("Sensor Information")
        sensor_layout = QFormLayout()
        
        # Create input fields
        self.sensor_name = ValidationLineEdit(required=True, parent=self)
        self.sensor_type = QComboBox(self)
        self.sensor_type.setEditable(True)
        self.sensor_type.addItems(self.SENSOR_TYPES)
        self.sensor_type.setCurrentText("")
        
        self.sensor_model = ValidationLineEdit(parent=self)
        self.sensor_manufacturer = ValidationLineEdit(parent=self)

        self.sensor_serial = ValidationLineEdit(
            validator=lambda x: bool(x.strip()),
            required=True, 
            parent=self)

        self.sensor_response = ValidationLineEdit(parent=self)
        self.sensor_unit = ValidationLineEdit(parent=self)
        self.sensor_lowFreq = ValidationLineEdit(
            validator=lambda x: x.replace('.', '', 1).isdigit() if x else True,
            parent=self
        )
        self.sensor_highFreq = ValidationLineEdit(
            validator=lambda x: x.replace('.', '', 1).isdigit() if x else True,
            parent=self
        )
        
        # Add tooltips
        self.sensor_name.setToolTip("Sensor name (required)")
        self.sensor_type.setToolTip("Type of sensor")
        self.sensor_model.setToolTip("Sensor model number/name")
        self.sensor_manufacturer.setToolTip("Manufacturer name")
        self.sensor_serial.setToolTip("Serial number (required)")
        self.sensor_serial.editingFinished.connect(self.handle_editing_finished)
        self.sensor_response.setToolTip("Response reference")
        self.sensor_unit.setToolTip("Measurement unit")
        self.sensor_lowFreq.setToolTip("Lower frequency limit (Hz)")
        self.sensor_highFreq.setToolTip("Upper frequency limit (Hz)")
        
        # Add fields to layout
        sensor_layout.addRow("Name:", self.sensor_name)
        sensor_layout.addRow("Type:", self.sensor_type)
        sensor_layout.addRow("Model:", self.sensor_model)
        sensor_layout.addRow("Manufacturer:", self.sensor_manufacturer)
        sensor_layout.addRow("Serial Number:", self.sensor_serial)
        sensor_layout.addRow("Response:", self.sensor_response)
        sensor_layout.addRow("Unit:", self.sensor_unit)
        sensor_layout.addRow("Low Frequency (Hz):", self.sensor_lowFreq)
        sensor_layout.addRow("High Frequency (Hz):", self.sensor_highFreq)
        
        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)
        
        # Add calibration information group
        calib_group = QGroupBox("Calibration Information")
        calib_layout = QFormLayout()
        
        self.calib_date = ValidationLineEdit(
            validator=self.validate_datetime,
            parent=self
        )
        self.calib_scale = ValidationLineEdit(
            validator=lambda x: x.replace('.', '', 1).isdigit() if x else True,
            parent=self
        )
        
        calib_layout.addRow("Calibration Date:", self.calib_date)
        calib_layout.addRow("Scale Factor:", self.calib_scale)
        
        calib_group.setLayout(calib_layout)
        layout.addWidget(calib_group)
        
        # Add update button
        self.update_button = QPushButton("Update Sensor")
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
        self.update_button.clicked.connect(self.update_sensor)
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
        
    def set_current_element(self, element: Optional[ET.Element]):
        """Set current sensor element and populate fields"""
        print("\n=== Sensor Tab Debug ===")
        print(f"Setting sensor element: {element is not None}")

        self.current_element = element
        if element is None:
            return
            
        # Get sensor data
        data = self.inventory_model.get_sensor_data(element)
        print(f"Sensor data loaded:")
        print(f"- Name: {data.name}")
        print(f"- Serial Number: {data.serialNumber}")  # Debug serial number
        print(f"- Model: {data.model}")
        
        # Populate fields
        self.sensor_name.setText(data.name)
        self.sensor_type.setCurrentText(data.type)
        self.sensor_model.setText(data.model)
        self.sensor_manufacturer.setText(data.manufacturer)
        self.sensor_serial.setText(data.serialNumber)
        self.sensor_response.setText(data.response)
        self.sensor_unit.setText(data.unit)
        self.sensor_lowFreq.setText(data.lowFrequency)
        self.sensor_highFreq.setText(data.highFrequency)
        self.calib_date.setText(data.calibrationDate)
        self.calib_scale.setText(data.calibrationScale)
        
        self.status_label.setText("")
        
    def get_current_data(self) -> Dict[str, str]:
        """Get current field values"""
        return {
            'name': self.sensor_name.text(),
            'type': self.sensor_type.currentText(),
            'model': self.sensor_model.text(),
            'manufacturer': self.sensor_manufacturer.text(),
            'serialNumber': self.sensor_serial.text().strip(),
            'response': self.sensor_response.text(),
            'unit': self.sensor_unit.text(),
            'lowFrequency': self.sensor_lowFreq.text(),
            'highFrequency': self.sensor_highFreq.text(),
            'calibrationDate': self.calib_date.text(),
            'calibrationScale': self.calib_scale.text()
        }
        
    @staticmethod
    def validate_datetime(text: str) -> bool:
        """Validate datetime string format"""
        return DateTimeValidator.validate(text)
            
        # datetime_pattern = r'^\d{4}-\d{2}-\d{2}(?:\s\d{2}:\d{2}:\d{2})?$'
        # if not re.match(datetime_pattern, text):
        #     return False
            
        # try:
        #     parts = text.split()
        #     date_parts = parts[0].split('-')
            
        #     year = int(date_parts[0])
        #     month = int(date_parts[1])
        #     day = int(date_parts[2])
            
        #     if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
        #         return False
                
        #     if len(parts) > 1:
        #         time_parts = parts[1].split(':')
        #         hour = int(time_parts[0])
        #         minute = int(time_parts[1])
        #         second = int(time_parts[2])
                
        #         if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        #             return False
                    
        #     return True
            
        # except (ValueError, IndexError):
        #     return False
            
    def validate_frequency(self) -> bool:
        """Validate frequency values"""
        try:
            if self.sensor_lowFreq.text():
                low_freq = float(self.sensor_lowFreq.text())
                if low_freq < 0:
                    return False
                    
            if self.sensor_highFreq.text():
                high_freq = float(self.sensor_highFreq.text())
                if high_freq < 0:
                    return False
                    
            # If both are provided, check high > low
            if self.sensor_lowFreq.text() and self.sensor_highFreq.text():
                if float(self.sensor_highFreq.text()) <= float(self.sensor_lowFreq.text()):
                    return False
                    
            return True
            
        except ValueError:
            return False
            
    def validate_calibration(self) -> bool:
        """Validate calibration values"""
        try:
            if self.calib_scale.text():
                scale = float(self.calib_scale.text())
                if scale <= 0:  # Scale factor should be positive
                    return False
                    
            return True
            
        except ValueError:
            return False
            
    def validate_all(self) -> bool:
        """Validate all input fields"""
        return all([
            self.sensor_name.validate(),
            self.sensor_serial.validate(),
            self.calib_date.validate(),
            self.validate_frequency(),
            self.validate_calibration()
        ])
        
    def update_sensor(self):
        """Update sensor data"""
        if not self.current_element or not self.inventory_model:
            return
            
        if not self.validate_all():
            self.status_label.setText("Please correct the invalid fields")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            return
            
        try:
            data = self.get_current_data()
            if self.inventory_model.update_sensor(self.current_element, data):
                self.status_label.setText("Sensor updated successfully")
                self.status_label.setStyleSheet("QLabel { color: #5cb85c; }")
                self.sensorUpdated.emit()
            else:
                self.status_label.setText("No changes to update")
                self.status_label.setStyleSheet("QLabel { color: #666; }")
                
        except Exception as e:
            self.status_label.setText(f"Error updating sensor: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            
    def handle_editing_finished(self):
        """Called when editing is finished in any field"""
        if self.current_element:
            self.update_sensor()