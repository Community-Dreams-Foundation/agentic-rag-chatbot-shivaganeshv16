#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path

class RAGKnowledgeAssistantTester:
    def __init__(self, base_url="https://semantic-doc-agent.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.document_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers={'Content-Type': 'application/json'})
            elif method == 'POST':
                if files:
                    # For file upload, don't set Content-Type header
                    response = requests.post(url, data=data, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    response_data = response.json()
                    print(f"   Response preview: {str(response_data)[:200]}...")
                    return True, response_data
                else:
                    print(f"   Response (non-JSON): {response.text[:200]}...")
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test GET / returns welcome message"""
        success, response = self.run_test(
            "Root endpoint",
            "GET",
            "",
            200
        )
        if success and isinstance(response, dict):
            assert "message" in response, "Root endpoint should return message field"
            print(f"   Welcome message: {response['message']}")
        return success

    def test_documents_empty_list(self):
        """Test GET /documents returns empty list initially"""
        success, response = self.run_test(
            "Documents empty list",
            "GET", 
            "documents",
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} existing documents")
        return success

    def test_upload_txt_file(self):
        """Test POST /upload - upload a .txt file and verify it gets indexed"""
        # Create a test file
        test_content = """
        # Test Document

        This is a comprehensive test document for the RAG Knowledge Assistant.
        
        ## Key Information
        - The system uses ChromaDB for vector storage
        - FastAPI serves the backend endpoints
        - React powers the frontend interface
        
        ## Technical Details
        The application supports PDF, MD, and TXT file formats.
        Documents are chunked into smaller pieces for better retrieval.
        
        ## Features
        1. Document upload and indexing
        2. Semantic search capabilities  
        3. Chat interface with citations
        4. Memory management system
        """
        
        # Prepare file for upload
        files = {
            'file': ('test_document.txt', test_content, 'text/plain')
        }
        
        success, response = self.run_test(
            "Upload TXT file",
            "POST",
            "upload",
            200,
            files=files
        )
        
        if success and isinstance(response, dict):
            assert "id" in response, "Upload should return document ID"
            assert "chunks" in response, "Upload should return chunks count"
            assert response["chunks"] > 0, "Document should have chunks"
            self.document_ids.append(response["id"])
            print(f"   Document ID: {response['id']}, Chunks: {response['chunks']}")
        
        return success

    def test_upload_unsupported_file(self):
        """Test POST /upload - reject unsupported file types"""
        files = {
            'file': ('test.docx', b'fake docx content', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        
        success, _ = self.run_test(
            "Upload unsupported file",
            "POST",
            "upload",
            400,  # Should reject with 400
            files=files
        )
        return success

    def test_documents_list_after_upload(self):
        """Test GET /documents - verify uploaded document appears"""
        success, response = self.run_test(
            "Documents list after upload",
            "GET",
            "documents", 
            200
        )
        
        if success and isinstance(response, list):
            if self.document_ids:
                doc_found = any(doc.get('id') == self.document_ids[0] for doc in response)
                if doc_found:
                    print("   ✅ Uploaded document found in list")
                else:
                    print("   ❌ Uploaded document NOT found in list")
                    return False
        return success

    def test_chat_simple(self):
        """Test POST /chat - send a message and get response with thoughts array"""
        chat_data = {
            "message": "What information do you have about ChromaDB?",
            "session_id": str(uuid.uuid4())
        }
        
        success, response = self.run_test(
            "Simple chat query",
            "POST",
            "chat",
            200,
            data=chat_data
        )
        
        if success and isinstance(response, dict):
            assert "response" in response, "Chat should return response field"
            assert "thoughts" in response, "Chat should return thoughts array"
            assert "citations" in response, "Chat should return citations array"
            
            print(f"   Response length: {len(response.get('response', ''))}")
            print(f"   Thoughts count: {len(response.get('thoughts', []))}")
            print(f"   Citations count: {len(response.get('citations', []))}")
            
            if response.get('thoughts'):
                print(f"   First thought: {response['thoughts'][0].get('step', 'N/A')}")
                
        return success

    def test_chat_weather(self):
        """Test POST /chat - ask about weather to trigger Open-Meteo tool"""
        chat_data = {
            "message": "What's the weather like in Tokyo today?",
            "session_id": str(uuid.uuid4())
        }
        
        success, response = self.run_test(
            "Weather query chat",
            "POST", 
            "chat",
            200,
            data=chat_data
        )
        
        if success and isinstance(response, dict):
            weather_mentioned = "weather" in response.get("response", "").lower()
            thoughts = response.get("thoughts", [])
            weather_thought = any("weather" in t.get("step", "").lower() for t in thoughts)
            
            print(f"   Weather in response: {weather_mentioned}")
            print(f"   Weather thought step: {weather_thought}")
            
        return success

    def test_memory_user(self):
        """Test GET /memory/user - read user memory file"""
        success, response = self.run_test(
            "Get user memory",
            "GET",
            "memory/user",
            200
        )
        
        if success and isinstance(response, dict):
            assert "type" in response, "Memory response should have type field"
            assert "content" in response, "Memory response should have content field"
            print(f"   Memory type: {response.get('type')}")
            print(f"   Content length: {len(response.get('content', ''))}")
            
        return success

    def test_memory_company(self):
        """Test GET /memory/company - read company memory file"""
        success, response = self.run_test(
            "Get company memory", 
            "GET",
            "memory/company",
            200
        )
        
        if success and isinstance(response, dict):
            assert "type" in response, "Memory response should have type field"
            assert "content" in response, "Memory response should have content field"
            print(f"   Memory type: {response.get('type')}")
            print(f"   Content length: {len(response.get('content', ''))}")
            
        return success

    def test_memory_feed(self):
        """Test GET /memory-feed - get memory feed entries"""
        success, response = self.run_test(
            "Get memory feed",
            "GET",
            "memory-feed", 
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Memory feed entries: {len(response)}")
            if response:
                print(f"   Latest entry: {response[0].get('fact', 'N/A')[:50]}...")
        return success

    def test_sanity_check(self):
        """Test GET /sanity - generates sanity_output.json"""
        success, response = self.run_test(
            "Sanity check",
            "GET",
            "sanity",
            200
        )
        
        if success and isinstance(response, dict):
            assert "status" in response, "Sanity check should have status"
            assert "agent_response" in response, "Sanity check should have agent_response"
            assert "documents_indexed" in response, "Should show documents count"
            
            print(f"   Status: {response.get('status')}")
            print(f"   Documents indexed: {response.get('documents_indexed')}")
            print(f"   Agent response: {response.get('agent_response', '')[:100]}...")
            
        return success

    def test_delete_document(self):
        """Test DELETE /documents/{doc_id} - delete a document"""
        if not self.document_ids:
            print("   ⚠️  No document to delete (skipping)")
            return True
            
        doc_id = self.document_ids[0]
        success, response = self.run_test(
            "Delete document",
            "DELETE",
            f"documents/{doc_id}",
            200
        )
        
        if success and isinstance(response, dict):
            assert "status" in response, "Delete should return status"
            print(f"   Delete status: {response.get('status')}")
            
        return success

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting RAG Knowledge Assistant API Tests")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Root endpoint", self.test_root_endpoint),
            ("Documents empty list", self.test_documents_empty_list),
            ("Upload TXT file", self.test_upload_txt_file),
            ("Upload unsupported file", self.test_upload_unsupported_file),
            ("Documents list after upload", self.test_documents_list_after_upload),
            ("Simple chat", self.test_chat_simple),
            ("Weather chat", self.test_chat_weather),
            ("User memory", self.test_memory_user),
            ("Company memory", self.test_memory_company),
            ("Memory feed", self.test_memory_feed),
            ("Sanity check", self.test_sanity_check),
            ("Delete document", self.test_delete_document),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test '{test_name}' failed with exception: {str(e)}")
                
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 Tests Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = RAGKnowledgeAssistantTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())