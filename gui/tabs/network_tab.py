# gui/tabs/network_tab.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                           QVBoxLayout, QLabel)
from PyQt5.QtCore import pyqtSignal
from gui.widgets.validation import ValidationLineEdit
import re
from typing import Optional, Dict
from xml.etree import ElementTree as ET
from core.datetime_validation import DateTimeValidator

class NetworkTab(QWidget):
    """Tab for editing network information"""
    
    networkUpdated = pyqtSignal()  # Signal when network is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element = None
        self.inventory_model = None
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
        
    @staticmethod
    def validate_datetime(text: str) -> bool:
        """Validate datetime string format"""
        return DateTimeValidator.validate(text)
        
        # # Basic datetime format validation
        # datetime_pattern = r'^\d{4}-\d{2}-\d{2}(?:\s\d{2}:\d{2}:\d{2})?$'
        # if not re.match(datetime_pattern, text):
        #     return False
            
        # try:
        #     # Split into date and optional time parts
        #     parts = text.split()
        #     date_parts = parts[0].split('-')
            
        #     # Validate year, month, day
        #     year = int(date_parts[0])
        #     month = int(date_parts[1])
        #     day = int(date_parts[2])
            
        #     if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
        #         return False
                
        #     # Validate time if present
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