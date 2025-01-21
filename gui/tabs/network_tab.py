# gui/tabs/network_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel)
from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from gui.widgets.validation import ValidationLineEdit
import re
from typing import Optional, Dict, List, Tuple
from xml.etree import ElementTree as ET
import folium
import os
import tempfile
from core.datetime_validation import DateTimeValidator

class NetworkTab(QWidget):
    """Tab for editing network information"""
    
    networkUpdated = pyqtSignal()  # Signal when network is updated
    
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
        network_group = QGroupBox("Network Information")
        network_layout = QFormLayout()
        
        # Create input fields with validation
        self.network_code = ValidationLineEdit(required=True, parent=self)
        self.network_start = ValidationLineEdit(
            validator='datetime',
            parent=self
        )
        self.network_end = ValidationLineEdit(
            validator='datetime',
            parent=self
        )
        self.network_description = ValidationLineEdit(parent=self)
        self.network_institutions = ValidationLineEdit(parent=self)
        self.network_region = ValidationLineEdit(parent=self)
        self.network_type = ValidationLineEdit(parent=self)
        self.network_netClass = ValidationLineEdit(parent=self)
        self.network_archive = ValidationLineEdit(parent=self)
        self.network_restricted = ValidationLineEdit(
            validator=lambda x: x.lower() in ['true', 'false', ''],
            parent=self
        )
        self.network_shared = ValidationLineEdit(
            validator=lambda x: x.lower() in ['true', 'false', ''],
            parent=self
        )
        
        # Add tooltips
        self.network_code.setToolTip("Network code (required)")
        self.network_start.setToolTip("Start date/time (YYYY-MM-DD HH:MM:SS)")
        self.network_end.setToolTip("End date/time (YYYY-MM-DD HH:MM:SS)")
        self.network_restricted.setToolTip("Access restriction flag (true/false)")
        self.network_shared.setToolTip("Shared resource flag (true/false)")
        
        # Add fields to layout with labels
        network_layout.addRow("Code:", self.network_code)
        network_layout.addRow("Start Time:", self.network_start)
        network_layout.addRow("End Time:", self.network_end)
        network_layout.addRow("Description:", self.network_description)
        network_layout.addRow("Institutions:", self.network_institutions)
        network_layout.addRow("Region:", self.network_region)
        network_layout.addRow("Type:", self.network_type)
        network_layout.addRow("Network Class:", self.network_netClass)
        network_layout.addRow("Archive:", self.network_archive)
        network_layout.addRow("Restricted:", self.network_restricted)
        network_layout.addRow("Shared:", self.network_shared)
        
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)

        # Add map button
        self.view_map_button = QPushButton("View Network Stations on Map")
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
        self.update_button = QPushButton("Update Network")
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
        self.update_button.clicked.connect(self.update_network)
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

    def get_network_stations(self) -> List[Tuple[str, str, float, float]]:
        """Get all stations in the current network"""
        stations = []
        if self.current_element and self.inventory_model:
            for station in self.inventory_model.xml_handler.get_stations(self.current_element):
                data = self.inventory_model.get_station_data(station)
                if data.latitude and data.longitude:
                    try:
                        lat = float(data.latitude)
                        lon = float(data.longitude)
                        name = data.name or data.code
                        stations.append((data.code, name, lat, lon))
                    except ValueError:
                        continue
        return stations

    def create_map(self, stations: List[Tuple[str, str, float, float]]):
        """Create a map with all station markers"""
        try:
            if not stations:
                return False

            # Calculate center point as average of all stations
            center_lat = sum(s[2] for s in stations) / len(stations)
            center_lon = sum(s[3] for s in stations) / len(stations)

            # Create map centered at the average position
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=6,
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google Maps'
            )

            # Add markers for all stations
            station_group = folium.FeatureGroup(name="Stations")
            for code, name, lat, lon in stations:
                folium.Marker(
                    [lat, lon],
                    popup=f"{code}: {name}",
                    tooltip=code,
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(station_group)

            station_group.add_to(m)

            # Add layer control
            folium.LayerControl().add_to(m)

            # Fit bounds to show all markers
            if len(stations) > 1:
                bounds = [[s[2], s[3]] for s in stations]
                m.fit_bounds(bounds)

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
        stations = self.get_network_stations()
        if stations:
            try:
                if self.create_map(stations):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(self.map_file))
                else:
                    self.status_label.setText("Error creating map")
                    self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            except Exception as e:
                self.status_label.setText(f"Error showing map: {str(e)}")
                self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
        else:
            self.status_label.setText("No stations with coordinates found")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")

    def set_inventory_model(self, model):
        """Set the inventory model reference"""
        self.inventory_model = model
        
    def set_current_element(self, element: Optional[ET.Element]):
        """Set current network element and populate fields"""
        self.current_element = element
        if element is None:
            return
            
        # Get network data
        data = self.inventory_model.get_network_data(element)
        
        # Populate fields
        self.network_code.setText(data.code)
        self.network_start.setText(data.start)
        self.network_end.setText(data.end)
        self.network_description.setText(data.description)
        self.network_institutions.setText(data.institutions)
        self.network_region.setText(data.region)
        self.network_type.setText(data.type)
        self.network_netClass.setText(data.netClass)
        self.network_archive.setText(data.archive)
        self.network_restricted.setText(data.restricted)
        self.network_shared.setText(data.shared)
        
        self.status_label.setText("")
        
    def get_current_data(self) -> Dict[str, str]:
        """Get current field values"""
        return {
            'code': self.network_code.text(),
            'start': self.network_start.text(),
            'end': self.network_end.text(),
            'description': self.network_description.text(),
            'institutions': self.network_institutions.text(),
            'region': self.network_region.text(),
            'type': self.network_type.text(),
            'netClass': self.network_netClass.text(),
            'archive': self.network_archive.text(),
            'restricted': self.network_restricted.text().lower(),
            'shared': self.network_shared.text().lower()
        }
        
    def validate_all(self) -> bool:
        """Validate all input fields"""
        return all([
            self.network_code.validate(),
            self.network_start.validate(),
            self.network_end.validate(),
            self.network_restricted.validate(),
            self.network_shared.validate()
        ])
        
    def update_network(self):
        """Update network data"""
        if not self.current_element or not self.inventory_model:
            return
            
        if not self.validate_all():
            self.status_label.setText("Please correct the invalid fields")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            return
            
        try:
            data = self.get_current_data()
            if self.inventory_model.update_network(self.current_element, data):
                self.status_label.setText("Network updated successfully")
                self.status_label.setStyleSheet("QLabel { color: #5cb85c; }")
                self.networkUpdated.emit()
            else:
                self.status_label.setText("No changes to update")
                self.status_label.setStyleSheet("QLabel { color: #666; }")
                
        except Exception as e:
            self.status_label.setText(f"Error updating network: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #d9534f; }")
            
    def handle_editing_finished(self):
        """Called when editing is finished in any field"""
        if self.current_element:
            self.update_network()

    def __del__(self):
        """Cleanup temporary map files"""
        if self.map_file and os.path.exists(self.map_file):
            try:
                os.unlink(self.map_file)
            except:
                pass