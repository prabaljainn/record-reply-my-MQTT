# Mock-my-MQTT 🚀

A powerful Python tool for recording and replaying MQTT message streams with precise timing reproduction. Perfect for testing, debugging, and simulating IoT environments.

## ✨ Features

- **📡 Universal Recording**: Subscribe to all MQTT topics (`#`) and capture every message
- **🔢 Auto-Incremental Files**: Automatically creates `mqtt_record_1.json`, `mqtt_record_2.json`, etc.
- **⏱️ Precise Timing**: Replay messages with exact original timing intervals
- **🎯 Flexible Replay**: Choose specific recordings or automatically use the latest
- **🔒 Secure Connections**: Full TLS/SSL support with certificate validation options
- **💾 Efficient Storage**: Buffered writes with configurable batch sizes for optimal performance
- **🛡️ Robust Error Handling**: Graceful shutdowns, connection recovery, and comprehensive logging
- **🔧 Flexible Configuration**: YAML-based configuration with environment-specific settings
- **📊 Progress Monitoring**: Real-time message counts and detailed logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MQTT Broker   │◄──►│   Subscriber    │───►│  JSON Storage   │
│  (Production)   │    │  (Record Mode)  │    │   (Messages)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MQTT Broker   │◄───│   Publisher     │◄───│  JSON Storage   │
│ (Test/Staging)  │    │ (Replay Mode)   │    │   (Messages)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- MQTT broker access
- Required Python packages (see `requirements.txt`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Mock-my-MQTT.git
   cd Mock-my-MQTT
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your MQTT settings**
   ```bash
   cp config.example.yml config.yml
   # Edit config.yml with your MQTT broker details
   ```

### Usage

#### 📥 Recording Messages
Start capturing all MQTT messages from your broker:
```bash
python subscriber.py
```

The subscriber will:
- Connect to your MQTT broker
- Subscribe to all topics (`#`)
- **Automatically create incremental files** (`mqtt_record_1.json`, `mqtt_record_2.json`, etc.)
- Save messages with timestamps for precise replay
- Provide real-time progress updates

#### 📤 Replaying Messages

**Replay the latest recording:**
```bash
python publisher.py
```

**Replay a specific recording:**
```bash
python publisher.py --file mqtt_record_3.json
```

**List all available recordings:**
```bash
python publisher.py --list
```

The publisher will:
- Automatically use the latest recording (if no file specified)
- Connect to the target MQTT broker
- Replay messages with precise timing intervals
- Maintain original message order and frequency

## ⚙️ Configuration

The `config.yml` file supports separate configurations for recording and replaying:

```yaml
# Subscriber configuration (recording)
mqtt:
  broker: "production.mqtt.example.com"
  port: 8883
  username: "recorder_user"
  password: "secure_password"
  tls: true
  validate_certificate: true

# Publisher configuration (replaying)
publish:
  broker: "test.mqtt.example.com"
  port: 1883
  username: "test_user"
  password: "test_password"
  tls: false
  validate_certificate: false

# Storage configuration
storage:
  file_path: "mqtt_messages.json"
```

## 📁 Project Structure

```
Mock-my-MQTT/
├── subscriber.py          # MQTT message recorder
├── publisher.py           # MQTT message replayer
├── config.example.yml     # Configuration template
├── sample_messages.json   # Example message format
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── .gitignore           # Git ignore patterns
```

## 🔧 Advanced Features

### Auto-Incremental Files
Each recording session creates a new file:
```
mqtt_record_1.json  # First recording
mqtt_record_2.json  # Second recording
mqtt_record_3.json  # Third recording
```

### Message Format
Messages are stored in JSON Lines format:
```json
{"topic": "sensors/temperature", "payload": "23.5", "timestamp": 1699123456.123}
{"topic": "sensors/humidity", "payload": "65.2", "timestamp": 1699123457.456}
```

### Publisher Command Options
```bash
# Replay latest recording
python publisher.py

# Replay specific recording
python publisher.py --file mqtt_record_2.json
python publisher.py -f mqtt_record_2.json

# List all recordings with details
python publisher.py --list
python publisher.py -l
```

### Logging
Both scripts provide comprehensive logging:
- Console output for real-time monitoring
- Log files for detailed debugging
- Configurable log levels

### Signal Handling
Graceful shutdown on `SIGINT` and `SIGTERM`:
- Flushes buffered messages
- Closes connections properly
- Provides final statistics

## 🛠️ Use Cases

- **🧪 Testing**: Replay production traffic in test environments
- **🐛 Debugging**: Reproduce specific message sequences
- **📊 Load Testing**: Simulate realistic MQTT traffic patterns
- **🔄 Migration**: Transfer messages between different brokers
- **📈 Performance Analysis**: Analyze message patterns and timing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [paho-mqtt](https://github.com/eclipse/paho.mqtt.python) for MQTT connectivity
- Uses [PyYAML](https://pyyaml.org/) for configuration management

---

**Happy MQTT Mocking! 🎭**
