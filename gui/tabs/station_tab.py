# gui/tabs/station_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel, QApplication)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
import re
from typing import Optional, Dict
from xml.etree import ElementTree as ET
import folium
import os
import tempfile
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

class StationTab(QWidget):
    """Tab for editing station information"""
    
    stationUpdated = pyqtSignal()  # Signal when station is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element = None
        self.inventory_model = None
        self.map_file = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create main form group
        station_group = QGroupBox("Station Information")
        station_layout = QFormLayout()
        
        # Create input fields with validation
        self.station_code = ValidationLineEdit(required=True, parent=self)
        self.station_name = ValidationLineEdit(parent=self)
        self.station_description = ValidationLineEdit(parent=self)
        self.station_start = ValidationLineEdit(
            validator=self.validate_datetime,
            parent=self
        )
        self.station_end = ValidationLineEdit(
            validator=self.validate_datetime,
            parent=self
        )
        self.station_lat = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) and -90 <= float(x) <= 90 if x else True,
            parent=self
        )
        self.station_lon = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) and -180 <= float(x) <= 180 if x else True,
            parent=self
        )
        self.station_elevation = ValidationLineEdit(
            validator=lambda x: re.match(r'^-?\d*\.?\d*$', x) if x else True,
            parent=self
        )
        self.station_affiliation = ValidationLineEdit(parent=self)
        self.station_country = ValidationLineEdit(parent=self)
        self.station_place = ValidationLineEdit(parent=self)
        
        # Add tooltips
        self.station_code.setToolTip("Station code (required)")
        self.station_name.setToolTip("Station name")
        self.station_lat.setToolTip("Latitude in decimal degrees (-90 to 90)")
        self.station_lon.setToolTip("Longitude in decimal degrees (-180 to 180)")
        self.station_elevation.setToolTip("Elevation in meters above sea level")
        self.station_start.setToolTip("Start date/time (YYYY-MM-DD HH:MM:SS)")
        self.station_end.setToolTip("End date/time (YYYY-MM-DD HH:MM:SS)")
        
        # Add fields to layout
        station_layout.addRow("Code:", self.station_code)
        station_layout.addRow("Name:", self.station_name)
        station_layout.addRow("Description:", self.station_description)
        station_layout.addRow("Start Time:", self.station_start)
        station_layout.addRow("End Time:", self.station_end)
        station_layout.addRow("Latitude (°):", self.station_lat)
        station_layout.addRow("Longitude (°):", self.station_lon)
        station_layout.addRow("Elevation (m):", self.station_elevation)
        station_layout.addRow("Affiliation:", self.station_affiliation)
        station_layout.addRow("Country:", self.station_country)
        station_layout.addRow("Place:", self.station_place)
        
        station_group.setLayout(station_layout)
        layout.addWidget(station_group)

        # Add map button
        self.view_map_button = QPushButton("View Station Location on Map")
        self.view_map_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.view_map_button.clicked.connect(self.show_map)
        layout.addWidget(self.view_map_button)
        
        # Add update button
        self.update_button = QPushButton("Update Station")
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
        self.update_button.clicked.connect(self.update_station)
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

        # Connect coordinate fields to map updates
        self.station_lat.editingFinished.connect(self.update_map_location)
        self.station_lon.editingFinished.connect(self.update_map_location)

    def create_map(self, lat, lon, station_name):
        """Create a map with station marker"""
        try:
            # Create a map centered at the station
            m = folium.Map(
                location=[float(lat), float(lon)],
                zoom_start=10,
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google Maps'
            )

            # Add marker for station
            folium.Marker(
                [float(lat), float(lon)],
                popup=station_name or 'Station Location',
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

            # Save to temporary file
            if self.map_file:
                try:
                    os.unlink(self.map_file)
                except:
                    pass

            fd, self.map_file = tempfile.mkstemp(suffix='.html')
            os.close(fd)
            m.save(self.map_file)

            return True
        except Exception as e:
            print(f"Error creating map: {str(e)}")
            return False

    def show_map(self):
        """Show the map in default web browser"""
        lat = self.station_lat.text()
        lon = self.station_lon.text()
        station_name = self.station_name.text() or self.station_code.text()

        if lat and lon:
            try:
                if self.create_map(lat, lon, station_name):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(self.map_file))
                else:
                    self.status_label.setText("Error creating map")
                    self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            except Exception as e:
                self.status_label.setText(f"Error showing map: {str(e)}")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
        else:
            self.status_label.setText("Please enter valid coordinates")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")

    def update_map_location(self):
        """Update map when coordinates change"""
        lat = self.station_lat.text()
        lon = self.station_lon.text()
        if lat and lon:
            try:
                float(lat)  # Validate coordinates
                float(lon)
                # Map will be updated when "View Map" is clicked
            except ValueError:
                pass

    def set_inventory_model(self, model):
        """Set the inventory model reference"""
        self.inventory_model = model
        
    def set_current_element(self, element: Optional[ET.Element]):
        """Set current station element and populate fields"""
        self.current_element = element
        if element is None:
            return
            
        # Get station data
        data = self.inventory_model.get_station_data(element)
        
        # Populate fields
        self.station_code.setText(data.code)
        self.station_name.setText(data.name)
        self.station_description.setText(data.description)
        self.station_start.setText(data.start)
        self.station_end.setText(data.end)
        self.station_lat.setText(data.latitude)
        self.station_lon.setText(data.longitude)
        self.station_elevation.setText(data.elevation)
        self.station_affiliation.setText(data.affiliation)
        self.station_country.setText(data.country)
        self.station_place.setText(data.place)
        
        self.status_label.setText("")

    def get_current_data(self) -> Dict[str, str]:
        """Get current field values"""
        return {
            'code': self.station_code.text(),
            'name': self.station_name.text(),
            'description': self.station_description.text(),
            'start': self.station_start.text(),
            'end': self.station_end.text(),
            'latitude': self.station_lat.text(),
            'longitude': self.station_lon.text(),
            'elevation': self.station_elevation.text(),
            'affiliation': self.station_affiliation.text(),
            'country': self.station_country.text(),
            'place': self.station_place.text()
        }

    def validate_datetime(self, text: str) -> bool:
        """Validate datetime string format"""
        from core.datetime_validation import DateTimeValidator
        
        if DateTimeValidator.validate(text):
            # If valid, automatically convert to SeisComP format
            if text:
                converted = DateTimeValidator.convert_to_seiscomp_format(text)
                if converted and converted != text:
                    # Update the field with converted format
                    sender = self.sender()
                    if sender:
                        sender.setText(converted)
            return True
            
        return False
            
    def validate_elevation(self) -> bool:
        """Validate elevation"""
        try:
            if self.station_elevation.text():
                float(self.station_elevation.text())  # Just check if it's a valid float
            return True
        except ValueError:
            return False

    def validate_coordinates(self) -> bool:
        """Validate latitude and longitude"""
        try:
            if self.station_lat.text():
                lat = float(self.station_lat.text())
                if not -90 <= lat <= 90:
                    return False
                    
            if self.station_lon.text():
                lon = float(self.station_lon.text())
                if not -180 <= lon <= 180:
                    return False
                    
            return True
            
        except ValueError:
            return False

    def validate_all(self) -> bool:
        """Validate all input fields"""
        return all([
            self.station_code.validate(),
            self.station_start.validate(),
            self.station_end.validate(),
            self.validate_coordinates(),
            self.validate_elevation()
        ])
        
    def update_station(self):
        """Update station data"""
        if not self.current_element or not self.inventory_model:
            return
            
        if not self.validate_all():
            self.status_label.setText("Please correct the invalid fields")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            return
            
        try:
            data = self.get_current_data()
            if self.inventory_model.update_station(self.current_element, data):
                self.status_label.setText("Station updated successfully")
                self.status_label.setStyleSheet("QLabel { color: #5cb85c; }")
                self.stationUpdated.emit()
            else:
                self.status_label.setText("No changes to update")
                self.status_label.setStyleSheet("QLabel { color: #666; }")
                
        except Exception as e:
            self.status_label.setText(f"Error updating station: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            
    def handle_editing_finished(self):
        """Called when editing is finished in any field"""
        if self.current_element:
            self.update_station()

    def __del__(self):
        """Cleanup temporary map files"""
        if self.map_file and os.path.exists(self.map_file):
            try:
                os.unlink(self.map_file)
            except:
                pass