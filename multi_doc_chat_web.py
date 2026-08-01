# File: multi_doc_chat_web.py
"""
MULTI-DOCUMENT CONVERSATION SYSTEM WITH LOCAL WEB SERVER
Complete plug-and-play solution with web interface
"""

import os
import re
import json
import time
import PyPDF2
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, deque
import hashlib
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import urllib.parse

# ==================== DOCUMENT PROCESSOR ====================
class MultiDocumentProcessor:
    """Process multiple documents and maintain cross-document context"""
    
    def __init__(self):
        self.documents = {}
        self.cross_references = defaultdict(set)
        self.document_topics = {}
        self.conversation_context = deque(maxlen=50)
        
    def load_all_documents(self, folder_path: str = "."):
        """Load all supported documents from folder"""
        print(f"\n📂 Loading documents from: {folder_path}")
        
        supported_extensions = ['.pdf', '.txt', '.md']
        loaded_count = 0
        
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                
                if ext in supported_extensions:
                    try:
                        doc_id = hashlib.md5(file.encode()).hexdigest()[:8]
                        
                        if ext == '.pdf':
                            content = self._extract_pdf_text(file_path)
                        else:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                        
                        if len(content.strip()) > 0:
                            processed = self._process_document(content, file, doc_id)
                            self.documents[doc_id] = processed
                            loaded_count += 1
                            print(f"  ✓ {file}")
                            
                    except Exception as e:
                        print(f"  ✗ {file}: {str(e)[:50]}")
        
        print(f"\n✅ Loaded {loaded_count} documents")
        
        if loaded_count > 0:
            self._build_cross_document_references()
            self._extract_document_topics()
            return True
        
        return False
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF files"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"  ⚠️ PDF error: {str(e)[:50]}")
            return ""
    
    def _process_document(self, content: str, filename: str, doc_id: str) -> Dict:
        """Process a single document"""
        sentences = self._extract_sentences(content)
        paragraphs = self._extract_paragraphs(content)
        keywords = self._extract_keywords(content)
        entities = self._extract_entities(content)
        document_type = self._classify_document(content)
        
        return {
            'id': doc_id,
            'filename': filename,
            'content': content,
            'sentences': sentences,
            'paragraphs': paragraphs,
            'keywords': keywords[:20],
            'entities': entities,
            'type': document_type,
            'length': len(content),
            'word_count': len(content.split()),
            'loaded_at': datetime.now().isoformat()
        }
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs
    
    def _extract_keywords(self, text: str, top_n: int = 30) -> List[str]:
        """Extract important keywords from text"""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in stop_words]
        
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        entities = []
        capital_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capital_words)
        
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        entities.extend(acronyms)
        
        return list(set(entities))
    
    def _classify_document(self, content: str) -> str:
        """Classify document type"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['contract', 'agreement', 'clause']):
            return 'contract'
        elif any(word in content_lower for word in ['report', 'analysis', 'findings']):
            return 'report'
        elif any(word in content_lower for word in ['manual', 'guide', 'instructions']):
            return 'manual'
        elif any(word in content_lower for word in ['research', 'study', 'experiment']):
            return 'research'
        elif any(word in content_lower for word in ['email', 'letter', 'correspondence']):
            return 'correspondence'
        else:
            return 'general'
    
    def _build_cross_document_references(self):
        """Build references between documents"""
        print("🔗 Building cross-document references...")
        
        all_entities = defaultdict(list)
        all_keywords = defaultdict(list)
        
        for doc_id, doc in self.documents.items():
            for entity in doc['entities']:
                all_entities[entity].append(doc_id)
            for keyword in doc['keywords']:
                all_keywords[keyword].append(doc_id)
        
        # Fixed: Use tuples instead of lists for hashable types
        for entity, doc_list in all_entities.items():
            if len(doc_list) > 1:
                ref_tuple = (entity, 'entity', tuple(doc_list))
                for doc_id in doc_list:
                    self.cross_references[doc_id].add(ref_tuple)
        
        for keyword, doc_list in all_keywords.items():
            if len(doc_list) > 1:
                ref_tuple = (keyword, 'keyword', tuple(doc_list))
                for doc_id in doc_list:
                    self.cross_references[doc_id].add(ref_tuple)
        
        print(f"  Found {sum(len(refs) for refs in self.cross_references.values())} cross-references")
    
    def _extract_document_topics(self):
        """Extract main topics from each document"""
        print("📊 Extracting document topics...")
        
        for doc_id, doc in self.documents.items():
            topics = doc['keywords'][:5]
            self.document_topics[doc_id] = topics
            self.document_topics[doc_id].append(f"type:{doc['type']}")
    
    def search_across_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for query across all documents"""
        query_lower = query.lower()
        results = []
        
        for doc_id, doc in self.documents.items():
            doc_content = doc['content'].lower()
            
            if query_lower in doc_content:
                matching_sentences = []
                for sentence in doc['sentences']:
                    if query_lower in sentence.lower():
                        matching_sentences.append(sentence[:200])
                        if len(matching_sentences) >= 3:
                            break
                
                if matching_sentences:
                    score = self._calculate_relevance_score(doc_content, query_lower)
                    results.append({
                        'doc_id': doc_id,
                        'filename': doc['filename'],
                        'score': score,
                        'sentences': matching_sentences,
                        'type': doc['type'],
                        'keywords': doc['keywords'][:5]
                    })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _calculate_relevance_score(self, doc_content: str, query: str) -> float:
        """Calculate relevance score"""
        query_words = query.split()
        score = 0
        
        for word in query_words:
            if len(word) > 3:
                score += doc_content.count(word.lower())
        
        return score
    
    def get_cross_document_insights(self, query: str) -> Dict:
        """Get insights about query across multiple documents"""
        search_results = self.search_across_documents(query, top_k=3)
        
        if not search_results:
            return {'found': False, 'message': 'No relevant documents found.'}
        
        insights = {
            'found': True,
            'total_documents': len(search_results),
            'documents': search_results,
            'common_themes': []
        }
        
        all_keywords = set()
        for result in search_results:
            all_keywords.update(result['keywords'])
        
        keyword_counts = defaultdict(int)
        for result in search_results:
            for keyword in result['keywords']:
                keyword_counts[keyword] += 1
        
        common_keywords = [kw for kw, count in keyword_counts.items() if count > 1]
        insights['common_themes'] = common_keywords[:5]
        
        return insights
    
    def add_to_conversation_context(self, user_input: str, response: str):
        """Add to conversation history"""
        self.conversation_context.append({
            'user': user_input,
            'assistant': response,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_conversation_summary(self) -> str:
        """Get summary of current conversation"""
        if not self.conversation_context:
            return "No conversation history yet."
        
        all_text = " ".join([f"{entry['user']} {entry['assistant']}" 
                           for entry in self.conversation_context])
        
        keywords = self._extract_keywords(all_text, top_n=10)
        return f"Conversation topics: {', '.join(keywords)}"

# ==================== CONVERSATION ENGINE ====================
class CrossDocumentConversation:
    """Real-time conversation engine with cross-document understanding"""
    
    def __init__(self):
        self.doc_processor = MultiDocumentProcessor()
        self.conversation_history = []
        self.active_documents = set()
        self.current_context = None
        
        self.response_templates = {
            'single_doc': [
                "Based on {doc_name}, I can tell you that {info}.",
                "The document {doc_name} mentions that {info}.",
                "According to {doc_name}, {info}."
            ],
            'multi_doc': [
                "Looking across multiple documents, I found that {info}.",
                "Based on {doc_count} documents, {info}.",
                "Several documents discuss this. {info}."
            ],
            'cross_ref': [
                "This topic appears in multiple documents. For example, {info}.",
                "There's a connection between documents here. {info}.",
                "Cross-referencing the documents, I see that {info}."
            ],
            'comparison': [
                "Comparing the documents, I notice that {info}.",
                "There are similarities and differences. {info}.",
                "Looking at this across documents, {info}."
            ]
        }
        
        print("=" * 70)
        print("🔍 CROSS-DOCUMENT REAL-TIME CONVERSATION SYSTEM")
        print("=" * 70)
    
    def load_documents(self, folder_path: str = "."):
        """Load documents from folder"""
        success = self.doc_processor.load_all_documents(folder_path)
        
        if success:
            self.active_documents = set(self.doc_processor.documents.keys())
            print("\n📚 Documents loaded and analyzed:")
            for doc_id, doc in self.doc_processor.documents.items():
                print(f"  • {doc['filename']} ({doc['type']})")
                print(f"    Topics: {', '.join(self.doc_processor.document_topics.get(doc_id, []))}")
            
            return True
        return False
    
    def process_query(self, user_query: str) -> Dict:
        """Process user query with cross-document analysis"""
        start_time = time.time()
        
        print(f"\n🔎 Processing query: {user_query}")
        
        search_results = self.doc_processor.search_across_documents(user_query)
        insights = self.doc_processor.get_cross_document_insights(user_query)
        
        if not search_results:
            response_type = 'no_results'
            response = self._generate_no_results_response(user_query)
        elif len(search_results) == 1:
            response_type = 'single_doc'
            response = self._generate_single_doc_response(search_results[0], user_query)
        else:
            response_type = 'multi_doc'
            response = self._generate_multi_doc_response(search_results, insights, user_query)
        
        processing_time = round(time.time() - start_time, 3)
        
        response_entry = {
            'query': user_query,
            'response': response,
            'response_type': response_type,
            'search_results': search_results,
            'insights': insights,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat(),
            'documents_referenced': [r['doc_id'] for r in search_results]
        }
        
        self.conversation_history.append(response_entry)
        self.doc_processor.add_to_conversation_context(user_query, response)
        
        print(f"⏱️  Processed in {processing_time}s")
        print(f"📊 Found {len(search_results)} relevant documents")
        
        return response_entry
    
    def _generate_no_results_response(self, query: str) -> str:
        """Generate response when no documents found"""
        responses = [
            f"I couldn't find specific information about '{query}' in the loaded documents.",
            f"The documents don't seem to contain information about '{query}'.",
            f"I don't see references to '{query}' in the current document collection."
        ]
        
        all_keywords = set()
        for doc in self.doc_processor.documents.values():
            all_keywords.update(doc['keywords'][:5])
        
        similar_keywords = [kw for kw in all_keywords if any(word in kw for word in query.lower().split()[:2])]
        
        if similar_keywords:
            return f"{random.choice(responses)} However, related topics include: {', '.join(similar_keywords[:3])}."
        
        return random.choice(responses)
    
    def _generate_single_doc_response(self, result: Dict, query: str) -> str:
        """Generate response for single document result"""
        template = random.choice(self.response_templates['single_doc'])
        
        info_parts = []
        if result['sentences']:
            info_parts.append(result['sentences'][0])
        
        if result['keywords']:
            info_parts.append(f"Key topics include {', '.join(result['keywords'][:3])}")
        
        info = " ".join(info_parts)
        return template.format(doc_name=result['filename'], info=info)
    
    def _generate_multi_doc_response(self, results: List[Dict], insights: Dict, query: str) -> str:
        """Generate response for multiple document results"""
        template = random.choice(self.response_templates['multi_doc'])
        
        doc_names = [r['filename'] for r in results[:2]]
        all_sentences = []
        
        for result in results[:3]:
            if result['sentences']:
                all_sentences.append(result['sentences'][0])
        
        common_info = ""
        if insights.get('common_themes'):
            common_info = f"Common themes are {', '.join(insights['common_themes'][:3])}. "
        
        info = f"{common_info}For example, {all_sentences[0] if all_sentences else 'this is discussed in multiple contexts.'}"
        
        return template.format(doc_count=len(results), info=info)
    
    def get_conversation_analytics(self) -> Dict:
        """Get analytics about current conversation"""
        if not self.conversation_history:
            return {}
        
        total_queries = len(self.conversation_history)
        unique_docs = set()
        response_types = defaultdict(int)
        
        for entry in self.conversation_history:
            unique_docs.update(entry.get('documents_referenced', []))
            response_types[entry['response_type']] += 1
        
        all_queries = " ".join([entry['query'] for entry in self.conversation_history])
        top_topics = self.doc_processor._extract_keywords(all_queries, top_n=5)
        
        return {
            'total_queries': total_queries,
            'unique_documents_referenced': len(unique_docs),
            'response_type_distribution': dict(response_types),
            'top_topics': top_topics,
            'avg_processing_time': sum(e['processing_time'] for e in self.conversation_history) / total_queries
        }
    
    def get_status(self) -> Dict:
        """Get system status"""
        return {
            'documents_loaded': len(self.doc_processor.documents),
            'conversation_history': len(self.conversation_history),
            'cross_references': sum(len(refs) for refs in self.doc_processor.cross_references.values()),
            'status': 'ready'
        }

# ==================== WEB SERVER ====================
class WebChatHandler(BaseHTTPRequestHandler):
    """HTTP handler for web interface"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self._get_html().encode())
        elif path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = self.server.conversation_engine.get_status()
            self.wfile.write(json.dumps(status).encode())
        elif path == '/chat':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            chat_data = {
                'history': self.server.conversation_engine.conversation_history[-20:],
                'documents': list(self.server.conversation_engine.doc_processor.documents.values())
            }
            self.wfile.write(json.dumps(chat_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/query':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            query = data.get('query', '')
            result = self.server.conversation_engine.process_query(query)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def _get_html(self):
        """Generate HTML interface"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Document Chat</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            background: #4a6fa5;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .chat-area {
            display: flex;
            gap: 20px;
        }
        .conversation {
            flex: 3;
            min-height: 500px;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            overflow-y: auto;
        }
        .documents {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background: #f9f9f9;
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .user {
            background: #e3f2fd;
            text-align: right;
        }
        .assistant {
            background: #f1f8e9;
            text-align: left;
        }
        .input-area {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            padding: 10px 20px;
            background: #4a6fa5;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #3a5a8a;
        }
        .doc-item {
            padding: 8px;
            margin: 5px 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .stats {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status {
            color: #388e3c;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Multi-Document Chat System</h1>
            <p>Chat with all your documents simultaneously</p>
            <div class="stats" id="stats">
                Loading system status...
            </div>
        </div>
        
        <div class="chat-area">
            <div class="conversation" id="conversation">
                <!-- Chat messages will appear here -->
            </div>
            
            <div class="documents">
                <h3>📄 Loaded Documents</h3>
                <div id="documents">
                    <!-- Documents will appear here -->
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="queryInput" placeholder="Ask a question about your documents..." 
                   onkeypress="if(event.keyCode==13) sendQuery()">
            <button onclick="sendQuery()">Send</button>
            <button onclick="clearChat()" style="background: #f44336;">Clear</button>
        </div>
    </div>
    
    <script>
        let conversation = [];
        let documents = [];
        
        function updateStats() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('stats').innerHTML = 
                        `<span class="status">✓ System Ready</span> | 
                         Documents: ${data.documents_loaded} | 
                         Conversations: ${data.conversation_history} |
                         Cross-references: ${data.cross_references}`;
                });
        }
        
        function loadChat() {
            fetch('/chat')
                .then(response => response.json())
                .then(data => {
                    conversation = data.history || [];
                    documents = data.documents || [];
                    displayConversation();
                    displayDocuments();
                });
        }
        
        function displayConversation() {
            const container = document.getElementById('conversation');
            container.innerHTML = '';
            
            if (conversation.length === 0) {
                container.innerHTML = '<p>No conversation yet. Start by asking a question!</p>';
                return;
            }
            
            conversation.forEach(msg => {
                const userDiv = document.createElement('div');
                userDiv.className = 'message user';
                userDiv.innerHTML = `<strong>You:</strong> ${msg.query}`;
                container.appendChild(userDiv);
                
                const assistantDiv = document.createElement('div');
                assistantDiv.className = 'message assistant';
                assistantDiv.innerHTML = `<strong>Assistant:</strong> ${msg.response}<br>
                                         <small>${msg.documents_referenced.length} documents referenced</small>`;
                container.appendChild(assistantDiv);
            });
            
            container.scrollTop = container.scrollHeight;
        }
        
        function displayDocuments() {
            const container = document.getElementById('documents');
            container.innerHTML = '';
            
            documents.forEach(doc => {
                const div = document.createElement('div');
                div.className = 'doc-item';
                div.innerHTML = `<strong>${doc.filename}</strong><br>
                                <small>${doc.type} | ${doc.word_count} words</small>`;
                container.appendChild(div);
            });
        }
        
        function sendQuery() {
            const input = document.getElementById('queryInput');
            const query = input.value.trim();
            
            if (!query) return;
            
            // Add user message immediately
            conversation.push({
                query: query,
                response: 'Thinking...',
                documents_referenced: []
            });
            displayConversation();
            
            // Clear input
            input.value = '';
            
            // Send to server
            fetch('/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: query})
            })
            .then(response => response.json())
            .then(data => {
                // Replace the "Thinking..." message
                conversation.pop();
                conversation.push(data);
                displayConversation();
                updateStats();
            });
        }
        
        function clearChat() {
            if (confirm('Clear conversation history?')) {
                conversation = [];
                displayConversation();
            }
        }
        
        // Load initial data
        updateStats();
        loadChat();
        
        // Refresh stats every 30 seconds
        setInterval(updateStats, 30000);
        
        // Focus on input field
        document.getElementById('queryInput').focus();
    </script>
</body>
</html>
"""
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

class WebChatServer(HTTPServer):
    """Custom HTTP server with conversation engine"""
    
    def __init__(self, server_address, conversation_engine):
        self.conversation_engine = conversation_engine
        super().__init__(server_address, WebChatHandler)

# ==================== MAIN APPLICATION ====================
def create_sample_documents():
    """Create sample documents if none exist"""
    samples = {
        'ai_research.txt': """Artificial Intelligence Research Report

This document discusses the current state of artificial intelligence research.
Key areas include machine learning, natural language processing, and computer vision.

Machine learning algorithms have advanced significantly in recent years.
Deep learning models now achieve human-level performance on many tasks.

Natural language processing enables machines to understand human language.
ChatGPT and similar models demonstrate remarkable language capabilities.

Computer vision systems can now identify objects with high accuracy.
Applications include autonomous vehicles and medical image analysis.

Ethical considerations in AI development are becoming increasingly important.
Researchers must consider bias, privacy, and societal impacts.""",
        
        'tech_report.txt': """Technology Trends Analysis

This report analyzes emerging technology trends for the next decade.
Key technologies include AI, blockchain, quantum computing, and IoT.

Artificial intelligence continues to transform industries.
AI adoption is accelerating across healthcare, finance, and manufacturing.

Blockchain technology enables secure, transparent transactions.
Applications extend beyond cryptocurrency to supply chain and voting systems.

Quantum computing promises exponential speedups for certain problems.
Practical quantum computers may become available within 5-10 years.

Internet of Things connects billions of devices worldwide.
Security and privacy remain major challenges for IoT adoption.""",
        
        'business_strategy.txt': """Business Strategy Document

This document outlines strategic priorities for technology adoption.
Focus areas include digital transformation, innovation, and talent development.

Digital transformation is essential for remaining competitive.
Companies must adopt cloud computing, AI, and automation technologies.

Innovation culture drives long-term success.
Organizations should invest in R&D and encourage experimentation.

Talent development ensures workforce readiness for future technologies.
Upskilling and reskilling programs are critical investments.

Cross-functional collaboration enables better decision-making.
Breaking down silos improves information sharing and innovation.

Risk management must evolve with technological changes.
Cybersecurity and data privacy are top concerns."""
    }
    
    created = 0
    for filename, content in samples.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            created += 1
    
    if created:
        print(f"\n✅ Created {created} sample documents for testing.")
    
    return created > 0

def start_web_server(port=8080):
    """Start the web server"""
    conversation_engine = CrossDocumentConversation()
    
    # Load documents
    print("\n🔄 Loading documents from current folder...")
    conversation_engine.load_documents()
    
    # Start web server
    server = WebChatServer(('localhost', port), conversation_engine)
    print(f"\n🌐 Web server started at: http://localhost:{port}")
    print("   Press Ctrl+C to stop the server\n")
    
    # Open browser automatically
    try:
        webbrowser.open(f'http://localhost:{port}')
    except:
        print("⚠️  Could not open browser automatically. Please open manually.")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped.")
        server.server_close()

def run_terminal_version():
    """Run terminal version"""
    conversation_engine = CrossDocumentConversation()
    
    # Auto-load documents from current folder
    print("\n🔄 Loading documents from current folder...")
    if not conversation_engine.load_documents():
        print("⚠️  No documents loaded. Place PDF/TXT files in folder.")
        create_sample_documents()
        conversation_engine.load_documents()
    
    print("\n💬 Ready! Ask questions about your documents.")
    print("   Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🤖 Processing...", end='', flush=True)
            result = conversation_engine.process_query(user_input)
            print("\r" + " " * 50 + "\r", end='')
            
            print(f"Assistant: {result['response']}")
            
            if result.get('search_results'):
                docs = result['search_results'][:3]
                print(f"\n📄 Referenced documents:")
                for doc in docs:
                    print(f"  • {doc['filename']} ({doc['type']})")
                    
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    """Main entry point"""
    print("\n" + "=" * 70)
    print("🚀 MULTI-DOCUMENT CHAT SYSTEM - COMPLETE EDITION")
    print("=" * 70)
    
    # Check if PyPDF2 is installed
    try:
        import PyPDF2
    except ImportError:
        print("\n📦 Installing required package: PyPDF2")
        import subprocess
        subprocess.check_call(["pip", "install", "PyPDF2"])
        import PyPDF2
    
    print("\n📋 Select mode:")
    print("  1. Web Interface (with local server)")
    print("  2. Terminal Interface")
    print("  3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        print("\n" + "=" * 70)
        print("🌐 Starting Web Interface...")
        print("=" * 70)
        start_web_server()
    elif choice == '2':
        print("\n" + "=" * 70)
        print("💻 Starting Terminal Interface...")
        print("=" * 70)
        run_terminal_version()
    else:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()