PROTO_DIR := ../proto
PYTHON_PROTO_DIR := proto
DESC_DIR := ../../cdk/filedescriptor

.PHONY: generate

generate:
	@echo "Generating Python code from .proto files..."
	@mkdir -p $(PYTHON_PROTO_DIR)
	@protoc -I=$(PROTO_DIR) --python_out=$(PYTHON_PROTO_DIR) $(PROTO_DIR)/*.proto
	@protoc -I=$(PROTO_DIR) --include_imports -o ${DESC_DIR}/filedescriptor.desc ${PROTO_DIR}/dummy_telemetry.proto
	@echo "Python code generation completed."
