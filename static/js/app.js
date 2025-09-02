// Antenna Analyzer Web Interface JavaScript

class AntennaAnalyzer {
    constructor() {
        this.currentResults = null;
        this.init();
    }

    init() {
        // Initialize the interface
        console.log('Antenna Analyzer Web Interface initialized');
    }

    async performSweep() {
        const startFreq = document.getElementById('startFreq').value;
        const stopFreq = document.getElementById('stopFreq').value;
        const points = document.getElementById('points').value;
        
        // Validate inputs
        if (!this.validateInputs(startFreq, stopFreq, points)) {
            return;
        }

        // Show loading state
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/sweep', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start_freq: parseFloat(startFreq),
                    stop_freq: parseFloat(stopFreq),
                    points: parseInt(points)
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.displayResults(data);
                this.currentResults = data;
            } else {
                this.showError('Error: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async quickTest() {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/quick-test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.displayResults(data);
                this.currentResults = data;
                
                // Update form fields with quick test parameters
                if (data.parameters) {
                    document.getElementById('startFreq').value = data.parameters.start_freq;
                    document.getElementById('stopFreq').value = data.parameters.stop_freq;
                    document.getElementById('points').value = data.parameters.points;
                }
            } else {
                this.showError('Error: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    validateInputs(startFreq, stopFreq, points) {
        const start = parseFloat(startFreq);
        const stop = parseFloat(stopFreq);
        const pts = parseInt(points);

        if (isNaN(start) || isNaN(stop) || isNaN(pts)) {
            this.showError('Please enter valid numbers for all fields');
            return false;
        }

        if (start >= stop) {
            this.showError('Start frequency must be less than stop frequency');
            return false;
        }

        if (pts < 10 || pts > 1000) {
            this.showError('Points must be between 10 and 1000');
            return false;
        }

        return true;
    }

    displayResults(data) {
        const resultsContent = document.getElementById('resultsContent');
        const plotImage = document.getElementById('plotImage');
        
        // Display results
        const rating = data.rating;
        const score = rating.score;
        
        // Determine rating color
        let ratingColor = '#ef4444'; // red
        if (score >= 80) ratingColor = '#22c55e'; // green
        else if (score >= 60) ratingColor = '#f59e0b'; // orange
        
        resultsContent.innerHTML = `
            <div style="margin-bottom: 15px;">
                <h4 style="color: ${ratingColor}; margin-bottom: 5px;">
                    Rating: ${rating.rating} (${score.toFixed(0)}/100)
                </h4>
                <p><strong>Test completed in:</strong> ${data.sweep_time.toFixed(1)} seconds</p>
                <p><strong>Measurements:</strong> ${data.measurements.length} points</p>
            </div>
            <div style="background: #3a3a3a; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                ${rating.analysis}
            </div>
        `;
        
        // Display plot
        if (data.plot_data) {
            plotImage.src = 'data:image/png;base64,' + data.plot_data;
        }
        
        this.showSuccess('Test completed successfully!');
    }

    async saveResults() {
        if (!this.currentResults) {
            this.showError('No results to save. Please run a test first.');
            return;
        }

        try {
            const response = await fetch('/api/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    measurements: this.currentResults.measurements,
                    rating: this.currentResults.rating,
                    parameters: {
                        start_freq: parseFloat(document.getElementById('startFreq').value),
                        stop_freq: parseFloat(document.getElementById('stopFreq').value),
                        points: parseInt(document.getElementById('points').value)
                    }
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.showSuccess(`Results saved as ${data.filename}`);
            } else {
                this.showError('Error saving results: ' + data.error);
            }
        } catch (error) {
            this.showError('Error saving results: ' + error.message);
        }
    }

    async showHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            if (data.success) {
                this.displayHistory(data.history);
            } else {
                this.showError('Error loading history: ' + data.error);
            }
        } catch (error) {
            this.showError('Error loading history: ' + error.message);
        }
    }

    displayHistory(history) {
        if (history.length === 0) {
            alert('No previous test results found.');
            return;
        }

        let historyText = 'Previous Test Results:\n\n';
        history.forEach((item, index) => {
            historyText += `${index + 1}. ${item.timestamp}\n`;
            historyText += `   Range: ${item.start_freq}-${item.stop_freq} MHz\n`;
            historyText += `   Rating: ${item.rating} (${item.score}/100)\n`;
            if (item.demo_mode) historyText += `   [DEMO MODE]\n`;
            historyText += '\n';
        });

        alert(historyText);
    }

    showLoading(show) {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.disabled = show;
        });

        if (show) {
            document.getElementById('resultsContent').innerHTML = '🔄 Running test... Please wait.';
        }
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type} show`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    clearResults() {
        document.getElementById('resultsContent').innerHTML = 'Ready for test results...';
        document.getElementById('plotImage').src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMmEyYTI5Ii8+PHRleHQgeD0iMzAwIiB5PSIyMDAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iI2NjY2NjYyIgdGV4dC1hbmNob3I9Im1pZGRsZSI+U1dSIEFuYWx5c2lzIFBsb3Q8L3RleHQ+PC9zdmc+';
        this.currentResults = null;
        this.showSuccess('Results cleared');
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.antennaAnalyzer = new AntennaAnalyzer();
});

// Global functions for HTML onclick handlers
function performSweep() {
    window.antennaAnalyzer.performSweep();
}

function quickTest() {
    window.antennaAnalyzer.quickTest();
}

function saveResults() {
    window.antennaAnalyzer.saveResults();
}

function showHistory() {
    window.antennaAnalyzer.showHistory();
}

function clearResults() {
    window.antennaAnalyzer.clearResults();
}

