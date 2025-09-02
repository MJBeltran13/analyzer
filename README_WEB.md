# Antenna Analyzer - Web Interface

A modern web-based interface for the Antenna Analyzer, providing the same functionality as the desktop version but accessible through any web browser.

## Features

- 🌐 **Web-based Interface**: Access from any device with a web browser
- 📡 **Real-time Testing**: Perform frequency sweeps and get instant results
- 📊 **Interactive Plots**: View SWR analysis with beautiful charts
- 💾 **Save & Load**: Save test results and load previous measurements
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🖥️ **Demo Mode**: Test the interface without real hardware

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_web.txt
```

### 2. Run the Web Server

**Option A: Using the batch file (Windows)**
```bash
run_web_analyzer.bat
```

**Option B: Direct Python command**
```bash
python web_analyzer.py
```

### 3. Access the Interface

Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

### Basic Testing

1. **Set Parameters**:
   - Start Frequency (MHz): Beginning of the frequency range
   - Stop Frequency (MHz): End of the frequency range
   - Measurement Points: Number of measurements (10-1000)

2. **Run Tests**:
   - **Start Sweep**: Run a custom frequency sweep
   - **Quick Test**: Run a predefined test (10-20 MHz, 25 points)

3. **View Results**:
   - Rating and score display
   - Detailed analysis
   - SWR plot visualization

### Advanced Features

- **Save Results**: Save test data to JSON files
- **Load History**: View and load previous test results
- **Clear Results**: Reset the interface for new tests

## File Structure

```
analyzer/
├── web_analyzer.py          # Main Flask application
├── templates/
│   └── index.html          # Web interface template
├── static/
│   ├── css/
│   │   └── style.css       # Styles (if using external CSS)
│   └── js/
│       └── app.js          # JavaScript functionality
├── requirements_web.txt    # Python dependencies
├── run_web_analyzer.bat    # Windows launcher
└── README_WEB.md          # This file
```

## API Endpoints

The web interface communicates with the backend through REST API endpoints:

- `POST /api/sweep` - Perform frequency sweep
- `POST /api/quick-test` - Run quick test
- `POST /api/save` - Save test results
- `GET /api/history` - Get test history
- `GET /api/load/<filename>` - Load specific test
- `GET /api/delete/<filename>` - Delete test file

## Hardware Support

### Demo Mode (Default)
- Runs without real hardware
- Simulates realistic antenna responses
- Perfect for testing and demonstration

### Real Hardware Mode
- Requires Raspberry Pi with GPIO connections
- Install additional dependencies: `pip install RPi.GPIO spidev`
- Connect antenna analyzer hardware

## Browser Compatibility

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

## Troubleshooting

### Server Won't Start
- Check if port 5000 is available
- Ensure all dependencies are installed
- Verify Python 3.6+ is installed

### Can't Access Web Interface
- Check if server is running on correct port
- Try accessing `http://127.0.0.1:5000` instead
- Check firewall settings

### Test Results Not Loading
- Ensure mock_hardware.py is in the same directory
- Check browser console for JavaScript errors
- Verify network connectivity

## Development

### Adding New Features
1. Modify `web_analyzer.py` for backend changes
2. Update `templates/index.html` for UI changes
3. Edit `static/js/app.js` for frontend functionality

### Customizing Styles
- Edit the CSS in `templates/index.html`
- Or create external CSS files in `static/css/`

### Extending API
- Add new routes in `web_analyzer.py`
- Update JavaScript functions in `app.js`
- Test with browser developer tools

## Security Notes

- The web interface is designed for local network use
- No authentication is implemented
- Don't expose to public internet without proper security measures

## Performance Tips

- Use fewer measurement points for faster tests
- Close other applications to free up system resources
- Use modern browsers for best performance

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the desktop version documentation
3. Check browser console for error messages
4. Verify all dependencies are correctly installed

---

**Note**: This web interface provides the same core functionality as the desktop version but with the convenience of web access. It's perfect for remote monitoring, mobile access, and integration with other web-based systems.

