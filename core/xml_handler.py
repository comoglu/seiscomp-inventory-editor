# core/xml_handler.py
from xml.etree import ElementTree as ET
from pathlib import Path
import re
from typing import Dict, Optional, Tuple, List
import logging

class XMLHandler:
    """Handles XML file operations for SeisComP inventory"""
    
    def __init__(self):
        self.ns = {'sc3': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.12'}
        self.current_file: Optional[str] = None
        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self.modified_elements: Dict[str, Dict[str, str]] = {}
        
    def load_file(self, filename: str) -> Tuple[bool, str]:
        """
        Load and validate XML file
        
        Args:
            filename: Path to XML file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            
            if not self._validate_xml_structure(root):
                return False, "Invalid SeisComP inventory structure"
                
            self.current_file = filename
            self.tree = tree
            self.root = root
            self.modified_elements = {}
            
            return True, "File loaded successfully"
            
        except ET.ParseError as e:
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            return False, f"Error loading file: {str(e)}"
            
    def _validate_xml_structure(self, root: ET.Element) -> bool:
        """Validate basic SeisComP XML structure"""
        if root.tag != f'{{{self.ns["sc3"]}}}seiscomp':
            return False
        inventory = root.find('sc3:Inventory', self.ns)
        return inventory is not None
        
    def save_file(self) -> Tuple[bool, str]:
        """Save XML while preserving formatting"""
        if not (self.current_file and self.tree):
            return False, "No file loaded"
            
        try:
            current_path = Path(self.current_file)
            backup_path = current_path.with_suffix('.xml.bak')
            
            # Create backup
            if current_path.exists():
                current_path.rename(backup_path)
            
            # Read original content
            with open(backup_path, 'r', encoding='UTF-8') as f:
                content = f.read()
            
            # Apply tracked changes
            content = self._apply_changes(content)
            
            # Write modified content
            with open(str(current_path), 'w', encoding='UTF-8') as f:
                f.write(content)
            
            self.modified_elements = {}
            return True, "File saved successfully"
            
        except Exception as e:
            if backup_path.exists():
                backup_path.rename(current_path)
            return False, f"Error saving file: {str(e)}"
    
    def _apply_changes(self, content: str) -> str:
        """Apply tracked changes to XML content"""
        for element_id, changes in self.modified_elements.items():
            element_start = content.find(f'publicID="{element_id}"')
            if element_start != -1:
                # Find element boundaries
                block_start = content.rfind('<', 0, element_start)
                block_end = content.find('</stream>', element_start)
                if block_end == -1:
                    block_end = content.find('>', element_start) + 1
                
                # Get element content and indentation
                element_content = content[block_start:block_end]
                indent_match = re.search(r'^\s+', element_content)
                child_indent = indent_match.group(0) if indent_match else '    '
                
                # Apply changes
                modified_content = self._modify_element_content(
                    element_content, 
                    changes, 
                    child_indent
                )
                
                # Replace in full content
                content = content[:block_start] + modified_content + content[block_end:]
        
        return content
    
    def _modify_element_content(self, content: str, changes: Dict[str, str], indent: str) -> str:
        """Modify individual element content with changes"""
        for field, new_value in changes.items():
            field_tag = f"<{field}>"
            field_start = content.find(field_tag)
            
            if field_start != -1:
                # Update existing field
                field_end = content.find(f"</{field}>", field_start)
                if field_end != -1:
                    old_content = content[field_start:field_end + len(f"</{field}>")]
                    new_content = f"<{field}>{new_value}</{field}>"
                    content = content.replace(old_content, new_content)
            else:
                # Add new field
                insert_pos = self._find_insert_position(content)
                new_field = f"\n{indent}<{field}>{new_value}</{field}>"
                content = content[:insert_pos] + new_field + content[insert_pos:]
        
        return content
    
    def _find_insert_position(self, content: str) -> int:
        """Find position to insert new field"""
        # Try to find last closing tag
        for tag in ['</shared>', '/>', '</stream>', '</sensorLocation>', 
                   '</station>', '</network>']:
            pos = content.rfind(tag)
            if pos != -1:
                return pos + len(tag)
        return len(content)
    
    def track_changes(self, element_id: str, changes: Dict[str, str]):
        """Track changes for an element"""
        if element_id not in self.modified_elements:
            self.modified_elements[element_id] = {}
        self.modified_elements[element_id].update(changes)
    
    def get_networks(self) -> List[ET.Element]:
        """Get all network elements"""
        if self.root is None:
            return []
        return self.root.findall('.//sc3:network', self.ns)
    
    def get_stations(self, network: ET.Element) -> List[ET.Element]:
        """Get all station elements for a network"""
        return network.findall('.//sc3:station', self.ns)
    
    def get_locations(self, station: ET.Element) -> List[ET.Element]:
        """Get all location elements for a station"""
        return station.findall('.//sc3:sensorLocation', self.ns)
    
    def get_streams(self, location: ET.Element) -> List[ET.Element]:
        """Get all stream elements for a location"""
        return location.findall('sc3:stream', self.ns)
    
    def get_sensors(self) -> List[ET.Element]:
        """Get all sensor elements"""
        if self.root is None:
            return []
        return self.root.findall('.//sc3:sensor', self.ns)
    
    def get_dataloggers(self) -> List[ET.Element]:
        """Get all datalogger elements"""
        if self.root is None:
            return []
        return self.root.findall('.//sc3:datalogger', self.ns)
    
    def get_element_text(self, element: ET.Element, tag: str, default: str = '') -> str:
        """Get element text with namespace"""
        elem = element.find(f'sc3:{tag}', self.ns)
        return elem.text if elem is not None and elem.text is not None else default
    
    def update_element_text(self, element: ET.Element, tag: str, value: str) -> bool:
        """Update element text and track changes"""
        if not element.get('publicID'):
            return False
            
        elem = element.find(f'sc3:{tag}', self.ns)
        current_value = elem.text if elem is not None else ''
        
        if value != current_value:
            if elem is None and value:
                elem = ET.SubElement(element, f'{{{self.ns["sc3"]}}}{tag}')
                elem.text = value
            elif elem is not None:
                if value:
                    elem.text = value
                else:
                    element.remove(elem)
                    
            self.track_changes(element.get('publicID'), {tag: value})
            return True
            
        return False

    def link_sensor_to_stream(self, stream: ET.Element, sensor: ET.Element) -> bool:
        """Link sensor to stream"""
        if not (stream.get('publicID') and sensor.get('publicID')):
            return False
            
        serial = self.get_element_text(sensor, 'serialNumber')
        if not serial:
            return False
            
        self.update_element_text(stream, 'sensorSerialNumber', serial)
        return True
        
    def link_datalogger_to_stream(self, stream: ET.Element, datalogger: ET.Element) -> bool:
        """Link datalogger to stream"""
        if not (stream.get('publicID') and datalogger.get('publicID')):
            return False
            
        serial = self.get_element_text(datalogger, 'serialNumber')
        if not serial:
            return False
            
        self.update_element_text(stream, 'dataloggerSerialNumber', serial)
        return True