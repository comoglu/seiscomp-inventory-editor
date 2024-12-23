#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys

def print_element_structure(element, level=0):
    """Print the complete structure of an XML element"""
    indent = "  " * level
    
    # Print current element
    print(f"{indent}<{element.tag}", end="")
    
    # Print attributes if any
    for key, value in element.attrib.items():
        print(f' {key}="{value}"', end="")
    print(">")
    
    # Print text content if any (and not just whitespace)
    if element.text and element.text.strip():
        print(f"{indent}  {element.text.strip()}")
    
    # Print all child elements
    for child in element:
        print_element_structure(child, level + 1)
    
    # Print closing tag
    print(f"{indent}</{element.tag}>")

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_xml_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        print_element_structure(root)
    except Exception as e:
        print(f"Error processing XML file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()