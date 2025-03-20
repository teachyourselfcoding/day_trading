"""
Register the new signal_visualization module with the project.
You'll need to place signal_visualization.py in the src/utils directory.
"""
import os

# Ensure the signal_visualization.py module is in the correct location
def setup_visualization_module():
    """
    Set up the signal_visualization module by ensuring it's in the correct location.
    """
    # Path to the source file
    source_path = "signal_visualization.py"
    # Destination in the utils directory
    dest_path = os.path.join("src", "utils", "signal_visualization.py")
    
    # If the module exists in the current directory but not in utils, move it
    if os.path.exists(source_path) and not os.path.exists(dest_path):
        import shutil
        # Make sure the utils directory exists
        os.makedirs(os.path.join("src", "utils"), exist_ok=True)
        # Copy the file
        shutil.copy2(source_path, dest_path)
        print(f"Moved signal_visualization.py to {dest_path}")

# Call this function when the module is imported
setup_visualization_module()