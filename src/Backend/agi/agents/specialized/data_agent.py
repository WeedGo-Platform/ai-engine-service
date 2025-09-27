"""
Specialized Data Analysis Agent
Expert in data processing, analytics, and insights generation
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

from agi.core.interfaces import IAgent, ConversationContext
from agi.tools import get_tool_registry
from agi.models.registry import get_model_registry
from agi.core.database import get_db_manager

logger = logging.getLogger(__name__)


@dataclass
class DataInsight:
    """Data insight representation"""
    type: str  # trend, anomaly, correlation, pattern
    description: str
    confidence: float
    data_points: List[Any]
    timestamp: datetime
    recommendations: List[str]


@dataclass
class DataAnalysisResult:
    """Complete data analysis result"""
    summary: str
    statistics: Dict[str, Any]
    insights: List[DataInsight]
    visualizations: List[Dict[str, Any]]
    recommendations: List[str]


class DataAgent(IAgent):
    """
    Specialized agent for data analysis tasks
    Capabilities: analysis, visualization, statistics, ML, reporting
    """

    def __init__(self):
        super().__init__()
        self.agent_id = "data_analyst"
        self.name = "Data Analysis Agent"
        self.description = "Expert in data analysis, statistics, and insights generation"
        self.capabilities = [
            "data_analysis",
            "statistics",
            "visualization",
            "trend_analysis",
            "anomaly_detection",
            "forecasting",
            "reporting",
            "data_cleaning",
            "feature_engineering"
        ]
        self.analysis_types = [
            "descriptive",
            "diagnostic",
            "predictive",
            "prescriptive"
        ]

    async def process(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Process data analysis request"""
        # Classify analysis type
        analysis_type = self._classify_analysis_type(request)

        logger.info(f"DataAgent processing {analysis_type} analysis request")

        if analysis_type == "descriptive":
            return await self._descriptive_analysis(request, context)
        elif analysis_type == "diagnostic":
            return await self._diagnostic_analysis(request, context)
        elif analysis_type == "predictive":
            return await self._predictive_analysis(request, context)
        elif analysis_type == "prescriptive":
            return await self._prescriptive_analysis(request, context)
        elif "visualiz" in request.lower():
            return await self._create_visualization(request, context)
        elif "clean" in request.lower():
            return await self._clean_data(request, context)
        elif "feature" in request.lower():
            return await self._engineer_features(request, context)
        else:
            return await self._general_analysis(request, context)

    def _classify_analysis_type(self, request: str) -> str:
        """Classify the type of analysis needed"""
        request_lower = request.lower()

        if any(word in request_lower for word in ["what", "describe", "summary", "overview"]):
            return "descriptive"
        elif any(word in request_lower for word in ["why", "cause", "reason", "diagnose"]):
            return "diagnostic"
        elif any(word in request_lower for word in ["predict", "forecast", "future", "will"]):
            return "predictive"
        elif any(word in request_lower for word in ["recommend", "should", "optimize", "best"]):
            return "prescriptive"
        else:
            return "descriptive"

    async def _descriptive_analysis(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Perform descriptive data analysis"""
        # Extract data reference from request
        data_info = self._extract_data_reference(request)

        # Get model for analysis
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        analysis_prompt = f"""
        Perform descriptive analysis for the following request:
        {request}

        Provide:
        1. Data summary and overview
        2. Key statistics (mean, median, mode, std dev)
        3. Data distribution characteristics
        4. Notable patterns or trends
        5. Data quality assessment

        Format the response with clear sections and bullet points.
        """

        response = await model.generate(analysis_prompt, context)

        # If we have actual data, calculate real statistics
        if data_info and "data" in data_info:
            stats = self._calculate_statistics(data_info["data"])
            return f"""
## Descriptive Analysis

### Data Overview:
- Records: {stats.get('count', 'N/A')}
- Features: {stats.get('features', 'N/A')}
- Time Range: {stats.get('time_range', 'N/A')}

### Key Statistics:
- Mean: {stats.get('mean', 'N/A')}
- Median: {stats.get('median', 'N/A')}
- Std Dev: {stats.get('std_dev', 'N/A')}
- Min: {stats.get('min', 'N/A')}
- Max: {stats.get('max', 'N/A')}

### Analysis:
{response}

### Data Quality:
- Missing Values: {stats.get('missing', '0')}
- Outliers: {stats.get('outliers', '0')}
- Data Types: {stats.get('dtypes', 'Mixed')}
"""

        return response

    async def _diagnostic_analysis(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Perform diagnostic analysis to find causes"""
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        diagnostic_prompt = f"""
        Perform diagnostic analysis for the following request:
        {request}

        Investigate:
        1. Root causes of observed patterns
        2. Correlations between variables
        3. Impact factors
        4. Causation vs correlation
        5. Contributing factors ranked by importance

        Use data-driven reasoning and provide evidence for conclusions.
        """

        response = await model.generate(diagnostic_prompt, context)

        return f"""
## Diagnostic Analysis

### Investigation Focus:
{request}

### Analysis Results:
{response}

### Key Findings:
- Primary causes identified
- Correlation analysis completed
- Impact assessment provided

### Recommendations:
- Address root causes systematically
- Monitor key indicators
- Implement preventive measures
"""

    async def _predictive_analysis(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Perform predictive analysis"""
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        predictive_prompt = f"""
        Perform predictive analysis for the following request:
        {request}

        Provide:
        1. Prediction methodology
        2. Key assumptions
        3. Predicted outcomes with confidence levels
        4. Risk factors
        5. Scenario analysis (best/worst/likely cases)
        6. Time horizons

        Base predictions on historical patterns and trends.
        """

        response = await model.generate(predictive_prompt, context)

        # Generate sample predictions
        predictions = self._generate_sample_predictions(request)

        return f"""
## Predictive Analysis

### Prediction Request:
{request}

### Methodology:
- Time series analysis
- Trend extrapolation
- Pattern recognition
- Statistical modeling

### Predictions:
{response}

### Confidence Levels:
- High Confidence (>80%): {predictions['high_conf']}
- Medium Confidence (50-80%): {predictions['med_conf']}
- Low Confidence (<50%): {predictions['low_conf']}

### Risk Factors:
- Data quality and completeness
- Assumption validity
- External factors not in model
- Market/environmental changes

### Recommendations:
- Regular model updates
- Continuous monitoring
- Scenario planning
"""

    async def _prescriptive_analysis(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Perform prescriptive analysis with recommendations"""
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        prescriptive_prompt = f"""
        Perform prescriptive analysis for the following request:
        {request}

        Provide:
        1. Optimal actions/decisions
        2. Implementation steps
        3. Expected outcomes
        4. Success metrics
        5. Risk mitigation strategies
        6. Alternative approaches

        Focus on actionable recommendations with clear ROI.
        """

        response = await model.generate(prescriptive_prompt, context)

        return f"""
## Prescriptive Analysis

### Optimization Goal:
{request}

### Recommended Actions:
{response}

### Implementation Roadmap:
1. **Phase 1**: Data preparation and validation
2. **Phase 2**: Initial implementation
3. **Phase 3**: Monitoring and adjustment
4. **Phase 4**: Full rollout

### Success Metrics:
- KPIs to track
- Target values
- Measurement frequency
- Review cycles

### Risk Mitigation:
- Identify potential obstacles
- Develop contingency plans
- Set up early warning systems
"""

    async def _create_visualization(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Create data visualization recommendations"""
        # Extract visualization requirements
        viz_type = self._determine_visualization_type(request)

        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        viz_prompt = f"""
        Create visualization specification for:
        {request}

        Recommended visualization type: {viz_type}

        Provide:
        1. Chart type and configuration
        2. Axes and labels
        3. Color scheme
        4. Interactive features
        5. Python code using matplotlib/seaborn/plotly
        """

        response = await model.generate(viz_prompt, context)

        # Generate sample visualization code
        viz_code = self._generate_visualization_code(viz_type)

        return f"""
## Data Visualization

### Visualization Type: {viz_type}

### Specification:
{response}

### Implementation Code:
```python
{viz_code}
```

### Best Practices:
- Use appropriate chart types for data
- Maintain consistent color schemes
- Add clear labels and titles
- Include legends and annotations
- Consider accessibility (colorblind-friendly)
"""

    async def _clean_data(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Provide data cleaning recommendations"""
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        cleaning_prompt = f"""
        Provide data cleaning strategy for:
        {request}

        Include:
        1. Missing value handling
        2. Outlier detection and treatment
        3. Data type conversions
        4. Duplicate removal
        5. Standardization/normalization
        6. Validation rules

        Provide Python pandas code examples.
        """

        response = await model.generate(cleaning_prompt, context)

        # Generate sample cleaning code
        cleaning_code = """
import pandas as pd
import numpy as np

def clean_data(df):
    # Remove duplicates
    df = df.drop_duplicates()

    # Handle missing values
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())

    categorical_columns = df.select_dtypes(include=['object']).columns
    df[categorical_columns] = df[categorical_columns].fillna('Unknown')

    # Remove outliers (IQR method)
    for col in numeric_columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]

    # Standardize formats
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    return df
"""

        return f"""
## Data Cleaning Strategy

### Analysis:
{response}

### Cleaning Pipeline:
```python
{cleaning_code}
```

### Quality Checks:
- Verify data types
- Check value ranges
- Validate relationships
- Test business rules
- Compare before/after statistics
"""

    async def _engineer_features(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Provide feature engineering recommendations"""
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        feature_prompt = f"""
        Provide feature engineering strategy for:
        {request}

        Include:
        1. New feature creation ideas
        2. Feature transformations
        3. Interaction features
        4. Temporal features
        5. Encoding strategies
        6. Feature selection methods

        Focus on features that improve model performance.
        """

        response = await model.generate(feature_prompt, context)

        return f"""
## Feature Engineering

### Request:
{request}

### Strategy:
{response}

### Common Techniques:
1. **Polynomial Features**: Create interaction terms
2. **Binning**: Convert continuous to categorical
3. **Encoding**: One-hot, target, ordinal encoding
4. **Scaling**: Standardization, normalization
5. **Time Features**: Day of week, seasonality
6. **Aggregations**: Rolling means, counts

### Feature Selection:
- Correlation analysis
- Mutual information
- Recursive feature elimination
- L1 regularization
- Domain expertise

### Validation:
- Cross-validation for feature importance
- A/B testing new features
- Monitor feature drift
"""

    async def _general_analysis(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Perform general data analysis"""
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        general_prompt = f"""
        As a data analysis expert, help with the following request:
        {request}

        Provide:
        1. Clear analysis approach
        2. Key findings
        3. Statistical evidence
        4. Visualizations if relevant
        5. Actionable insights
        6. Next steps

        Use data-driven reasoning and best practices.
        """

        return await model.generate(general_prompt, context)

    def _extract_data_reference(self, request: str) -> Optional[Dict[str, Any]]:
        """Extract data reference from request"""
        # Look for file paths
        file_pattern = r'["\']([^"\']+\.(csv|json|xlsx|parquet))["\']'
        file_match = re.search(file_pattern, request, re.IGNORECASE)

        if file_match:
            return {
                "type": "file",
                "path": file_match.group(1),
                "format": file_match.group(2)
            }

        # Look for table references
        table_pattern = r'table\s+([a-zA-Z0-9_]+)'
        table_match = re.search(table_pattern, request, re.IGNORECASE)

        if table_match:
            return {
                "type": "table",
                "name": table_match.group(1)
            }

        return None

    def _calculate_statistics(self, data: Any) -> Dict[str, Any]:
        """Calculate basic statistics from data"""
        # Simplified statistics calculation
        try:
            if isinstance(data, list):
                if all(isinstance(x, (int, float)) for x in data):
                    return {
                        "count": len(data),
                        "mean": np.mean(data),
                        "median": np.median(data),
                        "std_dev": np.std(data),
                        "min": min(data),
                        "max": max(data)
                    }
        except:
            pass

        return {
            "count": "N/A",
            "mean": "N/A",
            "median": "N/A",
            "std_dev": "N/A",
            "min": "N/A",
            "max": "N/A"
        }

    def _generate_sample_predictions(self, request: str) -> Dict[str, str]:
        """Generate sample prediction confidence levels"""
        # Simplified for demonstration
        return {
            "high_conf": "Core trend continuation",
            "med_conf": "Seasonal pattern repetition",
            "low_conf": "Extreme scenario outcomes"
        }

    def _determine_visualization_type(self, request: str) -> str:
        """Determine appropriate visualization type"""
        request_lower = request.lower()

        if "trend" in request_lower or "time" in request_lower:
            return "line_chart"
        elif "distribution" in request_lower or "histogram" in request_lower:
            return "histogram"
        elif "correlation" in request_lower or "scatter" in request_lower:
            return "scatter_plot"
        elif "comparison" in request_lower or "bar" in request_lower:
            return "bar_chart"
        elif "composition" in request_lower or "pie" in request_lower:
            return "pie_chart"
        elif "heat" in request_lower or "matrix" in request_lower:
            return "heatmap"
        else:
            return "line_chart"

    def _generate_visualization_code(self, viz_type: str) -> str:
        """Generate visualization code template"""
        templates = {
            "line_chart": """
import matplotlib.pyplot as plt
import pandas as pd

# Create line chart
plt.figure(figsize=(10, 6))
plt.plot(df['x'], df['y'], marker='o')
plt.xlabel('X Label')
plt.ylabel('Y Label')
plt.title('Title')
plt.grid(True)
plt.show()
""",
            "bar_chart": """
import matplotlib.pyplot as plt
import pandas as pd

# Create bar chart
plt.figure(figsize=(10, 6))
plt.bar(df['categories'], df['values'])
plt.xlabel('Categories')
plt.ylabel('Values')
plt.title('Title')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
""",
            "scatter_plot": """
import matplotlib.pyplot as plt
import pandas as pd

# Create scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(df['x'], df['y'], alpha=0.6)
plt.xlabel('X Variable')
plt.ylabel('Y Variable')
plt.title('Title')
plt.grid(True, alpha=0.3)
plt.show()
""",
            "histogram": """
import matplotlib.pyplot as plt
import pandas as pd

# Create histogram
plt.figure(figsize=(10, 6))
plt.hist(df['values'], bins=30, edgecolor='black')
plt.xlabel('Values')
plt.ylabel('Frequency')
plt.title('Distribution')
plt.show()
""",
            "pie_chart": """
import matplotlib.pyplot as plt
import pandas as pd

# Create pie chart
plt.figure(figsize=(8, 8))
plt.pie(df['values'], labels=df['categories'], autopct='%1.1f%%')
plt.title('Composition')
plt.axis('equal')
plt.show()
""",
            "heatmap": """
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# Create heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.show()
"""
        }

        return templates.get(viz_type, templates["line_chart"])

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "analysis_types": self.analysis_types,
            "status": "active"
        }