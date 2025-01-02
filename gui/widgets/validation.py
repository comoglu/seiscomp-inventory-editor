from PyQt5.QtWidgets import QLineEdit
from typing import Optional, Callable, Union
from core.datetime_validation import DateTimeValidator

class ValidationLineEdit(QLineEdit):
    """Line edit with validation and styling"""
    
    def __init__(self, 
                 validator: Optional[Union[Callable[[str], bool], str]] = None,
                 required: bool = False,
                 parent: Optional[QLineEdit] = None):
        super().__init__(parent)
        self.validator_type = None
        self.required = required
        
        # Handle datetime validator specially
        if isinstance(validator, str) and validator == 'datetime':
            self.validator = DateTimeValidator.validate
            self.validator_type = 'datetime'
        else:
            self.validator = validator
            
        # Connect signals
        self.textChanged.connect(self.validate)
        self.editingFinished.connect(self.on_editing_finished)
        self.apply_default_style()
        
    def validate(self) -> bool:
        """Validate current text and handle datetime conversion"""
        text = self.text().strip()
        
        # Check required field
        if not text and self.required:
            self.apply_error_style()
            return False
            
        # Skip validation if empty and not required
        if not text and not self.required:
            self.apply_default_style()
            return True
            
        # Handle validation
        if self.validator:
            try:
                if not self.validator(text):
                    self.apply_error_style()
                    return False
                    
                # Handle datetime conversion
                if self.validator_type == 'datetime' and text:
                    converted = DateTimeValidator.convert_to_seiscomp_format(text)
                    if converted and converted != text:
                        # Block signals to prevent recursive validation
                        self.blockSignals(True)
                        self.setText(converted)
                        self.blockSignals(False)
            except Exception as e:
                print(f"Validation error: {str(e)}")  # Debug logging
                self.apply_error_style()
                return False
                
        self.apply_default_style()
        return True
        
    def apply_default_style(self):
        """Apply default styling"""
        self.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #66afe9;
            }
        """)
        
    def apply_error_style(self):
        """Apply error styling"""
        self.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #d9534f;
                border-radius: 3px;
                background-color: #ffe6e6;
            }
            QLineEdit:focus {
                border-color: #d43f3a;
            }
        """)
        
    def on_editing_finished(self):
        """Handle editing finished event"""
        if self.parent() and hasattr(self.parent(), 'handle_editing_finished'):
            self.parent().handle_editing_finished()
            
    def validate_and_get(self) -> tuple[bool, str]:
        """Validate and return current text"""
        is_valid = self.validate()
        return is_valid, self.text().strip()