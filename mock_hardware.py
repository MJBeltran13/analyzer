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

  class MockADS1115:
    """Mock ADS1115 I2C ADC for Windows development"""
    
    # Mock pin constants
    P0 = 0
    P1 = 1
    P2 = 2
    P3 = 3
    
    def __init__(self, i2c):
        print("Mock ADS1115: Initialized I2C ADC")
        self.i2c = i2c
    
    class AnalogIn:
        """Mock AnalogIn for ADS1115 channels"""
        def __init__(self, ads, pin):
            self.ads = ads
            self.pin = pin
            print(f"Mock ADS1115: Setup channel {pin}")
        
        @property
        def voltage(self):
            # Return mock voltage reading with some variation
            base_voltage = 1.5 + random.uniform(-0.5, 0.5)
            return max(0.0, min(3.3, base_voltage))
    
    class board:
        """Mock board for I2C pins"""
        SCL = "SCL"
        SDA = "SDA"
    
    class busio:
        """Mock busio for I2C"""
        @staticmethod
        def I2C(scl, sda):
            print(f"Mock I2C: Setup on {scl}/{sda}")
            return "mock_i2c"