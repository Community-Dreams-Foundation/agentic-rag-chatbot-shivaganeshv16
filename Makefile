.PHONY: sanity

sanity:
	@echo "Running sanity check..."
	@curl -s http://localhost:8001/api/sanity | python3 -m json.tool
	@echo "\nSanity check complete. See backend/artifacts/sanity_output.json"
