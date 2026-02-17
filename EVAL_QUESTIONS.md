# Evaluation Questions

Use these prompts to test the chatbot's features end-to-end.

## Feature A - RAG (File Upload + Grounded Q&A)

### Setup
Upload a document first (PDF, MD, or TXT), then ask questions about it.

### Test Prompts

1. **Basic Retrieval**
   > "What are the main topics covered in the uploaded document?"
   - Expected: Answer grounded in document content with citations

2. **Specific Detail**
   > "Can you explain [specific concept from your document]?"
   - Expected: Detailed answer citing the relevant chunk/section

3. **Groundedness Check (No Docs)**
   > "What is the capital of Mars?"
   - Expected: "I couldn't find that in your files." (no hallucination)

4. **Multi-chunk Retrieval**
   > "Summarize the key findings from my uploaded files."
   - Expected: Summary pulling from multiple chunks, multiple citations

5. **Code/Technical Content**
   > "Show me the code examples from the documentation."
   - Expected: Code blocks properly formatted with syntax highlighting

## Feature B - Memory

### Test Prompts

6. **User Preference Memory**
   > "I'm a Project Finance Analyst and I prefer weekly summaries on Mondays."
   - Expected: Response acknowledges preference; USER_MEMORY.md updated

7. **Company Learning Memory**
   > "We discovered that the Asset Management team's workflow bottleneck is the approval queue taking 3+ days."
   - Expected: Response acknowledges finding; COMPANY_MEMORY.md updated

8. **Verify Memory Written**
   - Check the Memory Feed sidebar for extracted facts
   - Click "User" and "Org" tabs to see raw markdown content

## Feature C - Weather / Safe Compute

### Test Prompts

9. **Basic Weather Query**
   > "What's the weather like in Tokyo?"
   - Expected: Temperature data, humidity, wind speed from Open-Meteo

10. **Weather Analysis**
    > "Analyze the weather forecast for London. What's the temperature volatility?"
    - Expected: 24h rolling average, min/max range, volatility calculation

11. **Multi-city Comparison**
    > "How's the weather in Dubai compared to Berlin?"
    - Expected: Data for both cities with comparative analysis

## Edge Cases

12. **Empty Knowledge Base**
    > "What does my documentation say about deployment?"
    - Expected: Graceful response noting no documents are uploaded

13. **Unsupported File Upload**
    - Try uploading a .jpg or .exe file
    - Expected: Error message about unsupported file types

14. **Long Query**
    > "Given all the information in my uploaded documents, provide a comprehensive summary of every topic, including technical details, code examples, and any recommendations mentioned."
    - Expected: Thorough response with multiple citations
