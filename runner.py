#!/usr/bin/env python3

import os
import sys
import subprocess
import time
import yaml
import glob
import signal
from pathlib import Path


def run_command(command, shell=True, new_window=False):
    try:
        if new_window and sys.platform == "darwin":
            # Get current working directory
            current_dir = os.getcwd()
            # Escape double quotes in the command and directory
            escaped_command = command.replace('"', '\\"')
            escaped_dir = current_dir.replace('"', '\\"')
            # Create an AppleScript command to open a new Terminal window, cd to the right directory, and run the command
            apple_script = f"""
                tell application "Terminal"
                    do script "cd \\"" & "{escaped_dir}" & "\\" && {escaped_command}"
                    activate
                end tell
            """
            process = subprocess.Popen(["osascript", "-e", apple_script])
            # Sleep briefly to allow the window to open
            time.sleep(1)
            return process
        else:
            return subprocess.Popen(command, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)


def kill_process(process):
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def kill_ngrok():
    # Kill any existing ngrok processes more thoroughly
    try:
        # Try killing by pkill
        subprocess.run(["pkill", "ngrok"], capture_output=True)
    except Exception:
        pass

    # Also try killing by lsof on the ports we use
    try:
        for port in [3000, 8765]:
            subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True)
    except Exception:
        pass


def start_ngrok(port, url):
    # Kill any existing ngrok processes first
    kill_ngrok()
    # Start ngrok with the specific URL
    return run_command(
        f"ngrok http --domain={url.replace('https://', '')} {port}", new_window=True
    )


def start_voicemail_server():
    # Change to voicemail directory and start the server
    os.chdir("voicemail")
    return run_command("node app.js", new_window=True)


def process_caller_data():
    # Use absolute path for the script
    root_dir = str(Path(__file__).parent)
    script_path = os.path.join(root_dir, "data_processing", "process_caller_data.py")
    print(f"\nCurrent directory before process_caller_data: {os.getcwd()}")
    print(f"Changing to root directory: {root_dir}")
    # Change back to root directory
    os.chdir(root_dir + "/data_processing")
    print(f"Current directory after change: {os.getcwd()}")
    print(f"Looking for script at: {script_path}")
    print(f"Script exists: {os.path.exists(script_path)}")
    print("\nProcessing caller data...")
    subprocess.run([sys.executable, script_path])


def get_available_numbers():
    numbers = []
    # Use absolute paths
    root_dir = str(Path(__file__).parent)
    data_dir = os.path.join(root_dir, "data")

    print(f"\nCurrent directory in get_available_numbers: {os.getcwd()}")
    print(f"Looking for data directory at: {data_dir}")
    print(f"Data directory exists: {os.path.exists(data_dir)}")

    # Ensure data directory exists
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found at {data_dir}")
        return numbers

    # List contents of data directory if it exists
    if os.path.exists(data_dir):
        print("\nContents of data directory:")
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path):
                print(f"  Directory: {item}")
            else:
                print(f"  File: {item}")

    # Search for full_metadata.yaml files in data directory using absolute path
    pattern = os.path.join(data_dir, "*/full_metadata.yaml")
    print(f"\nSearching for metadata files with pattern: {pattern}")
    metadata_files = glob.glob(pattern)
    print(f"Found {len(metadata_files)} metadata files: {metadata_files}")

    for metadata_file in metadata_files:
        try:
            print(f"\nReading metadata file: {metadata_file}")
            with open(metadata_file, "r") as f:
                metadata = yaml.safe_load(f)
                print(f"Metadata: {metadata}")
                if metadata and "number" in metadata and "name" in metadata:
                    numbers.append(
                        {
                            "number": metadata["number"],
                            "name": metadata["name"],
                            "path": os.path.dirname(metadata_file),
                        }
                    )
                    print(f"Successfully loaded number for: {metadata['name']}")
                else:
                    print("Metadata file missing required fields (number or name)")
        except Exception as e:
            print(f"Error reading {metadata_file}: {e}")

    if not numbers:
        print(f"\nNo metadata files found in {data_dir}")

    return numbers


def select_number(numbers):
    print("\nAvailable phone numbers:")
    for i, entry in enumerate(numbers, 1):
        print(f"{i}. {entry['name']} - {entry['number']}")

    while True:
        try:
            choice = int(input("\nSelect a number (enter the index): "))
            if 1 <= choice <= len(numbers):
                return numbers[choice - 1]
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def start_convo_server(phone_number):
    # Change to convo directory
    os.chdir(str(Path(__file__).parent) + "/convo")
    return run_command(f"python server.py --n {phone_number}", new_window=True)


def run_convo_dial(phone_number):
    # Already in convo directory
    return run_command(f"python dial.py {phone_number}", new_window=True)


def main():
    # Store the root directory
    root_dir = str(Path(__file__).parent)

    # Make sure no ngrok processes are running at start
    kill_ngrok()

    # Step 1: Start ngrok for voicemail
    print("Starting ngrok for voicemail server...")
    ngrok_process = start_ngrok(
        3000, "https://splendid-working-stallion.ngrok-free.app"
    )

    # Step 2: Start voicemail server
    print("\nStarting voicemail server...")
    voicemail_process = start_voicemail_server()

    # Step 3: Wait for user to finish with voicemail
    input("\nPress Enter when you're ready to stop the voicemail server and proceed...")

    # Kill both processes
    kill_process(voicemail_process)
    kill_process(ngrok_process)
    kill_ngrok()  # Make extra sure ngrok is killed

    # Step 4: Process caller data
    process_caller_data()

    # Step 5: Get and select phone number
    numbers = get_available_numbers()
    if not numbers:
        print("No phone numbers found in the data directory!")
        sys.exit(1)

    selected = select_number(numbers)
    print(f"\nSelected: {selected['name']} - {selected['number']}")

    # Step 6: Start ngrok for convo server
    print("\nStarting ngrok for convo server...")
    ngrok_process = start_ngrok(
        8765, "https://splendid-working-stallion.ngrok-free.app"
    )

    # Step 7: Start convo server
    print("\nStarting convo server...")
    server_process = start_convo_server(selected["number"])

    # Give the server a moment to start
    time.sleep(2)

    # Step 8: Run convo dial
    print("\nStarting convo dial...")
    dial_process = run_convo_dial(selected["number"])

    # Step 9: Wait for user to end the call
    input("\nPress Enter when you're ready to end the call and stop all processes...")

    # Kill all processes
    kill_process(dial_process)
    kill_process(server_process)
    kill_process(ngrok_process)
    kill_ngrok()  # Make extra sure ngrok is killed

    print("\nAll processes terminated. Script complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Cleaning up...")
        kill_ngrok()  # Make sure to kill ngrok on interrupt too
        sys.exit(0)
