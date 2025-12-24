#!/bin/bash
# Script to generate protobuf Python files

echo "Generating protobuf files for BG Smart Local Control..."

cd /config/custom_components/bg_smart_local

# Check if protobuf compiler is available
if ! command -v protoc &> /dev/null; then
    echo "Installing protobuf compiler..."
    pip3 install grpcio-tools
fi

# Generate Python code from .proto file
echo "Compiling esp_local_ctrl.proto..."
python3 -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    esp_local_ctrl.proto

if [ $? -eq 0 ]; then
    echo "✓ Successfully generated esp_local_ctrl_pb2.py"
    
    # Check the file was created
    if [ -f "esp_local_ctrl_pb2.py" ]; then
        echo "✓ File esp_local_ctrl_pb2.py exists"
        echo "✓ Size: $(wc -c < esp_local_ctrl_pb2.py) bytes"
    else
        echo "✗ Error: esp_local_ctrl_pb2.py was not created"
        exit 1
    fi
else
    echo "✗ Error: Failed to compile .proto file"
    exit 1
fi

echo ""
echo "Done! Now restart Home Assistant."