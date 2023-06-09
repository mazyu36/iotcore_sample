PROTO_DIR := ../proto
PYTHON_PROTO_DIR := proto

.PHONY: generate

generate:
	@echo "Generating Python code from .proto files..."
	@mkdir -p $(PYTHON_PROTO_DIR)
	@protoc -I=$(PROTO_DIR) --python_out=$(PYTHON_PROTO_DIR) $(PROTO_DIR)/*.proto
	@echo "Python code generation completed."
