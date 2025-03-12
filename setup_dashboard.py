#!/usr/bin/env python3
"""
Setup script for the Trading Signals Dashboard.
This will create the necessary directories and files.
"""
import os
import sys
import shutil
import subprocess

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(CURRENT_DIR, 'templates')

def print_colored(text, color):
    """Print colored text to the console."""
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def create_directory(path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print_colored(f"Created directory: {path}", 'green')
        return True
    else:
        print_colored(f"Directory already exists: {path}", 'yellow')
        return False

def create_static_directory():
    """Create static directory for CSS and JS files."""
    static_dir = os.path.join(CURRENT_DIR, 'static')
    css_dir = os.path.join(static_dir, 'css')
    js_dir = os.path.join(static_dir, 'js')
    
    create_directory(static_dir)
    create_directory(css_dir)
    create_directory(js_dir)
    
    # Create a basic CSS file
    css_file = os.path.join(css_dir, 'dashboard.css')
    if not os.path.exists(css_file):
        with open(css_file, 'w') as f:
            f.write("/* Dashboard CSS styles */\n")
        print_colored(f"Created CSS file: {css_file}", 'green')

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ['flask', 'pandas']
    
    print_colored("Checking dependencies...", 'blue')
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_colored(f"✓ {package} is installed", 'green')
        except ImportError:
            print_colored(f"✗ {package} is not installed", 'red')
            missing_packages.append(package)
    
    if missing_packages:
        print_colored("\nMissing packages. Installing...", 'blue')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print_colored("Dependencies installed successfully!", 'green')
    else:
        print_colored("All dependencies are installed.", 'green')

def copy_template_content():
    """Copy template content to template files."""
    # This would normally contain the template HTML content
    # In a real implementation, we could have template content as strings
    # or read from files bundled with the script
    print_colored("Note: In a real implementation, this would copy actual template content", 'yellow')
    print_colored("For now, please manually copy the template content to the template files", 'yellow')

def setup_dashboard():
    """Set up the dashboard."""
    print_colored("Setting up Trading Signals Dashboard...", 'blue')
    
    # Create templates directory
    created = create_directory(TEMPLATES_DIR)
    
    # Check if dashboard.py exists
    dashboard_path = os.path.join(CURRENT_DIR, 'dashboard.py')
    if not os.path.exists(dashboard_path):
        print_colored(f"Error: dashboard.py not found at {dashboard_path}", 'red')
        print_colored("Please make sure dashboard.py is in the same directory as this script.", 'yellow')
        return False
    
    # Create template files
    templates = {
        'base.html': os.path.join(TEMPLATES_DIR, 'base.html'),
        'index.html': os.path.join(TEMPLATES_DIR, 'index.html'),
        'symbol.html': os.path.join(TEMPLATES_DIR, 'symbol.html'),
        'chart.html': os.path.join(TEMPLATES_DIR, 'chart.html'),
        'scan.html': os.path.join(TEMPLATES_DIR, 'scan.html')
    }
    
    print_colored("Creating template files...", 'blue')
    for template_name, template_path in templates.items():
        if os.path.exists(template_path):
            print_colored(f"Template already exists: {template_name}", 'yellow')
        else:
            # In a real implementation, this would copy template content from a source
            # For this example, we'll just create placeholder files
            with open(template_path, 'w') as f:
                f.write(f"<!-- {template_name} placeholder - Replace with actual template content -->")
            print_colored(f"Created template file: {template_name}", 'green')
    
    return True