# gui/tabs/stream_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel, QComboBox, QLineEdit)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
import re
from typing import Optional, Dict, List
from xml.etree import ElementTree as ET
from core.datetime_validation import DateTimeValidator  

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
            validator=lambda x: bool(re.match(r'^-?\d*\.?\d+(?:[eE][+-]?\d+)?$', x)) if x else True,
            parent=self
        )

        # Add sample rate field with proper validation
        self.stream_sampleRateNumerator = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^\d+$', x)) if x else True,
            parent=self
        )
        self.stream_sampleRateDenominator = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^\d+$', x)) if x else True,
            parent=self
        )

        # Updated gainFrequency validator similarly
        self.stream_gainFrequency = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^-?\d*\.?\d+(?:[eE][+-]?\d+)?$', x)) if x else True,
            parent=self
        )

        self.stream_gainUnit = ValidationLineEdit(parent=self)
        # Add flags field
        self.stream_flags = ValidationLineEdit(parent=self)  # No specific validation for flags

        # Add sensor and datalogger serial number display fields (read-only)
        self.sensor_serial_display = QLineEdit(self)
        self.sensor_serial_display.setReadOnly(True)
        self.sensor_serial_display.setPlaceholderText("Sensor Serial Number")
        
        self.datalogger_serial_display = QLineEdit(self)
        self.datalogger_serial_display.setReadOnly(True)
        self.datalogger_serial_display.setPlaceholderText("Datalogger Serial Number")


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
        self.stream_gain.setToolTip("Gain value (scientific notation supported, e.g. 1.23e+10)")
        self.stream_sampleRateNumerator.setToolTip("Sample rate numerator")
        self.stream_sampleRateDenominator.setToolTip("Sample rate denominator")
        self.stream_gainFrequency.setToolTip("Gain frequency in Hz")
        self.stream_gainUnit.setToolTip("Gain unit")
        self.stream_flags.setToolTip("Stream flags (e.g., G, GC)")

        
        # Add fields to layout
        stream_layout.addRow("Code:", self.stream_code)
        stream_layout.addRow("Start Time:", self.stream_start)
        stream_layout.addRow("End Time:", self.stream_end)
        stream_layout.addRow("Depth (m):", self.stream_depth)
        stream_layout.addRow("Azimuth (°):", self.stream_azimuth)
        stream_layout.addRow("Dip (°):", self.stream_dip)
        stream_layout.addRow("Gain:", self.stream_gain)
        stream_layout.addRow("Sample Rate Numerator:", self.stream_sampleRateNumerator)
        stream_layout.addRow("Sample Rate Denominator:", self.stream_sampleRateDenominator)
        stream_layout.addRow("Gain Frequency (Hz):", self.stream_gainFrequency)
        stream_layout.addRow("Gain Unit:", self.stream_gainUnit)
        stream_layout.addRow("Flags:", self.stream_flags)
        stream_layout.addRow("Sensor Serial:", self.sensor_serial_display)
        stream_layout.addRow("Datalogger Serial:", self.datalogger_serial_display)
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
        for sensor in self.inventory_model.get_sensors():
            name = sensor.get('name', '')
            model = self.inventory_model.xml_handler.get_element_text(sensor, 'model') or ''
            manufacturer = self.inventory_model.xml_handler.get_element_text(sensor, 'manufacturer') or ''
            display = f"{manufacturer} {model} - {name}" if manufacturer or model else name
            if name:
                self.sensor_combo.addItem(display, name)
        
        # Add dataloggers
        for datalogger in self.inventory_model.get_dataloggers():
            name = datalogger.get('name', '')
            model = self.inventory_model.xml_handler.get_element_text(datalogger, 'model') or ''
            manufacturer = self.inventory_model.xml_handler.get_element_text(datalogger, 'manufacturer') or ''
            display = f"{manufacturer} {model} - {name}" if manufacturer or model else name
            if name:
                self.datalogger_combo.addItem(display, name)


    def populate_sensor_datalogger(self):
        """Populate sensor and datalogger combo boxes"""
        print("\n=== Populating Combos Debug ===")
        
        if not self.inventory_model:
            print("No inventory model available!")
            return
        
        self.sensor_combo.clear()
        self.datalogger_combo.clear()
        
        # Debug: Get all streams to collect used serial numbers
        all_sensor_serials = set()
        all_datalogger_serials = set()
        
        print("Collecting serial numbers from streams...")
        for element in self.inventory_model.get_all_streams():
            sensor_serial = self.inventory_model.xml_handler.get_element_text(element, 'sensorSerialNumber')
            datalogger_serial = self.inventory_model.xml_handler.get_element_text(element, 'dataloggerSerialNumber')
            
            if sensor_serial:
                all_sensor_serials.add(sensor_serial)
                print(f"Found sensor serial: {sensor_serial}")
            if datalogger_serial:
                all_datalogger_serials.add(datalogger_serial)
                print(f"Found datalogger serial: {datalogger_serial}")
        
        # Add empty options
        self.sensor_combo.addItem("Select Sensor...", None)
        self.datalogger_combo.addItem("Select Datalogger...", None)
        
        # Add sensor serials to combo
        print("\nPopulating sensor combo...")
        for serial in sorted(all_sensor_serials):
            display_text = f"Sensor {serial}"
            print(f"Adding sensor: {display_text} with value {serial}")
            self.sensor_combo.addItem(display_text, serial)
        
        # Add datalogger serials to combo
        print("\nPopulating datalogger combo...")
        for serial in sorted(all_datalogger_serials):
            display_text = f"Datalogger {serial}"
            print(f"Adding datalogger: {display_text} with value {serial}")
            self.datalogger_combo.addItem(display_text, serial)
        
        print("=======================\n")

    def set_current_element(self, element: Optional[ET.Element]):
        """Set current stream element and populate fields"""
        print("\n=== Stream Tab Debug ===")
        print(f"Setting current element: {element is not None}")
        print("========================\n")

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
        self.stream_sampleRateNumerator.setText(data.sampleRateNumerator)
        self.stream_sampleRateDenominator.setText(data.sampleRateDenominator)
        self.stream_gainFrequency.setText(data.gainFrequency)
        self.stream_gainUnit.setText(data.gainUnit)
        self.sensor_serial_display.setText(data.sensor_serialnumber or "")
        self.datalogger_serial_display.setText(data.datalogger_serialnumber or "")
        self.stream_flags.setText(data.flags)

        print(f"Stream data loaded:")
        print(f"- Code: {data.code}")
        print(f"- Sensor Serial: {data.sensor_serialnumber}")
        print(f"- Datalogger Serial: {data.datalogger_serialnumber}")
       
        # Set combo box selections for sensor and datalogger
        sensor_index = self.sensor_combo.findData(data.sensor_serialnumber)
        if sensor_index >= 0:
            self.sensor_combo.setCurrentIndex(sensor_index)
            
        datalogger_index = self.datalogger_combo.findData(data.datalogger_serialnumber)
        if datalogger_index >= 0:
            self.datalogger_combo.setCurrentIndex(datalogger_index)

        print(f"Combo box indices - Sensor: {sensor_index}, Datalogger: {datalogger_index}")
        print("=======================\n")

            
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
        return DateTimeValidator.validate(text)
           
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
            'sampleRateNumerator': self.stream_sampleRateNumerator.text().strip(),
            'sampleRateDenominator': self.stream_sampleRateDenominator.text().strip(),
            'gainFrequency': self.stream_gainFrequency.text(),
            'gainUnit': self.stream_gainUnit.text(),
            'flags': self.stream_flags.text().strip(),
            'sensorSerialNumber': self.sensor_combo.currentData(),
            'dataloggerSerialNumber': self.datalogger_combo.currentData()
        }

        
    def validate_all(self) -> bool:
        """Validate all input fields"""
        validations = []
        
        # Check required code field
        code_valid = self.stream_code.validate()
        if not code_valid:
            self.status_label.setText("Stream code is required")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            validations.append(False)
        
        # Validate dates
        if self.stream_start.text():
            start_valid = DateTimeValidator.validate(self.stream_start.text())
            if not start_valid:
                self.status_label.setText("Invalid start time format")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        if self.stream_end.text():
            end_valid = DateTimeValidator.validate(self.stream_end.text())
            if not end_valid:
                self.status_label.setText("Invalid end time format")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate depth
        if self.stream_depth.text():
            try:
                float(self.stream_depth.text())
            except ValueError:
                self.status_label.setText("Invalid depth value")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate azimuth
        if self.stream_azimuth.text():
            try:
                azimuth = float(self.stream_azimuth.text())
                if not 0 <= azimuth <= 360:
                    self.status_label.setText("Azimuth must be between 0 and 360 degrees")
                    self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                    validations.append(False)
            except ValueError:
                self.status_label.setText("Invalid azimuth value")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate dip
        if self.stream_dip.text():
            try:
                dip = float(self.stream_dip.text())
                if not -90 <= dip <= 90:
                    self.status_label.setText("Dip must be between -90 and 90 degrees")
                    self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                    validations.append(False)
            except ValueError:
                self.status_label.setText("Invalid dip value")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate gain with scientific notation
        if self.stream_gain.text():
            try:
                float(self.stream_gain.text())  # This handles scientific notation properly
            except ValueError:
                self.status_label.setText("Invalid gain value")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate gain frequency
        if self.stream_gainFrequency.text():
            try:
                gain_freq = float(self.stream_gainFrequency.text())
                if gain_freq < 0:
                    self.status_label.setText("Gain frequency must be non-negative")
                    self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                    validations.append(False)
            except ValueError:
                self.status_label.setText("Invalid gain frequency value")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate sample rate if present
        if hasattr(self, 'stream_sampleRate') and self.stream_sampleRate.text():
            try:
                sample_rate = float(self.stream_sampleRate.text())
                if sample_rate <= 0:
                    self.status_label.setText("Sample rate must be positive")
                    self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                    validations.append(False)
            except ValueError:
                self.status_label.setText("Invalid sample rate value")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Clear status if all validations pass
        if not False in validations:
            self.status_label.setText("")
            self.status_label.setStyleSheet("")
            return True
        
        return False
        
    def validate_numeric(self, value: str, allow_scientific: bool = True) -> bool:
        """Validate numeric values with proper scientific notation support"""
        if not value:
            return True
            
        try:
            # Convert to float - this handles both standard and scientific notation
            float_val = float(value)
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