import re
import random
import time
import json
from collections import defaultdict, Counter
from datetime import datetime
import threading

# ============================================
# REAL-TIME CONVERSATION ENGINE
# ============================================

class RealTimeDialogueEngine:
    """Real-time Bible conversation where YOU participate"""
    
    def __init__(self, bible_file="bible.txt"):
        self.bible = self.load_bible(bible_file)
        self.participants = []
        self.conversation_log = []
        self.current_topic = ""
        self.user_name = "You"
        self.thinking_phrases = [
            "Let me think about that...",
            "Hmm, interesting point...",
            "Give me a moment to consider...",
            "I need to reflect on that..."
        ]
        self.running = False
        
    def load_bible(self, filename):
        """Load and parse Bible text"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Parse verses
            verses = []
            lines = text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to parse verse reference
                verse_match = re.match(r'(\w+)?\s*(\d+):(\d+)\s+(.+)', line)
                if verse_match:
                    book, chapter, verse, content = verse_match.groups()
                    book = book or "Unknown"
                    verses.append({
                        'book': book,
                        'chapter': int(chapter),
                        'verse': int(verse),
                        'content': content.strip(),
                        'reference': f"{book} {chapter}:{verse}",
                        'keywords': self.extract_keywords(content),
                        'themes': self.detect_themes(content)
                    })
            
            print(f"📖 Loaded {len(verses)} Bible verses")
            return verses
            
        except FileNotFoundError:
            print(f"⚠️  File {filename} not found. Using sample verses.")
            return self.create_sample_verses()
    
    def extract_keywords(self, text):
        """Extract important keywords from text"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {'the', 'and', 'but', 'for', 'with', 'that', 'this', 'was', 'were'}
        return [w for w in words if w not in stopwords]
    
    def detect_themes(self, text):
        """Detect themes in the text"""
        text_lower = text.lower()
        themes = []
        
        theme_patterns = {
            'creation': r'created|made|beginning|earth|heaven',
            'grace': r'grace|mercy|forgive|kindness',
            'love': r'love|beloved|charity|affection',
            'faith': r'faith|believe|trust|hope',
            'sin': r'sin|evil|wicked|transgression',
            'justice': r'justice|right|judgment|righteous',
            'salvation': r'save|salvation|redeem|rescue',
            'hope': r'hope|future|promise|expect'
        }
        
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, text_lower):
                themes.append(theme)
        
        return themes if themes else ['general']
    
    def create_sample_verses(self):
        """Create sample verses if no file is found"""
        samples = [
            "Genesis 1:1 In the beginning God created the heavens and the earth.",
            "John 3:16 For God so loved the world, that he gave his only Son...",
            "Romans 3:23 For all have sinned and fall short of the glory of God",
            "Ephesians 2:8 For by grace you have been saved through faith...",
            "Matthew 5:3 Blessed are the poor in spirit, for theirs is the kingdom of heaven.",
            "Psalm 23:1 The LORD is my shepherd; I shall not want.",
            "Jeremiah 29:11 For I know the plans I have for you, declares the LORD...",
            "Romans 8:28 And we know that for those who love God all things work together for good...",
            "Philippians 4:13 I can do all things through him who strengthens me.",
            "1 Corinthians 13:4 Love is patient and kind; love does not envy or boast..."
        ]
        
        verses = []
        for sample in samples:
            match = re.match(r'(\w+)\s+(\d+):(\d+)\s+(.+)', sample)
            if match:
                book, chapter, verse, content = match.groups()
                verses.append({
                    'book': book,
                    'chapter': int(chapter),
                    'verse': int(verse),
                    'content': content,
                    'reference': f"{book} {chapter}:{verse}",
                    'keywords': self.extract_keywords(content),
                    'themes': self.detect_themes(content)
                })
        
        return verses
    
    class ConversationParticipant:
        """A participant in the conversation"""
        
        def __init__(self, name, personality):
            self.name = name
            self.personality = personality
            self.knowledge_base = []
            self.conversation_style = personality.get('style', 'balanced')
            self.focus_themes = personality.get('focus_themes', ['general'])
            self.response_speed = personality.get('response_speed', 1.0)
            
        def understand_message(self, message, context):
            """Understand the meaning of a message"""
            message_lower = message.lower()
            
            # Extract intent
            intent = 'discuss'
            if '?' in message:
                intent = 'question'
            elif any(word in message_lower for word in ['agree', 'yes', 'true']):
                intent = 'agree'
            elif any(word in message_lower for word in ['but', 'however', 'although']):
                intent = 'challenge'
            
            # Extract topics
            topics = []
            for theme in ['creation', 'grace', 'love', 'faith', 'sin', 'justice', 'hope']:
                if theme in message_lower:
                    topics.append(theme)
            
            # Extract emotions
            emotions = []
            if any(word in message_lower for word in ['wonderful', 'amazing', 'beautiful']):
                emotions.append('positive')
            if any(word in message_lower for word in ['difficult', 'hard', 'struggle']):
                emotions.append('concerned')
            
            return {
                'intent': intent,
                'topics': topics if topics else ['general'],
                'emotions': emotions,
                'keywords': re.findall(r'\b\w{4,}\b', message_lower)[:5]
            }
        
        def find_relevant_verses(self, topics, bible_verses, limit=3):
            """Find Bible verses relevant to the topics"""
            relevant = []
            
            for verse in bible_verses:
                score = 0
                
                # Check theme match
                for topic in topics:
                    if topic in verse['themes']:
                        score += 3
                
                # Check keyword match
                if 'keywords' in verse:
                    for keyword in topics:
                        if any(keyword in word for word in verse['keywords']):
                            score += 2
                
                if score > 0:
                    relevant.append((score, verse))
            
            # Sort by relevance
            relevant.sort(key=lambda x: x[0], reverse=True)
            return [verse for _, verse in relevant[:limit]]
        
        def generate_response(self, message_analysis, bible_verses, user_name="You"):
            """Generate a human-like response"""
            
            # Start with a natural opening
            openings = {
                'agree': ["I agree with you.", "Yes, that's right.", "Exactly!", "You've got a point there."],
                'challenge': ["I see what you mean, but...", "That's interesting, however...", "I understand, yet..."],
                'question': ["That's a good question.", "Let me think about that.", "I've wondered about that too."],
                'discuss': ["That reminds me...", "I was thinking about something similar.", "You know, that connects to..."]
            }
            
            intent = message_analysis['intent']
            opening = random.choice(openings.get(intent, ["I see.", "Interesting.", "Hmm."]))
            
            # Find relevant Bible verses
            topics = message_analysis['topics']
            relevant_verses = self.find_relevant_verses(topics, bible_verses)
            
            # Construct the response based on personality
            if self.conversation_style == 'scholarly':
                response_parts = [opening]
                
                if relevant_verses:
                    verse = random.choice(relevant_verses)
                    response_parts.append(f" In {verse['reference']}, we read: '{verse['content'][:80]}...'")
                    response_parts.append(f" This speaks to the theological significance of {topics[0] if topics else 'this'}.")
                
                response_parts.append(" What are your further thoughts on this?")
                
            elif self.conversation_style == 'pastoral':
                response_parts = [opening]
                
                if relevant_verses:
                    verse = random.choice(relevant_verses)
                    response_parts.append(f" Scripture says in {verse['reference']}: '{verse['content'][:70]}...'")
                    response_parts.append(f" This offers us hope and guidance for {topics[0] if topics else 'our lives'}.")
                
                response_parts.append(" How does this resonate with your experience?")
                
            else:  # general
                response_parts = [opening]
                
                if relevant_verses:
                    verse = random.choice(relevant_verses)
                    response_parts.append(f" The Bible mentions in {verse['reference']}: '{verse['content'][:60]}...'")
                
                response_parts.append(" I'd love to hear more of your perspective.")
            
            return ' '.join(response_parts)
    
    def create_participants(self):
        """Create conversation participants"""
        participants = [
            self.ConversationParticipant("James", {
                'style': 'scholarly',
                'focus_themes': ['creation', 'justice', 'covenant'],
                'response_speed': 1.2
            }),
            self.ConversationParticipant("Sarah", {
                'style': 'pastoral', 
                'focus_themes': ['grace', 'love', 'hope'],
                'response_speed': 0.8
            }),
            self.ConversationParticipant("Michael", {
                'style': 'general',
                'focus_themes': ['faith', 'salvation', 'general'],
                'response_speed': 1.0
            })
        ]
        
        return participants
    
    def display_thinking(self, participant_name):
        """Display thinking animation"""
        thinking = random.choice(self.thinking_phrases)
        print(f"\n{participant_name}: {thinking}")
        time.sleep(1.5)
    
    def start_conversation(self):
        """Start the real-time conversation"""
        print("\n" + "="*70)
        print("🤔 REAL-TIME BIBLE CONVERSATION")
        print("="*70)
        print("\nYou are now in a conversation about the Bible.")
        print("Type your thoughts, questions, or responses.")
        print("Type 'quit' to end the conversation.")
        print("Type 'new topic' to change the subject.")
        print("Type 'verses about [topic]' to request specific verses.")
        print("-"*70)
        
        # Create participants
        self.participants = self.create_participants()
        print(f"\n👥 Participants: {', '.join([p.name for p in self.participants])}")
        
        # Start with an opening
        self.current_topic = random.choice(['faith', 'hope', 'love', 'grace'])
        print(f"\n💭 Starting topic: {self.current_topic.upper()}")
        
        # Show a relevant verse
        relevant = self.find_verses_by_theme(self.current_topic, limit=1)
        if relevant:
            print(f"📖 {relevant[0]['reference']}: {relevant[0]['content'][:100]}...")
        
        print("\n" + "-"*70)
        
        # Get user's name
        user_name = input("\nWhat's your name? (Press Enter for 'You'): ").strip()
        if user_name:
            self.user_name = user_name
        
        # Start conversation loop
        self.running = True
        self.conversation_log = []
        
        # Initial prompt from a participant
        first_speaker = random.choice(self.participants)
        initial_topics = ["What are your thoughts on faith?", 
                         "I've been reflecting on God's grace lately.", 
                         "How do you understand hope in difficult times?"]
        
        print(f"\n{first_speaker.name}: {random.choice(initial_topics)}")
        
        # Main conversation loop
        while self.running:
            try:
                # Get user input
                user_input = input(f"\n{self.user_name}: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print("\nEnding conversation...")
                    self.running = False
                    break
                
                if user_input.lower() == 'new topic':
                    new_topic = input("What topic would you like to discuss? ").strip()
                    if new_topic:
                        self.current_topic = new_topic
                        print(f"\n[Topic changed to: {self.current_topic.upper()}]")
                        continue
                
                if user_input.lower().startswith('verses about '):
                    topic = user_input[13:].strip()
                    verses = self.find_verses_by_theme(topic, limit=3)
                    if verses:
                        print(f"\n📚 Verses about {topic}:")
                        for verse in verses:
                            print(f"   {verse['reference']}: {verse['content'][:80]}...")
                    else:
                        print(f"\nNo verses found about '{topic}'")
                    continue
                
                # Log user's message
                self.conversation_log.append({
                    'speaker': self.user_name,
                    'message': user_input,
                    'time': datetime.now().strftime("%H:%M:%S")
                })
                
                # Participants respond
                for participant in random.sample(self.participants, 
                                               min(2, len(self.participants))):  # 1-2 respond
                    
                    # Show thinking
                    self.display_thinking(participant.name)
                    
                    # Analyze user's message
                    message_analysis = participant.understand_message(
                        user_input, 
                        self.conversation_log[-3:] if len(self.conversation_log) > 3 else self.conversation_log
                    )
                    
                    # Generate response
                    response = participant.generate_response(
                        message_analysis, 
                        self.bible,
                        self.user_name
                    )
                    
                    print(f"{participant.name}: {response}")
                    
                    # Log participant's response
                    self.conversation_log.append({
                        'speaker': participant.name,
                        'message': response,
                        'time': datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Small pause between responses
                    time.sleep(0.5)
                
                # Occasionally a participant might add something
                if random.random() > 0.7 and len(self.participants) > 2:
                    third = [p for p in self.participants if p.name != self.conversation_log[-1]['speaker']]
                    if third:
                        participant = random.choice(third)
                        time.sleep(0.5)
                        print(f"\n{participant.name}: {random.choice(['I was also thinking...', 'To add to that...', 'Another perspective...'])}")
                        
                        # Generate additional response
                        new_analysis = participant.understand_message(
                            self.conversation_log[-1]['message'],
                            self.conversation_log[-2:]
                        )
                        response = participant.generate_response(new_analysis, self.bible, self.user_name)
                        print(f"{participant.name}: {response}")
                        
                        self.conversation_log.append({
                            'speaker': participant.name,
                            'message': response,
                            'time': datetime.now().strftime("%H:%M:%S")
                        })
                
                # Occasionally suggest a new topic
                if random.random() > 0.85:
                    new_topic = random.choice(['forgiveness', 'perseverance', 'joy', 'peace'])
                    print(f"\n💡 [Perhaps we could discuss {new_topic}? Type 'new topic' to switch.]")
                    
            except KeyboardInterrupt:
                print("\n\nConversation interrupted.")
                self.running = False
                break
            except Exception as e:
                print(f"\n⚠️  Error: {e}")
                continue
        
        # End conversation
        self.end_conversation()
    
    def find_verses_by_theme(self, theme, limit=5):
        """Find verses by theme"""
        results = []
        for verse in self.bible:
            if theme.lower() in [t.lower() for t in verse['themes']]:
                results.append(verse)
                if len(results) >= limit:
                    break
        
        # If no direct theme match, try keyword match
        if not results:
            for verse in self.bible:
                if 'keywords' in verse:
                    if any(theme.lower() in kw.lower() for kw in verse['keywords']):
                        results.append(verse)
                        if len(results) >= limit:
                            break
        
        return results
    
    def end_conversation(self):
        """End the conversation gracefully"""
        print("\n" + "="*70)
        print("📝 CONVERSATION SUMMARY")
        print("="*70)
        
        print(f"\nTotal exchanges: {len(self.conversation_log)}")
        
        # Count contributions
        contributions = Counter([entry['speaker'] for entry in self.conversation_log])
        print("\nContributions:")
        for speaker, count in contributions.most_common():
            print(f"  {speaker}: {count}")
        
        # Extract topics discussed
        all_messages = ' '.join([entry['message'] for entry in self.conversation_log])
        topics_discussed = set()
        
        for theme in ['creation', 'grace', 'love', 'faith', 'sin', 'justice', 'hope', 
                     'salvation', 'forgiveness', 'peace', 'joy']:
            if theme in all_messages.lower():
                topics_discussed.add(theme)
        
        if topics_discussed:
            print(f"\nTopics discussed: {', '.join(sorted(topics_discussed))}")
        
        # Save conversation log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("BIBLE CONVERSATION LOG\n")
            f.write("="*50 + "\n\n")
            for entry in self.conversation_log:
                f.write(f"[{entry['time']}] {entry['speaker']}: {entry['message']}\n")
        
        print(f"\n💾 Conversation saved to: {filename}")
        print("\n" + "="*70)
        print("🙏 Thank you for the meaningful conversation!")
        print("="*70)

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Run the real-time conversation"""
    
    print("🚀 REAL-TIME BIBLE DIALOGUE SYSTEM")
    print("Loading...")
    
    # Create and start engine
    engine = RealTimeDialogueEngine("bible.txt")
    
    # Start conversation
    engine.start_conversation()

if __name__ == "__main__":
    main()