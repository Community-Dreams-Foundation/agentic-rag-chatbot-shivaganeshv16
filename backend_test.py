#!/usr/bin/env python3

import requests
import json
import time
import sys
import os
from pathlib import Path

class AgenticRAGTester:
    def __init__(self):
        self.base_url = "https://semantic-doc-agent.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🚀 Testing Agentic RAG Knowledge Assistant")
        print(f"   Base URL: {self.base_url}")
        print("=" * 50)

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": name,
            "passed": success,
            "details": details,
            "response_data": response_data
        })

    def test_sanity_check(self):
        """Test basic sanity endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/sanity", timeout=30)
            success = response.status_code == 200
            
            data = response.json() if success else {}
            details = f"Status: {response.status_code}"
            if success:
                details += f", Documents: {data.get('documents_indexed', 0)}, LLM Status: {'OK' if 'agent_response' in data else 'FAIL'}"
            
            self.log_test("GET /api/sanity", success, details, data)
            return success, data
            
        except Exception as e:
            self.log_test("GET /api/sanity", False, f"Error: {str(e)}")
            return False, {}

    def test_upload_document(self):
        """Test document upload with sample file"""
        try:
            # Use the sample technical document
            sample_file = "/app/sample_docs/sample_technical_doc.md"
            if not os.path.exists(sample_file):
                self.log_test("POST /api/upload", False, "Sample file not found")
                return False, None
            
            with open(sample_file, 'rb') as f:
                files = {'file': ('sample_technical_doc.md', f, 'text/markdown')}
                # Remove Content-Type header for file upload
                headers = {k: v for k, v in self.session.headers.items() if k != 'Content-Type'}
                response = requests.post(f"{self.base_url}/upload", files=files, headers=headers, timeout=30)
            
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}"
            if success:
                details += f", Chunks: {data.get('chunks', 0)}, Doc ID: {data.get('id', 'N/A')[:8]}..."
            
            self.log_test("POST /api/upload", success, details, data)
            return success, data.get('id') if success else None
            
        except Exception as e:
            self.log_test("POST /api/upload", False, f"Error: {str(e)}")
            return False, None

    def test_chat_with_rag(self, session_id="test_session_rag"):
        """Test chat with RAG about uploaded document"""
        try:
            payload = {
                "message": "What are the key principles of microservices architecture?",
                "session_id": session_id
            }
            
            response = self.session.post(f"{self.base_url}/chat", json=payload, timeout=60)
            success = response.status_code == 200
            
            data = response.json() if success else {}
            details = f"Status: {response.status_code}"
            if success:
                citations = len(data.get('citations', []))
                thoughts = len(data.get('thoughts', []))
                memory_updates = len(data.get('memory_updates', []))
                details += f", Citations: {citations}, Thoughts: {thoughts}, Memory Updates: {memory_updates}"
                
                # Check if response contains expected content about microservices
                response_text = data.get('response', '').lower()
                if any(term in response_text for term in ['microservice', 'single responsibility', 'decentralized']):
                    details += ", RAG Content: ✓"
                else:
                    details += ", RAG Content: ?"
            
            self.log_test("POST /api/chat (RAG)", success, details, data)
            return success, data
            
        except Exception as e:
            self.log_test("POST /api/chat (RAG)", False, f"Error: {str(e)}")
            return False, {}

    def test_chat_general_with_memory(self, session_id="test_session_general"):
        """Test general chat that should trigger memory extraction"""
        try:
            payload = {
                "message": "I am a Data Engineer who prefers Python for data processing and machine learning tasks",
                "session_id": session_id
            }
            
            response = self.session.post(f"{self.base_url}/chat", json=payload, timeout=60)
            success = response.status_code == 200
            
            data = response.json() if success else {}
            details = f"Status: {response.status_code}"
            if success:
                memory_updates = data.get('memory_updates', [])
                details += f", Memory Updates: {len(memory_updates)}"
                
                # Check if memory extraction worked
                if memory_updates:
                    user_memories = [m for m in memory_updates if m.get('target') == 'user']
                    details += f", User Memories: {len(user_memories)}"
                    if user_memories:
                        details += " ✓"
                else:
                    details += " (No memory extracted)"
                
                thoughts = data.get('thoughts', [])
                memory_steps = [t for t in thoughts if 'memory' in t.get('step', '').lower()]
                details += f", Memory Steps: {len(memory_steps)}"
            
            self.log_test("POST /api/chat (Memory)", success, details, data)
            return success, data
            
        except Exception as e:
            self.log_test("POST /api/chat (Memory)", False, f"Error: {str(e)}")
            return False, {}

    def test_chat_weather(self, session_id="test_session_weather"):
        """Test weather query functionality"""
        try:
            payload = {
                "message": "What's the weather like in Tokyo today?",
                "session_id": session_id
            }
            
            response = self.session.post(f"{self.base_url}/chat", json=payload, timeout=60)
            success = response.status_code == 200
            
            data = response.json() if success else {}
            details = f"Status: {response.status_code}"
            if success:
                thoughts = data.get('thoughts', [])
                weather_steps = [t for t in thoughts if 'weather' in t.get('step', '').lower()]
                details += f", Weather Steps: {len(weather_steps)}"
                
                response_text = data.get('response', '').lower()
                if any(term in response_text for term in ['tokyo', 'temperature', 'celsius', 'weather']):
                    details += ", Weather Data: ✓"
                else:
                    details += ", Weather Data: ?"
            
            self.log_test("POST /api/chat (Weather)", success, details, data)
            return success, data
            
        except Exception as e:
            self.log_test("POST /api/chat (Weather)", False, f"Error: {str(e)}")
            return False, {}

    def test_memory_endpoints(self):
        """Test memory retrieval endpoints"""
        results = []
        
        # Test user memory
        try:
            response = self.session.get(f"{self.base_url}/memory/user", timeout=30)
            success = response.status_code == 200
            data = response.json() if success else {}
            content_length = len(data.get('content', '')) if success else 0
            details = f"Status: {response.status_code}, Content Length: {content_length}"
            
            self.log_test("GET /api/memory/user", success, details, data)
            results.append(success)
        except Exception as e:
            self.log_test("GET /api/memory/user", False, f"Error: {str(e)}")
            results.append(False)
        
        # Test company memory
        try:
            response = self.session.get(f"{self.base_url}/memory/company", timeout=30)
            success = response.status_code == 200
            data = response.json() if success else {}
            content_length = len(data.get('content', '')) if success else 0
            details = f"Status: {response.status_code}, Content Length: {content_length}"
            
            self.log_test("GET /api/memory/company", success, details, data)
            results.append(success)
        except Exception as e:
            self.log_test("GET /api/memory/company", False, f"Error: {str(e)}")
            results.append(False)
        
        return all(results)

    def test_memory_feed(self):
        """Test memory feed endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/memory-feed", timeout=30)
            success = response.status_code == 200
            
            data = response.json() if success else []
            details = f"Status: {response.status_code}"
            if success:
                feed_count = len(data) if isinstance(data, list) else 0
                details += f", Feed Entries: {feed_count}"
                
                # Check for recent entries with user/company targets
                if data and isinstance(data, list):
                    user_entries = sum(1 for entry in data if entry.get('target') == 'user')
                    company_entries = sum(1 for entry in data if entry.get('target') == 'company')
                    details += f", User: {user_entries}, Company: {company_entries}"
            
            self.log_test("GET /api/memory-feed", success, details, data)
            return success, data
            
        except Exception as e:
            self.log_test("GET /api/memory-feed", False, f"Error: {str(e)}")
            return False, []

    def test_documents_endpoint(self):
        """Test documents listing endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/documents", timeout=30)
            success = response.status_code == 200
            
            data = response.json() if success else []
            details = f"Status: {response.status_code}"
            if success:
                doc_count = len(data) if isinstance(data, list) else 0
                details += f", Documents: {doc_count}"
                
                if data and isinstance(data, list):
                    sample_doc = next((d for d in data if 'sample_technical_doc' in d.get('filename', '')), None)
                    if sample_doc:
                        details += f", Sample Doc Found: ✓ ({sample_doc.get('chunks', 0)} chunks)"
            
            self.log_test("GET /api/documents", success, details, data)
            return success, data
            
        except Exception as e:
            self.log_test("GET /api/documents", False, f"Error: {str(e)}")
            return False, []

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("Starting comprehensive API testing...\n")
        
        # 1. Basic sanity check
        sanity_success, _ = self.test_sanity_check()
        
        # 2. Upload sample document
        upload_success, doc_id = self.test_upload_document()
        
        # 3. Test documents endpoint
        self.test_documents_endpoint()
        
        # 4. Test chat with RAG (requires uploaded doc)
        if upload_success:
            # Small delay to ensure indexing is complete
            time.sleep(2)
            self.test_chat_with_rag()
        
        # 5. Test general chat with memory extraction
        self.test_chat_general_with_memory()
        
        # 6. Test weather functionality
        self.test_chat_weather()
        
        # 7. Test memory endpoints (after chat tests)
        time.sleep(1)  # Allow memory to be written
        self.test_memory_endpoints()
        
        # 8. Test memory feed
        self.test_memory_feed()
        
        # Print final results
        self.print_summary()
        return self.tests_passed == self.tests_run

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print(f"📊 TEST SUMMARY")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed != self.tests_run:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   - {result['test']}: {result['details']}")
        else:
            print(f"\n🎉 ALL TESTS PASSED!")
        
        print("=" * 50)

def main():
    tester = AgenticRAGTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())