# gui/tabs/location_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
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
        self.location_code = ValidationLineEdit(required=True, parent=self)
        self.location_start = ValidationLineEdit(
            validator='datetime',
            parent=self
        )
        self.location_end = ValidationLineEdit(
            validator='datetime',
            parent=self
        )
        self.location_lat = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) and -90 <= float(x) <= 90 if x else True,
            parent=self
        )
        self.location_lon = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) and -180 <= float(x) <= 180 if x else True,
            parent=self
        )
        self.location_elevation = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) if x else True,
            parent=self
        )
        self.location_depth = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) if x else True,
            parent=self
        )
        self.location_country = ValidationLineEdit(parent=self)
        self.location_description = ValidationLineEdit(parent=self)
        self.location_affiliation = ValidationLineEdit(parent=self)
        
        # Add tooltips
        self.location_code.setToolTip("Location code (required)")
        self.location_lat.setToolTip("Latitude in decimal degrees (-90 to 90)")
        self.location_lon.setToolTip("Longitude in decimal degrees (-180 to 180)")
        self.location_elevation.setToolTip("Elevation in meters above sea level")
        self.location_depth.setToolTip("Depth in meters below surface (positive down)")
        self.location_start.setToolTip("Start date/time (YYYY-MM-DD HH:MM:SS)")
        self.location_end.setToolTip("End date/time (YYYY-MM-DD HH:MM:SS)")
        
        # Add fields to layout
        location_layout.addRow("Code:", self.location_code)
        location_layout.addRow("Start Time:", self.location_start)
        location_layout.addRow("End Time:", self.location_end)
        location_layout.addRow("Latitude (°):", self.location_lat)
        location_layout.addRow("Longitude (°):", self.location_lon)
        location_layout.addRow("Elevation (m):", self.location_elevation)
        location_layout.addRow("Depth (m):", self.location_depth)
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
        self.location_depth.setText(data.depth)
        self.location_country.setText(data.country)
        self.location_description.setText(data.description)
        self.location_affiliation.setText(data.affiliation)
        
        self.status_label.setText("")
        
    def get_current_data(self) -> Dict[str, str]:
        """Get current field values"""
        return {
            'code': self.location_code.text(),
            'start': self.location_start.text(),
            'end': self.location_end.text(),
            'latitude': self.location_lat.text(),
            'longitude': self.location_lon.text(),
            'elevation': self.location_elevation.text(),
            'depth': self.location_depth.text(),
            'country': self.location_country.text(),
            'description': self.location_description.text(),
            'affiliation': self.location_affiliation.text()
        }
        
    @staticmethod
    def validate_datetime(text: str) -> bool:
        """Validate datetime string format"""
        if not text:  # Empty is valid
            return True
            
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
        return all([
            self.location_code.validate(),
            self.location_start.validate(),
            self.location_end.validate(),
            self.validate_coordinates(),
            self.validate_elevation()
        ])
        
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
            self.update_location()