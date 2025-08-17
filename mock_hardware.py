"""
Mock hardware module for Windows development
Simulates Raspberry Pi GPIO and SPI functionality
"""

import random
import time

class MockGPIO:
    """Mock GPIO class for Windows development"""
    BCM = "BCM"
    OUT = "OUT"
    LOW = 0
    HIGH = 1
    
    @staticmethod
    def setmode(mode):
        print(f"Mock GPIO: Set mode to {mode}")
    
    @staticmethod
    def setup(pins, mode):
        if isinstance(pins, list):
            for pin in pins:
                print(f"Mock GPIO: Setup pin {pin} as {mode}")
        else:
            print(f"Mock GPIO: Setup pin {pins} as {mode}")
    
    @staticmethod
    def output(pins, value):
        if isinstance(pins, list):
            for pin in pins:
                print(f"Mock GPIO: Set pin {pin} to {value}")
        else:
            print(f"Mock GPIO: Set pin {pins} to {value}")
    
    @staticmethod
    def cleanup():
        print("Mock GPIO: Cleanup completed")

class MockSpiDevModule:
    """Mock SPI module for Windows development"""
    
    def __init__(self):
        self.max_speed_hz = 1000000
        self.mock_data = 0
    
    def open(self, bus, device):
        print(f"Mock SPI: Opened bus {bus}, device {device}")
    
    def xfer2(self, data):
        # Simulate ADC reading with some variation
        self.mock_data = (self.mock_data + random.randint(0, 100)) % 1024
        return [1, (self.mock_data >> 8) & 0xFF, self.mock_data & 0xFF]

# Create SpiDev class for compatibility
class SpiDev:
    """Mock SpiDev class for Windows development"""
    
    def __init__(self):
        self.max_speed_hz = 1000000
        self.mock_data = 0
    
    def open(self, bus, device):
        print(f"Mock SPI: Opened bus {bus}, device {device}")
    
    def xfer2(self, data):
        # Simulate ADC reading with some variation
        self.mock_data = (self.mock_data + random.randint(0, 100)) % 1024
        return [1, (self.mock_data >> 8) & 0xFF, self.mock_data & 0xFF]

# Add SpiDev to the module
MockSpiDevModule.SpiDev = SpiDev
