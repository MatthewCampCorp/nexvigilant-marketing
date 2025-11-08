"""
Unit tests for Predictive Insights Agent.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from predictive_insights.main import PredictiveInsightsAgent, Prediction, PredictionBatch


class TestPredictiveInsightsAgent:
    """Test suite for Predictive Insights Agent."""

    @pytest.fixture
    def agent(self):
        """Create Predictive Insights Agent instance."""
        try:
            agent = PredictiveInsightsAgent()
            return agent
        except ValueError:
            pytest.skip("GOOGLE_CLOUD_PROJECT not set")

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.project_id is not None
        assert agent.location == "us-central1"

    def test_predict_lead_score(self, agent):
        """Test lead scoring prediction."""
        test_leads = [
            {'lead_id': 'L001', 'company_size': 'large', 'engagement_score': 0.85},
            {'lead_id': 'L002', 'company_size': 'small', 'engagement_score': 0.45}
        ]

        result = agent.predict_lead_score(test_leads)

        assert result['success'] is True
        assert result['prediction_type'] == 'lead_scoring'
        assert 'predictions' in result
        assert len(result['predictions']) == 2
        assert all('lead_id' in pred for pred in result['predictions'])
        assert all('score' in pred for pred in result['predictions'])
        assert all('conversion_probability' in pred for pred in result['predictions'])

    def test_predict_churn(self, agent):
        """Test churn prediction."""
        test_customers = [
            {'customer_id': 'C001', 'tenure_months': 36},
            {'customer_id': 'C002', 'tenure_months': 6}
        ]

        result = agent.predict_churn(test_customers)

        assert result['success'] is True
        assert result['prediction_type'] == 'churn_prediction'
        assert len(result['predictions']) == 2
        assert all('customer_id' in pred for pred in result['predictions'])
        assert all('churn_probability' in pred for pred in result['predictions'])
        assert all('risk_level' in pred for pred in result['predictions'])

    def test_forecast_clv(self, agent):
        """Test CLV forecasting."""
        test_customers = [
            {'customer_id': 'C001', 'current_spend': 10000},
            {'customer_id': 'C002', 'current_spend': 2000}
        ]

        result = agent.forecast_clv(test_customers, time_horizon_months=12)

        assert result['success'] is True
        assert result['prediction_type'] == 'clv_forecast'
        assert len(result['predictions']) == 2
        assert all('customer_id' in pred for pred in result['predictions'])
        assert all('predicted_clv' in pred for pred in result['predictions'])
        assert all('value_segment' in pred for pred in result['predictions'])

    def test_execute_lead_scoring(self, agent):
        """Test execute method with lead scoring."""
        leads = [{'lead_id': 'test_lead'}]
        result = agent.execute(prediction_type='lead_scoring', leads=leads)

        assert result['success'] is True
        assert result['prediction_type'] == 'lead_scoring'

    def test_execute_churn_prediction(self, agent):
        """Test execute method with churn prediction."""
        customers = [{'customer_id': 'test_customer'}]
        result = agent.execute(prediction_type='churn', customers=customers)

        assert result['success'] is True
        assert result['prediction_type'] == 'churn_prediction'

    def test_execute_clv_forecast(self, agent):
        """Test execute method with CLV forecasting."""
        customers = [{'customer_id': 'test_customer'}]
        result = agent.execute(prediction_type='clv', customers=customers)

        assert result['success'] is True
        assert result['prediction_type'] == 'clv_forecast'

    def test_get_lead_recommendation_high_score(self, agent):
        """Test lead recommendation for high score."""
        recommendation = agent._get_lead_recommendation(0.85)
        assert 'High priority' in recommendation or 'immediate' in recommendation.lower()

    def test_get_lead_recommendation_medium_score(self, agent):
        """Test lead recommendation for medium score."""
        recommendation = agent._get_lead_recommendation(0.65)
        assert 'Medium priority' in recommendation or 'nurture' in recommendation.lower()

    def test_get_lead_recommendation_low_score(self, agent):
        """Test lead recommendation for low score."""
        recommendation = agent._get_lead_recommendation(0.35)
        assert 'Low priority' in recommendation or 'automated' in recommendation.lower()

    def test_get_churn_risk_level(self, agent):
        """Test churn risk level classification."""
        assert agent._get_churn_risk_level(0.8) == "HIGH"
        assert agent._get_churn_risk_level(0.5) == "MEDIUM"
        assert agent._get_churn_risk_level(0.2) == "LOW"

    def test_get_value_segment(self, agent):
        """Test customer value segmentation."""
        assert agent._get_value_segment(15000) == "PREMIUM"
        assert agent._get_value_segment(7000) == "HIGH_VALUE"
        assert agent._get_value_segment(3000) == "MEDIUM_VALUE"
        assert agent._get_value_segment(1000) == "LOW_VALUE"

    def test_stub_lead_score_response(self, agent):
        """Test stub lead score response."""
        leads = [{'lead_id': 'L001'}, {'lead_id': 'L002'}]
        result = agent._stub_lead_score_response(leads)

        assert result['success'] is True
        assert len(result['predictions']) == 2
        assert 'model_metrics' in result

    def test_stub_churn_response(self, agent):
        """Test stub churn response."""
        customers = [{'customer_id': 'C001'}]
        result = agent._stub_churn_response(customers)

        assert result['success'] is True
        assert len(result['predictions']) == 1

    def test_stub_clv_response(self, agent):
        """Test stub CLV response."""
        customers = [{'customer_id': 'C001'}]
        result = agent._stub_clv_response(customers, 12)

        assert result['success'] is True
        assert result['metadata']['time_horizon_months'] == 12


class TestPrediction:
    """Test suite for Prediction dataclass."""

    def test_prediction_creation(self):
        """Test creating Prediction instance."""
        prediction = Prediction(
            entity_id='L001',
            score=0.85,
            probability=0.82,
            confidence=0.9,
            features_used={'engagement': 0.8},
            recommendations=['Follow up immediately']
        )

        assert prediction.entity_id == 'L001'
        assert prediction.score == 0.85
        assert prediction.probability == 0.82
        assert prediction.confidence == 0.9
        assert len(prediction.recommendations) == 1


class TestPredictionBatch:
    """Test suite for PredictionBatch dataclass."""

    def test_prediction_batch_creation(self):
        """Test creating PredictionBatch instance."""
        predictions = [
            Prediction(entity_id='L001', score=0.85),
            Prediction(entity_id='L002', score=0.65)
        ]

        batch = PredictionBatch(
            prediction_type='lead_scoring',
            predictions=predictions,
            model_metadata={'model_version': '1.0'},
            performance_metrics={'accuracy': 0.84},
            timestamp='2025-01-08T00:00:00'
        )

        assert batch.prediction_type == 'lead_scoring'
        assert len(batch.predictions) == 2
        assert batch.model_metadata['model_version'] == '1.0'
        assert batch.performance_metrics['accuracy'] == 0.84


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
