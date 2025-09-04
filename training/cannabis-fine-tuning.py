#!/usr/bin/env python3
"""
Cannabis-Specific Fine-Tuning Dataset Generator
Creates training data from OCS products for Llama 2 fine-tuning
"""

import json
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import random

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "database": "ai_engine",
    "user": "weedgo",
    "password": "weedgo123"
}

class CannabisTrainingDataGenerator:
    """Generate high-quality training data for cannabis domain"""
    
    def __init__(self):
        self.training_data = []
        self.products = self.load_products()
        print(f"📊 Loaded {len(self.products)} products from database")
    
    def load_products(self) -> List[Dict]:
        """Load all products from database"""
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE thc_max_percent IS NOT NULL 
                    LIMIT 1000
                """)
                return cursor.fetchall()
        finally:
            conn.close()
    
    def generate_training_examples(self):
        """Generate diverse training examples"""
        
        # 1. Product recommendation conversations
        self.generate_recommendation_examples()
        
        # 2. Medical condition examples
        self.generate_medical_examples()
        
        # 3. Dosage guidance examples
        self.generate_dosage_examples()
        
        # 4. Terpene education examples
        self.generate_terpene_examples()
        
        # 5. Effect-based queries
        self.generate_effect_examples()
        
        # 6. Comparison questions
        self.generate_comparison_examples()
        
        print(f"✅ Generated {len(self.training_data)} training examples")
    
    def generate_recommendation_examples(self):
        """Generate product recommendation examples"""
        
        # Indica recommendations
        indica_products = [p for p in self.products if 'Indica' in str(p.get('plant_type', ''))]
        if indica_products:
            for _ in range(20):
                product = random.choice(indica_products)
                examples = [
                    {
                        "instruction": "I need something to help me sleep",
                        "input": "",
                        "output": f"For sleep, I recommend {product['brand']} - {product['product_name']}, an Indica-dominant strain with {product['thc_max_percent']}% THC. Indica strains are known for their sedating effects, perfect for nighttime use. This particular strain will help you relax and drift off to sleep. Start with a small amount about an hour before bedtime."
                    },
                    {
                        "instruction": "What's good for relaxation after work?",
                        "input": "",
                        "output": f"For post-work relaxation, try {product['brand']} - {product['product_name']}. With {product['thc_max_percent']}% THC and an Indica-dominant profile, it provides deep relaxation without being overwhelming. The {product.get('terpenes', 'terpene profile')} enhances the calming effects. Perfect for unwinding after a stressful day."
                    }
                ]
                self.training_data.extend(examples)
        
        # Sativa recommendations  
        sativa_products = [p for p in self.products if 'Sativa' in str(p.get('plant_type', ''))]
        if sativa_products:
            for _ in range(20):
                product = random.choice(sativa_products)
                examples = [
                    {
                        "instruction": "I want something energizing for daytime",
                        "input": "",
                        "output": f"For daytime energy, I recommend {product['brand']} - {product['product_name']}, a Sativa-dominant strain with {product['thc_max_percent']}% THC. Sativa strains provide uplifting, energizing effects perfect for daytime activities. This strain will keep you focused and creative without the couch-lock effect."
                    },
                    {
                        "instruction": "What's good for creativity and focus?",
                        "input": "",
                        "output": f"{product['brand']} - {product['product_name']} is excellent for creativity and focus. As a Sativa with {product['thc_max_percent']}% THC, it provides cerebral stimulation and enhanced focus. Many artists and creators prefer this type of strain for their work."
                    }
                ]
                self.training_data.extend(examples)
        
        # CBD recommendations
        cbd_products = [p for p in self.products if float(p.get('cbd_max_percent', 0)) > 5]
        if cbd_products:
            for _ in range(20):
                product = random.choice(cbd_products)
                examples = [
                    {
                        "instruction": "I want the medical benefits without getting high",
                        "input": "",
                        "output": f"For therapeutic benefits without intoxication, try {product['brand']} - {product['product_name']} with {product['cbd_max_percent']}% CBD and only {product['thc_max_percent']}% THC. CBD provides anti-inflammatory, anti-anxiety, and pain-relieving benefits without the psychoactive effects of THC."
                    },
                    {
                        "instruction": "What's good for anxiety without the high?",
                        "input": "",
                        "output": f"{product['brand']} - {product['product_name']} is perfect for anxiety relief without intoxication. With {product['cbd_max_percent']}% CBD and minimal THC ({product['thc_max_percent']}%), it provides calming effects while keeping you clear-headed and functional."
                    }
                ]
                self.training_data.extend(examples)
    
    def generate_medical_examples(self):
        """Generate medical condition examples"""
        
        medical_qa = [
            {
                "instruction": "Can cannabis help with chronic pain?",
                "input": "",
                "output": "Cannabis can be effective for chronic pain management. Both THC and CBD have analgesic properties. THC activates CB1 receptors in the pain processing areas of the brain and spinal cord, while CBD reduces inflammation. For chronic pain, a balanced 1:1 THC:CBD ratio often works well. Start with 2.5mg of each and gradually increase. Always consult with a healthcare provider for chronic conditions."
            },
            {
                "instruction": "What about cannabis for arthritis?",
                "input": "",
                "output": "Cannabis may help with arthritis through multiple mechanisms. CBD's anti-inflammatory properties can reduce joint inflammation, while THC helps with pain perception. Topical cannabis products can provide localized relief without psychoactive effects. For systemic relief, consider a 2:1 CBD:THC ratio. The terpene caryophyllene also has anti-inflammatory properties. Consult your doctor before replacing any prescribed medications."
            },
            {
                "instruction": "Can cannabis help with PTSD?",
                "input": "",
                "output": "Research suggests cannabis may help with PTSD symptoms. CBD can reduce anxiety and improve sleep, while controlled THC doses may help with nightmare reduction and emotional regulation. Many PTSD patients find success with CBD-dominant strains (3:1 or higher CBD:THC ratio). The terpenes linalool and limonene provide additional anxiolytic effects. This should be part of a comprehensive treatment plan with professional support."
            },
            {
                "instruction": "What's recommended for cancer treatment side effects?",
                "input": "",
                "output": "Cannabis can help manage cancer treatment side effects. THC is effective for chemotherapy-induced nausea and vomiting, while also stimulating appetite. CBD helps with pain, anxiety, and may have anti-tumor properties (though more research is needed). For nausea, THC-dominant products work well. For general symptom management, balanced ratios are often preferred. Always coordinate with your oncology team."
            },
            {
                "instruction": "Can cannabis help with epilepsy?",
                "input": "",
                "output": "CBD has shown significant promise for certain types of epilepsy. Epidiolex, a pharmaceutical CBD product, is FDA-approved for Dravet and Lennox-Gastaut syndromes. CBD appears to reduce seizure frequency without the psychoactive effects of THC. High-CBD, low-THC products (20:1 or higher) are typically recommended. This must be managed by a healthcare provider as it can interact with anti-epileptic medications."
            }
        ]
        
        self.training_data.extend(medical_qa)
    
    def generate_dosage_examples(self):
        """Generate dosage guidance examples"""
        
        dosage_qa = [
            {
                "instruction": "I'm new to cannabis, how much should I take?",
                "input": "",
                "output": "As a beginner, 'start low and go slow' is the golden rule. For smoking/vaping: Start with one small puff and wait 15 minutes. For edibles: Start with 2.5mg THC and wait 2-3 hours before taking more (edibles can take up to 2 hours to kick in). For oils: Start with 0.25ml. Keep a journal to track effects and find your optimal dose."
            },
            {
                "instruction": "How much edible should I take?",
                "input": "",
                "output": "Edible dosing depends on your tolerance. Beginners: 2.5mg THC. Occasional users: 5-10mg THC. Regular users: 10-20mg THC. Heavy users: 20mg+ THC. Remember, edibles take 30-120 minutes to take effect and last 4-8 hours. Never take more within the first 2 hours - many people make this mistake and get too high. If you take too much, stay calm, hydrate, and rest it out."
            },
            {
                "instruction": "What's the difference between smoking and edible dosing?",
                "input": "",
                "output": "Smoking and edibles differ significantly. Smoking: Effects in 2-10 minutes, peak at 30 minutes, last 1-3 hours. Easier to control dose. Edibles: Effects in 30-120 minutes, peak at 2-4 hours, last 4-8 hours. Stronger effects due to liver metabolism (THC converts to 11-hydroxy-THC). Smoking allows quick dose adjustment, while edibles require patience and planning."
            },
            {
                "instruction": "How do I microdose cannabis?",
                "input": "",
                "output": "Microdosing involves taking sub-perceptual doses for therapeutic benefits without intoxication. Typical microdoses: 1-2.5mg THC or 5-10mg CBD. For flowers, use a one-hitter or vaporizer at low temperature. For oils, measure precisely with a syringe. Take your microdose 2-3 times daily. Benefits include improved mood, focus, and creativity without impairment. Keep a journal to find your sweet spot."
            }
        ]
        
        self.training_data.extend(dosage_qa)
    
    def generate_terpene_examples(self):
        """Generate terpene education examples"""
        
        terpene_qa = [
            {
                "instruction": "What are terpenes and why do they matter?",
                "input": "",
                "output": "Terpenes are aromatic compounds found in cannabis and many other plants. They're responsible for cannabis flavors and aromas, but more importantly, they contribute to effects through the 'entourage effect.' For example, myrcene is sedating, limonene is uplifting, and pinene promotes alertness. Understanding terpenes helps you choose strains beyond just THC/CBD content for more predictable effects."
            },
            {
                "instruction": "Which terpene is best for anxiety?",
                "input": "",
                "output": "Linalool is excellent for anxiety. Also found in lavender, it has proven anxiolytic and sedating properties. Limonene (citrus) is another great option, providing mood elevation and stress relief. Beta-caryophyllene activates CB2 receptors, providing anti-anxiety effects without intoxication. Look for strains high in these terpenes, often found in products labeled 'calming' or 'relaxing.'"
            },
            {
                "instruction": "What terpene helps with pain?",
                "input": "",
                "output": "Beta-caryophyllene is the best terpene for pain relief. It's unique because it directly activates CB2 receptors like a cannabinoid, providing anti-inflammatory and analgesic effects. Myrcene also helps with pain and enhances THC absorption. Pinene has anti-inflammatory properties. Look for strains with this terpene profile for enhanced pain management."
            },
            {
                "instruction": "Which terpenes give energy?",
                "input": "",
                "output": "For energy and focus, look for pinene, limonene, and terpinolene. Pinene (pine scent) promotes alertness and may counteract THC-induced memory impairment. Limonene (citrus) is uplifting and mood-enhancing. Terpinolene has stimulating effects. These terpenes are common in Sativa-dominant strains and contribute to their energizing reputation."
            }
        ]
        
        self.training_data.extend(terpene_qa)
    
    def generate_effect_examples(self):
        """Generate effect-based query examples"""
        
        for product in random.sample(self.products, min(50, len(self.products))):
            if 'Indica' in str(product.get('plant_type', '')):
                effect = random.choice(['relaxation', 'sleep', 'pain relief', 'stress relief'])
            elif 'Sativa' in str(product.get('plant_type', '')):
                effect = random.choice(['energy', 'creativity', 'focus', 'social'])
            else:
                effect = random.choice(['balanced', 'mild effects', 'all-day use', 'versatile'])
            
            example = {
                "instruction": f"I want something for {effect}",
                "input": "",
                "output": f"For {effect}, I recommend {product['brand']} - {product['product_name']}. This {product.get('plant_type', 'cannabis product')} with {product['thc_max_percent']}% THC and {product['cbd_max_percent']}% CBD is perfect for your needs. {product.get('short_description', 'It provides the effects you are looking for.')} Available in {product.get('size', 'various sizes')} for ${product.get('unit_price', 'competitive pricing')}."
            }
            self.training_data.append(example)
    
    def generate_comparison_examples(self):
        """Generate strain comparison examples"""
        
        comparison_qa = [
            {
                "instruction": "What's the difference between Indica and Sativa?",
                "input": "",
                "output": "Indica and Sativa describe different effects profiles. Indica: Body-focused, relaxing, sedating effects. Best for evening, sleep, pain relief, and relaxation. Often described as 'body high.' Sativa: Mind-focused, energizing, uplifting effects. Best for daytime, creativity, social activities, and focus. Often described as 'head high.' Hybrid: Combines both effects, can be Indica or Sativa dominant. Modern cannabis is mostly hybrid with varying ratios."
            },
            {
                "instruction": "THC vs CBD - what's the difference?",
                "input": "",
                "output": "THC (Tetrahydrocannabinol) and CBD (Cannabidiol) are the main cannabinoids but have different effects. THC: Psychoactive (gets you 'high'), euphoria, increased appetite, pain relief, may cause anxiety in high doses. CBD: Non-psychoactive, anti-anxiety, anti-inflammatory, neuroprotective, reduces THC side effects. Together they create the 'entourage effect' where they work synergistically. Different ratios serve different purposes."
            },
            {
                "instruction": "Should I choose high THC or balanced strains?",
                "input": "",
                "output": "The choice depends on your goals and tolerance. High THC (20%+): Strong psychoactive effects, better for experienced users, effective for severe pain, strong euphoria, higher risk of anxiety. Balanced (equal THC:CBD): Milder psychoactive effects, reduced anxiety risk, good for medical use, suitable for beginners, therapeutic without overwhelming effects. Start balanced if you're new or want functionality."
            }
        ]
        
        self.training_data.extend(comparison_qa)
    
    def save_training_data(self, format='jsonl'):
        """Save training data in various formats"""
        
        if format == 'jsonl':
            # JSONL format for Llama fine-tuning
            with open('cannabis_training_data.jsonl', 'w') as f:
                for example in self.training_data:
                    f.write(json.dumps(example) + '\n')
            print(f"📁 Saved {len(self.training_data)} examples to cannabis_training_data.jsonl")
        
        elif format == 'alpaca':
            # Alpaca format for instruction tuning
            with open('cannabis_training_alpaca.json', 'w') as f:
                json.dump(self.training_data, f, indent=2)
            print(f"📁 Saved {len(self.training_data)} examples to cannabis_training_alpaca.json")
        
        # Create validation split
        random.shuffle(self.training_data)
        split_point = int(len(self.training_data) * 0.9)
        
        train_data = self.training_data[:split_point]
        val_data = self.training_data[split_point:]
        
        with open('cannabis_train.jsonl', 'w') as f:
            for example in train_data:
                f.write(json.dumps(example) + '\n')
        
        with open('cannabis_val.jsonl', 'w') as f:
            for example in val_data:
                f.write(json.dumps(example) + '\n')
        
        print(f"📊 Split: {len(train_data)} training, {len(val_data)} validation examples")
    
    def generate_system_prompts(self):
        """Generate optimized system prompts for different scenarios"""
        
        prompts = {
            "general": """You are an expert cannabis budtender with comprehensive knowledge of strains, terpenes, cannabinoids, and their effects. Provide accurate, helpful, and safe guidance while following Canadian regulations. Always prioritize customer safety and recommend starting with low doses.""",
            
            "medical": """You are a medical cannabis consultant with expertise in cannabinoid therapeutics. Provide evidence-based information about cannabis for medical conditions while always recommending consultation with healthcare providers. Never make definitive medical claims.""",
            
            "beginner": """You are a friendly cannabis educator helping beginners. Explain things simply, emphasize safety, and always recommend 'start low and go slow.' Focus on preventing overconsumption and ensuring positive first experiences.""",
            
            "experienced": """You are a cannabis sommelier for experienced users. Discuss nuanced effects, terpene profiles, and advanced consumption methods. Provide detailed strain comparisons and help optimize their cannabis experience."""
        }
        
        with open('system_prompts.json', 'w') as f:
            json.dump(prompts, f, indent=2)
        
        print("📝 Generated system prompts for different contexts")

def main():
    """Generate comprehensive cannabis training data"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     Cannabis Training Data Generator for Llama 2       ║
    ║     Creating Domain-Specific Fine-Tuning Dataset       ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    generator = CannabisTrainingDataGenerator()
    
    print("\n🔨 Generating training examples...")
    generator.generate_training_examples()
    
    print("\n💾 Saving training data...")
    generator.save_training_data('jsonl')
    generator.save_training_data('alpaca')
    
    print("\n📝 Generating system prompts...")
    generator.generate_system_prompts()
    
    print(f"""
    ✅ Training Data Generation Complete!
    
    Files created:
    • cannabis_training_data.jsonl - Full dataset in JSONL format
    • cannabis_training_alpaca.json - Alpaca format for instruction tuning
    • cannabis_train.jsonl - 90% training split
    • cannabis_val.jsonl - 10% validation split
    • system_prompts.json - Optimized system prompts
    
    Total examples: {len(generator.training_data)}
    
    Next steps:
    1. Fine-tune Llama 2 with this data
    2. Test the fine-tuned model
    3. Deploy to production
    """)

if __name__ == "__main__":
    main()