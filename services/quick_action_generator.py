"""
Quick Action Generator for AI Chat Responses
Generates contextual quick action buttons dynamically based on conversation
"""
import json
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)

class QuickActionGenerator:
    """Generates dynamic quick action suggestions based on conversation context"""
    
    def __init__(self):
        pass
    
    def generate_actions(self, 
                        intent: str, 
                        context: Dict[str, Any],
                        products_shown: bool = False,
                        stage: str = 'greeting',
                        ai_response: str = None,
                        user_message: str = None) -> List[Dict[str, Any]]:
        """
        Generate dynamic quick actions based on conversation context
        
        Args:
            intent: The detected intent from the conversation
            context: Current conversation context
            products_shown: Whether products were shown in the response
            stage: Current conversation stage
            ai_response: The AI's response text
            user_message: The user's original message
            
        Returns:
            List of quick action dictionaries
        """
        
        # Use dynamic generation
        return self.generate_contextual_actions(
            ai_response=ai_response or context.get('last_response', ''),
            user_message=user_message or context.get('last_message', ''),
            conversation_context=context,
            stage=stage,
            intent=intent
        )
    
    def generate_contextual_actions(self, 
                                   ai_response: str, 
                                   user_message: str,
                                   conversation_context: Dict,
                                   stage: str = None,
                                   intent: str = None) -> List[Dict]:
        """
        Generate truly dynamic quick actions by analyzing conversation
        
        Args:
            ai_response: The AI's response to the user
            user_message: The user's original message
            conversation_context: Additional context about the conversation
            stage: Current conversation stage
            intent: Detected intent
            
        Returns:
            List of contextually relevant quick actions
        """
        
        actions = []
        ai_lower = ai_response.lower() if ai_response else ''
        user_lower = user_message.lower() if user_message else ''
        
        # Analyze what was discussed
        discussed_product = None
        discussed_effect = None
        discussed_category = None
        asked_question = '?' in ai_response
        
        # Extract product mentions from AI response
        product_patterns = [
            r'(blue dream|og kush|purple kush|northern lights|sour diesel|granddaddy purple)',
            r'\b(indica|sativa|hybrid)\b',
            r'\b(flower|edibles?|vapes?|extracts?|pre-rolls?|joints?)\b',
        ]
        for pattern in product_patterns:
            match = re.search(pattern, ai_lower)
            if match:
                discussed_product = match.group(1)
                break
        
        # Extract category mentions
        category_patterns = [
            r'\b(flower|edibles?|vapes?|extracts?|pre-rolls?|topicals?|accessories)\b',
        ]
        for pattern in category_patterns:
            match = re.search(pattern, ai_lower)
            if match:
                discussed_category = match.group(1)
                break
        
        # Extract effect mentions
        effect_patterns = [
            r'\b(relax|sleep|pain|anxiety|energy|focus|creative|appetite|stress|depression)\b',
            r'\b(calm|uplift|euphori|happy|sedating|energizing)\b',
        ]
        for pattern in effect_patterns:
            match = re.search(pattern, ai_lower)
            if match:
                discussed_effect = match.group(1)
                break
        
        # Check for price discussions
        discussed_price = '$' in ai_response or 'price' in ai_lower or 'cost' in ai_lower
        
        # Generate contextual actions based on analysis
        if discussed_product and not asked_question:
            # Specific product was mentioned - offer related actions
            product_name = discussed_product.title()
            actions.extend([
                {'label': f'More about {product_name[:12]}', 'value': f'Tell me more about {discussed_product}', 'type': 'info'},
                {'label': 'Add to cart', 'value': f'Add {discussed_product} to my cart', 'type': 'confirm'},
                {'label': 'Similar options', 'value': f'Show me similar to {discussed_product}', 'type': 'product'},
                {'label': 'Check price', 'value': f'What\'s the price of {discussed_product}?', 'type': 'price'}
            ])
        
        elif discussed_effect and not asked_question:
            # Effect was discussed - offer products for that effect
            effect_name = discussed_effect.title()
            actions.extend([
                {'label': f'Best for {effect_name}', 'value': f'What\'s best for {discussed_effect}?', 'type': 'product'},
                {'label': f'All {effect_name} products', 'value': f'Show all for {discussed_effect}', 'type': 'product'},
                {'label': 'Compare strains', 'value': f'Compare strains for {discussed_effect}', 'type': 'info'},
                {'label': 'Other effects', 'value': 'What about other effects?', 'type': 'navigate'}
            ])
        
        elif discussed_category:
            # Category mentioned - offer navigation within category
            cat_name = discussed_category.title()
            actions.extend([
                {'label': f'Browse {cat_name}', 'value': f'Show me all {discussed_category}', 'type': 'category'},
                {'label': f'Best {cat_name}', 'value': f'What are your best {discussed_category}?', 'type': 'product'},
                {'label': 'Price ranges', 'value': f'{cat_name} price ranges?', 'type': 'price'},
                {'label': 'Other categories', 'value': 'Show other categories', 'type': 'navigate'}
            ])
        
        elif asked_question:
            # AI asked a question - provide contextual responses
            if 'how much' in ai_lower or 'quantity' in ai_lower:
                actions.extend([
                    {'label': '1 gram', 'value': 'Just 1 gram', 'type': 'product'},
                    {'label': 'Eighth (3.5g)', 'value': 'An eighth please', 'type': 'product'},
                    {'label': 'Quarter (7g)', 'value': 'A quarter ounce', 'type': 'product'},
                    {'label': 'Help me decide', 'value': 'What do you recommend?', 'type': 'info'}
                ])
            elif 'help' in ai_lower or 'looking for' in ai_lower or 'need' in ai_lower:
                actions.extend([
                    {'label': 'Relaxation', 'value': 'Something to relax', 'type': 'effect'},
                    {'label': 'Pain relief', 'value': 'For pain relief', 'type': 'effect'},
                    {'label': 'Energy boost', 'value': 'Something energizing', 'type': 'effect'},
                    {'label': 'Browse all', 'value': 'Just show me options', 'type': 'navigate'}
                ])
            elif 'prefer' in ai_lower or 'like' in ai_lower or 'type' in ai_lower:
                actions.extend([
                    {'label': 'Flower', 'value': 'I prefer flower', 'type': 'category'},
                    {'label': 'Edibles', 'value': 'I like edibles', 'type': 'category'},
                    {'label': 'Vapes', 'value': 'Vaping products', 'type': 'category'},
                    {'label': 'Surprise me', 'value': 'Recommend something', 'type': 'info'}
                ])
            elif 'experience' in ai_lower or 'new' in ai_lower or 'first' in ai_lower:
                actions.extend([
                    {'label': 'First timer', 'value': 'This is my first time', 'type': 'info'},
                    {'label': 'Some experience', 'value': 'I have some experience', 'type': 'info'},
                    {'label': 'Regular user', 'value': 'I use regularly', 'type': 'info'},
                    {'label': 'Need guidance', 'value': 'Help me understand', 'type': 'navigate'}
                ])
        
        elif 'welcome' in ai_lower or 'hello' in ai_lower or 'hi' in ai_lower or stage == 'greeting':
            # Greeting - show initial exploration options
            actions.extend([
                {'label': 'Browse products', 'value': 'Show me products', 'type': 'product'},
                {'label': 'Get recommendation', 'value': 'Recommend something', 'type': 'info'},
                {'label': 'New to cannabis', 'value': 'I\'m new to this', 'type': 'info'},
                {'label': 'Specific need', 'value': 'I have a specific need', 'type': 'navigate'}
            ])
        
        elif discussed_price or '$' in ai_response:
            # Price was mentioned
            actions.extend([
                {'label': 'Buy it', 'value': 'I\'ll take it', 'type': 'confirm'},
                {'label': 'Cheaper options', 'value': 'Show cheaper options', 'type': 'price'},
                {'label': 'Compare prices', 'value': 'Compare similar products', 'type': 'product'},
                {'label': 'Keep browsing', 'value': 'Show me more', 'type': 'navigate'}
            ])
        
        elif 'cart' in ai_lower or 'added' in ai_lower:
            # Cart action performed
            actions.extend([
                {'label': 'Checkout', 'value': 'Ready to checkout', 'type': 'confirm'},
                {'label': 'Keep shopping', 'value': 'Show more products', 'type': 'navigate'},
                {'label': 'View cart', 'value': 'Show my cart', 'type': 'info'},
                {'label': 'Remove item', 'value': 'Remove from cart', 'type': 'confirm'}
            ])
        
        # Default fallback if no specific context matched
        if not actions:
            # Analyze user intent for fallback
            if 'what' in user_lower or 'show' in user_lower:
                actions.extend([
                    {'label': 'All products', 'value': 'Show all products', 'type': 'product'},
                    {'label': 'Categories', 'value': 'Show categories', 'type': 'navigate'},
                    {'label': 'Best sellers', 'value': 'What\'s popular?', 'type': 'product'},
                    {'label': 'Help me choose', 'value': 'Help me decide', 'type': 'info'}
                ])
            else:
                actions.extend([
                    {'label': 'Tell me more', 'value': 'Can you explain more?', 'type': 'info'},
                    {'label': 'Show products', 'value': 'What do you have?', 'type': 'product'},
                    {'label': 'Get help', 'value': 'I need help', 'type': 'navigate'},
                    {'label': 'Start fresh', 'value': 'Let\'s start over', 'type': 'navigate'}
                ])
        
        # Ensure unique actions and proper formatting
        seen_labels = set()
        unique_actions = []
        for i, action in enumerate(actions):
            if action['label'] not in seen_labels:
                seen_labels.add(action['label'])
                # Add unique ID if not present
                if 'id' not in action:
                    action['id'] = f"{action['type']}_{intent or 'general'}_{i}"
                unique_actions.append(action)
                if len(unique_actions) >= 4:
                    break
        
        return unique_actions