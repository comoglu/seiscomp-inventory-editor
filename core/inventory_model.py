# core/inventory_model.py
from xml.etree import ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class StreamData:
    code: str
    start: str = ''
    end: str = ''
    depth: str = ''
    azimuth: str = ''
    dip: str = ''
    gain: str = ''
    sampleRate: str = ''
    gainFrequency: str = ''
    gainUnit: str = ''
    sensor_serialnumber: str = ''
    datalogger_serialnumber: str = ''
    flags: str = ''
    sampleRateNumerator: str = ''
    sampleRateDenominator: str = ''
    sensor_ref: str = ''
    datalogger_ref: str = ''

@dataclass
class SensorData:
    name: str
    type: str = ''
    model: str = ''
    manufacturer: str = ''
    serialNumber: str = ''
    response: str = ''
    unit: str = ''
    lowFrequency: str = ''
    highFrequency: str = ''
    calibrationDate: str = ''
    calibrationScale: str = ''

@dataclass
class DataloggerData:
    name: str
    type: str = ''
    model: str = ''
    manufacturer: str = ''
    serialNumber: str = ''
    description: str = ''
    maxClockDrift: str = ''
    recordLength: str = ''
    sampleRate: str = ''
    sampleRateMultiplier: str = ''

@dataclass
class NetworkData:
    code: str
    start: str = ''
    end: str = ''
    description: str = ''
    institutions: str = ''
    region: str = ''
    type: str = ''
    netClass: str = ''
    archive: str = ''
    restricted: str = ''
    shared: str = ''

@dataclass
class StationData:
    code: str
    name: str = ''
    description: str = ''
    start: str = ''
    end: str = ''
    latitude: str = ''
    longitude: str = ''
    elevation: str = ''
    depth: str = ''
    place: str = ''
    country: str = ''
    affiliation: str = ''

@dataclass
class LocationData:
    code: str
    start: str = ''
    end: str = ''
    latitude: str = ''
    longitude: str = ''
    elevation: str = ''
    depth: str = ''
    country: str = ''
    description: str = ''
    affiliation: str = ''

class InventoryModel:
    """Manages inventory data and relationships"""
    
    def __init__(self, xml_handler):
        self.xml_handler = xml_handler
        self.sensor_map = {}  # serial -> element
        self.datalogger_map = {}  # serial -> element
        self.ns = {'sc3': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.12'}

        
    def load_inventory(self) -> None:
        """Load sensor and datalogger mappings"""
        self.sensor_map.clear()
        self.datalogger_map.clear()
        
        # Map sensors by their serial numbers
        for sensor in self.get_sensors():
            name = sensor.get('name', '')
            if name:
                self.sensor_map[name] = sensor
                
        # Map dataloggers by their serial numbers
        for datalogger in self.get_dataloggers():
            name = datalogger.get('name', '')
            if name:
                self.datalogger_map[name] = datalogger

    def get_location_data(self, element: ET.Element) -> LocationData:
        """Extract location data from element"""
        return LocationData(
            code=element.get('code', ''),
            start=self.xml_handler.get_element_text(element, 'start'),
            end=self.xml_handler.get_element_text(element, 'end'),
            latitude=self.xml_handler.get_element_text(element, 'latitude'),
            longitude=self.xml_handler.get_element_text(element, 'longitude'),
            elevation=self.xml_handler.get_element_text(element, 'elevation'),
            depth=self.xml_handler.get_element_text(element, 'depth'),
            country=self.xml_handler.get_element_text(element, 'country'),
            description=self.xml_handler.get_element_text(element, 'description'),
            affiliation=self.xml_handler.get_element_text(element, 'affiliation')
        )
    
    def update_location(self, element: ET.Element, data: Dict[str, str]) -> bool:
        """Update location element with data"""
        if data['code']:
            element.set('code', data['code'])
        
        updated = False
        fields = {
            'start': data['start'],
            'end': data['end'],
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'elevation': data['elevation'],
            'depth': data['depth'],
            'country': data['country'],
            'description': data['description'],
            'affiliation': data['affiliation']
        }
        
        for field, value in fields.items():
            if self.xml_handler.update_element_text(element, field, value):
                updated = True
        
        return updated


    def get_sensors(self) -> List[ET.Element]:
        """Get all sensor elements"""
        if not self.xml_handler.root:
            return []
        return self.xml_handler.get_sensors()
    
    def get_dataloggers(self) -> List[ET.Element]:
        """Get all datalogger elements"""
        if not self.xml_handler.root:
            return []
        return self.xml_handler.get_dataloggers()
    
    def get_stream_data(self, element: ET.Element) -> StreamData:
        datalogger_ref = element.get('datalogger', '')
        sensor_ref = element.get('sensor', '')
        """Extract stream data from element"""
        return StreamData(
            code=element.get('code', ''),
            start=self.xml_handler.get_element_text(element, 'start'),
            end=self.xml_handler.get_element_text(element, 'end'),
            depth=self.xml_handler.get_element_text(element, 'depth'),
            azimuth=self.xml_handler.get_element_text(element, 'azimuth'),
            dip=self.xml_handler.get_element_text(element, 'dip'),
            gain=self.xml_handler.get_element_text(element, 'gain'),
            gainFrequency=self.xml_handler.get_element_text(element, 'gainFrequency'),
            gainUnit=self.xml_handler.get_element_text(element, 'gainUnit'),
            sampleRate=self.xml_handler.get_element_text(element, 'sampleRate'),
            sampleRateNumerator=self.xml_handler.get_element_text(element, 'sampleRateNumerator'),
            sampleRateDenominator=self.xml_handler.get_element_text(element, 'sampleRateDenominator'),
            sensor_ref=sensor_ref,
            datalogger_ref=datalogger_ref,
            flags=self.xml_handler.get_element_text(element, 'flags')
        )

    def get_sensor_by_serial(self, serial: str) -> Optional[ET.Element]:
        """Get sensor element by serial number"""
        return self.sensor_map.get(serial)

    def get_datalogger_by_serial(self, serial: str) -> Optional[ET.Element]:
        """Get datalogger element by serial number"""
        return self.datalogger_map.get(serial)


    def update_stream(self, element: ET.Element, data: Dict[str, str]) -> bool:
        """Update stream element with data"""
        if data['code']:
            element.set('code', data['code'])
        
        updated = False
        fields = {
            'start': data['start'],
            'end': data['end'],
            'depth': data['depth'],
            'azimuth': data['azimuth'],
            'dip': data['dip'],
            'gain': data['gain'],
            'sampleRate': data['sampleRate'],
            'gainFrequency': data['gainFrequency'],
            'gainUnit': data['gainUnit'],
            'sensorSerialNumber': data['sensor_serialnumber'],
            'dataloggerSerialNumber': data['datalogger_serialnumber'],
            'flags': data['flags']
        }
        
        for field, value in fields.items():
            if self.xml_handler.update_element_text(element, field, value):
                updated = True
        
        return updated
    
    def get_sensor_data(self, element: ET.Element) -> SensorData:
        """Extract sensor data from element"""
        data = SensorData(
            name=element.get('name', ''),
            type=self.xml_handler.get_element_text(element, 'type'),
            model=self.xml_handler.get_element_text(element, 'model'),
            manufacturer=self.xml_handler.get_element_text(element, 'manufacturer'),
            serialNumber=self.xml_handler.get_element_text(element, 'serialNumber'),
            response=self.xml_handler.get_element_text(element, 'response'),
            unit=self.xml_handler.get_element_text(element, 'unit'),
            lowFrequency=self.xml_handler.get_element_text(element, 'lowFrequency'),
            highFrequency=self.xml_handler.get_element_text(element, 'highFrequency'),
            calibrationDate=self.xml_handler.get_element_text(element, 'calibrationDate'),
            calibrationScale=self.xml_handler.get_element_text(element, 'calibrationScale')
        )
        return data

    
    def update_sensor(self, element: ET.Element, data: Dict[str, str]) -> bool:
        """Update sensor element with data"""
        if data['name']:
            element.set('name', data['name'])
        
        updated = False
        fields = {
            'type': data['type'],
            'model': data['model'],
            'manufacturer': data['manufacturer'],
            'serialNumber': data['serialNumber'],
            'response': data['response'],
            'unit': data['unit'],
            'lowFrequency': data['lowFrequency'],
            'highFrequency': data['highFrequency'],
            'calibrationDate': data['calibrationDate'],
            'calibrationScale': data['calibrationScale']
        }
        
        for field, value in fields.items():
            if self.xml_handler.update_element_text(element, field, value):
                updated = True
        
        # Update sensor mapping if serial number changed
        if data['serialNumber']:
            self.sensor_map[data['serialNumber']] = element
        
        return updated
    
    def get_datalogger_data(self, element: ET.Element) -> DataloggerData:
        """Extract datalogger data from element"""
        data = DataloggerData(
            name=element.get('name', ''),
            type=self.xml_handler.get_element_text(element, 'type'),
            model=self.xml_handler.get_element_text(element, 'model'),
            manufacturer=self.xml_handler.get_element_text(element, 'manufacturer'),
            serialNumber=self.xml_handler.get_element_text(element, 'serialNumber'),
            description=self.xml_handler.get_element_text(element, 'description'),
            maxClockDrift=self.xml_handler.get_element_text(element, 'maxClockDrift'),
            recordLength=self.xml_handler.get_element_text(element, 'recordLength'),
            sampleRate=self.xml_handler.get_element_text(element, 'sampleRate'),
            sampleRateMultiplier=self.xml_handler.get_element_text(element, 'sampleRateMultiplier')
        )
        return data
    
    def update_datalogger(self, element: ET.Element, data: Dict[str, str]) -> bool:
        """Update datalogger element with data"""
        if data['name']:
            element.set('name', data['name'])
        
        updated = False
        fields = {
            'type': data['type'],
            'model': data['model'],
            'manufacturer': data['manufacturer'],
            'serialNumber': data['serialNumber'],
            'description': data['description'],
            'maxClockDrift': data['maxClockDrift'],
            'recordLength': data['recordLength'],
            'sampleRate': data['sampleRate'],
            'sampleRateMultiplier': data['sampleRateMultiplier']
        }
        
        for field, value in fields.items():
            if self.xml_handler.update_element_text(element, field, value):
                updated = True
        
        # Update datalogger mapping if serial number changed
        if data['serialNumber']:
            self.datalogger_map[data['serialNumber']] = element
        
        return updated
    
    def get_network_data(self, element: ET.Element) -> NetworkData:
        """Extract network data from element"""
        return NetworkData(
            code=element.get('code', ''),
            start=self.xml_handler.get_element_text(element, 'start'),
            end=self.xml_handler.get_element_text(element, 'end'),
            description=self.xml_handler.get_element_text(element, 'description'),
            institutions=self.xml_handler.get_element_text(element, 'institutions'),
            region=self.xml_handler.get_element_text(element, 'region'),
            type=self.xml_handler.get_element_text(element, 'type'),
            netClass=self.xml_handler.get_element_text(element, 'netClass'),
            archive=self.xml_handler.get_element_text(element, 'archive'),
            restricted=self.xml_handler.get_element_text(element, 'restricted'),
            shared=self.xml_handler.get_element_text(element, 'shared')
        )
    
    def update_network(self, element: ET.Element, data: Dict[str, str]) -> bool:
        """Update network element with data"""
        if data['code']:
            element.set('code', data['code'])
        
        updated = False
        fields = {
            'start': data['start'],
            'end': data['end'],
            'description': data['description'],
            'institutions': data['institutions'],
            'region': data['region'],
            'type': data['type'],
            'netClass': data['netClass'],
            'archive': data['archive'],
            'restricted': data['restricted'],
            'shared': data['shared']
        }
        
        for field, value in fields.items():
            if self.xml_handler.update_element_text(element, field, value):
                updated = True
        
        return updated
    
    def get_station_data(self, element: ET.Element) -> StationData:
        """Extract station data from element"""
        return StationData(
            code=element.get('code', ''),
            name=element.get('name', ''),
            description=self.xml_handler.get_element_text(element, 'description'),
            start=self.xml_handler.get_element_text(element, 'start'),
            end=self.xml_handler.get_element_text(element, 'end'),
            latitude=self.xml_handler.get_element_text(element, 'latitude'),
            longitude=self.xml_handler.get_element_text(element, 'longitude'),
            elevation=self.xml_handler.get_element_text(element, 'elevation'),
            depth=self.xml_handler.get_element_text(element, 'depth'),
            place=self.xml_handler.get_element_text(element, 'place'),
            country=self.xml_handler.get_element_text(element, 'country'),
            affiliation=self.xml_handler.get_element_text(element, 'affiliation')
        )
    
    def update_station(self, element: ET.Element, data: Dict[str, str]) -> bool:
        """Update station element with data"""
        if data['code']:
            element.set('code', data['code'])
        if data['name']:
            element.set('name', data['name'])
        elif 'name' in element.attrib:
            del element.attrib['name']
        
        updated = False
        fields = {
            'description': data['description'],
            'start': data['start'],
            'end': data['end'],
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'elevation': data['elevation'],
            'depth': data['depth'],
            'place': data['place'],
            'country': data['country'],
            'affiliation': data['affiliation']
        }
        
        for field, value in fields.items():
            if self.xml_handler.update_element_text(element, field, value):
                updated = True
        
        return updated