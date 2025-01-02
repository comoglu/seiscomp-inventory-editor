# core/reference_manager.py
from typing import Dict, Set, Optional, List
from xml.etree import ElementTree as ET
import logging
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class ReferenceMapping:
    """Class to store reference information"""
    public_id: str
    serial_number: str
    type: str  # 'sensor' or 'datalogger'
    name: str
    streams: Set[str]  # Set of stream public_ids that reference this component

class ReferenceManager:
    """Manages component references and namespaces for SeisComP inventory"""
    
    def __init__(self):
        self.references: Dict[str, ReferenceMapping] = {}  # publicID -> ReferenceMapping
        self.serial_map: Dict[str, str] = {}  # serial -> publicID
        self.namespaces: Dict[str, str] = {
            'sc3': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.12'
        }
        self.logger = logging.getLogger('ReferenceManager')

    def add_namespace(self, prefix: str, uri: str):
        """Add a new namespace"""
        self.namespaces[prefix] = uri

    def get_namespace(self, prefix: str) -> Optional[str]:
        """Get namespace URI by prefix"""
        return self.namespaces.get(prefix)

    def register_component(self, element: ET.Element, component_type: str) -> bool:
        """Register a sensor or datalogger component"""
        try:
            public_id = element.get('publicID')
            if not public_id:
                self.logger.error(f"Component missing publicID: {element}")
                return False

            # Find serial number using any available namespace
            serial = None
            for prefix, uri in self.namespaces.items():
                serial_elem = element.find(f'{prefix}:serialNumber', self.namespaces)
                if serial_elem is not None and serial_elem.text:
                    serial = serial_elem.text
                    break

            if not serial:
                self.logger.error(f"Component missing serial number: {public_id}")
                return False

            name = element.get('name', '')

            # Create new reference mapping
            ref_mapping = ReferenceMapping(
                public_id=public_id,
                serial_number=serial,
                type=component_type,
                name=name,
                streams=set()
            )

            # Update mappings
            self.references[public_id] = ref_mapping
            self.serial_map[serial] = public_id

            self.logger.info(f"Registered {component_type}: {serial} -> {public_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering component: {str(e)}")
            return False

    def update_component_serial(self, public_id: str, new_serial: str) -> bool:
        """Update serial number for a component"""
        try:
            if public_id not in self.references:
                return False

            old_ref = self.references[public_id]
            old_serial = old_ref.serial_number

            # Update serial in reference mapping
            old_ref.serial_number = new_serial
            
            # Update serial map
            if old_serial in self.serial_map:
                del self.serial_map[old_serial]
            self.serial_map[new_serial] = public_id

            # Update all related streams
            self._update_stream_references(old_ref)

            return True

        except Exception as e:
            self.logger.error(f"Error updating serial: {str(e)}")
            return False

    def _update_stream_references(self, ref_mapping: ReferenceMapping):
        """Update all streams that reference this component"""
        for stream_id in ref_mapping.streams:
            try:
                # Find stream element and update reference
                # This requires access to XML - could be passed in or stored
                pass
            except Exception as e:
                self.logger.error(f"Error updating stream reference: {str(e)}")

    def link_stream(self, stream: ET.Element, component_public_id: str) -> bool:
        """Link a stream to a component"""
        try:
            stream_id = stream.get('publicID')
            if not stream_id or component_public_id not in self.references:
                return False

            ref = self.references[component_public_id]
            ref.streams.add(stream_id)

            # Update stream element with serial reference
            serial_tag = ('sensorSerialNumber' if ref.type == 'sensor' 
                         else 'dataloggerSerialNumber')
            
            # Try to find/create serial number element using available namespaces
            serial_elem = None
            for prefix in self.namespaces:
                serial_elem = stream.find(f'{prefix}:{serial_tag}', self.namespaces)
                if serial_elem is not None:
                    break

            if serial_elem is None:
                # Create new element using default namespace
                serial_elem = ET.SubElement(stream, 
                                         f'{{{self.namespaces["sc3"]}}}{serial_tag}')

            serial_elem.text = ref.serial_number
            return True

        except Exception as e:
            self.logger.error(f"Error linking stream: {str(e)}")
            return False

    def save_state(self, filepath: Path):
        """Save reference state to file"""
        try:
            state = {
                'references': {
                    pid: {
                        'serial_number': ref.serial_number,
                        'type': ref.type,
                        'name': ref.name,
                        'streams': list(ref.streams)
                    }
                    for pid, ref in self.references.items()
                },
                'serial_map': self.serial_map,
                'namespaces': self.namespaces
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving state: {str(e)}")

    def load_state(self, filepath: Path):
        """Load reference state from file"""
        try:
            with open(filepath) as f:
                state = json.load(f)

            self.references = {
                pid: ReferenceMapping(
                    public_id=pid,
                    serial_number=data['serial_number'],
                    type=data['type'],
                    name=data['name'],
                    streams=set(data['streams'])
                )
                for pid, data in state['references'].items()
            }
            
            self.serial_map = state['serial_map']
            self.namespaces = state['namespaces']

        except Exception as e:
            self.logger.error(f"Error loading state: {str(e)}")
