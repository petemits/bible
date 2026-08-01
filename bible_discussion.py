import re
import random
import json
import collections
import itertools
import math
import datetime
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter, deque
from dataclasses import dataclass
from enum import Enum
import statistics
import heapq

# ============================================
# PART 1: BIBLE TEXT PROCESSING ENGINE
# ============================================

class BibleParser:
    """Advanced Bible text parser using only Python standard libraries"""
    
    def __init__(self, bible_text: str):
        self.raw_text = bible_text
        self.verses = []
        self.books = {}
        self.word_network = defaultdict(set)
        self.theme_graph = defaultdict(dict)
        self._parse_structure()
        self._build_semantic_networks()
    
    def _parse_structure(self):
        """Parse Bible text into structured verses with metadata"""
        lines = self.raw_text.strip().split('\n')
        current_book = ""
        chapter_verse_pattern = re.compile(r'(\d+):(\d+)\s+(.*)')
        book_pattern = re.compile(r'^([A-Za-z\s]+)\s+\d+:\d+')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to detect book name (like "Genesis 1:1")
            book_match = re.match(r'^([A-Za-z\s]+?)\s+\d+:\d+', line)
            if book_match:
                current_book = book_match.group(1).strip()
            
            # Parse verse: "1:1 In the beginning..."
            verse_match = chapter_verse_pattern.search(line)
            if verse_match:
                chapter, verse, content = verse_match.groups()
                
                verse_obj = {
                    'book': current_book,
                    'chapter': int(chapter),
                    'verse': int(verse),
                    'content': content.strip(),
                    'reference': f"{current_book} {chapter}:{verse}",
                    'words': self._extract_meaningful_words(content),
                    'entities': self._extract_entities(content),
                    'themes': self._extract_themes(content),
                    'speech_acts': self._analyze_speech_act(content)
                }
                self.verses.append(verse_obj)
                
                # Index by book
                if current_book not in self.books:
                    self.books[current_book] = []
                self.books[current_book].append(verse_obj)
    
    def _extract_meaningful_words(self, text: str) -> List[str]:
        """Extract meaningful words (nouns, important terms)"""
        words = re.findall(r'\b([A-Z][a-z]+|\w+ing|\w+ed)\b', text.lower())
        stopwords = {'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by'}
        return [w for w in words if w not in stopwords and len(w) > 2]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities (people, places, divine names)"""
        # Pattern for common Bible entities
        patterns = [
            r'\b(God|Lord|LORD|Jesus|Christ|Holy\s+Spirit)\b',
            r'\b(Abraham|Moses|David|Paul|Peter|John)\b',
            r'\b(Jerusalem|Bethlehem|Nazareth|Egypt|Israel|Jordan)\b',
            r'\b(angel|prophet|apostle|disciple|priest)\b',
        ]
        
        entities = []
        for pattern in patterns:
            entities.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(entities))
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract thematic elements"""
        theme_patterns = {
            'covenant': r'\b(covenant|promise|oath|swear|agreement)\b',
            'faith': r'\b(faith|believe|trust|hope)\b',
            'sin': r'\b(sin|transgression|iniquity|evil|wicked)\b',
            'grace': r'\b(grace|mercy|forgive|redemption|salvation)\b',
            'law': r'\b(law|commandment|statute|ordinance|decree)\b',
            'love': r'\b(love|charity|kindness|compassion)\b',
            'justice': r'\b(justice|judgment|righteous|fair)\b',
            'creation': r'\b(create|made|form|earth|heaven)\b'
        }
        
        themes = []
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                themes.append(theme)
        return themes
    
    def _analyze_speech_act(self, text: str) -> List[str]:
        """Analyze the type of speech act"""
        acts = []
        
        if re.search(r'[\?]', text):
            acts.append('question')
        if re.search(r'^["\']|said|speak|declared', text, re.IGNORECASE):
            acts.append('dialogue')
        if re.search(r'!', text):
            acts.append('exclamation')
        if re.search(r'\b(blessed|woe|curse)\b', text, re.IGNORECASE):
            acts.append('benediction')
        if re.search(r'\b(command|must|shall|should)\b', text, re.IGNORECASE):
            acts.append('command')
        if re.search(r'\b(pray|ask|plead)\b', text, re.IGNORECASE):
            acts.append('prayer')
        
        return acts if acts else ['statement']
    
    def _build_semantic_networks(self):
        """Build word co-occurrence and theme networks"""
        # Build word co-occurrence network
        for verse in self.verses:
            words = verse['words']
            for i, word1 in enumerate(words):
                for word2 in words[i+1:]:
                    self.word_network[word1].add(word2)
                    self.word_network[word2].add(word1)
        
        # Build theme co-occurrence network
        for verse in self.verses:
            themes = verse['themes']
            for i, theme1 in enumerate(themes):
                for theme2 in themes[i+1:]:
                    if theme2 not in self.theme_graph[theme1]:
                        self.theme_graph[theme1][theme2] = 0
                    self.theme_graph[theme1][theme2] += 1
    
    def find_related_verses(self, theme: str, limit: int = 5) -> List[Dict]:
        """Find verses related to a theme with semantic similarity"""
        related = []
        theme_words = set(theme.lower().split())
        
        for verse in self.verses:
            score = 0
            verse_words = set(verse['words'])
            verse_themes = set(verse['themes'])
            
            # Direct theme match
            if theme in verse_themes:
                score += 3
            
            # Word overlap
            overlap = len(theme_words.intersection(verse_words))
            score += overlap
            
            # Network proximity
            for word in theme_words:
                if word in self.word_network:
                    connected_words = self.word_network[word]
                    verse_connections = len(connected_words.intersection(verse_words))
                    score += verse_connections * 0.5
            
            if score > 0:
                related.append((score, verse))
        
        # Sort by score and return top results
        related.sort(key=lambda x: x[0], reverse=True)
        return [verse for _, verse in related[:limit]]
    
    def generate_story_path(self, start_theme: str, depth: int = 3) -> List[List[Dict]]:
        """Generate a branching story path through related themes"""
        story_paths = []
        visited = set()
        
        def dfs(current_theme: str, path: List[Dict], current_depth: int):
            if current_depth >= depth or current_theme in visited:
                story_paths.append(path.copy())
                return
            
            visited.add(current_theme)
            
            # Get verses for current theme
            verses = self.find_related_verses(current_theme, limit=3)
            
            for verse in verses:
                new_path = path + [verse]
                
                # Find next theme from this verse or connected themes
                if verse['themes']:
                    next_theme = random.choice(verse['themes'])
                    # Avoid immediate backtracking
                    if next_theme != current_theme:
                        dfs(next_theme, new_path, current_depth + 1)
                
                # Also try network-connected themes
                if current_theme in self.theme_graph:
                    connected = list(self.theme_graph[current_theme].keys())
                    if connected:
                        next_theme = random.choice(connected)
                        dfs(next_theme, new_path, current_depth + 1)
            
            visited.remove(current_theme)
        
        dfs(start_theme, [], 0)
        return story_paths

# ============================================
# PART 2: CONVERSATION AGENT SYSTEM
# ============================================

class ConversationAgent:
    """An agent that can discuss Bible passages intelligently"""
    
    def __init__(self, name: str, personality: Dict, knowledge_base: BibleParser):
        self.name = name
        self.personality = personality
        self.knowledge = knowledge_base
        self.memory = deque(maxlen=100)  # Conversation memory
        self.beliefs = defaultdict(float)
        self.conversation_state = {
            'agreement_level': 0.5,
            'engagement': 0.7,
            'topic_focus': None,
            'last_spoke': None
        }
        
        # Initialize beliefs from personality
        for theme in personality.get('emphasized_themes', []):
            self.beliefs[theme] = 0.8 + random.random() * 0.2
        
        # Specialize knowledge based on personality
        self.specialized_knowledge = self._build_specialized_knowledge()
    
    def _build_specialized_knowledge(self) -> Dict:
        """Build agent's specialized understanding of themes"""
        specialized = {}
        
        for theme in self.personality.get('emphasized_themes', []):
            verses = self.knowledge.find_related_verses(theme, limit=20)
            
            # Analyze patterns in these verses
            word_freq = Counter()
            entity_freq = Counter()
            
            for verse in verses:
                word_freq.update(verse['words'])
                entity_freq.update(verse['entities'])
            
            specialized[theme] = {
                'key_verses': verses,
                'common_words': [word for word, _ in word_freq.most_common(10)],
                'common_entities': [entity for entity, _ in entity_freq.most_common(5)],
                'interpretations': self._generate_interpretations(theme, verses)
            }
        
        return specialized
    
    def _generate_interpretations(self, theme: str, verses: List[Dict]) -> List[str]:
        """Generate agent's personal interpretations of a theme"""
        interpretations = []
        
        # Different interpretation styles based on personality
        style = self.personality.get('interpretation_style', 'literal')
        
        if style == 'literal':
            templates = [
                f"The scriptures clearly teach that {theme} means ",
                f"From these passages, we see {theme} as ",
                f"The consistent testimony is that {theme} involves "
            ]
        elif style == 'allegorical':
            templates = [
                f"On a deeper level, {theme} symbolizes ",
                f"This points beyond itself to show {theme} as ",
                f"The spiritual meaning reveals {theme} to be "
            ]
        else:  # practical
            templates = [
                f"For our lives today, {theme} teaches us to ",
                f"The practical application of {theme} is ",
                f"This shows how {theme} affects our "
            ]
        
        # Sample some key verses to base interpretation on
        sample_verses = random.sample(verses, min(3, len(verses)))
        
        for template in templates:
            verse_refs = [v['reference'] for v in sample_verses]
            key_terms = list(set([w for v in sample_verses for w in v['words'][:3]]))
            
            interpretation = template
            if key_terms:
                interpretation += f"{', '.join(key_terms[:3])}"
            interpretation += f" (cf. {', '.join(verse_refs[:2])})"
            
            interpretations.append(interpretation)
        
        return interpretations
    
    def process_statement(self, speaker: str, statement: str, context: List[Dict]) -> Dict:
        """Process what another agent said"""
        # Analyze statement
        words = set(re.findall(r'\b\w+\b', statement.lower()))
        themes_present = [t for t in self.specialized_knowledge.keys() 
                         if any(word in statement.lower() for word in t.split())]
        
        # Update conversation state
        self.memory.append({
            'speaker': speaker,
            'statement': statement,
            'themes': themes_present,
            'timestamp': datetime.datetime.now()
        })
        
        # Update beliefs based on agreement
        if themes_present:
            main_theme = themes_present[0]
            if main_theme in self.beliefs:
                # Adjust belief based on who spoke and what was said
                adjustment = 0.1
                if speaker == self.name:
                    adjustment = 0  # Don't adjust based on own statements
                elif "agree" in statement.lower() or "yes" in statement.lower():
                    self.beliefs[main_theme] += adjustment
                elif "disagree" in statement.lower() or "but" in statement.lower():
                    self.beliefs[main_theme] -= adjustment
                
                # Keep beliefs in reasonable range
                self.beliefs[main_theme] = max(0.1, min(0.95, self.beliefs[main_theme]))
        
        return {
            'understood_themes': themes_present,
            'agreement': self.conversation_state['agreement_level'],
            'requires_response': len(themes_present) > 0
        }
    
    def generate_response(self, context: List[Dict], current_topic: str = None) -> str:
        """Generate a response based on conversation context"""
        if not current_topic and context:
            # Extract topic from last few statements
            recent_words = []
            for msg in context[-3:]:
                recent_words.extend(re.findall(r'\b\w+\b', msg.get('statement', '').lower()))
            
            if recent_words:
                word_counts = Counter(recent_words)
                current_topic = word_counts.most_common(1)[0][0] if word_counts else None
        
        # Decide response strategy
        strategy = self._choose_response_strategy(context)
        
        if strategy == "elaborate":
            return self._elaborate_on_topic(current_topic)
        elif strategy == "question":
            return self._ask_question(current_topic)
        elif strategy == "agree":
            return self._express_agreement(context[-1] if context else None)
        elif strategy == "share_insight":
            return self._share_personal_insight(current_topic)
        else:
            return self._introduce_new_angle(current_topic)
    
    def _choose_response_strategy(self, context: List[Dict]) -> str:
        """Choose how to respond based on personality and context"""
        strategies = self.personality.get('conversation_style', [])
        
        if not strategies:
            strategies = ['elaborate', 'question', 'agree', 'share_insight', 'new_angle']
        
        # Weight strategies based on context
        weights = [1.0] * len(strategies)
        
        if len(context) > 5:  # Long conversation
            if 'new_angle' in strategies:
                idx = strategies.index('new_angle')
                weights[idx] = 2.0  # Prefer new angles
        
        if any('?' in msg.get('statement', '') for msg in context[-2:]):
            if 'elaborate' in strategies:
                idx = strategies.index('elaborate')
                weights[idx] = 1.5  # Prefer elaboration after questions
        
        # Choose strategy
        total = sum(weights)
        r = random.random() * total
        cumulative = 0
        
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return strategies[i]
        
        return strategies[0]
    
    def _elaborate_on_topic(self, topic: str) -> str:
        """Elaborate on a topic with scriptural support"""
        if not topic:
            topic = random.choice(list(self.specialized_knowledge.keys()))
        
        if topic in self.specialized_knowledge:
            knowledge = self.specialized_knowledge[topic]
            verse = random.choice(knowledge['key_verses']) if knowledge['key_verses'] else None
            
            elaborations = [
                f"Building on that, {topic} is further explained in {verse['reference'] if verse else 'scripture'} where we read: '{verse['content'][:100] if verse else '...'}'",
                f"This connects with what we find about {topic} throughout scripture, particularly in the concept of {random.choice(knowledge['common_words'][:3])}",
                f"The narrative of {topic} develops from {knowledge['common_entities'][0] if knowledge['common_entities'] else 'biblical history'} to show us..."
            ]
            
            return f"{self.name}: {random.choice(elaborations)}"
        
        return f"{self.name}: I've been considering {topic} in light of God's word..."
    
    def _ask_question(self, topic: str) -> str:
        """Ask a thoughtful question"""
        questions = [
            f"How do you see {topic} relating to God's covenant promises?",
            f"What practical implications does {topic} have for us today?",
            f"Can we trace the development of {topic} through scripture?",
            f"How would you respond to someone who questions the biblical view of {topic}?",
            f"What other passages shed light on our understanding of {topic}?"
        ]
        
        return f"{self.name}: {random.choice(questions)}"
    
    def _express_agreement(self, last_message: Dict) -> str:
        """Express agreement with previous statement"""
        if not last_message:
            return self._elaborate_on_topic(None)
        
        agreements = [
            f"I appreciate that insight. It aligns with what I see in scripture about {random.choice(list(self.beliefs.keys())[:3])}",
            f"Yes, and that connects to the broader biblical theme of {random.choice(list(self.specialized_knowledge.keys())[:2])}",
            f"You've articulated well what I also believe. This is consistent with {random.choice(list(self.beliefs.keys())[:3])}",
            f"I agree, and it reminds me of how this truth is manifested in {random.choice(list(self.specialized_knowledge.keys())[:2])}"
        ]
        
        return f"{self.name}: {random.choice(agreements)}"
    
    def _share_personal_insight(self, topic: str) -> str:
        """Share a personal interpretation or insight"""
        if topic in self.specialized_knowledge:
            interpretations = self.specialized_knowledge[topic]['interpretations']
            if interpretations:
                return f"{self.name}: From my study, {random.choice(interpretations)}"
        
        insights = [
            f"In my reflection on scripture, I've come to see this as revealing God's character in a particular way",
            f"This has personal significance because it speaks to how we live out our faith daily",
            f"The historical context here helps us understand the depth of this teaching"
        ]
        
        return f"{self.name}: {random.choice(insights)}"
    
    def _introduce_new_angle(self, topic: str) -> str:
        """Introduce a new perspective or related theme"""
        all_themes = list(self.specialized_knowledge.keys())
        
        if len(all_themes) >= 2:
            current_idx = all_themes.index(topic) if topic in all_themes else -1
            if current_idx != -1 and len(all_themes) > current_idx + 1:
                new_theme = all_themes[current_idx + 1]
            else:
                new_theme = random.choice(all_themes)
            
            angles = [
                f"That makes me think about how this relates to {new_theme}",
                f"Speaking of {topic}, have you considered its connection to {new_theme}?",
                f"This discussion about {topic} naturally leads us to consider {new_theme}"
            ]
            
            return f"{self.name}: {random.choice(angles)}"
        
        return self._elaborate_on_topic(topic)

# ============================================
# PART 3: CONVERSATION ORCHESTRATOR
# ============================================

class ConversationOrchestrator:
    """Manages the flow of conversation between multiple agents"""
    
    def __init__(self, agents: List[ConversationAgent], bible_parser: BibleParser):
        self.agents = {agent.name: agent for agent in agents}
        self.bible = bible_parser
        self.conversation_history = []
        self.current_topic = None
        self.conversation_graph = defaultdict(list)
        
        # Consensus tracking
        self.consensus_state = {
            'agreed_themes': set(),
            'contested_themes': set(),
            'explored_paths': [],
            'agreement_levels': defaultdict(float)
        }
    
    def start_conversation(self, initial_topic: str, max_turns: int = 20):
        """Start and manage a conversation"""
        print(f"\n{'='*60}")
        print(f"CONVERSATION STARTED: {initial_topic}")
        print(f"{'='*60}\n")
        
        self.current_topic = initial_topic
        agent_names = list(self.agents.keys())
        turn = 0
        
        # Get initial verses for context
        initial_verses = self.bible.find_related_verses(initial_topic, limit=2)
        if initial_verses:
            print(f"Context: {initial_verses[0]['reference']} - {initial_verses[0]['content'][:150]}...\n")
        
        while turn < max_turns:
            # Select next speaker (round-robin with some variation)
            speaker_name = agent_names[turn % len(agent_names)]
            speaker = self.agents[speaker_name]
            
            # Get last few messages for context
            recent_context = self.conversation_history[-3:] if len(self.conversation_history) >= 3 else self.conversation_history
            
            # Generate response
            response = speaker.generate_response(recent_context, self.current_topic)
            
            # Print response
            print(response)
            print()
            
            # Store in history
            self.conversation_history.append({
                'speaker': speaker_name,
                'message': response,
                'turn': turn,
                'topic': self.current_topic
            })
            
            # Update other agents
            for name, agent in self.agents.items():
                if name != speaker_name:
                    agent.process_statement(speaker_name, response, recent_context)
            
            # Update conversation graph
            self._update_conversation_graph(speaker_name, response)
            
            # Update consensus tracking
            self._update_consensus(response)
            
            # Occasionally introduce new topic from story paths
            if turn % 5 == 4:  # Every 5 turns
                self._maybe_introduce_new_angle()
            
            # Check for natural conclusion
            if self._check_for_consensus() and turn > max_turns // 2:
                print(f"→ Consensus emerging on {self.current_topic}")
                if random.random() > 0.7:  # 70% chance to conclude
                    break
            
            turn += 1
        
        self._conclude_conversation()
    
    def _update_conversation_graph(self, speaker: str, message: str):
        """Track conversation structure"""
        words = re.findall(r'\b\w+\b', message.lower())
        if len(words) > 5:  # Only track substantial messages
            key_terms = [w for w in words if len(w) > 4][:3]
            self.conversation_graph[speaker].extend(key_terms)
    
    def _update_consensus(self, message: str):
        """Track themes and agreement levels"""
        # Extract themes from message
        message_lower = message.lower()
        all_themes = set()
        
        for theme in self.bible.theme_graph.keys():
            if theme in message_lower:
                all_themes.add(theme)
        
        # Check for agreement indicators
        agreement_words = {'agree', 'yes', 'true', 'indeed', 'certainly', 'exactly'}
        disagreement_words = {'but', 'however', 'although', 'disagree', 'differ'}
        
        has_agreement = any(word in message_lower for word in agreement_words)
        has_disagreement = any(word in message_lower for word in disagreement_words)
        
        # Update consensus state
        for theme in all_themes:
            if theme not in self.consensus_state['agreement_levels']:
                self.consensus_state['agreement_levels'][theme] = 0.5
            
            if has_agreement:
                self.consensus_state['agreement_levels'][theme] += 0.05
                self.consensus_state['agreed_themes'].add(theme)
            elif has_disagreement:
                self.consensus_state['agreement_levels'][theme] -= 0.05
                self.consensus_state['contested_themes'].add(theme)
            
            # Keep in bounds
            self.consensus_state['agreement_levels'][theme] = max(0, min(1, 
                self.consensus_state['agreement_levels'][theme]))
    
    def _maybe_introduce_new_angle(self):
        """Introduce new topic from story paths"""
        if self.current_topic:
            story_paths = self.bible.generate_story_path(self.current_topic, depth=2)
            if story_paths:
                random_path = random.choice(story_paths)
                if len(random_path) > 1:
                    new_verse = random_path[1]
                    if new_verse['themes']:
                        new_topic = random.choice(new_verse['themes'])
                        if new_topic != self.current_topic:
                            self.current_topic = new_topic
                            print(f"↳ Conversation shifting to explore: {new_topic}")
                            print()
    
    def _check_for_consensus(self) -> bool:
        """Check if consensus is emerging"""
        if not self.consensus_state['agreement_levels']:
            return False
        
        # Calculate average agreement on current topic themes
        if self.current_topic:
            topic_words = set(self.current_topic.lower().split())
            relevant_themes = [t for t in self.consensus_state['agreement_levels'].keys() 
                             if any(word in t for word in topic_words)]
            
            if relevant_themes:
                avg_agreement = statistics.mean(
                    [self.consensus_state['agreement_levels'][t] for t in relevant_themes]
                )
                return avg_agreement > 0.7
        
        return False
    
    def _conclude_conversation(self):
        """Generate conversation summary"""
        print(f"\n{'='*60}")
        print("CONVERSATION SUMMARY")
        print(f"{'='*60}")
        
        # Most discussed themes
        all_words = []
        for msg in self.conversation_history:
            all_words.extend(re.findall(r'\b\w+\b', msg['message'].lower()))
        
        word_counts = Counter(all_words)
        common_themes = [word for word, count in word_counts.most_common(10) 
                        if len(word) > 4 and count > 1]
        
        print(f"\nKey Themes Discussed: {', '.join(common_themes[:5])}")
        
        # Agreement analysis
        if self.consensus_state['agreed_themes']:
            print(f"Themes with Agreement: {', '.join(list(self.consensus_state['agreed_themes'])[:3])}")
        
        if self.consensus_state['contested_themes']:
            print(f"Themes with Diversity of View: {', '.join(list(self.consensus_state['contested_themes'])[:3])}")
        
        # Generate story from conversation
        story = self._generate_story_from_conversation()
        print(f"\nNarrative Arc: {story}")
        
        print(f"\nTotal Exchanges: {len(self.conversation_history)}")
        print(f"Final Topic: {self.current_topic}")
    
    def _generate_story_from_conversation(self) -> str:
        """Generate a narrative summary of the conversation"""
        if len(self.conversation_history) < 3:
            return "Brief discussion that touched on key themes."
        
        # Extract key elements
        speakers = set(msg['speaker'] for msg in self.conversation_history)
        topics = [msg.get('topic', '') for msg in self.conversation_history if msg.get('topic')]
        
        if topics:
            main_topic = max(set(topics), key=topics.count)
        else:
            main_topic = "biblical themes"
        
        # Create narrative
        narrative_templates = [
            f"A thoughtful exchange between {', '.join(sorted(speakers))} exploring {main_topic} "
            f"through {len(self.conversation_history)} turns of dialogue.",
            
            f"The conversation journeyed from initial questions about {main_topic} "
            f"to deeper reflections, with moments of agreement and thoughtful questioning.",
            
            f"An unfolding discovery where {', '.join(sorted(speakers)[:2])} and {sorted(speakers)[-1]} "
            f"collectively illuminated aspects of {main_topic} from different angles."
        ]
        
        return random.choice(narrative_templates)

# ============================================
# PART 4: MAIN EXECUTION AND DEMONSTRATION
# ============================================

def load_bible_text(filename: str = "bible.txt") -> str:
    """Load Bible text from file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Return sample text for demonstration if file not found
        return """Genesis 1:1 In the beginning God created the heavens and the earth.
Genesis 1:2 The earth was without form and void, and darkness was over the face of the deep. And the Spirit of God was hovering over the face of the waters.
Genesis 1:3 And God said, "Let there be light," and there was light.
Genesis 1:4 And God saw that the light was good. And God separated the light from the darkness.
John 1:1 In the beginning was the Word, and the Word was with God, and the Word was God.
John 1:14 And the Word became flesh and dwelt among us, and we have seen his glory, glory as of the only Son from the Father, full of grace and truth.
Romans 3:23 For all have sinned and fall short of the glory of God,
Romans 6:23 For the wages of sin is death, but the free gift of God is eternal life in Christ Jesus our Lord.
John 3:16 For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.
Ephesians 2:8 For by grace you have been saved through faith. And this is not your own doing; it is the gift of God,
Matthew 5:3 Blessed are the poor in spirit, for theirs is the kingdom of heaven.
Psalm 23:1 The LORD is my shepherd; I shall not want."""

def create_sample_agents(bible_parser: BibleParser) -> List[ConversationAgent]:
    """Create sample conversation agents with different personalities"""
    
    agents = [
        ConversationAgent(
            name="Theologian",
            personality={
                'interpretation_style': 'literal',
                'conversation_style': ['elaborate', 'question', 'share_insight'],
                'emphasized_themes': ['covenant', 'law', 'justice']
            },
            knowledge_base=bible_parser
        ),
        
        ConversationAgent(
            name="Pastor",
            personality={
                'interpretation_style': 'practical',
                'conversation_style': ['agree', 'share_insight', 'new_angle'],
                'emphasized_themes': ['grace', 'love', 'faith']
            },
            knowledge_base=bible_parser
        ),
        
        ConversationAgent(
            name="Scholar",
            personality={
                'interpretation_style': 'allegorical',
                'conversation_style': ['question', 'new_angle', 'elaborate'],
                'emphasized_themes': ['creation', 'sin', 'redemption']
            },
            knowledge_base=bible_parser
        )
    ]
    
    return agents

def run_demonstration():
    """Run a complete demonstration"""
    print("🚀 BIBLE CONVERSATION SIMULATOR")
    print("=" * 50)
    
    # Load and parse Bible text
    print("\n📖 Loading and parsing Bible text...")
    bible_text = load_bible_text()
    parser = BibleParser(bible_text)
    
    print(f"   Parsed {len(parser.verses)} verses")
    print(f"   Identified {len(parser.theme_graph)} major themes")
    print(f"   Books: {', '.join(list(parser.books.keys())[:3])}...")
    
    # Create agents
    print("\n👥 Creating conversation agents...")
    agents = create_sample_agents(parser)
    print(f"   Created {len(agents)} agents with different perspectives")
    
    # Create orchestrator
    orchestrator = ConversationOrchestrator(agents, parser)
    
    # Run multiple conversations
    conversation_topics = ['creation', 'grace', 'covenant', 'faith']
    
    for i, topic in enumerate(conversation_topics[:2]):  # Run first 2 as demo
        print(f"\n💬 Conversation {i+1} of {len(conversation_topics[:2])}")
        orchestrator.start_conversation(topic, max_turns=15)
        
        if i < len(conversation_topics[:2]) - 1:
            print("\n" + "─" * 60)
            print("PAUSE BETWEEN CONVERSATIONS")
            print("─" * 60 + "\n")
    
    # Demonstrate story generation
    print("\n📚 GENERATING STORY PATHS")
    print("=" * 50)
    
    for theme in ['creation', 'grace'][:2]:
        print(f"\nStory paths from '{theme}':")
        paths = parser.generate_story_path(theme, depth=2)
        
        for j, path in enumerate(paths[:2]):  # Show first 2 paths
            if path:
                print(f"\n  Path {j+1}: ", end="")
                path_desc = []
                for verse in path[:3]:  # First 3 verses in path
                    if verse['themes']:
                        path_desc.append(f"{verse['themes'][0]} ({verse['reference'][:10]}...)")
                print(" → ".join(path_desc))
    
    print("\n" + "=" * 50)
    print("✨ SIMULATION COMPLETE")
    print("=" * 50)

# ============================================
# PART 5: ADVANCED FEATURES - STORY GENERATOR
# ============================================

class BibleStoryGenerator:
    """Generate narratives from Bible passages using algorithms"""
    
    @staticmethod
    def generate_character_driven_story(parser: BibleParser, character: str) -> str:
        """Generate a story focused on a biblical character"""
        # Find verses mentioning the character
        character_verses = []
        for verse in parser.verses:
            if character.lower() in verse['content'].lower():
                character_verses.append(verse)
        
        if not character_verses:
            return f"No verses found about {character}"
        
        # Sort chronologically by book/chapter/verse
        def verse_sort_key(v):
            book_order = list(parser.books.keys())
            try:
                book_idx = book_order.index(v['book'])
            except ValueError:
                book_idx = 999
            return (book_idx, v['chapter'], v['verse'])
        
        character_verses.sort(key=verse_sort_key)
        
        # Create narrative
        story_parts = [f"The story of {character} unfolds in Scripture:"]
        
        for i, verse in enumerate(character_verses[:5]):  # Limit to 5 verses
            if i == 0:
                story_parts.append(f"It begins in {verse['reference']} where {verse['content']}")
            elif i == len(character_verses[:5]) - 1:
                story_parts.append(f"Finally, in {verse['reference']} we see {verse['content'][:100]}...")
            else:
                story_parts.append(f"Then in {verse['reference']}, {verse['content'][:80]}...")
        
        return " ".join(story_parts)
    
    @staticmethod
    def generate_thematic_story(parser: BibleParser, theme: str) -> str:
        """Generate a story tracing a theme through scripture"""
        related_verses = parser.find_related_verses(theme, limit=8)
        
        if not related_verses:
            return f"No significant verses found about {theme}"
        
        # Group by testament/era
        old_testament = [v for v in related_verses if v['book'] in ['Genesis', 'Exodus', 'Psalms', 'Isaiah']]
        new_testament = [v for v in related_verses if v['book'] in ['Matthew', 'John', 'Romans', 'Ephesians']]
        
        story_parts = [f"The theme of {theme} weaves through Scripture:"]
        
        if old_testament:
            story_parts.append(f"In the Old Testament, {old_testament[0]['book']} shows {old_testament[0]['content'][:120]}...")
        
        if new_testament:
            story_parts.append(f"In the New Testament, {new_testament[0]['book']} reveals {new_testament[0]['content'][:120]}...")
        
        if len(old_testament) > 1 and len(new_testament) > 1:
            story_parts.append(f"This development from {old_testament[0]['book']} to {new_testament[0]['book']} "
                              f"shows the unfolding understanding of {theme}.")
        
        # Add a concluding reflection
        reflections = [
            f"This scriptural journey illuminates different facets of {theme}.",
            f"Together, these passages provide a multi-dimensional view of {theme}.",
            f"The biblical narrative consistently returns to and deepens {theme}."
        ]
        
        story_parts.append(random.choice(reflections))
        
        return " ".join(story_parts)

# ============================================
# EXECUTE THE DEMONSTRATION
# ============================================

if __name__ == "__main__":
    run_demonstration()
    
    # Additional demonstration of story generation
    print("\n" + "=" * 60)
    print("ADDITIONAL STORY GENERATION EXAMPLES")
    print("=" * 60)
    
    # Load parser for story generation
    bible_text = load_bible_text()
    parser = BibleParser(bible_text)
    
    # Generate character story
    print("\n📖 Character-Based Story:")
    print("-" * 40)
    character_story = BibleStoryGenerator.generate_character_driven_story(parser, "God")
    print(character_story[:500] + "..." if len(character_story) > 500 else character_story)
    
    # Generate thematic story
    print("\n📖 Thematic Story:")
    print("-" * 40)
    theme_story = BibleStoryGenerator.generate_thematic_story(parser, "love")
    print(theme_story[:500] + "..." if len(theme_story) > 500 else theme_story)