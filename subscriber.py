#!/usr/bin/env python3
"""
MQTT Message Subscriber and Recorder

This script subscribes to all MQTT topics and saves the received messages
to a JSON file with timestamps for later replay.
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
from typing import Dict, List, Any


class MQTTSubscriber:
    """MQTT Subscriber that records all messages to a JSON file."""
    
    def __init__(self, config_file: str = "config.yml"):
        """Initialize the MQTT subscriber with configuration."""
        self.config = self._load_config(config_file)
        self.mqtt_config = self.config["mqtt"]
        self.storage_file = self.config["storage"]["file_path"]
        
        # Message buffering
        self.buffer: List[Dict[str, Any]] = []
        self.buffer_size = 1000
        self.message_count = 0
        
        # Setup logging
        self._setup_logging()
        
        # Setup MQTT client
        self.client = self._setup_mqtt_client()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if not os.path.exists(config_file):
                raise FileNotFoundError(f"Configuration file {config_file} not found")
            
            with open(config_file, "r") as file:
                config = yaml.safe_load(file)
            
            # Validate required configuration
            required_keys = ["mqtt", "storage"]
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing required configuration key: {key}")
            
            return config
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("mqtt_subscriber.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _setup_mqtt_client(self) -> mqtt.Client:
        """Setup and configure MQTT client."""
        client = mqtt.Client()
        client.username_pw_set(
            self.mqtt_config["username"], 
            self.mqtt_config["password"]
        )
        
        # Set callbacks
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        
        # Setup TLS if required
        if self.mqtt_config.get("tls"):
            client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
            if not self.mqtt_config.get("validate_certificate"):
                client.tls_insecure_set(True)
        
        return client
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logging.info("Successfully connected to MQTT broker")
            client.subscribe("#")  # Subscribe to all topics
        else:
            logging.error(f"Failed to connect, return code {rc}")
            sys.exit(1)
    
    def _on_message(self, client, userdata, message):
        """Callback for when a message is received."""
        try:
            data = {
                "topic": message.topic,
                "payload": message.payload.decode('utf-8', errors='ignore'),
                "timestamp": time.time()
            }
            
            self.buffer.append(data)
            self.message_count += 1
            
            # Flush buffer when it reaches the buffer size
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()
            
            # Log progress every 10000 messages
            if self.message_count % 10000 == 0:
                logging.info(f"Received {self.message_count} messages")
                
        except Exception as e:
            logging.error(f"Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects."""
        if rc != 0:
            logging.error(f"Unexpected disconnection, return code {rc}")
        else:
            logging.info("Disconnected from MQTT broker")
    
    def _flush_buffer(self):
        """Write buffered messages to file."""
        if not self.buffer:
            return
        
        try:
            with open(self.storage_file, "a", encoding='utf-8') as file:
                for msg in self.buffer:
                    file.write(json.dumps(msg) + "\n")
            
            logging.debug(f"Flushed {len(self.buffer)} messages to {self.storage_file}")
            self.buffer.clear()
            
        except Exception as e:
            logging.error(f"Error writing to file: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the MQTT subscriber."""
        try:
            logging.info("Starting MQTT subscriber...")
            self.client.connect(
                self.mqtt_config["broker"], 
                self.mqtt_config["port"], 
                60
            )
            
            # Start the loop
            self.client.loop_forever()
            
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            sys.exit(1)
    
    def stop(self):
        """Stop the MQTT subscriber and cleanup."""
        logging.info("Stopping MQTT subscriber...")
        
        # Flush any remaining messages
        self._flush_buffer()
        
        # Disconnect from broker
        self.client.disconnect()
        self.client.loop_stop()
        
        logging.info(f"Total messages received: {self.message_count}")
        logging.info("Subscriber stopped")
        sys.exit(0)


def main():
    """Main function to run the MQTT subscriber."""
    try:
        subscriber = MQTTSubscriber()
        subscriber.start()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 