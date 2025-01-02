# gui/tabs/location_tab.py

from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
from core.datetime_validation import DateTimeValidator
import re
from typing import Optional, Dict
from xml.etree import ElementTree as ET

class LocationTab(QWidget):
    """Tab for editing sensor location information"""
    
    locationUpdated = pyqtSignal()  # Signal when location is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element = None
        self.inventory_model = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create main form group
        location_group = QGroupBox("Sensor Location Information")
        location_layout = QFormLayout()
        
        # Create input fields with validation
        # Code validation should check for non-empty and alphanumeric
        self.location_code = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^[A-Za-z0-9]*$', x)),  # Note the * instead of + to allow empty
            required=False,  # Changed to False since it's not always required
            parent=self
        )
        
        # Use DateTimeValidator for start/end times
        self.location_start = ValidationLineEdit(
            validator=lambda x: DateTimeValidator.validate(x),
            parent=self
        )
        self.location_end = ValidationLineEdit(
            validator=lambda x: DateTimeValidator.validate(x),
            parent=self
        )
        
        # Coordinate validation
        self.location_lat = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^-?\d*\.?\d*$', x)) and -90 <= float(x) <= 90 if x else True,
            parent=self
        )
        self.location_lon = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^-?\d*\.?\d*$', x)) and -180 <= float(x) <= 180 if x else True,
            parent=self
        )
        
        # Numeric validation for elevation and depth
        self.location_elevation = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^-?\d*\.?\d*$', x)) if x else True,
            parent=self
        )
        self.location_depth = ValidationLineEdit(
            validator=lambda x: bool(re.match(r'^-?\d*\.?\d*$', x)) if x else True,
            parent=self
        )
        
        # Optional text fields
        self.location_country = ValidationLineEdit(parent=self)
        self.location_description = ValidationLineEdit(parent=self)
        self.location_affiliation = ValidationLineEdit(parent=self)
        
        # Add tooltips with validation requirements
        self.location_code.setToolTip("Location code (required, alphanumeric only)")
        self.location_start.setToolTip("Start date/time (YYYY-MM-DD HH:MM:SS)")
        self.location_end.setToolTip("End date/time (YYYY-MM-DD HH:MM:SS)")
        self.location_lat.setToolTip("Latitude in decimal degrees (-90 to 90)")
        self.location_lon.setToolTip("Longitude in decimal degrees (-180 to 180)")
        self.location_elevation.setToolTip("Elevation in meters above sea level")
        
        # Add fields to layout
        location_layout.addRow("Code*:", self.location_code)
        location_layout.addRow("Start Time:", self.location_start)
        location_layout.addRow("End Time:", self.location_end)
        location_layout.addRow("Latitude (°):", self.location_lat)
        location_layout.addRow("Longitude (°):", self.location_lon)
        location_layout.addRow("Elevation (m):", self.location_elevation)
        location_layout.addRow("Country:", self.location_country)
        location_layout.addRow("Description:", self.location_description)
        location_layout.addRow("Affiliation:", self.location_affiliation)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Add update button
        self.update_button = QPushButton("Update Location")
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
        self.update_button.clicked.connect(self.update_location)
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
        
        # Connect editing finished signals
        self.location_code.editingFinished.connect(self.handle_editing_finished)
        self.location_start.editingFinished.connect(self.handle_editing_finished)
        self.location_end.editingFinished.connect(self.handle_editing_finished)
        self.location_lat.editingFinished.connect(self.handle_editing_finished)
        self.location_lon.editingFinished.connect(self.handle_editing_finished)
        self.location_elevation.editingFinished.connect(self.handle_editing_finished)
    
    def set_inventory_model(self, model):
        """Set the inventory model reference"""
        self.inventory_model = model
        
    def set_current_element(self, element: Optional[ET.Element]):
        """Set current location element and populate fields"""
        self.current_element = element
        if element is None:
            return
            
        # Get location data
        data = self.inventory_model.get_location_data(element)
        
        # Populate fields
        self.location_code.setText(data.code)
        self.location_start.setText(data.start)
        self.location_end.setText(data.end)
        self.location_lat.setText(data.latitude)
        self.location_lon.setText(data.longitude)
        self.location_elevation.setText(data.elevation)
        self.location_country.setText(data.country)
        self.location_description.setText(data.description)
        self.location_affiliation.setText(data.affiliation)
        
        self.status_label.setText("")
        
    def get_current_data(self) -> Dict[str, str]:
        """Get current field values"""
        data = {
            'code': self.location_code.text().strip(),
            'start': self.location_start.text().strip(),
            'end': self.location_end.text().strip(),
            'latitude': self.location_lat.text().strip(),
            'longitude': self.location_lon.text().strip(),
            'elevation': self.location_elevation.text().strip(),
            'depth': self.location_depth.text().strip(),
            'country': self.location_country.text().strip(),
            'description': self.location_description.text().strip(),
            'affiliation': self.location_affiliation.text().strip()
        }
        
        # Convert datetime formats if needed
        if data['start']:
            data['start'] = DateTimeValidator.convert_to_seiscomp_format(data['start']) or data['start']
        if data['end']:
            data['end'] = DateTimeValidator.convert_to_seiscomp_format(data['end']) or data['end']
            
        return data
        
    def validate_coordinates(self) -> bool:
        """Validate latitude and longitude"""
        try:
            if self.location_lat.text():
                lat = float(self.location_lat.text())
                if not -90 <= lat <= 90:
                    return False
                    
            if self.location_lon.text():
                lon = float(self.location_lon.text())
                if not -180 <= lon <= 180:
                    return False
                    
            return True
            
        except ValueError:
            return False
            
    def validate_elevation(self) -> bool:
        """Validate elevation and depth"""
        try:
            if self.location_elevation.text():
                float(self.location_elevation.text())
                
            if self.location_depth.text():
                float(self.location_depth.text())
                
            return True
            
        except ValueError:
            return False

    def validate_all(self) -> bool:
        """Validate all input fields"""
        validations = []
        
        # Check code field - only validate if not empty
        if self.location_code.text().strip():
            code_valid = self.location_code.validate()
            if not code_valid:
                self.status_label.setText("Location code must be alphanumeric")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)

        
        # Validate dates
        if self.location_start.text():
            start_valid = DateTimeValidator.validate(self.location_start.text())
            if not start_valid:
                self.status_label.setText("Invalid start time format")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        if self.location_end.text():
            end_valid = DateTimeValidator.validate(self.location_end.text())
            if not end_valid:
                self.status_label.setText("Invalid end time format")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate coordinates if provided
        if self.location_lat.text() or self.location_lon.text():
            coord_valid = self.validate_coordinates()
            if not coord_valid:
                self.status_label.setText("Invalid coordinates")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # Validate numeric fields if provided
        if self.location_elevation.text() or self.location_depth.text():
            numeric_valid = self.validate_elevation()
            if not numeric_valid:
                self.status_label.setText("Invalid elevation or depth values")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
                validations.append(False)
        
        # If any validation failed, return False
        if False in validations:
            return False
        
        return True
        
    def update_location(self):
        """Update location data"""
        if not self.current_element or not self.inventory_model:
            return
            
        if not self.validate_all():
            self.status_label.setText("Please correct the invalid fields")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            return
            
        try:
            data = self.get_current_data()
            if self.inventory_model.update_location(self.current_element, data):
                self.status_label.setText("Location updated successfully")
                self.status_label.setStyleSheet("QLabel { color: #5cb85c; }")
                self.locationUpdated.emit()
            else:
                self.status_label.setText("No changes to update")
                self.status_label.setStyleSheet("QLabel { color: #666; }")
                
        except Exception as e:
            self.status_label.setText(f"Error updating location: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            
    def handle_editing_finished(self):
        """Called when editing is finished in any field"""
        if self.current_element:
            # Convert datetime formats if needed
            sender = self.sender()
            if sender in [self.location_start, self.location_end] and sender.text():
                converted = DateTimeValidator.convert_to_seiscomp_format(sender.text())
                if converted and converted != sender.text():
                    sender.setText(converted)
            
            # Validate the field
            self.validate_all()

    def clear_fields(self):
        """Clear all input fields"""
        self.location_code.clear()
        self.location_start.clear()
        self.location_end.clear()
        self.location_lat.clear()
        self.location_lon.clear()
        self.location_elevation.clear()
        self.location_depth.clear()
        self.location_country.clear()
        self.location_description.clear()
        self.location_affiliation.clear()
        self.status_label.clear()