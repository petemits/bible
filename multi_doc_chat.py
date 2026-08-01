# File: multi_doc_chat.py
"""
MULTI-DOCUMENT REAL-TIME CONVERSATION SYSTEM
Chat with multiple documents simultaneously with cross-document understanding
"""

import os
import re
import json
import time
import PyPDF2
import textract
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict, deque
import hashlib
import pickle

# ==================== DOCUMENT PROCESSOR ====================
class MultiDocumentProcessor:
    """Process multiple documents and maintain cross-document context"""
    
    def __init__(self):
        self.documents = {}  # Store all documents
        self.document_vectors = {}  # Semantic vectors per document
        self.cross_references = defaultdict(set)  # Cross-document references
        self.document_topics = {}  # Topics per document
        self.conversation_context = deque(maxlen=50)  # Recent conversation
        
    def load_all_documents(self, folder_path: str = "."):
        """Load all supported documents from folder"""
        print(f"\n📂 Loading all documents from: {folder_path}")
        
        supported_extensions = ['.pdf', '.txt', '.md', '.docx']
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
                        
                        # Process document
                        processed = self._process_document(content, file, doc_id)
                        self.documents[doc_id] = processed
                        loaded_count += 1
                        
                        print(f"  ✓ Loaded: {file} ({len(content):,} chars)")
                        
                    except Exception as e:
                        print(f"  ✗ Error loading {file}: {e}")
        
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
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except:
            # Fallback to textract
            try:
                return textract.process(pdf_path).decode('utf-8')
            except:
                return ""
    
    def _process_document(self, content: str, filename: str, doc_id: str) -> Dict:
        """Process a single document and extract features"""
        
        # Basic NLP processing
        sentences = self._extract_sentences(content)
        paragraphs = self._extract_paragraphs(content)
        keywords = self._extract_keywords(content)
        entities = self._extract_entities(content)
        
        # Document analysis
        document_type = self._classify_document(content)
        
        return {
            'id': doc_id,
            'filename': filename,
            'content': content,
            'sentences': sentences,
            'paragraphs': paragraphs,
            'keywords': keywords[:20],  # Top 20 keywords
            'entities': entities,
            'type': document_type,
            'length': len(content),
            'word_count': len(content.split()),
            'loaded_at': datetime.now().isoformat(),
            'metadata': {
                'sentence_count': len(sentences),
                'paragraph_count': len(paragraphs),
                'entity_count': len(entities),
                'keyword_count': len(keywords)
            }
        }
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs
    
    def _extract_keywords(self, text: str, top_n: int = 30) -> List[str]:
        """Extract important keywords from text"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        words = [w for w in words if w not in stop_words]
        
        # Count frequency
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        entities = []
        
        # Capitalized phrases (potential proper nouns)
        capital_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capital_words)
        
        # Acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        entities.extend(acronyms)
        
        # Dates
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
        entities.extend(dates)
        
        return list(set(entities))
    
    def _classify_document(self, content: str) -> str:
        """Classify document type based on content"""
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
        """Build references between documents based on shared content"""
        print("\n🔗 Building cross-document references...")
        
        # Collect all entities and keywords across documents
        all_entities = defaultdict(list)
        all_keywords = defaultdict(list)
        
        for doc_id, doc in self.documents.items():
            for entity in doc['entities']:
                all_entities[entity].append(doc_id)
            for keyword in doc['keywords']:
                all_keywords[keyword].append(doc_id)
        
        # Create cross-references
        for entity, doc_list in all_entities.items():
            if len(doc_list) > 1:  # Entity appears in multiple documents
                for doc_id in doc_list:
                    self.cross_references[doc_id].add((entity, 'entity', doc_list))
        
        for keyword, doc_list in all_keywords.items():
            if len(doc_list) > 1:  # Keyword appears in multiple documents
                for doc_id in doc_list:
                    self.cross_references[doc_id].add((keyword, 'keyword', doc_list))
        
        print(f"  Found {sum(len(refs) for refs in self.cross_references.values())} cross-references")
    
    def _extract_document_topics(self):
        """Extract main topics from each document"""
        print("\n📊 Extracting document topics...")
        
        for doc_id, doc in self.documents.items():
            # Use keywords as topics
            topics = doc['keywords'][:5]  # Top 5 keywords as topics
            self.document_topics[doc_id] = topics
            
            # Add document type as topic
            self.document_topics[doc_id].append(f"type:{doc['type']}")
    
    def search_across_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for query across all documents"""
        query_lower = query.lower()
        results = []
        
        for doc_id, doc in self.documents.items():
            doc_content = doc['content'].lower()
            
            # Check for direct matches
            if query_lower in doc_content:
                # Find sentences containing the query
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
        
        # Sort by relevance score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _calculate_relevance_score(self, doc_content: str, query: str) -> float:
        """Calculate relevance score between document and query"""
        # Simple frequency-based scoring
        query_words = query.split()
        score = 0
        
        for word in query_words:
            if len(word) > 3:  # Ignore short words
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
            'common_themes': [],
            'contradictions': [],
            'complementary_info': []
        }
        
        # Find common themes across documents
        all_keywords = set()
        for result in search_results:
            all_keywords.update(result['keywords'])
        
        # Keywords that appear in multiple documents
        keyword_counts = defaultdict(int)
        for result in search_results:
            for keyword in result['keywords']:
                keyword_counts[keyword] += 1
        
        common_keywords = [kw for kw, count in keyword_counts.items() if count > 1]
        insights['common_themes'] = common_keywords[:5]
        
        # Check for cross-references
        doc_ids = [r['doc_id'] for r in search_results]
        cross_refs = []
        
        for doc_id in doc_ids:
            if doc_id in self.cross_references:
                for ref in self.cross_references[doc_id]:
                    entity, ref_type, ref_docs = ref
                    # Check if this reference involves our searched documents
                    if len(set(ref_docs) & set(doc_ids)) > 1:
                        cross_refs.append({
                            'entity': entity,
                            'type': ref_type,
                            'documents': ref_docs
                        })
        
        insights['cross_references'] = cross_refs[:5]
        
        return insights
    
    def add_to_conversation_context(self, user_input: str, response: str):
        """Add to conversation history for context"""
        self.conversation_context.append({
            'user': user_input,
            'assistant': response,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_conversation_summary(self) -> str:
        """Get summary of current conversation"""
        if not self.conversation_context:
            return "No conversation history yet."
        
        # Extract topics from conversation
        all_text = " ".join([f"{entry['user']} {entry['assistant']}" 
                           for entry in self.conversation_context])
        
        keywords = self._extract_keywords(all_text, top_n=10)
        
        return f"Conversation topics: {', '.join(keywords)}"

# ==================== REAL-TIME CONVERSATION ENGINE ====================
class CrossDocumentConversation:
    """Real-time conversation engine with cross-document understanding"""
    
    def __init__(self):
        self.doc_processor = MultiDocumentProcessor()
        self.conversation_history = []
        self.active_documents = set()
        self.current_context = None
        
        # Response templates for different scenarios
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
        
        # Search across all documents
        search_results = self.doc_processor.search_across_documents(user_query)
        
        # Get cross-document insights
        insights = self.doc_processor.get_cross_document_insights(user_query)
        
        # Determine response type
        if not search_results:
            response_type = 'no_results'
            response = self._generate_no_results_response(user_query)
        
        elif len(search_results) == 1:
            response_type = 'single_doc'
            response = self._generate_single_doc_response(search_results[0], user_query)
        
        else:
            response_type = 'multi_doc'
            response = self._generate_multi_doc_response(search_results, insights, user_query)
        
        # Check for cross-references
        if insights.get('cross_references'):
            cross_ref_info = self._extract_cross_reference_info(insights['cross_references'])
            if cross_ref_info:
                response += f" {cross_ref_info}"
                response_type = 'cross_ref'
        
        # Add document comparison if multiple documents
        if len(search_results) > 1:
            comparison = self._generate_document_comparison(search_results)
            if comparison:
                response += f" {comparison}"
                response_type = 'comparison'
        
        # Process conversation context
        context_info = self._get_conversation_context()
        if context_info:
            response = f"{context_info} {response}"
        
        # Create response entry
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
        
        # Add to history
        self.conversation_history.append(response_entry)
        
        # Update conversation context
        self.doc_processor.add_to_conversation_context(user_query, response)
        
        # Update current context
        self.current_context = {
            'last_query': user_query,
            'referenced_docs': [r['doc_id'] for r in search_results],
            'topics': insights.get('common_themes', [])
        }
        
        print(f"⏱️  Processed in {processing_time}s")
        print(f"📊 Found {len(search_results)} relevant documents")
        if insights.get('common_themes'):
            print(f"🎯 Common themes: {', '.join(insights['common_themes'][:3])}")
        
        return response_entry
    
    def _generate_no_results_response(self, query: str) -> str:
        """Generate response when no documents found"""
        responses = [
            f"I couldn't find specific information about '{query}' in the loaded documents.",
            f"The documents don't seem to contain information about '{query}'.",
            f"I don't see references to '{query}' in the current document collection."
        ]
        
        # Suggest similar topics
        all_keywords = set()
        for doc in self.doc_processor.documents.values():
            all_keywords.update(doc['keywords'][:5])
        
        similar_keywords = [kw for kw in all_keywords if any(word in kw for word in query.lower().split()[:2])]
        
        if similar_keywords:
            return f"{np.random.choice(responses)} However, related topics include: {', '.join(similar_keywords[:3])}."
        
        return np.random.choice(responses)
    
    def _generate_single_doc_response(self, result: Dict, query: str) -> str:
        """Generate response for single document result"""
        template = np.random.choice(self.response_templates['single_doc'])
        
        # Extract relevant info
        info_parts = []
        if result['sentences']:
            info_parts.append(result['sentences'][0])
        
        if result['keywords']:
            info_parts.append(f"Key topics include {', '.join(result['keywords'][:3])}")
        
        info = " ".join(info_parts)
        
        return template.format(doc_name=result['filename'], info=info)
    
    def _generate_multi_doc_response(self, results: List[Dict], insights: Dict, query: str) -> str:
        """Generate response for multiple document results"""
        template = np.random.choice(self.response_templates['multi_doc'])
        
        # Combine information from multiple documents
        doc_names = [r['filename'] for r in results[:2]]
        all_sentences = []
        
        for result in results[:3]:
            if result['sentences']:
                all_sentences.append(result['sentences'][0])
        
        # Get common themes
        common_info = ""
        if insights.get('common_themes'):
            common_info = f"Common themes are {', '.join(insights['common_themes'][:3])}. "
        
        info = f"{common_info}For example, {all_sentences[0] if all_sentences else 'this is discussed in multiple contexts.'}"
        
        return template.format(
            doc_count=len(results),
            info=info
        )
    
    def _extract_cross_reference_info(self, cross_refs: List[Dict]) -> str:
        """Extract cross-reference information"""
        if not cross_refs:
            return ""
        
        ref = cross_refs[0]  # Use first cross-reference
        entity = ref['entity']
        docs = ref['documents']
        
        doc_names = []
        for doc_id in docs[:3]:
            if doc_id in self.doc_processor.documents:
                doc_names.append(self.doc_processor.documents[doc_id]['filename'])
        
        if doc_names:
            return f"The term '{entity}' appears in {len(docs)} documents including {', '.join(doc_names)}."
        
        return ""
    
    def _generate_document_comparison(self, results: List[Dict]) -> str:
        """Generate document comparison information"""
        if len(results) < 2:
            return ""
        
        # Compare document types
        doc_types = [r['type'] for r in results]
        unique_types = list(set(doc_types))
        
        if len(unique_types) > 1:
            return f"These documents include different types: {', '.join(unique_types)}."
        
        # Compare keywords
        all_keywords = []
        for result in results[:3]:
            all_keywords.extend(result['keywords'][:3])
        
        # Find most common keywords
        keyword_counts = defaultdict(int)
        for keyword in all_keywords:
            keyword_counts[keyword] += 1
        
        common_keywords = [kw for kw, count in keyword_counts.items() if count > 1]
        
        if common_keywords:
            return f"Shared topics include: {', '.join(common_keywords[:3])}."
        
        return "The documents approach this topic from different perspectives."
    
    def _get_conversation_context(self) -> str:
        """Get context from recent conversation"""
        if len(self.doc_processor.conversation_context) < 2:
            return ""
        
        # Get last user query
        last_entries = list(self.doc_processor.conversation_context)[-2:]
        last_topics = []
        
        for entry in last_entries:
            # Extract keywords from last conversation
            text = f"{entry['user']} {entry['assistant']}"
            keywords = self.doc_processor._extract_keywords(text, top_n=3)
            last_topics.extend(keywords)
        
        if last_topics:
            unique_topics = list(set(last_topics))[:3]
            return f"Continuing our discussion about {', '.join(unique_topics)}... "
        
        return ""
    
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
        
        # Most discussed topics
        all_queries = " ".join([entry['query'] for entry in self.conversation_history])
        top_topics = self.doc_processor._extract_keywords(all_queries, top_n=5)
        
        return {
            'total_queries': total_queries,
            'unique_documents_referenced': len(unique_docs),
            'response_type_distribution': dict(response_types),
            'top_topics': top_topics,
            'avg_processing_time': sum(e['processing_time'] for e in self.conversation_history) / total_queries
        }

# ==================== USER INTERFACE ====================
class DocumentChatInterface:
    """Interactive interface for cross-document conversation"""
    
    def __init__(self):
        self.conversation_engine = CrossDocumentConversation()
        self.running = True
    
    def display_banner(self):
        """Display application banner"""
        print("\n" + "=" * 70)
        print("💬 MULTI-DOCUMENT INTELLIGENT CONVERSATION")
        print("=" * 70)
        print("\n📚 Features:")
        print("  • Chat with multiple documents simultaneously")
        print("  • Cross-document analysis and references")
        print("  • Real-time document comparison")
        print("  • Intelligent topic tracking")
        print("\n📋 Commands:")
        print("  /load    - Load/reload documents from folder")
        print("  /docs    - Show loaded documents")
        print("  /topics  - Show document topics")
        print("  /stats   - Conversation statistics")
        print("  /export  - Export conversation")
        print("  /clear   - Clear conversation")
        print("  /help    - Show this help")
        print("  /quit    - Exit application")
        print("=" * 70)
    
    def run(self):
        """Main application loop"""
        self.display_banner()
        
        # Auto-load documents from current folder
        print("\n🔄 Auto-loading documents from current folder...")
        if not self.conversation_engine.load_documents():
            print("⚠️  No documents loaded. Place PDF/TXT files in folder or use /load")
        
        print("\n💬 Ready! Ask questions about your documents.")
        print("   Example: 'What do the documents say about AI?'")
        print("   Example: 'Compare the approaches in different documents'")
        print("   Example: 'Find common themes across all documents'\n")
        
        while self.running:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                    continue
                
                # Process query
                print("🤖 Processing...", end='', flush=True)
                result = self.conversation_engine.process_query(user_input)
                print("\r" + " " * 50 + "\r", end='')  # Clear line
                
                # Display response
                print(f"Assistant: {result['response']}")
                
                # Show document references
                if result.get('search_results'):
                    docs = result['search_results'][:3]
                    print(f"\n📄 Referenced documents:")
                    for doc in docs:
                        print(f"  • {doc['filename']} ({doc['type']})")
                
                # Show insights if available
                if result['insights'].get('cross_references'):
                    print(f"\n🔗 Cross-document connections found!")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted. Type /quit to exit.")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type /help for assistance.")
    
    def handle_command(self, command: str):
        """Handle user commands"""
        cmd = command.lower().strip()
        
        if cmd == '/load':
            print("\n📂 Loading documents...")
            self.conversation_engine.load_documents()
            
        elif cmd == '/docs':
            self._show_documents()
            
        elif cmd == '/topics':
            self._show_topics()
            
        elif cmd == '/stats':
            self._show_statistics()
            
        elif cmd == '/export':
            self._export_conversation()
            
        elif cmd == '/clear':
            self.conversation_engine.conversation_history = []
            print("\n🗑️  Conversation cleared!")
            
        elif cmd == '/help':
            self.display_banner()
            
        elif cmd == '/quit':
            self.running = False
            print("\n👋 Goodbye! Thanks for using the system.")
            
        else:
            print("❌ Unknown command. Type /help for available commands.")
    
    def _show_documents(self):
        """Show loaded documents"""
        if not self.conversation_engine.doc_processor.documents:
            print("\n📭 No documents loaded.")
            return
        
        print(f"\n📚 LOADED DOCUMENTS ({len(self.conversation_engine.doc_processor.documents)})")
        print("-" * 60)
        
        for doc_id, doc in self.conversation_engine.doc_processor.documents.items():
            print(f"\n📄 {doc['filename']}")
            print(f"  Type: {doc['type']}")
            print(f"  Size: {doc['word_count']:,} words")
            print(f"  Topics: {', '.join(self.conversation_engine.doc_processor.document_topics.get(doc_id, []))}")
            
            # Show cross-references
            if doc_id in self.conversation_engine.doc_processor.cross_references:
                refs = list(self.conversation_engine.doc_processor.cross_references[doc_id])[:3]
                if refs:
                    entities = [ref[0] for ref in refs]
                    print(f"  Cross-references: {', '.join(entities)}")
    
    def _show_topics(self):
        """Show topics across all documents"""
        if not self.conversation_engine.doc_processor.document_topics:
            print("\n📊 No topics extracted yet.")
            return
        
        print("\n📊 DOCUMENT TOPICS ANALYSIS")
        print("-" * 60)
        
        # Collect all topics
        all_topics = defaultdict(list)
        for doc_id, topics in self.conversation_engine.doc_processor.document_topics.items():
            for topic in topics:
                all_topics[topic].append(doc_id)
        
        # Show most common topics
        print("\n🔥 Most Common Topics:")
        for topic, doc_list in sorted(all_topics.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            doc_names = []
            for doc_id in doc_list[:3]:
                if doc_id in self.conversation_engine.doc_processor.documents:
                    doc_names.append(self.conversation_engine.doc_processor.documents[doc_id]['filename'])
            
            print(f"  • {topic}: {len(doc_list)} documents")
            if doc_names:
                print(f"    Examples: {', '.join(doc_names)}")
    
    def _show_statistics(self):
        """Show conversation statistics"""
        analytics = self.conversation_engine.get_conversation_analytics()
        
        if not analytics:
            print("\n📊 No conversation statistics yet.")
            return
        
        print("\n📊 CONVERSATION ANALYTICS")
        print("-" * 60)
        print(f"Total queries: {analytics['total_queries']}")
        print(f"Documents referenced: {analytics['unique_documents_referenced']}")
        print(f"Average processing time: {analytics['avg_processing_time']:.2f}s")
        
        if analytics['top_topics']:
            print(f"\n🔥 Top discussion topics:")
            for topic in analytics['top_topics']:
                print(f"  • {topic}")
        
        if analytics['response_type_distribution']:
            print(f"\n📈 Response types:")
            for rtype, count in analytics['response_type_distribution'].items():
                print(f"  • {rtype}: {count}")
    
    def _export_conversation(self):
        """Export conversation to file"""
        if not self.conversation_engine.conversation_history:
            print("\n📭 No conversation to export.")
            return
        
        filename = f"cross_doc_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("CROSS-DOCUMENT CONVERSATION EXPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total queries: {len(self.conversation_engine.conversation_history)}\n\n")
            
            # Document list
            f.write("📚 DOCUMENTS:\n")
            for doc in self.conversation_engine.doc_processor.documents.values():
                f.write(f"  • {doc['filename']} ({doc['type']})\n")
            
            f.write("\n" + "=" * 60 + "\n\n")
            f.write("💬 CONVERSATION:\n\n")
            
            # Conversation history
            for i, entry in enumerate(self.conversation_engine.conversation_history, 1):
                f.write(f"Q{i}: {entry['query']}\n")
                f.write(f"A{i}: {entry['response']}\n")
                
                if entry.get('search_results'):
                    f.write(f"   📄 Referenced: ")
                    docs = [r['filename'] for r in entry['search_results'][:3]]
                    f.write(f"{', '.join(docs)}\n")
                
                f.write("\n")
            
            # Analytics
            analytics = self.conversation_engine.get_conversation_analytics()
            if analytics:
                f.write("\n" + "=" * 60 + "\n")
                f.write("📊 STATISTICS:\n")
                f.write(f"  Total queries: {analytics['total_queries']}\n")
                f.write(f"  Unique documents: {analytics['unique_documents_referenced']}\n")
                f.write(f"  Avg processing time: {analytics['avg_processing_time']:.2f}s\n")
        
        print(f"✅ Conversation exported to {filename}")

# ==================== MAIN EXECUTION ====================
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
        
        'business_strategy.pdf.txt': """Business Strategy Document

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
            print(f"  Created: {filename}")
    
    if created:
        print(f"\n✅ Created {created} sample documents for testing.")
    
    return created > 0

def main():
    """Main entry point"""
    print("\n" + "=" * 70)
    print("🚀 CROSS-DOCUMENT CONVERSATION SYSTEM - STARTING UP")
    print("=" * 70)
    
    # Check for documents
    supported_files = [f for f in os.listdir('.') 
                      if f.lower().endswith(('.pdf', '.txt', '.md', '.docx'))]
    
    if not supported_files:
        print("\n📝 No documents found. Creating sample documents...")
        create_sample_documents()
        supported_files = ['ai_research.txt', 'tech_report.txt', 'business_strategy.pdf.txt']
    
    print(f"\n📂 Found {len(supported_files)} document(s) in folder:")
    for file in supported_files:
        print(f"  • {file}")
    
    # Start the application
    ui = DocumentChatInterface()
    ui.run()

if __name__ == "__main__":
    main()