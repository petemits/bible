import re
import random
import time
import json
from collections import defaultdict, Counter, deque
from datetime import datetime

# ============================================
# IMPROVED REAL-TIME DIALOGUE ENGINE
# ============================================

class ImprovedDialogueEngine:
    """Fixed version with better memory and verse management"""
    
    def __init__(self, bible_file="bible.txt"):
        self.bible = self.load_bible(bible_file)
        self.participants = []
        self.conversation_log = deque(maxlen=50)  # Increased memory
        self.used_verses = set()  # Track used verses
        self.topic_history = deque(maxlen=10)  # Track topics
        self.current_topic = ""
        self.user_name = "You"
        self.verse_cache = {}  # Cache verses by theme
        self.conversation_depth = 0  # Track how deep we've gone
        
        # Better thinking phrases
        self.thinking_phrases = [
            "Let me reflect on that...",
            "That's an interesting angle...",
            "I need to consider this carefully...",
            "Hmm, you've given me something to ponder...",
            "Let me search the scriptures on this..."
        ]
        
        self.running = False
        
    def load_bible(self, filename):
        """Load and parse Bible text with better indexing"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                text = f.read()
            
            verses = []
            lines = text.strip().split('\n')
            verse_count = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # More robust verse parsing
                patterns = [
                    r'^(\w+)\s+(\d+):(\d+)\s+(.+)$',
                    r'^(\d+):(\d+)\s+(.+)$',
                    r'^(.+?)\s+(\d+):(\d+)\s+(.+)$'
                ]
                
                verse_data = None
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        groups = match.groups()
                        if len(groups) == 4:
                            book, chapter, verse, content = groups
                        elif len(groups) == 3:
                            chapter, verse, content = groups
                            book = "Unknown"
                        else:
                            book, chapter, verse, content = "Unknown", "1", "1", line
                        
                        # Clean content
                        content = content.strip()
                        if not content:
                            continue
                        
                        # Extract themes and keywords
                        themes = self.detect_themes(content)
                        keywords = self.extract_keywords(content)
                        
                        verse_obj = {
                            'id': verse_count,
                            'book': book,
                            'chapter': int(chapter) if chapter.isdigit() else 1,
                            'verse': int(verse) if verse.isdigit() else 1,
                            'content': content,
                            'reference': f"{book} {chapter}:{verse}",
                            'keywords': keywords,
                            'themes': themes,
                            'length': len(content),
                            'used': False
                        }
                        
                        verses.append(verse_obj)
                        verse_count += 1
                        break
            
            print(f"📖 Loaded {len(verses)} Bible verses")
            print(f"📊 Found {len(set([v['book'] for v in verses]))} different books")
            
            # Build theme index
            self.build_theme_index(verses)
            
            return verses
            
        except FileNotFoundError:
            print(f"⚠️  File {filename} not found.")
            return self.create_sample_verses()
    
    def build_theme_index(self, verses):
        """Build comprehensive theme index"""
        self.theme_index = defaultdict(list)
        self.book_index = defaultdict(list)
        
        for verse in verses:
            # Index by theme
            for theme in verse['themes']:
                self.theme_index[theme].append(verse['id'])
            
            # Index by book
            self.book_index[verse['book']].append(verse['id'])
            
            # Index by keyword
            for keyword in verse['keywords']:
                if len(keyword) > 3:  # Only meaningful keywords
                    self.theme_index.setdefault(keyword, []).append(verse['id'])
    
    def extract_keywords(self, text):
        """Extract important keywords with better filtering"""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Comprehensive stopwords
        stopwords = {
            'that', 'this', 'with', 'from', 'have', 'were', 'they', 'their',
            'there', 'what', 'when', 'where', 'which', 'who', 'whom', 'will',
            'would', 'could', 'should', 'been', 'being', 'said', 'says'
        }
        
        # Bible-specific common words to filter
        bible_common = {'lord', 'god', 'shall', 'unto', 'thee', 'thou', 'thy'}
        
        filtered_words = []
        for word in words:
            if (word not in stopwords and 
                word not in bible_common and
                len(word) > 3):
                filtered_words.append(word)
        
        return list(set(filtered_words))[:10]  # Limit to 10 unique keywords
    
    def detect_themes(self, text):
        """Detect themes in the text with better accuracy"""
        text_lower = text.lower()
        themes = []
        
        # Expanded theme patterns
        theme_patterns = {
            'creation': r'created|creat|made|beginning|earth|heaven|light|darkness|day|night',
            'grace': r'grace|mercy|forgive|kindness|compassion|favor|undeserved',
            'love': r'love|beloved|charity|affection|cherish|adore|devotion',
            'faith': r'faith|believe|trust|hope|confidence|assurance|reliance',
            'sin': r'sin|evil|wicked|transgression|wrong|rebellion|disobedience',
            'justice': r'justice|right|judgment|righteous|fair|equity|law',
            'salvation': r'save|salvation|redeem|rescue|deliver|ransom|atonement',
            'hope': r'hope|future|promise|expect|anticipate|look forward',
            'covenant': r'covenant|promise|oath|agreement|pledge|contract|vow',
            'wisdom': r'wisdom|wise|understanding|knowledge|insight|discernment',
            'peace': r'peace|calm|tranquil|serene|harmony|reconciliation',
            'joy': r'joy|rejoice|happy|glad|delight|pleasure|cheerful',
            'perseverance': r'endure|persevere|patience|steadfast|persist|continue',
            'redemption': r'redeem|redemption|restore|recover|reclaim|buy back',
            'forgiveness': r'forgive|pardon|absolve|excuse|release|let go'
        }
        
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, text_lower):
                themes.append(theme)
        
        # If no theme detected, use general categories based on content
        if not themes:
            if len(text) > 100:
                themes.append('teaching')
            elif '?' in text:
                themes.append('question')
            else:
                themes.append('general')
        
        return list(set(themes))  # Remove duplicates
    
    def create_sample_verses(self):
        """Create diverse sample verses"""
        samples = [
            "Genesis 1:1 In the beginning God created the heavens and the earth.",
            "Genesis 1:3 And God said, Let there be light: and there was light.",
            "Genesis 1:5 And God called the light Day, and the darkness he called Night.",
            "Genesis 1:27 So God created man in his own image, in the image of God created he him.",
            "Psalm 23:1 The LORD is my shepherd; I shall not want.",
            "Psalm 23:4 Yea, though I walk through the valley of the shadow of death, I will fear no evil.",
            "Matthew 5:3 Blessed are the poor in spirit: for theirs is the kingdom of heaven.",
            "Matthew 5:9 Blessed are the peacemakers: for they shall be called the children of God.",
            "John 3:16 For God so loved the world, that he gave his only begotten Son.",
            "John 14:6 Jesus saith unto him, I am the way, the truth, and the life.",
            "Romans 3:23 For all have sinned, and come short of the glory of God.",
            "Romans 8:28 And we know that all things work together for good to them that love God.",
            "1 Corinthians 13:4 Charity suffereth long, and is kind; charity envieth not.",
            "1 Corinthians 13:13 And now abideth faith, hope, charity, these three; but the greatest of these is charity.",
            "Philippians 4:13 I can do all things through Christ which strengtheneth me.",
            "Hebrews 11:1 Now faith is the substance of things hoped for, the evidence of things not seen.",
            "James 1:2 My brethren, count it all joy when ye fall into divers temptations.",
            "Revelation 21:4 And God shall wipe away all tears from their eyes; and there shall be no more death."
        ]
        
        verses = []
        for i, sample in enumerate(samples):
            match = re.match(r'^(\w+)\s+(\d+):(\d+)\s+(.+)$', sample)
            if match:
                book, chapter, verse, content = match.groups()
                themes = self.detect_themes(content)
                keywords = self.extract_keywords(content)
                
                verses.append({
                    'id': i,
                    'book': book,
                    'chapter': int(chapter),
                    'verse': int(verse),
                    'content': content,
                    'reference': f"{book} {chapter}:{verse}",
                    'keywords': keywords,
                    'themes': themes,
                    'length': len(content),
                    'used': False
                })
        
        # Build indexes for sample verses too
        self.build_theme_index(verses)
        
        return verses
    
    class ImprovedParticipant:
        """Participant with better memory and response generation"""
        
        def __init__(self, name, personality):
            self.name = name
            self.personality = personality
            self.conversation_memory = deque(maxlen=15)  # Remember last 15 messages
            self.verse_memory = deque(maxlen=20)  # Remember last 20 verses used
            self.focus_themes = personality.get('focus_themes', [])
            self.response_style = personality.get('style', 'balanced')
            self.response_count = 0
            
            # Personal preferences
            self.preferred_books = personality.get('preferred_books', [])
            self.avoid_repetition = personality.get('avoid_repetition', True)
            
        def analyze_message(self, message, full_context):
            """Deep analysis of the message"""
            message_lower = message.lower()
            
            # Detect multiple intents
            intents = []
            if '?' in message:
                intents.append('question')
            if any(word in message_lower for word in ['why', 'how', 'explain']):
                intents.append('explanation')
            if any(word in message_lower for word in ['agree', 'yes', 'right', 'correct']):
                intents.append('agreement')
            if any(word in message_lower for word in ['but', 'however', 'although', 'disagree']):
                intents.append('challenge')
            if any(word in message_lower for word in ['story', 'narrative', 'happened']):
                intents.append('narrative')
            
            # Extract topics from message
            topics = []
            for theme in ['creation', 'grace', 'love', 'faith', 'sin', 'justice', 
                         'hope', 'salvation', 'wisdom', 'peace', 'joy', 'covenant']:
                if theme in message_lower:
                    topics.append(theme)
            
            # Extract emotions
            emotions = []
            positive_words = ['wonderful', 'amazing', 'beautiful', 'joy', 'peace', 'love']
            negative_words = ['difficult', 'hard', 'struggle', 'pain', 'suffering', 'confused']
            
            if any(word in message_lower for word in positive_words):
                emotions.append('positive')
            if any(word in message_lower for word in negative_words):
                emotions.append('concerned')
            
            # Get keywords
            keywords = re.findall(r'\b\w{4,}\b', message_lower)
            
            # Determine depth needed
            word_count = len(message.split())
            if word_count > 25:
                depth = 'deep'
            elif word_count > 10:
                depth = 'medium'
            else:
                depth = 'light'
            
            return {
                'intents': intents if intents else ['discuss'],
                'topics': topics if topics else ['general'],
                'emotions': emotions,
                'keywords': keywords[:8],
                'depth': depth,
                'word_count': word_count
            }
        
        def find_fresh_verses(self, topics, bible_verses, used_verse_ids, limit=3):
            """Find fresh, relevant verses avoiding repetition"""
            candidates = []
            
            for verse in bible_verses:
                # Skip if used recently
                if verse['id'] in used_verse_ids:
                    continue
                
                score = 0
                
                # Theme match (highest priority)
                for topic in topics:
                    if topic in verse['themes']:
                        score += 5
                
                # Keyword match
                for keyword in topics:
                    if any(keyword in word for word in verse['keywords']):
                        score += 2
                
                # Book preference
                if self.preferred_books and verse['book'] in self.preferred_books:
                    score += 1
                
                # Length consideration (avoid very long verses for quick responses)
                if 20 < verse['length'] < 150:
                    score += 1
                
                if score > 0:
                    candidates.append((score, verse))
            
            # Sort by score
            candidates.sort(key=lambda x: x[0], reverse=True)
            
            # Return top candidates
            selected = []
            for score, verse in candidates[:limit]:
                selected.append(verse)
            
            # If no fresh verses found, use less fresh ones
            if not selected and candidates:
                selected = [verse for _, verse in candidates[:limit]]
            
            return selected
        
        def generate_response(self, message_analysis, bible_verses, used_verse_ids, conversation_depth, user_name="You"):
            """Generate unique, context-aware response"""
            
            self.response_count += 1
            
            # Get topics from analysis
            topics = message_analysis['topics']
            intents = message_analysis['intents']
            depth = message_analysis['depth']
            
            # Find fresh verses
            relevant_verses = self.find_fresh_verses(topics, bible_verses, used_verse_ids, 
                                                   limit=3 if depth == 'deep' else 2)
            
            # Remember which verses we're using
            for verse in relevant_verses:
                self.verse_memory.append(verse['id'])
            
            # Generate based on personality
            if self.response_style == 'scholarly':
                response = self._scholarly_response(topics, relevant_verses, intents, depth)
            elif self.response_style == 'pastoral':
                response = self._pastoral_response(topics, relevant_verses, intents, depth, user_name)
            elif self.response_style == 'practical':
                response = self._practical_response(topics, relevant_verses, intents, depth)
            else:
                response = self._general_response(topics, relevant_verses, intents, depth)
            
            # Add variety based on conversation depth
            if conversation_depth > 5:
                # Deeper in conversation, ask more specific questions
                follow_ups = [
                    " What specific aspect interests you most?",
                    " How have you experienced this in your own life?",
                    " What other scriptures come to mind on this topic?"
                ]
                if random.random() > 0.5:
                    response += random.choice(follow_ups)
            
            return response
        
        def _scholarly_response(self, topics, verses, intents, depth):
            """Scholarly, analytical response"""
            if not verses:
                return f"This topic of {topics[0] if topics else 'discussion'} has significant theological implications worth exploring."
            
            verse = random.choice(verses)
            
            openings = [
                f"From a theological perspective on {topics[0] if topics else 'this'}, ",
                f"Examining {topics[0] if topics else 'the scripture'} carefully, ",
                f"The biblical text offers important insights regarding {topics[0] if topics else 'this matter'}. "
            ]
            
            middle = f"Consider {verse['reference']}: '{self._trim_verse(verse['content'], 70)}' "
            
            reflections = [
                "This passage reveals important aspects of divine nature and human response.",
                "We should analyze this in its historical and literary context.",
                "This contributes to our understanding of biblical theology."
            ]
            
            questions = [
                " What interpretive approaches might we apply here?",
                " How does this connect to other biblical themes?",
                " What are the implications for doctrine?"
            ]
            
            return random.choice(openings) + middle + random.choice(reflections) + (random.choice(questions) if random.random() > 0.3 else "")
        
        def _pastoral_response(self, topics, verses, intents, depth, user_name):
            """Pastoral, caring response"""
            if not verses:
                return f"Thinking about {topics[0] if topics else 'this'} brings comfort and challenge to our spiritual journey."
            
            verse = random.choice(verses)
            
            openings = [
                f"Dear {user_name}, as we consider {topics[0] if topics else 'this'}, ",
                f"In pastoral reflection on {topics[0] if topics else 'these things'}, ",
                f"For our spiritual lives regarding {topics[0] if topics else 'this'}, "
            ]
            
            middle = f"the scriptures offer guidance in {verse['reference']}: '{self._trim_verse(verse['content'], 65)}' "
            
            applications = [
                "This speaks to our hearts and calls us to deeper relationship with God.",
                "We can find both comfort and challenge in these words for daily living.",
                "This wisdom guides us in practical faith and loving others."
            ]
            
            questions = [
                f" How does this resonate in your heart, {user_name}?",
                " Where do you see God at work in this?",
                " How might we apply this in our community?"
            ]
            
            return random.choice(openings) + middle + random.choice(applications) + (random.choice(questions) if random.random() > 0.4 else "")
        
        def _practical_response(self, topics, verses, intents, depth):
            """Practical, applicable response"""
            if not verses:
                return f"Regarding {topics[0] if topics else 'this'}, there are meaningful applications for our daily walk."
            
            verse = random.choice(verses)
            
            openings = [
                f"Practically speaking about {topics[0] if topics else 'this'}, ",
                f"For everyday application of {topics[0] if topics else 'biblical truth'}, ",
                f"In terms of living out {topics[0] if topics else 'our faith'}, "
            ]
            
            middle = f"we find direction in {verse['reference']}: '{self._trim_verse(verse['content'], 60)}' "
            
            applications = [
                "This gives us concrete ways to live differently today.",
                "We can implement this wisdom in relationships and decisions.",
                "This translates heavenly truth into earthly action."
            ]
            
            return random.choice(openings) + middle + random.choice(applications)
        
        def _general_response(self, topics, verses, intents, depth):
            """General, conversational response"""
            if not verses:
                return f"Reflecting on {topics[0] if topics else 'this topic'} brings various scriptures to mind."
            
            verse = random.choice(verses)
            
            openings = [
                f"Thinking about {topics[0] if topics else 'that'}, ",
                f"Regarding {topics[0] if topics else 'what you mentioned'}, ",
                f"In response to {topics[0] if topics else 'your thoughts'}, "
            ]
            
            middle = f"I'm reminded of {verse['reference']}: '{self._trim_verse(verse['content'], 75)}' "
            
            connections = [
                "This connects to so much of what we've been discussing.",
                "There's depth here that relates to many aspects of faith.",
                "This verse opens up interesting avenues for conversation."
            ]
            
            return random.choice(openings) + middle + random.choice(connections)
        
        def _trim_verse(self, content, max_length):
            """Trim verse content intelligently"""
            if len(content) <= max_length:
                return content
            
            # Try to cut at sentence end
            sentences = re.split(r'[.!?]+', content)
            result = ""
            for sentence in sentences:
                if len(result + sentence) <= max_length - 3:
                    if result:
                        result += ". " + sentence.strip()
                    else:
                        result = sentence.strip()
                else:
                    break
            
            if result:
                return result + "..."
            
            # If no good sentence break, cut at word boundary
            return content[:max_length-3] + "..."
    
    def create_diverse_participants(self):
        """Create participants with diverse characteristics"""
        participants = [
            self.ImprovedParticipant("James", {
                'style': 'scholarly',
                'focus_themes': ['creation', 'justice', 'covenant', 'wisdom'],
                'preferred_books': ['Genesis', 'Romans', 'Hebrews'],
                'avoid_repetition': True
            }),
            self.ImprovedParticipant("Sarah", {
                'style': 'pastoral',
                'focus_themes': ['grace', 'love', 'hope', 'peace'],
                'preferred_books': ['Psalms', 'John', 'Philippians'],
                'avoid_repetition': True
            }),
            self.ImprovedParticipant("Michael", {
                'style': 'practical',
                'focus_themes': ['faith', 'salvation', 'perseverance', 'forgiveness'],
                'preferred_books': ['Matthew', 'James', '1 Corinthians'],
                'avoid_repetition': True
            }),
            self.ImprovedParticipant("Rachel", {
                'style': 'general',
                'focus_themes': ['joy', 'hope', 'love', 'peace'],
                'preferred_books': ['Psalms', 'Isaiah', 'Ephesians'],
                'avoid_repetition': True
            })
        ]
        
        return participants
    
    def get_fresh_topic(self):
        """Get a fresh topic not recently discussed"""
        all_topics = ['faith', 'hope', 'love', 'grace', 'peace', 'joy', 
                     'wisdom', 'perseverance', 'forgiveness', 'redemption',
                     'covenant', 'creation', 'salvation', 'justice']
        
        # Filter out recently used topics
        recent_topics = list(self.topic_history)[-3:] if len(self.topic_history) >= 3 else []
        available = [t for t in all_topics if t not in recent_topics]
        
        if available:
            return random.choice(available)
        else:
            # If all topics recently used, pick least recent
            return all_topics[0]
    
    def get_verses_for_topic(self, topic, limit=5, avoid_used=True):
        """Get fresh verses for a topic"""
        if topic in self.theme_index:
            verse_ids = self.theme_index[topic]
            
            # Filter out used verses if needed
            if avoid_used:
                fresh_ids = [vid for vid in verse_ids if vid not in self.used_verses]
                if fresh_ids:
                    verse_ids = fresh_ids
            
            # Limit and shuffle
            verse_ids = verse_ids[:limit*3]  # Get more for shuffling
            random.shuffle(verse_ids)
            
            # Convert to verse objects
            verses = []
            for vid in verse_ids[:limit]:
                verse = next((v for v in self.bible if v['id'] == vid), None)
                if verse:
                    verses.append(verse)
            
            return verses
        
        return []
    
    def display_thinking(self, participant_name):
        """Display unique thinking message"""
        phrase = random.choice(self.thinking_phrases)
        print(f"\n{participant_name}: {phrase}")
        time.sleep(1.2 + random.random() * 0.6)  # Variable thinking time
    
    def start_conversation(self):
        """Start the improved conversation"""
        print("\n" + "="*70)
        print("💭 IMPROVED BIBLE CONVERSATION")
        print("="*70)
        print("\nYou're now in a meaningful Bible discussion.")
        print("Participants will remember what's been said and avoid repetition.")
        print("\nCommands:")
        print("  'new topic' - Change discussion subject")
        print("  'verses about X' - Get specific verses")
        print("  'summary' - See conversation summary")
        print("  'quit' - End conversation")
        print("-"*70)
        
        # Create diverse participants
        self.participants = self.create_diverse_participants()
        participant_names = ", ".join([p.name for p in self.participants])
        print(f"\n👥 Today's participants: {participant_names}")
        
        # Get user's name
        user_name = input("\nWhat's your name? (Press Enter for 'You'): ").strip()
        if user_name:
            self.user_name = user_name
        
        # Start with a fresh topic
        self.current_topic = self.get_fresh_topic()
        self.topic_history.append(self.current_topic)
        
        print(f"\n💡 Starting topic: {self.current_topic.upper()}")
        
        # Show a fresh verse
        verses = self.get_verses_for_topic(self.current_topic, limit=1)
        if verses:
            verse = verses[0]
            self.used_verses.add(verse['id'])
            print(f"📖 {verse['reference']}: {self._trim_for_display(verse['content'], 100)}")
        
        print("\n" + "-"*70)
        
        # Initial question from a participant
        first_speaker = random.choice(self.participants)
        questions = [
            f"What are your thoughts on {self.current_topic}?",
            f"How do you understand {self.current_topic} in your spiritual journey?",
            f"What does {self.current_topic} mean to you personally?"
        ]
        
        print(f"\n{first_speaker.name}: {random.choice(questions)}")
        
        # Main conversation loop
        self.running = True
        turn_count = 0
        
        while self.running:
            try:
                # Get user input
                prompt = f"\n{self.user_name}: "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() == 'quit':
                    print("\nEnding conversation...")
                    self.running = False
                    break
                
                if user_input.lower() == 'new topic':
                    new_topic = input("What topic would you like to discuss? ").strip().lower()
                    if new_topic:
                        self.current_topic = new_topic
                        self.topic_history.append(new_topic)
                        self.conversation_depth = 0  # Reset depth for new topic
                        print(f"\n[Topic changed to: {self.current_topic.upper()}]")
                        
                        # Show a fresh verse for new topic
                        verses = self.get_verses_for_topic(self.current_topic, limit=1)
                        if verses:
                            verse = verses[0]
                            self.used_verses.add(verse['id'])
                            print(f"📖 {verse['reference']}: {self._trim_for_display(verse['content'], 90)}...")
                        
                        # Ask about new topic
                        speaker = random.choice(self.participants)
                        print(f"\n{speaker.name}: So, what are your thoughts on {self.current_topic}?")
                    
                    continue
                
                if user_input.lower().startswith('verses about '):
                    topic = user_input[13:].strip()
                    verses = self.get_verses_for_topic(topic, limit=3, avoid_used=False)
                    if verses:
                        print(f"\n📚 Verses about {topic}:")
                        for i, verse in enumerate(verses, 1):
                            print(f"   {i}. {verse['reference']}: {self._trim_for_display(verse['content'], 70)}")
                    else:
                        print(f"\nNo verses found about '{topic}'")
                    continue
                
                if user_input.lower() == 'summary':
                    self.show_current_summary()
                    continue
                
                # Log user's message
                self.conversation_log.append({
                    'speaker': self.user_name,
                    'message': user_input,
                    'turn': turn_count,
                    'topic': self.current_topic
                })
                
                # Update conversation depth
                self.conversation_depth += 1
                turn_count += 1
                
                # Determine how many participants respond (1-2)
                num_responders = 1 if self.conversation_depth < 3 else random.randint(1, 2)
                responders = random.sample(self.participants, min(num_responders, len(self.participants)))
                
                for participant in responders:
                    # Show thinking
                    self.display_thinking(participant.name)
                    
                    # Analyze message with full context
                    recent_context = list(self.conversation_log)[-5:] if len(self.conversation_log) >= 5 else list(self.conversation_log)
                    message_analysis = participant.analyze_message(user_input, recent_context)
                    
                    # Generate response
                    used_ids = list(self.used_verses)
                    response = participant.generate_response(
                        message_analysis, 
                        self.bible,
                        used_ids,
                        self.conversation_depth,
                        self.user_name
                    )
                    
                    print(f"{participant.name}: {response}")
                    
                    # Log response
                    self.conversation_log.append({
                        'speaker': participant.name,
                        'message': response,
                        'turn': turn_count,
                        'topic': self.current_topic
                    })
                    
                    # Extract and mark verse references as used
                    verse_refs = re.findall(r'(\w+\s+\d+:\d+)', response)
                    for ref in verse_refs:
                        # Find verse by reference
                        for verse in self.bible:
                            if verse['reference'].startswith(ref):
                                self.used_verses.add(verse['id'])
                                break
                    
                    turn_count += 1
                
                # Occasionally suggest topic change when conversation gets deep
                if self.conversation_depth > 8 and random.random() > 0.7:
                    new_topic = self.get_fresh_topic()
                    print(f"\n💡 [We've discussed {self.current_topic} deeply. Would you like to explore {new_topic} instead? Type 'new topic' to switch.]")
                
                # Occasionally have a participant add unsolicited thought
                if random.random() > 0.8 and len(self.participants) > num_responders:
                    remaining = [p for p in self.participants if p not in responders]
                    if remaining:
                        participant = random.choice(remaining)
                        time.sleep(0.8)
                        
                        additions = [
                            "I'd like to add something to this...",
                            "Another thought occurs to me...",
                            "This discussion reminds me of something else..."
                        ]
                        
                        print(f"\n{participant.name}: {random.choice(additions)}")
                        
                        # Generate additional response based on conversation
                        last_messages = [entry['message'] for entry in list(self.conversation_log)[-3:]]
                        combined_context = ' '.join(last_messages)
                        analysis = participant.analyze_message(combined_context, [])
                        
                        used_ids = list(self.used_verses)
                        response = participant.generate_response(
                            analysis,
                            self.bible,
                            used_ids,
                            self.conversation_depth,
                            self.user_name
                        )
                        
                        print(f"{participant.name}: {response}")
                        
                        self.conversation_log.append({
                            'speaker': participant.name,
                            'message': response,
                            'turn': turn_count,
                            'topic': self.current_topic
                        })
                        
                        turn_count += 1
                
            except KeyboardInterrupt:
                print("\n\nConversation ended.")
                self.running = False
                break
            except Exception as e:
                print(f"\n⚠️  Error: {e}")
                continue
        
        # End conversation
        self.end_conversation()
    
    def _trim_for_display(self, text, max_len):
        """Trim text for display"""
        if len(text) <= max_len:
            return text
        return text[:max_len-3] + "..."
    
    def show_current_summary(self):
        """Show current conversation summary"""
        print("\n" + "="*50)
        print("CURRENT CONVERSATION SUMMARY")
        print("="*50)
        
        print(f"\nTopic: {self.current_topic.upper()}")
        print(f"Depth: {self.conversation_depth} exchanges")
        print(f"Participants active: {len(set([entry['speaker'] for entry in list(self.conversation_log)[-10:]]))}")
        
        # Recent themes
        recent_messages = ' '.join([entry['message'] for entry in list(self.conversation_log)[-5:]])
        themes_mentioned = []
        for theme in ['faith', 'hope', 'love', 'grace', 'peace', 'joy', 'wisdom']:
            if theme in recent_messages.lower():
                themes_mentioned.append(theme)
        
        if themes_mentioned:
            print(f"Recent themes: {', '.join(themes_mentioned)}")
        
        print(f"Verses used: {len(self.used_verses)}")
        print("\n" + "-"*50)
    
    def end_conversation(self):
        """End conversation with summary"""
        print("\n" + "="*70)
        print("📊 CONVERSATION COMPLETE - SUMMARY")
        print("="*70)
        
        total_exchanges = len(self.conversation_log)
        print(f"\nTotal exchanges: {total_exchanges}")
        
        # Participant contributions
        contributions = Counter([entry['speaker'] for entry in self.conversation_log])
        print("\nContributions:")
        for speaker, count in contributions.most_common():
            if speaker != self.user_name:
                print(f"  {speaker}: {count} responses")
        
        # Topics covered
        topics_covered = set()
        for entry in self.conversation_log:
            message = entry['message'].lower()
            for theme in ['faith', 'hope', 'love', 'grace', 'peace', 'joy', 
                         'wisdom', 'creation', 'salvation', 'justice']:
                if theme in message:
                    topics_covered.add(theme)
        
        if topics_covered:
            print(f"\nTopics covered: {', '.join(sorted(topics_covered))}")
        
        # Verses used
        print(f"\nUnique verses referenced: {len(self.used_verses)}")
        
        # Save conversation
        self.save_conversation()
        
        print("\n" + "="*70)
        print("🙏 Thank you for the meaningful discussion!")
        print("="*70)
    
    def save_conversation(self):
        """Save conversation to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bible_conversation_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("MEANINGFUL BIBLE CONVERSATION\n")
            f.write("="*60 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Participants: {self.user_name}, {', '.join([p.name for p in self.participants])}\n")
            f.write(f"Main topic: {self.current_topic}\n\n")
            f.write("CONVERSATION LOG:\n")
            f.write("-"*60 + "\n\n")
            
            for entry in self.conversation_log:
                f.write(f"[{entry.get('turn', '?')}] {entry['speaker']}: {entry['message']}\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write(f"Total exchanges: {len(self.conversation_log)}\n")
            f.write(f"Unique verses: {len(self.used_verses)}\n")
        
        print(f"\n💾 Full conversation saved to: {filename}")

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Run the improved conversation system"""
    
    print("🚀 IMPROVED BIBLE CONVERSATION SYSTEM")
    print("Loading with better memory and verse management...")
    
    # Create and start engine
    engine = ImprovedDialogueEngine("bible.txt")
    
    # Start conversation
    engine.start_conversation()

if __name__ == "__main__":
    main()