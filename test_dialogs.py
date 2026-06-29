#!/usr/bin/env python3
"""Test the migration confirmation dialogs"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Migration Dialog Test")
        self.setGeometry(100, 100, 300, 200)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Buttons
        btn_upgrade = QPushButton("Test Database Upgrade Dialog")
        btn_upgrade.clicked.connect(self.test_upgrade_dialog)
        layout.addWidget(btn_upgrade)
        
        btn_version = QPushButton("Test Version Update Dialog")
        btn_version.clicked.connect(self.test_version_dialog)
        layout.addWidget(btn_version)
    
    def test_upgrade_dialog(self):
        """Test the database upgrade confirmation dialog"""
        result = self.show_database_upgrade_confirmation("1.6.0", "1.7.0")
        print(f"Upgrade dialog result: {result}")
    
    def test_version_dialog(self):
        """Test the version update warning dialog"""
        result = self.show_version_update_message("1.6.0", "1.7.0")
        print(f"Version dialog result: {result}")
    
    def show_database_upgrade_confirmation(self, from_version, to_version):
        """Show a properly styled database upgrade confirmation dialog"""
        try:
            # Create the message box with proper parent
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Database Upgrade Required")
            msg_box.setIcon(QMessageBox.Information)
            
            # Set the main text
            msg_box.setText(f"Database Upgrade to v{to_version}")
            
            # Set detailed information
            detailed_text = (
                f"Your database will be upgraded from v{from_version} to v{to_version}.\n\n"
                f"This upgrade will:\n"
                f"• Add multi-race monitoring capabilities\n"
                f"• Create new Sessions and SessionParticipants tables\n"
                f"• Add performance indexes for better speed\n"
                f"• Preserve all existing race data\n\n"
                f"The upgrade process includes automatic verification and repair tools.\n\n"
                f"Do you want to proceed with the database upgrade?"
            )
            msg_box.setInformativeText(detailed_text)
            
            # Set buttons
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            
            # Apply styling to prevent black background
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMessageBox QLabel {
                    color: #000000;
                    background-color: transparent;
                }
                QMessageBox QPushButton {
                    background-color: #e1e1e1;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #d4edda;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #c3e6cb;
                }
            """)
            
            # Set a reasonable font
            font = QFont()
            font.setPointSize(9)
            msg_box.setFont(font)
            
            # Show the dialog and get response
            response = msg_box.exec_()
            
            return response == QMessageBox.Yes
            
        except Exception as e:
            print(f"Failed to show upgrade confirmation: {e}")
            return True
    
    def show_version_update_message(self, existing_version, new_version):
        """Show version update confirmation dialog with proper styling"""
        try:
            # Create the message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Version Update Warning")
            msg_box.setIcon(QMessageBox.Warning)
            
            # Set the main text
            msg_box.setText(f"Version {new_version} Update Warning")
            
            # Set detailed information
            detailed_text = (
                f"WARNING: Version {new_version} will delete existing Race Data!\n\n"
                f"Your current version: {existing_version}\n"
                f"New version: {new_version}\n\n"
                f"This operation cannot be undone.\n\n"
                f"Do you want to proceed and delete existing data?"
            )
            msg_box.setInformativeText(detailed_text)
            
            # Set buttons
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Cancel)  # Default to safer option
            
            # Apply styling to prevent black background
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMessageBox QLabel {
                    color: #000000;
                    background-color: transparent;
                }
                QMessageBox QPushButton {
                    background-color: #e1e1e1;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #f8d7da;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #f5c6cb;
                }
            """)
            
            # Set a reasonable font
            font = QFont()
            font.setPointSize(9)
            msg_box.setFont(font)

            # Show the message box and get the response
            response = msg_box.exec_()

            return response == QMessageBox.Ok
            
        except Exception as e:
            print(f"Failed to show version update dialog: {e}")
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
