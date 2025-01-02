# core/xml_handler.py
from xml.etree import ElementTree as ET
from pathlib import Path
import re
from typing import Dict, Generator, Optional, Tuple, List
import logging
from .reference_manager import ReferenceManager

class XMLHandler:
    """Handles XML file operations for SeisComP inventory"""
    
    # Define supported schema versions and their namespaces
    SUPPORTED_SCHEMAS = {
        '0.10': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.10',
        '0.11': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.11',
        '0.12': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.12',
        '0.13': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.13'
    }
    
    def __init__(self):
        self.ref_manager = ReferenceManager()
        self.current_file: Optional[str] = None
        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self.modified_elements: Dict[str, Dict[str, str]] = {}
        self.logger = logging.getLogger('XMLHandler')
        
        # Initialize with default namespace
        self.ns = {'sc3': self.SUPPORTED_SCHEMAS['0.12']}
        self.schema_version = '0.12'
        
    def load_file(self, filename: str) -> Tuple[bool, str]:
        """
        Load and validate XML file
        
        Args:
            filename: Path to XML file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.tree = ET.parse(filename)
            self.root = self.tree.getroot()
            
            # Extract namespaces and validate structure
            if not self._validate_xml_structure(self.root):
                return False, "Invalid SeisComP inventory structure"
                
            self.current_file = filename
            self.modified_elements = {}
            
            # Register components for reference tracking
            self._register_components()
            
            return True, "File loaded successfully"
            
        except ET.ParseError as e:
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            self.logger.error(f"Error loading file: {str(e)}")
            return False, f"Error loading file: {str(e)}"

    def lazy_load_elements(self) -> Generator[ET.Element, None, None]:
        """Lazy load elements for large XML files"""
        if not self.root:
            return
            
        context = ET.iterparse(self.current_file, events=('end',))
        for event, elem in context:
            if elem.tag.endswith('}network'):
                yield elem
                elem.clear()

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

    def restore_backup(self) -> bool:
        """Restore from backup if available"""
        try:
            if self.current_file:
                current_path = Path(self.current_file)
                backup_path = current_path.with_suffix('.xml.bak')
                if backup_path.exists():
                    backup_path.rename(current_path)
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error restoring backup: {str(e)}")
            return False
                    
    def _extract_namespaces(self, root: ET.Element) -> None:
        """Extract and register namespaces from root element"""
        # Keep track of all found namespaces
        found_namespaces = {}
        
        # Look for schema namespace in root tag
        match = re.match(r'\{(.+?)\}', root.tag)
        if match:
            found_namespaces['root_tag'] = match.group(1)
        
        # Get namespaces from xmlns attributes
        for key, value in root.attrib.items():
            if key.startswith('xmlns:'):
                prefix = key.split(':')[1]
                found_namespaces[prefix] = value
            elif key == 'xmlns':
                found_namespaces['default'] = value
                
        # Try to find a matching supported schema
        for ns_value in found_namespaces.values():
            for version, schema_ns in self.SUPPORTED_SCHEMAS.items():
                if schema_ns in ns_value:
                    self.schema_version = version
                    self.ns = {'sc3': schema_ns}
                    return

    def _validate_xml_structure(self, root: ET.Element) -> bool:
        """Validate XML structure and detect schema version"""
        # Extract and set namespaces
        self._extract_namespaces(root)
        
        # Try with current namespace
        if self._check_inventory_exists(root):
            return True
            
        # Try all supported schemas
        for version, ns in self.SUPPORTED_SCHEMAS.items():
            test_ns = {'sc3': ns}
            if self._check_inventory_exists(root, test_ns):
                self.schema_version = version
                self.ns = test_ns
                return True
                
        return False
        
    def _check_inventory_exists(self, root: ET.Element, namespace: Optional[Dict] = None) -> bool:
        """Check if inventory element exists using given namespace"""
        ns = namespace if namespace is not None else self.ns
        try:
            inventory = root.find('sc3:Inventory', ns)
            return inventory is not None
        except ET.ParseError:
            return False

    def _apply_changes(self, content: str) -> str:
        """Apply tracked changes to XML content"""
        for element_id, changes in self.modified_elements.items():
            element_start = content.find(f'publicID="{element_id}"')
            if element_start != -1:
                # Find element boundaries
                block_start = content.rfind('<', 0, element_start)
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
        for field, value in changes.items():
            field_tag = f"<{field}>"
            field_start = content.find(field_tag)
            
            if field_start != -1:
                # Update existing field
                field_end = content.find(f"</{field}>", field_start)
                if field_end != -1:
                    old_content = content[field_start:field_end + len(f"</{field}>")]
                    new_content = f"<{field}>{value}</{field}>"
                    content = content.replace(old_content, new_content)
            else:
                # Add new field
                insert_pos = self._find_insert_position(content)
                new_field = f"\n{indent}<{field}>{value}</{field}>"
                content = content[:insert_pos] + new_field + content[insert_pos:]
        
        return content
    
    def _find_insert_position(self, content: str) -> int:
        """Find position to insert new field"""
        for tag in ['</shared>', '/>', '</stream>', '</sensorLocation>', 
                   '</station>', '</network>']:
            pos = content.rfind(tag)
            if pos != -1:
                return pos
        return len(content)

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
        try:
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
        except Exception as e:
            self.logger.error(f"Error updating element text for tag {tag}: {str(e)}")
            return False

    def track_changes(self, element_id: str, changes: Dict[str, str]) -> None:
        """Track changes for an element"""
        if element_id not in self.modified_elements:
            self.modified_elements[element_id] = {}
        self.modified_elements[element_id].update(changes)

    def _register_components(self) -> None:
        """Register all sensors and dataloggers"""
        try:
            # Register sensors
            for sensor in self.get_sensors():
                serial = self.get_element_text(sensor, 'serialNumber')
                if serial:  # Only register if has serial number
                    self.ref_manager.register_component(sensor, 'sensor')
                else:
                    self.logger.debug(f"Sensor without serial number: {sensor.get('name', '')}")
                    
            # Register dataloggers
            for datalogger in self.get_dataloggers():
                serial = self.get_element_text(datalogger, 'serialNumber')
                if serial:  # Only register if has serial number
                    self.ref_manager.register_component(datalogger, 'datalogger')
                else:
                    self.logger.debug(f"Datalogger without serial number: {datalogger.get('name', '')}")
                    
        except Exception as e:
            self.logger.error(f"Error registering components: {str(e)}")

    def link_sensor_to_stream(self, stream: ET.Element, sensor: ET.Element) -> bool:
        """Link sensor to stream"""
        try:
            if not sensor.get('publicID'):
                return False
                
            serial = self.get_element_text(sensor, 'serialNumber')
            if not serial:
                return False
                
            return self.update_element_text(stream, 'sensorSerialNumber', serial)
            
        except Exception as e:
            self.logger.error(f"Error linking sensor to stream: {str(e)}")
            return False
        
    def link_datalogger_to_stream(self, stream: ET.Element, datalogger: ET.Element) -> bool:
        """Link datalogger to stream"""
        try:
            if not datalogger.get('publicID'):
                return False
                
            serial = self.get_element_text(datalogger, 'serialNumber')
            if not serial:
                return False
                
            return self.update_element_text(stream, 'dataloggerSerialNumber', serial)
            
        except Exception as e:
            self.logger.error(f"Error linking datalogger to stream: {str(e)}")
            return False
