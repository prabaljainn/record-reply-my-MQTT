#!/usr/bin/env python3
"""
MQTT Message Publisher and Replayer

This script reads previously recorded MQTT messages from a JSON file
and replays them with the same timing and order as originally received.
"""

import paho.mqtt.client as mqtt
import json
import time
import yaml
import logging
import ssl
import sys
import signal
import os
import glob
import argparse
from typing import Dict, Any, Iterator, List


class MQTTPublisher:
    """MQTT Publisher that replays recorded messages."""
    
    def __init__(self, config_file: str = "config.yml", storage_file: str = None):
        """Initialize the MQTT publisher with configuration."""
        self.config = self._load_config(config_file)
        self.publish_config = self.config["publish"]
        
        # Use provided storage file or determine from existing recordings
        if storage_file:
            self.storage_file = storage_file
        else:
            self.storage_file = self._get_latest_recording()
        
        # Setup logging
        self._setup_logging()
        
        # Setup MQTT client
        self.client = self._setup_mqtt_client()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.should_stop = False
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if not os.path.exists(config_file):
                raise FileNotFoundError(f"Configuration file {config_file} not found")
            
            with open(config_file, "r") as file:
                config = yaml.safe_load(file)
            
            # Validate required configuration
            required_keys = ["publish", "storage"]
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing required configuration key: {key}")
            
            return config
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def _get_latest_recording(self) -> str:
        """Find the latest recording file or use config default."""
        # Look for mqtt_record_*.json files
        pattern = "mqtt_record_*.json"
        recording_files = glob.glob(pattern)
        
        if recording_files:
            # Sort by modification time, newest first
            recording_files.sort(key=os.path.getmtime, reverse=True)
            latest_file = recording_files[0]
            logging.info(f"Using latest recording: {latest_file}")
            return latest_file
        else:
            # Fall back to config file path
            config_file = self.config["storage"]["file_path"]
            logging.info(f"No mqtt_record_*.json files found, using config file: {config_file}")
            return config_file
    
    def list_available_recordings(self) -> List[str]:
        """List all available recording files."""
        pattern = "mqtt_record_*.json"
        recording_files = glob.glob(pattern)
        recording_files.sort(key=lambda x: int(x.split('_')[2].split('.')[0]))
        return recording_files
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("mqtt_publisher.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _setup_mqtt_client(self) -> mqtt.Client:
        """Setup and configure MQTT client."""
        client = mqtt.Client()
        client.username_pw_set(
            self.publish_config["username"], 
            self.publish_config["password"]
        )
        
        # Set callbacks
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_publish = self._on_publish
        
        # Setup TLS if required
        if self.publish_config.get("tls"):
            client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
            if not self.publish_config.get("validate_certificate"):
                client.tls_insecure_set(True)
        
        return client
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logging.info("Successfully connected to MQTT broker")
        else:
            logging.error(f"Failed to connect, return code {rc}")
            sys.exit(1)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects."""
        if rc != 0:
            logging.error(f"Unexpected disconnection, return code {rc}")
        else:
            logging.info("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published."""
        logging.debug(f"Message {mid} published successfully")
    
    def _read_messages(self) -> Iterator[Dict[str, Any]]:
        """Generator to read messages from the storage file."""
        try:
            if not os.path.exists(self.storage_file):
                raise FileNotFoundError(f"Storage file {self.storage_file} not found")
            
            with open(self.storage_file, "r", encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        message = json.loads(line)
                        yield message
                    except json.JSONDecodeError as e:
                        logging.warning(f"Invalid JSON on line {line_num}: {e}")
                        continue
        
        except Exception as e:
            logging.error(f"Error reading messages: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.should_stop = True
    
    def start(self):
        """Start the MQTT publisher and replay messages."""
        try:
            logging.info("Starting MQTT publisher...")
            logging.info(f"Replaying messages from: {self.storage_file}")
            
            # Connect to broker
            self.client.connect(
                self.publish_config["broker"], 
                self.publish_config["port"], 
                60
            )
            
            # Start the loop in a separate thread
            self.client.loop_start()
            
            # Wait for connection
            time.sleep(1)
            
            # Start publishing messages
            self._publish_messages()
            
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            sys.exit(1)
        finally:
            self.client.loop_stop()
    
    def _publish_messages(self):
        """Publish messages with original timing."""
        try:
            previous_timestamp = None
            message_count = 0
            
            logging.info("Starting message replay...")
            
            for message in self._read_messages():
                if self.should_stop:
                    break
                
                # Calculate delay based on original timestamps
                if previous_timestamp is not None:
                    delay = message["timestamp"] - previous_timestamp
                    if delay > 0:
                        time.sleep(min(delay, 60))  # Cap delay at 60 seconds
                
                # Publish the message
                try:
                    result = self.client.publish(
                        message["topic"], 
                        message["payload"]
                    )
                    
                    if result.rc != mqtt.MQTT_ERR_SUCCESS:
                        logging.warning(f"Failed to publish message to {message['topic']}")
                    else:
                        message_count += 1
                        if message_count % 1000 == 0:
                            logging.info(f"Published {message_count} messages")
                
                except Exception as e:
                    logging.error(f"Error publishing message: {e}")
                
                previous_timestamp = message["timestamp"]
            
            logging.info(f"Finished replaying {message_count} messages")
            
        except Exception as e:
            logging.error(f"Error during message replay: {e}")
            raise
    
    def stop(self):
        """Stop the MQTT publisher."""
        logging.info("Stopping MQTT publisher...")
        self.should_stop = True
        self.client.disconnect()
        logging.info("Publisher stopped")


def main():
    """Main function to run the MQTT publisher."""
    parser = argparse.ArgumentParser(description="MQTT Message Publisher and Replayer")
    parser.add_argument(
        "--file", "-f", 
        type=str, 
        help="Specific recording file to replay (e.g., mqtt_record_1.json)"
    )
    parser.add_argument(
        "--list", "-l", 
        action="store_true", 
        help="List available recording files"
    )
    
    args = parser.parse_args()
    
    try:
        publisher = MQTTPublisher()
        
        if args.list:
            recordings = publisher.list_available_recordings()
            if recordings:
                print("Available recording files:")
                for i, recording in enumerate(recordings, 1):
                    file_size = os.path.getsize(recording)
                    file_time = time.ctime(os.path.getmtime(recording))
                    print(f"  {i}. {recording} ({file_size:,} bytes, {file_time})")
            else:
                print("No recording files found.")
            return
        
        if args.file:
            if not os.path.exists(args.file):
                print(f"Error: File '{args.file}' not found.")
                sys.exit(1)
            publisher.storage_file = args.file
        
        publisher.start()
        
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 