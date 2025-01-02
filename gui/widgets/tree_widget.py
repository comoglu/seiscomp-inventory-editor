# gui/widgets/tree_widget.py
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, List, Optional, Any, Tuple
from xml.etree import ElementTree as ET

class TreeWidgetWithKeyboardNav(QTreeWidget):
    """Enhanced QTreeWidget with keyboard navigation"""
    
    elementSelected = pyqtSignal(str, ET.Element)  # Signal for element selection (type, element)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.currentItemChanged.connect(self._handle_current_item_changed)
        self.setup_style()
        
    def setup_style(self):
        """Setup widget styling"""
        self.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #e6f3ff;
                color: black;
            }
            QTreeWidget::item:hover {
                background-color: #f5f5f5;
            }
            QTreeWidget::branch {
                background: transparent;
            }
        """)
        
    def _handle_current_item_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """Handle item selection change with improved stability"""
        if not current:
            return
            
        try:
            self.itemClicked.emit(current, 0)
            data = current.data(0, Qt.UserRole)
            
            # More robust type checking
            if not data:
                print("Warning: No data associated with tree item")
                return
                
            # Handle both tuple data and direct element data
            if isinstance(data, tuple):
                if len(data) == 2 and isinstance(data[0], str) and isinstance(data[1], ET.Element):
                    self.elementSelected.emit(data[0], data[1])
                else:
                    print(f"Warning: Invalid tuple data format: {data}")
            elif isinstance(data, ET.Element):
                # Try to determine type from element tag
                element_type = data.tag.split('}')[-1].lower()
                self.elementSelected.emit(element_type, data)
            else:
                print(f"Warning: Unexpected data type in tree item: {type(data)}")
                
        except Exception as e:
            print(f"Error handling tree item selection: {str(e)}")
              
    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        key = event.key()
        current_item = self.currentItem()
        
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            if current_item:
                self.itemClicked.emit(current_item, 0)
                
        elif key == Qt.Key_Right:
            if current_item and not current_item.isExpanded():
                current_item.setExpanded(True)
            elif current_item and current_item.childCount() > 0:
                self.setCurrentItem(current_item.child(0))
                
        elif key == Qt.Key_Left:
            if current_item:
                if current_item.isExpanded():
                    current_item.setExpanded(False)
                else:
                    parent = current_item.parent()
                    if parent:
                        self.setCurrentItem(parent)
                        
        elif key == Qt.Key_Home:
            first_item = self.topLevelItem(0)
            if first_item:
                self.setCurrentItem(first_item)
                
        elif key == Qt.Key_End:
            last_item = self.get_last_visible_item()
            if last_item:
                self.setCurrentItem(last_item)
                
        elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
            
    def get_last_visible_item(self) -> Optional[QTreeWidgetItem]:
        """Get the last visible item in the tree"""
        last_item = self.topLevelItem(self.topLevelItemCount() - 1)
        if not last_item:
            return None
            
        while last_item.isExpanded() and last_item.childCount() > 0:
            last_item = last_item.child(last_item.childCount() - 1)
            
        return last_item
        
    def save_expanded_state(self) -> List[str]:
        """Save the current expanded state"""
        expanded_items = []
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            if item.isExpanded():
                # Save the path to this item (e.g., "Network/Station/Location")
                path = []
                current = item
                while current:
                    path.insert(0, current.text(0))
                    current = current.parent()
                expanded_items.append('/'.join(path))
            iterator += 1
        return expanded_items
        
    def restore_expanded_state(self, expanded_items: List[str]):
        """Restore previously saved expanded state"""
        if not expanded_items:
            return
            
        def expand_path(item: QTreeWidgetItem, path_parts: List[str]):
            """Recursively expand items matching the path"""
            if not path_parts:
                return
                
            for i in range(item.childCount()):
                child = item.child(i)
                if child.text(0) == path_parts[0]:
                    if len(path_parts) == 1:
                        child.setExpanded(True)
                    else:
                        child.setExpanded(True)
                        expand_path(child, path_parts[1:])
        
        # Process each saved path
        for path in expanded_items:
            path_parts = path.split('/')
            # Start from root items
            for i in range(self.topLevelItemCount()):
                root_item = self.topLevelItem(i)
                if root_item.text(0) == path_parts[0]:
                    root_item.setExpanded(True)
                    if len(path_parts) > 1:
                        expand_path(root_item, path_parts[1:])
                        
    def populate_inventory(self, xml_handler):
        """Populate tree with inventory data"""
        try:
            self.clear()
            
            # Get inventory element with proper error checking
            inventory = xml_handler.root.find('sc3:Inventory', xml_handler.ns)
            if inventory is None:
                print("Warning: No inventory found in XML")
                return
                
            # Add networks with error handling
            for network in xml_handler.get_networks():
                try:
                    network_item = QTreeWidgetItem(self)
                    network_code = network.get('code', '')
                    network_item.setText(0, f"Network: {network_code}")
                    network_item.setData(0, Qt.UserRole, ('network', network))
                    
                    # Add stations
                    for station in xml_handler.get_stations(network):
                        try:
                            station_item = QTreeWidgetItem(network_item)
                            station_code = station.get('code', '')
                            station_item.setText(0, f"Station: {station_code}")
                            station_item.setData(0, Qt.UserRole, ('station', station))
                            
                            # Add sensor locations
                            for location in xml_handler.get_locations(station):
                                try:
                                    location_item = QTreeWidgetItem(station_item)
                                    location_code = location.get('code', '')
                                    location_item.setText(0, f"Location: {location_code}")
                                    location_item.setData(0, Qt.UserRole, ('location', location))
                                    
                                    # Add streams
                                    streams = xml_handler.get_streams(location)
                                    for stream in self.sort_streams(streams):
                                        try:
                                            stream_item = QTreeWidgetItem(location_item)
                                            stream_code = stream.get('code', '')
                                            stream_item.setText(0, f"Stream: {stream_code}")
                                            stream_item.setData(0, Qt.UserRole, ('stream', stream))
                                        except Exception as e:
                                            print(f"Error adding stream item: {str(e)}")
                                            continue
                                except Exception as e:
                                    print(f"Error adding location item: {str(e)}")
                                    continue
                        except Exception as e:
                            print(f"Error adding station item: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Error adding network item: {str(e)}")
                    continue
                    
            # Add sensors section with error handling
            try:
                sensors = xml_handler.get_sensors()
                if sensors:
                    sensors_item = QTreeWidgetItem(self)
                    sensors_item.setText(0, "Sensors")
                    
                    for sensor in sensors:
                        try:
                            sensor_item = QTreeWidgetItem(sensors_item)
                            name = sensor.get('name', '')
                            serial = xml_handler.get_element_text(sensor, 'serialNumber')
                            sensor_item.setText(0, f"Sensor: {name} ({serial})" if serial else f"Sensor: {name}")
                            sensor_item.setData(0, Qt.UserRole, ('sensor', sensor))
                        except Exception as e:
                            print(f"Error adding sensor item: {str(e)}")
                            continue
            except Exception as e:
                print(f"Error adding sensors section: {str(e)}")
                
            # Add dataloggers section with error handling
            try:
                dataloggers = xml_handler.get_dataloggers()
                if dataloggers:
                    dataloggers_item = QTreeWidgetItem(self)
                    dataloggers_item.setText(0, "Dataloggers")
                    
                    for datalogger in dataloggers:
                        try:
                            datalogger_item = QTreeWidgetItem(dataloggers_item)
                            name = datalogger.get('name', '')
                            serial = xml_handler.get_element_text(datalogger, 'serialNumber')
                            datalogger_item.setText(0, f"Datalogger: {name} ({serial})" if serial else f"Datalogger: {name}")
                            datalogger_item.setData(0, Qt.UserRole, ('datalogger', datalogger))
                        except Exception as e:
                            print(f"Error adding datalogger item: {str(e)}")
                            continue
            except Exception as e:
                print(f"Error adding dataloggers section: {str(e)}")
                
        except Exception as e:
            print(f"Error populating inventory tree: {str(e)}")
            # Clear tree on major error to prevent partial/invalid state
            self.clear()
                
    def sort_streams(self, streams: List[ET.Element]) -> List[ET.Element]:
        """
        Sort streams according to seismological convention:
        1. First by band and instrument code (B, H, etc.)
        2. Then by orientation (E/1, N/2, Z) or (1, 2, Z)
        """
        def get_sort_key(stream: ET.Element) -> tuple:
            code = stream.get('code', '')
            if not code or len(code) < 3:
                return ('', '', 999)
                
            band_code = code[0]
            instrument_code = code[1]
            orientation = code[2]
            
            orientation_order = {
                'E': 0, '1': 0,  # E and 1 are equivalent
                'N': 1, '2': 1,  # N and 2 are equivalent
                'Z': 2,          # Z always comes last
            }
            orientation_value = orientation_order.get(orientation, 3)
            
            return (band_code, instrument_code, orientation_value)
            
        return sorted(streams, key=get_sort_key)
