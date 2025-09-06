"""
AI processing module for email analysis and response generation using Google Gemini.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
import google.generativeai as genai
import chromadb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AICore:
    """Core AI processing class for email analysis and response generation."""
    
    def __init__(self):
        """Initialize AI core with Gemini API and ChromaDB."""
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Initialize models
        self.generation_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        self.embedding_model = 'models/embedding-001'
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        self.collection = None
        
    def setup_and_run_rag(self, knowledge_file: str) -> None:
        """
        Set up RAG pipeline by loading knowledge base into ChromaDB.
        
        Args:
            knowledge_file: Path to the knowledge base text file
        """
        try:
            # Create or get collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Read knowledge base file
            if not os.path.exists(knowledge_file):
                print(f"Knowledge base file {knowledge_file} not found")
                return
            
            with open(knowledge_file, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Split content into Q&A chunks
            chunks = self._split_knowledge_base(content)
            
            if not chunks:
                print("No knowledge chunks found")
                return
            
            # Generate embeddings and store in ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk['text'])
                metadatas.append({
                    'question': chunk['question'],
                    'answer': chunk['answer'],
                    'type': 'knowledge_base'
                })
                ids.append(f"kb_chunk_{i}")
            
            # Add documents to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Successfully loaded {len(chunks)} knowledge chunks into ChromaDB")
            
        except Exception as e:
            print(f"Error setting up RAG pipeline: {str(e)}")
    
    def _split_knowledge_base(self, content: str) -> List[Dict[str, str]]:
        """
        Split knowledge base content into Q&A chunks.
        
        Args:
            content: Raw text content from knowledge base file
            
        Returns:
            List of dictionaries containing question and answer pairs
        """
        chunks = []
        lines = content.strip().split('\n')
        
        current_question = None
        current_answer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Q:'):
                # Save previous Q&A pair if it exists
                if current_question and current_answer:
                    answer_text = ' '.join(current_answer).strip()
                    if answer_text:
                        chunks.append({
                            'question': current_question,
                            'answer': answer_text,
                            'text': f"{current_question} {answer_text}"
                        })
                
                # Start new question
                current_question = line[2:].strip()
                current_answer = []
                
            elif line.startswith('A:'):
                current_answer = [line[2:].strip()]
                
            elif current_answer:  # Continue answer
                current_answer.append(line)
        
        # Add the last Q&A pair
        if current_question and current_answer:
            answer_text = ' '.join(current_answer).strip()
            if answer_text:
                chunks.append({
                    'question': current_question,
                    'answer': answer_text,
                    'text': f"{current_question} {answer_text}"
                })
        
        return chunks
    
    def analyze_email_content(self, email_body: str) -> Dict[str, Any]:
        """
        Analyze email content for sentiment, priority, and key information.
        
        Args:
            email_body: Raw text content of the email
            
        Returns:
            Dictionary containing analysis results
        """
        prompt = f"""
Analyze the following customer email and provide a JSON response with these exact keys:

1. "sentiment": Must be exactly one of: "Positive", "Negative", or "Neutral"
2. "priority": Must be exactly one of: "Urgent" or "Not Urgent" 
   - Use "Urgent" if the email contains words like: urgent, critical, asap, emergency, down, not working, broken, issue, problem, help needed, cannot access
   - Otherwise use "Not Urgent"
3. "summary": A clear, concise one-sentence summary of what the customer is asking for or reporting
4. "extracted_info": A JSON object containing any important details like order numbers, product names, contact info, etc. Use empty object {{}} if none found.

Email to analyze:
{email_body}

Respond with ONLY a valid JSON object in this exact format:
{{
    "sentiment": "Positive|Negative|Neutral",
    "priority": "Urgent|Not Urgent", 
    "summary": "Brief summary here",
    "extracted_info": {{}}
}}
"""
        
        try:
            response = self.generation_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response text more thoroughly
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = re.sub(r'^```\s*', '', response_text)
            response_text = response_text.strip()
            
            # Try to find JSON in the response if it's wrapped with other text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group()
            
            analysis = json.loads(response_text)
            
            # Validate and fix the response
            if 'sentiment' not in analysis or analysis['sentiment'] not in ['Positive', 'Negative', 'Neutral']:
                analysis['sentiment'] = 'Neutral'
            
            if 'priority' not in analysis or analysis['priority'] not in ['Urgent', 'Not Urgent']:
                # Re-check for urgent keywords
                urgent_keywords = ['urgent', 'critical', 'asap', 'emergency', 'down', 'not working', 
                                 'broken', 'issue', 'problem', 'help needed', 'cannot access']
                if any(keyword in email_body.lower() for keyword in urgent_keywords):
                    analysis['priority'] = 'Urgent'
                else:
                    analysis['priority'] = 'Not Urgent'
            
            if 'summary' not in analysis or not analysis['summary']:
                analysis['summary'] = 'Customer inquiry requiring assistance'
            
            if 'extracted_info' not in analysis:
                analysis['extracted_info'] = {}
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Raw response: {response_text}")
            # Fallback analysis
            return self._fallback_analysis(email_body)
            
        except Exception as e:
            print(f"Error analyzing email content: {str(e)}")
            return self._fallback_analysis(email_body)
    
    def _fallback_analysis(self, email_body: str) -> Dict[str, Any]:
        """
        Fallback analysis when AI analysis fails.
        
        Args:
            email_body: Email content to analyze
            
        Returns:
            Basic analysis dictionary
        """
        # Simple keyword-based analysis as fallback
        urgent_keywords = ['urgent', 'critical', 'asap', 'emergency', 'down', 'not working', 
                          'broken', 'issue', 'problem', 'help needed', 'cannot access']
        negative_keywords = ['problem', 'issue', 'broken', 'not working', 'error', 'failed', 'wrong']
        positive_keywords = ['thank', 'great', 'excellent', 'good', 'satisfied', 'happy']
        
        email_lower = email_body.lower()
        
        # Determine priority
        priority = 'Urgent' if any(keyword in email_lower for keyword in urgent_keywords) else 'Not Urgent'
        
        # Determine sentiment
        if any(keyword in email_lower for keyword in negative_keywords):
            sentiment = 'Negative'
        elif any(keyword in email_lower for keyword in positive_keywords):
            sentiment = 'Positive'
        else:
            sentiment = 'Neutral'
        
        # Create simple summary
        summary = f"Customer email requiring {priority.lower()} attention"
        
        return {
            'sentiment': sentiment,
            'priority': priority,
            'summary': summary,
            'extracted_info': {}
        }
    
    def generate_contextual_response(self, email_analysis: Dict[str, Any], email_body: str) -> str:
        """
        Generate contextual response using RAG pipeline.
        
        Args:
            email_analysis: Analysis results from analyze_email_content
            email_body: Original email content
            
        Returns:
            Generated response text
        """
        try:
            # Query ChromaDB for relevant knowledge
            retrieved_knowledge = self._query_knowledge_base(email_analysis['summary'])
            
            sentiment = email_analysis['sentiment']
            priority = email_analysis['priority']
            
            prompt = f"""
You are Alex, a professional Customer Support Assistant. Write a helpful email response based on the analysis below.

Customer Email Analysis:
- Sentiment: {sentiment}
- Priority: {priority}
- Summary: {email_analysis['summary']}

Relevant Knowledge Base Information:
{retrieved_knowledge}

Original Customer Email:
{email_body}

Instructions:
1. Start with a professional greeting
2. If sentiment is Negative, acknowledge their concern empathetically
3. If priority is Urgent, acknowledge the urgency
4. Use the knowledge base information to address their specific question
5. If knowledge base doesn't have the answer, say you're investigating and will follow up
6. Maintain a helpful, professional tone
7. End with: "Best regards,\\nAlex\\nCustomer Support Team"

Write the email response:
"""
            
            response = self.generation_model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return """Dear Customer,

Thank you for contacting us. We have received your email and are reviewing your request.

We will get back to you with a detailed response within 24 hours. If this is an urgent matter, please don't hesitate to call our support line.

Best regards,
Alex
Customer Support Team"""
    
    def _query_knowledge_base(self, query: str, n_results: int = 3) -> str:
        """
        Query the knowledge base for relevant information.
        
        Args:
            query: Search query (typically the email summary)
            n_results: Number of results to retrieve
            
        Returns:
            Formatted string of relevant knowledge
        """
        if not self.collection:
            return "No knowledge base available."
        
        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "No relevant information found in knowledge base."
            
            # Format the retrieved knowledge
            knowledge_chunks = []
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                knowledge_chunks.append(f"Q: {metadata['question']}\nA: {metadata['answer']}")
            
            return "\n\n".join(knowledge_chunks)
            
        except Exception as e:
            print(f"Error querying knowledge base: {str(e)}")
            return "Error retrieving knowledge base information."


# Create global instance
ai_core = AICore()


def get_ai_core() -> AICore:
    """Get the global AI core instance."""
    return ai_core