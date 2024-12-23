# gui/tabs/datalogger_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel, QLineEdit, QComboBox)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
from typing import Optional, Dict
from xml.etree import ElementTree as ET
from core.datetime_validation import DateTimeValidator

class DataloggerTab(QWidget):
    """Tab for editing datalogger information"""
    
    dataloggerUpdated = pyqtSignal()  # Signal when datalogger is updated
    
    # Common datalogger types for dropdown
    DATALOGGER_TYPES = [
        "Analog",
        "Digital",
        "Hybrid",
        "Other"
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element = None
        self.inventory_model = None
        self.setup_ui()

    def validate_datetime(self, text: str) -> bool:
        """Validate datetime string format"""
        return DateTimeValidator.validate(text)

    def setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create main form group
        datalogger_group = QGroupBox("Datalogger Information")
        datalogger_layout = QFormLayout()
        
        # Create input fields
        self.datalogger_name = ValidationLineEdit(required=True, parent=self)
        self.datalogger_type = QComboBox(self)
        self.datalogger_type.setEditable(True)
        self.datalogger_type.addItems(self.DATALOGGER_TYPES)
        self.datalogger_type.setCurrentText("")
        
        self.datalogger_model = ValidationLineEdit(parent=self)
        self.datalogger_manufacturer = ValidationLineEdit(parent=self)
        self.datalogger_serial = ValidationLineEdit(
            validator=lambda x: bool(x.strip()),  # Strip whitespace
            required=True,
            parent=self)
        
        self.datalogger_description = ValidationLineEdit(parent=self)
        
        # Create sampling group
        sampling_group = QGroupBox("Sampling Configuration")
        sampling_layout = QFormLayout()
        
        self.max_clock_drift = ValidationLineEdit(
            validator=lambda x: x.replace('.', '', 1).isdigit() if x else True,
            parent=self
        )
        self.record_length = ValidationLineEdit(
            validator=lambda x: x.isdigit() if x else True,
            parent=self
        )
        self.sample_rate = ValidationLineEdit(
            validator=lambda x: x.replace('.', '', 1).isdigit() if x else True,
            parent=self
        )
        self.sample_rate_multiplier = ValidationLineEdit(
            validator=lambda x: x.isdigit() if x else True,
            parent=self
        )
        
        # Add tooltips
        self.datalogger_name.setToolTip("Datalogger name (required)")
        self.datalogger_type.setToolTip("Type of datalogger")
        self.datalogger_model.setToolTip("Datalogger model number/name")
        self.datalogger_manufacturer.setToolTip("Manufacturer name")
        self.datalogger_serial.setToolTip("Serial number (required)")
        self.datalogger_serial.editingFinished.connect(self.handle_editing_finished)
        self.datalogger_description.setToolTip("Additional description")
        self.max_clock_drift.setToolTip("Maximum clock drift in seconds per day")
        self.record_length.setToolTip("Record length in samples")
        self.sample_rate.setToolTip("Sample rate in Hz")
        self.sample_rate_multiplier.setToolTip("Sample rate multiplier")
        
        # Add fields to main layout
        datalogger_layout.addRow("Name:", self.datalogger_name)
        datalogger_layout.addRow("Type:", self.datalogger_type)
        datalogger_layout.addRow("Model:", self.datalogger_model)
        datalogger_layout.addRow("Manufacturer:", self.datalogger_manufacturer)
        datalogger_layout.addRow("Serial Number:", self.datalogger_serial)
        datalogger_layout.addRow("Description:", self.datalogger_description)
        
        datalogger_group.setLayout(datalogger_layout)
        layout.addWidget(datalogger_group)
        
        # Add fields to sampling layout
        sampling_layout.addRow("Max Clock Drift (s/day):", self.max_clock_drift)
        sampling_layout.addRow("Record Length (samples):", self.record_length)
        sampling_layout.addRow("Sample Rate (Hz):", self.sample_rate)
        sampling_layout.addRow("Sample Rate Multiplier:", self.sample_rate_multiplier)
        
        sampling_group.setLayout(sampling_layout)
        layout.addWidget(sampling_group)
        
        # Add update button
        self.update_button = QPushButton("Update Datalogger")
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
        self.update_button.clicked.connect(self.update_datalogger)
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
        """Set current datalogger element and populate fields"""
        print("\n=== Datalogger Tab Debug ===")
        print(f"Setting datalogger element: {element is not None}")

        self.current_element = element
        if element is None:
            return
            
        # Get datalogger data
        data = self.inventory_model.get_datalogger_data(element)
        print(f"Datalogger data loaded:")
        print(f"- Name: {data.name}")
        print(f"- Serial Number: {data.serialNumber}")  # Debug serial number
        print(f"- Model: {data.model}")
        
        # Populate fields
        self.datalogger_name.setText(data.name)
        self.datalogger_type.setCurrentText(data.type)
        self.datalogger_model.setText(data.model)
        self.datalogger_manufacturer.setText(data.manufacturer)
        self.datalogger_serial.setText(data.serialNumber)
        self.datalogger_description.setText(data.description)
        
        # Populate sampling fields
        self.max_clock_drift.setText(data.maxClockDrift)
        self.record_length.setText(data.recordLength)
        self.sample_rate.setText(data.sampleRate)
        self.sample_rate_multiplier.setText(data.sampleRateMultiplier)
        
        self.status_label.setText("")
        
    def get_current_data(self) -> Dict[str, str]:
        """Get current field values"""
        return {
            'name': self.datalogger_name.text(),
            'type': self.datalogger_type.currentText(),
            'model': self.datalogger_model.text(),
            'manufacturer': self.datalogger_manufacturer.text(),
            'serialNumber': self.datalogger_serial.text().strip(),
            'description': self.datalogger_description.text(),
            'maxClockDrift': self.max_clock_drift.text(),
            'recordLength': self.record_length.text(),
            'sampleRate': self.sample_rate.text(),
            'sampleRateMultiplier': self.sample_rate_multiplier.text()
        }
        
    def validate_numeric(self, value: str, allow_float: bool = True) -> bool:
        """Validate numeric values"""
        if not value:  # Empty is valid
            return True
            
        try:
            if allow_float:
                num = float(value)
            else:
                num = int(value)
            return num >= 0  # All these values should be positive
            
        except ValueError:
            return False
            
    def validate_all(self) -> bool:
        """Validate all input fields"""
        # Required fields
        if not all([
            self.datalogger_name.validate(),
            self.datalogger_serial.validate()
        ]):
            return False
            
        # Numeric fields
        if not all([
            self.validate_numeric(self.max_clock_drift.text(), True),  # Allow float
            self.validate_numeric(self.record_length.text(), False),   # Integer only
            self.validate_numeric(self.sample_rate.text(), True),      # Allow float
            self.validate_numeric(self.sample_rate_multiplier.text(), False)  # Integer only
        ]):
            return False
            
        # Additional validation for sample rate
        if self.sample_rate.text():
            try:
                if float(self.sample_rate.text()) <= 0:
                    return False
            except ValueError:
                return False
                
        return True
        
    def update_datalogger(self):
        """Update datalogger data"""
        if not self.current_element or not self.inventory_model:
            return
            
        if not self.validate_all():
            self.status_label.setText("Please correct the invalid fields")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            return
            
        try:
            data = self.get_current_data()
            if self.inventory_model.update_datalogger(self.current_element, data):
                self.status_label.setText("Datalogger updated successfully")
                self.status_label.setStyleSheet("QLabel { color: #5cb85c; }")
                self.dataloggerUpdated.emit()
            else:
                self.status_label.setText("No changes to update")
                self.status_label.setStyleSheet("QLabel { color: #666; }")
                
        except Exception as e:
            self.status_label.setText(f"Error updating datalogger: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            
    def handle_editing_finished(self):
        """Called when editing is finished in any field"""
        if self.current_element:
            self.update_datalogger()
            
    def get_serial_number(self) -> str:
        """Get current datalogger serial number"""
        return self.datalogger_serial.text()
        
    def clear_fields(self):
        """Clear all input fields"""
        self.datalogger_name.clear()
        self.datalogger_type.setCurrentText("")
        self.datalogger_model.clear()
        self.datalogger_manufacturer.clear()
        self.datalogger_serial.clear()
        self.datalogger_description.clear()
        self.max_clock_drift.clear()
        self.record_length.clear()
        self.sample_rate.clear()
        self.sample_rate_multiplier.clear()
        self.status_label.clear()