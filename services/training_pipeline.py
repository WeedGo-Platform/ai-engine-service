#!/usr/bin/env python3
"""
AI Training Pipeline for WeedGo Budtender
Collects interaction data, feedback, and trains models
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

@dataclass
class TrainingDataPoint:
    """Single training interaction"""
    customer_message: str
    inferred_params: Dict
    actual_products_shown: List[Dict]
    customer_action: str  # clicked, purchased, ignored, complained
    feedback_score: Optional[float] = None  # 1-5 stars
    correction: Optional[Dict] = None  # Human-corrected parameters
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class AITrainingPipeline:
    """
    Strategic training system for the AI budtender
    Focuses on improving accuracy through feedback loops
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.connect_db()
        self._create_training_tables()
    
    def connect_db(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
    
    def _create_training_tables(self):
        """Create tables for training data collection"""
        cur = self.conn.cursor()
        
        # Training data table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_training_data (
                id SERIAL PRIMARY KEY,
                customer_message TEXT NOT NULL,
                inferred_params JSONB NOT NULL,
                search_results JSONB,
                customer_action VARCHAR(50),
                feedback_score FLOAT,
                correction JSONB,
                response_time_ms INTEGER,
                model_confidence FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_training_action ON ai_training_data(customer_action);
            CREATE INDEX IF NOT EXISTS idx_training_score ON ai_training_data(feedback_score);
            CREATE INDEX IF NOT EXISTS idx_training_created ON ai_training_data(created_at DESC);
        """)
        
        # Parameter accuracy tracking
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parameter_accuracy (
                id SERIAL PRIMARY KEY,
                parameter_type VARCHAR(50) NOT NULL,  -- query, category, intent, size, price
                inferred_value TEXT,
                correct_value TEXT,
                is_correct BOOLEAN,
                confidence_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_param_type ON parameter_accuracy(parameter_type);
            CREATE INDEX IF NOT EXISTS idx_param_correct ON parameter_accuracy(is_correct);
        """)
        
        # Model performance metrics
        cur.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id SERIAL PRIMARY KEY,
                model_name VARCHAR(100),
                accuracy_score FLOAT,
                precision_score FLOAT,
                recall_score FLOAT,
                f1_score FLOAT,
                average_response_time_ms INTEGER,
                evaluation_date DATE DEFAULT CURRENT_DATE,
                training_samples INTEGER,
                notes TEXT
            );
        """)
        
        self.conn.commit()
    
    def record_interaction(self, 
                          customer_message: str,
                          inferred_params: Dict,
                          search_results: List[Dict],
                          response_time_ms: int,
                          model_confidence: float) -> int:
        """Record an interaction for training"""
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO ai_training_data 
            (customer_message, inferred_params, search_results, response_time_ms, model_confidence)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            customer_message,
            json.dumps(inferred_params),
            json.dumps(search_results),
            response_time_ms,
            model_confidence
        ))
        
        interaction_id = cur.fetchone()['id']
        self.conn.commit()
        
        return interaction_id
    
    def record_customer_action(self, interaction_id: int, action: str, feedback_score: Optional[float] = None):
        """Record what the customer did after seeing results"""
        
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE ai_training_data 
            SET customer_action = %s, feedback_score = %s
            WHERE id = %s
        """, (action, feedback_score, interaction_id))
        
        self.conn.commit()
    
    def record_correction(self, interaction_id: int, corrected_params: Dict):
        """Record human correction of AI inference"""
        
        cur = self.conn.cursor()
        
        # Get original data
        cur.execute("SELECT inferred_params FROM ai_training_data WHERE id = %s", (interaction_id,))
        original = cur.fetchone()
        
        if original:
            # Record the correction
            cur.execute("""
                UPDATE ai_training_data 
                SET correction = %s
                WHERE id = %s
            """, (json.dumps(corrected_params), interaction_id))
            
            # Track parameter-level accuracy
            inferred = json.loads(original['inferred_params'])
            for param_type in ['query', 'category', 'intent', 'size']:
                if param_type in corrected_params:
                    is_correct = inferred.get(param_type) == corrected_params[param_type]
                    cur.execute("""
                        INSERT INTO parameter_accuracy 
                        (parameter_type, inferred_value, correct_value, is_correct)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        param_type,
                        str(inferred.get(param_type, '')),
                        str(corrected_params[param_type]),
                        is_correct
                    ))
            
            self.conn.commit()
    
    def get_training_data(self, limit: int = 1000) -> List[Dict]:
        """Get training data for model fine-tuning"""
        
        cur = self.conn.cursor()
        
        # Prioritize corrected data and high-confidence successes
        cur.execute("""
            SELECT 
                customer_message,
                COALESCE(correction, inferred_params) as params,
                customer_action,
                feedback_score
            FROM ai_training_data
            WHERE 
                (correction IS NOT NULL OR feedback_score >= 4 OR customer_action = 'purchased')
            ORDER BY 
                CASE 
                    WHEN correction IS NOT NULL THEN 1
                    WHEN customer_action = 'purchased' THEN 2
                    WHEN feedback_score >= 4 THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT %s
        """, (limit,))
        
        return cur.fetchall()
    
    def calculate_accuracy_metrics(self) -> Dict:
        """Calculate current model accuracy metrics"""
        
        cur = self.conn.cursor()
        metrics = {}
        
        # Overall accuracy
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN customer_action IN ('clicked', 'purchased') THEN 1 END)::float / 
                COUNT(*)::float as success_rate,
                AVG(feedback_score) as avg_feedback,
                COUNT(*) as total_interactions
            FROM ai_training_data
            WHERE created_at > NOW() - INTERVAL '7 days'
        """)
        
        overall = cur.fetchone()
        metrics['success_rate'] = overall['success_rate'] or 0
        metrics['avg_feedback'] = overall['avg_feedback'] or 0
        metrics['total_interactions'] = overall['total_interactions']
        
        # Parameter-level accuracy
        cur.execute("""
            SELECT 
                parameter_type,
                COUNT(CASE WHEN is_correct THEN 1 END)::float / COUNT(*)::float as accuracy
            FROM parameter_accuracy
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY parameter_type
        """)
        
        param_accuracy = {}
        for row in cur.fetchall():
            param_accuracy[row['parameter_type']] = row['accuracy']
        
        metrics['parameter_accuracy'] = param_accuracy
        
        # Common mistakes
        cur.execute("""
            SELECT 
                parameter_type,
                inferred_value,
                correct_value,
                COUNT(*) as frequency
            FROM parameter_accuracy
            WHERE NOT is_correct
            AND created_at > NOW() - INTERVAL '7 days'
            GROUP BY parameter_type, inferred_value, correct_value
            ORDER BY frequency DESC
            LIMIT 10
        """)
        
        metrics['common_mistakes'] = cur.fetchall()
        
        return metrics
    
    def generate_training_examples(self) -> List[Dict]:
        """Generate training examples for fine-tuning"""
        
        training_data = self.get_training_data(limit=5000)
        examples = []
        
        for data in training_data:
            # Format for Llama2 fine-tuning
            example = {
                "instruction": f"Extract search parameters from: {data['customer_message']}",
                "input": data['customer_message'],
                "output": json.dumps(data['params']),
                "metadata": {
                    "action": data['customer_action'],
                    "score": data['feedback_score']
                }
            }
            examples.append(example)
        
        return examples
    
    def evaluate_model_performance(self, model_name: str) -> Dict:
        """Evaluate and record model performance"""
        
        metrics = self.calculate_accuracy_metrics()
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO model_metrics 
            (model_name, accuracy_score, average_response_time_ms, training_samples, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            model_name,
            metrics['success_rate'],
            0,  # TODO: Calculate average response time
            metrics['total_interactions'],
            json.dumps(metrics['parameter_accuracy'])
        ))
        
        self.conn.commit()
        
        return metrics


class ActiveLearningStrategy:
    """
    Active learning to identify which interactions need human review
    """
    
    def __init__(self, training_pipeline: AITrainingPipeline):
        self.pipeline = training_pipeline
    
    def identify_uncertain_cases(self) -> List[Dict]:
        """Find cases where AI was uncertain"""
        
        cur = self.pipeline.conn.cursor()
        
        # Low confidence cases
        cur.execute("""
            SELECT 
                id,
                customer_message,
                inferred_params,
                model_confidence
            FROM ai_training_data
            WHERE 
                model_confidence < 0.7
                AND correction IS NULL
                AND created_at > NOW() - INTERVAL '24 hours'
            ORDER BY model_confidence ASC
            LIMIT 50
        """)
        
        return cur.fetchall()
    
    def identify_failure_cases(self) -> List[Dict]:
        """Find cases where customer was unsatisfied"""
        
        cur = self.pipeline.conn.cursor()
        
        # Customer complaints or low ratings
        cur.execute("""
            SELECT 
                id,
                customer_message,
                inferred_params,
                search_results,
                customer_action,
                feedback_score
            FROM ai_training_data
            WHERE 
                (customer_action = 'complained' OR feedback_score < 3)
                AND correction IS NULL
                AND created_at > NOW() - INTERVAL '24 hours'
            ORDER BY feedback_score ASC NULLS LAST
            LIMIT 50
        """)
        
        return cur.fetchall()
    
    def generate_review_queue(self) -> List[Dict]:
        """Generate queue of interactions for human review"""
        
        uncertain = self.identify_uncertain_cases()
        failures = self.identify_failure_cases()
        
        # Combine and prioritize
        review_queue = []
        
        for case in failures:
            case['priority'] = 'HIGH'
            case['reason'] = 'Customer dissatisfaction'
            review_queue.append(case)
        
        for case in uncertain:
            case['priority'] = 'MEDIUM'
            case['reason'] = 'Low confidence'
            review_queue.append(case)
        
        return review_queue[:100]  # Limit to 100 per day


class SearchEndpointOptimizer:
    """
    Optimizer for the search endpoint to make it more useful
    """
    
    @staticmethod
    def explain_search_parameters():
        """
        Document expected search parameters and their behavior
        """
        
        return {
            "query": {
                "description": "Free-text search across product names and brands",
                "examples": ["pink kush", "sativa", "cookies", "high thc"],
                "behavior": "Searches product_name and brand fields using fuzzy matching"
            },
            "category": {
                "description": "Product category filter",
                "values": ["Flower", "Edibles", "Vapes", "Extracts", "Topicals", "Accessories"],
                "behavior": "Exact match filter (case-insensitive). Empty = all categories"
            },
            "intent": {
                "description": "Effect/purpose the customer is seeking",
                "values": ["sleep", "relax", "energy", "pain", "focus", "creativity", "appetite"],
                "behavior": "Searches long_description for effect mentions"
            },
            "min_price": {
                "description": "Minimum price filter",
                "behavior": "Inclusive lower bound. Products >= this price"
            },
            "max_price": {
                "description": "Maximum price filter",
                "behavior": "Inclusive upper bound. Products <= this price"
            },
            "min_thc": {
                "description": "Minimum THC percentage",
                "behavior": "Products with THC >= this value"
            },
            "max_thc": {
                "description": "Maximum THC percentage",
                "behavior": "Products with THC <= this value"
            },
            "filters": {
                "description": "Additional flexible filters",
                "examples": {
                    "plant_type": "Indica/Sativa/Hybrid",
                    "brand": "Specific brand name",
                    "size": "3.5g/7g/14g/28g"
                }
            },
            "limit": {
                "description": "Maximum results to return",
                "default": 10,
                "max": 50
            },
            "default_behavior": {
                "description": "When no filters provided",
                "behavior": "Returns ALL products, sorted by relevance/popularity"
            }
        }
    
    @staticmethod
    def generate_smart_query(user_message: str) -> str:
        """
        Generate smart query from natural language
        
        Examples:
        - "something strong" -> "high thc"
        - "for beginners" -> "low thc mild"
        - "party weed" -> "sativa energetic social"
        """
        
        # Query expansion mappings
        expansions = {
            # Strength
            "strong": "high thc potent",
            "mild": "low thc gentle",
            "beginner": "low thc mild balanced",
            
            # Effects
            "sleep": "indica sleep nighttime sedative",
            "party": "sativa energy social uplifting",
            "chill": "relax calm mellow",
            "creative": "sativa creative focus artistic",
            
            # Time of day
            "morning": "sativa daytime energy focus",
            "evening": "indica nighttime relax",
            "night": "indica sleep sedative",
            
            # Medical
            "pain": "pain relief medical cbd",
            "anxiety": "calm cbd balanced relax",
            "appetite": "appetite hunger munchies"
        }
        
        query = user_message.lower()
        
        # Apply expansions
        for term, expansion in expansions.items():
            if term in query:
                query = query.replace(term, expansion)
        
        return query