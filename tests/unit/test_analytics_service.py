"""
tests/unit/test_analytics_service_refactored.py
-------------------------------------------------
Tests for refactored AnalyticsService with status-aware scoring
"""

import pytest
from datetime import datetime, timedelta
from services.analytics_service import AnalyticsService
from services.deal_service import DealService

@pytest.mark.unit
class TestDealServiceStatusDetection:
    """Test new status detection methods in DealService"""
    @pytest.mark.unit
    def test_detect_status_won_by_timestamp(self, test_repositories):
        """Test detecting WON deal by change_to_won_time column"""
        deal_service = DealService(test_repositories)
        
        deal = {
            'Id': '1',
            'Status': 'در حال پیگیری',  # Even says "in progress"
            'change_to_won_time': (datetime.now() - timedelta(days=5)).isoformat(),  # But has won timestamp
            'ChangeToWonTime': None
        }
        
        status = deal_service.detect_deal_status(deal)
        assert status == 'won', f"Expected 'won', got '{status}'"
    @pytest.mark.unit
    def test_detect_status_lost_by_timestamp(self, test_repositories):
        """Test detecting LOST deal by change_to_loss_time column"""
        deal_service = DealService(test_repositories)
        
        deal = {
            'Id': '2',
            'Status': 'در حال پیگیری',  # Says "in progress"
            'change_to_won_time': None,
            'change_to_loss_time': (datetime.now() - timedelta(days=3)).isoformat(),  # Has loss timestamp
            'ChangeToLossTime': None
        }
        
        status = deal_service.detect_deal_status(deal)
        assert status == 'lost', f"Expected 'lost', got '{status}'"
    @pytest.mark.unit
    def test_detect_status_open_by_text(self, test_repositories):
        """Test detecting OPEN deal by Status text"""
        deal_service = DealService(test_repositories)
        
        deal = {
            'Id': '3',
            'Status': 'در حال پیگیری',
            'change_to_won_time': None,
            'change_to_loss_time': None
        }
        
        status = deal_service.detect_deal_status(deal)
        assert status == 'open', f"Expected 'open', got '{status}'"
    @pytest.mark.unit
    def test_detect_status_unknown(self, test_repositories):
        """Test detecting UNKNOWN status"""
        deal_service = DealService(test_repositories)
        
        deal = {
            'Id': '4',
            'Status': 'unknown_status_xyz',
            'change_to_won_time': None,
            'change_to_loss_time': None
        }
        
        status = deal_service.detect_deal_status(deal)
        assert status == 'unknown', f"Expected 'unknown', got '{status}'"
    @pytest.mark.unit
    def test_get_days_since_last_activity(self, test_repositories, sample_activities_list):
        """Test calculating days since last activity"""
        deal_service = DealService(test_repositories)
        
        # Make first activity 10 days ago
        sample_activities_list[0].registerdate = datetime.now() - timedelta(days=10)
        
        days = deal_service.get_days_since_last_activity(sample_activities_list[:1])
        
        assert days == 10, f"Expected 10 days, got {days}"
    @pytest.mark.unit
    def test_get_days_since_last_activity_no_activities(self, test_repositories):
        """Test with no activities"""
        deal_service = DealService(test_repositories)
        
        days = deal_service.get_days_since_last_activity([])
        
        assert days == 999, f"Expected 999 (no activities), got {days}"

@pytest.mark.unit
class TestHealthScoreScoringWonDeal:
    """Test health score calculation for WON deals"""
    @pytest.mark.unit
    def test_won_deal_high_score(self, test_repositories, sample_deal, sample_activities_list):
        """Test that WON deals get high score (85+)"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup won deal
        deal_dict = sample_deal.to_dict()
        deal_dict['change_to_won_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        deal_dict['Status'] = 'بسته شده'
        
        # Add recent activity for followup
        recent_activity = sample_activities_list[0]
        recent_activity.registerdate = datetime.now() - timedelta(days=2)
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(deal_dict, [recent_activity], sentiment_summary)
        
        assert score >= 85, f"WON deal should score >= 85, got {score}"
        assert score <= 100, f"WON deal should not exceed 100, got {score}"
    @pytest.mark.unit
    def test_won_deal_no_followup_penalty(self, test_repositories, sample_deal):
        """Test that WON deals without followup get penalty"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup won deal
        deal_dict = sample_deal.to_dict()
        deal_dict['change_to_won_time'] = (datetime.now() - timedelta(days=60)).isoformat()
        deal_dict['Status'] = 'بسته شده'
        
        # No recent activities (no followup)
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(deal_dict, [], sentiment_summary)
        
        assert 80 <= score <= 90, f"WON deal without followup should be 80-90, got {score}"
    @pytest.mark.unit
    def test_won_deal_differs_from_lost_deal(self, test_repositories, sample_deal):
        """Test that WON deal scores are MUCH higher than LOST deal"""
        analytics_service = AnalyticsService(test_repositories)
        
        deal_dict = sample_deal.to_dict()
        sentiment_summary = {'sentiment_available': False}
        
        # Won deal
        deal_dict['change_to_won_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        deal_dict['change_to_loss_time'] = None
        deal_dict['Status'] = 'بسته شده'
        won_score = analytics_service._calculate_health_score(deal_dict, [], sentiment_summary)
        
        # Lost deal
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        deal_dict['Status'] = 'لغو شده'
        lost_score = analytics_service._calculate_health_score(deal_dict, [], sentiment_summary)
        
        print(f"\nWON score: {won_score}, LOST score: {lost_score}")
        assert won_score > lost_score + 30, f"WON ({won_score}) should be much higher than LOST ({lost_score})"

@pytest.mark.unit
class TestHealthScoreScoringLostDeal:
    """Test health score calculation for LOST deals"""
    @pytest.mark.unit
    def test_lost_deal_low_score(self, test_repositories, sample_deal):
        """Test that LOST deals get low score (~20)"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup lost deal
        deal_dict = sample_deal.to_dict()
        deal_dict['change_to_loss_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        deal_dict['Status'] = 'لغو شده'
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(deal_dict, [], sentiment_summary)
        
        assert score <= 40, f"LOST deal should score <= 40, got {score}"
    
@pytest.mark.unit
class TestHealthScoreScoringOpenDeal:
    """Test health score calculation for OPEN deals"""
    @pytest.mark.unit
    def test_open_deal_recent_activity_bonus(self, test_repositories, sample_deal, sample_activities_list):
        """Test that OPEN deals with recent activity get bonus"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        # Recent activity (< 7 days)
        recent_activity = sample_activities_list[0]
        recent_activity.registerdate = datetime.now() - timedelta(days=3)
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(deal_dict, [recent_activity], sentiment_summary)
        
        assert score >= 60, f"OPEN deal with recent activity should score >= 60, got {score}"
    
    @pytest.mark.unit
    def test_open_deal_critical_inactivity_penalty(self, test_repositories, sample_deal, sample_activities_list):
        """Test that OPEN deals with critical inactivity get heavy penalty"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        # Critical inactivity (75 days)
        old_activity = sample_activities_list[0]
        old_activity.registerdate = datetime.now() - timedelta(days=75)
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(deal_dict, [old_activity], sentiment_summary)
        
        assert score <= 20, f"OPEN deal with critical inactivity should score <= 20, got {score}"
    @pytest.mark.unit
    def test_open_deal_no_activities(self, test_repositories, sample_deal):
        """Test that OPEN deals with no activities get low score"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(deal_dict, [], sentiment_summary)
        
        assert score <= 30, f"OPEN deal with no activities should score <= 30, got {score}"
    @pytest.mark.unit
    def test_open_deal_high_activity_frequency(self, test_repositories, sample_deal, sample_activities_list):
        """Test that OPEN deals with many activities get bonus"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        # Recent activities
        for activity in sample_activities_list[:10]:
            activity.registerdate = datetime.now() - timedelta(days=2)
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(deal_dict, sample_activities_list[:10], sentiment_summary)
        
        assert score >= 70, f"OPEN deal with many recent activities should score >= 70, got {score}"
    @pytest.mark.unit
    def test_open_deal_positive_sentiment_bonus(self, test_repositories, sample_deal, sample_activities_list):
        """Test that positive sentiment gives bonus for OPEN deals"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        recent_activity = sample_activities_list[0]
        recent_activity.registerdate = datetime.now() - timedelta(days=3)
        
        # Positive sentiment
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'مثبت',
            'average_confidence': 0.85
        }
        
        score = analytics_service._calculate_health_score(deal_dict, [recent_activity], sentiment_summary)
        
        assert score >= 70, f"OPEN deal with positive sentiment should score >= 70, got {score}"
    @pytest.mark.unit
    def test_open_deal_negative_sentiment_penalty(self, test_repositories, sample_deal, sample_activities_list):
        """Test that negative sentiment gives penalty for OPEN deals"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        recent_activity = sample_activities_list[0]
        recent_activity.registerdate = datetime.now() - timedelta(days=3)
        
        # Negative sentiment
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'منفی',
            'average_confidence': 0.85
        }
        
        score = analytics_service._calculate_health_score(deal_dict, [recent_activity], sentiment_summary)
        
        assert score < 50, f"OPEN deal with negative sentiment should score < 50, got {score}"
@pytest.mark.unit
class TestHealthScoreActivityImpact:
    """Test how activities impact health scores across all deal states"""
    
    def test_activity_recency_affects_all_states(self, test_repositories, sample_deal, sample_activities_list):
        """Test recent vs stale activities impact scores for OPEN/WON/LOST deals"""
        analytics_service = AnalyticsService(test_repositories)
        
        deal_dict = sample_deal.to_dict()
        sentiment_summary = {'sentiment_available': False}
        
        # Recent activity
        recent = sample_activities_list[0]
        recent.registerdate = datetime.now() - timedelta(days=2)
        
        # Stale activity
        stale = sample_activities_list[1]  
        stale.registerdate = datetime.now() - timedelta(days=30)
        
        # =========================================
        # Test OPEN deal
        # =========================================
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        score_open_recent = analytics_service._calculate_health_score(deal_dict, [recent], sentiment_summary)
        score_open_stale = analytics_service._calculate_health_score(deal_dict, [stale], sentiment_summary)
        assert score_open_recent > score_open_stale, "Open: Recent should score higher"
        
        # =========================================
        # Test WON deal - FIXED!
        # =========================================
        # WON deals care about POST-CLOSE follow-up, not pre-close activity recency
        deal_dict['Status'] = 'بسته شده'
        won_time = datetime.now() - timedelta(days=10)  # ← Deal closed 10 days ago
        deal_dict['change_to_won_time'] = won_time.isoformat()
        
        # Post-close follow-up activity (recent)
        followup_recent = sample_activities_list[0]
        followup_recent.registerdate = won_time + timedelta(days=2)  # ← 2 days AFTER close
        
        # No follow-up (empty activities)
        score_won_followup = analytics_service._calculate_health_score(deal_dict, [followup_recent], sentiment_summary)
        score_won_no_followup = analytics_service._calculate_health_score(deal_dict, [], sentiment_summary)
        assert score_won_followup > score_won_no_followup, "Won: Follow-up scores higher than no follow-up"
        
        # =========================================
        # Test LOST deal
        # =========================================
        deal_dict['Status'] = 'لغو شده'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = datetime.now().isoformat()
        score_lost_effort = analytics_service._calculate_health_score(deal_dict, sample_activities_list[:8], sentiment_summary)
        score_lost_no_effort = analytics_service._calculate_health_score(deal_dict, [], sentiment_summary)
        assert score_lost_effort > score_lost_no_effort, "Lost: Effort should improve score"
@pytest.mark.unit
class TestRiskIndicatorsWonDeal:
    """Test risk detection for WON deals"""
    @pytest.mark.unit
    def test_won_deal_minimal_risks(self, test_repositories, sample_deal, sample_activities_list):
        """Test that WON deals have minimal risks"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup won deal with followup
        deal_dict = sample_deal.to_dict()
        deal_dict['change_to_won_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        deal_dict['Status'] = 'بسته شده'
        
        recent_activity = sample_activities_list[0]
        recent_activity.registerdate = datetime.now() - timedelta(days=2)
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [recent_activity], health_score=90)
        
        assert len(risks) == 0, f"WON deal with followup should have no risks, got {len(risks)}"
    @pytest.mark.unit
    def test_won_deal_no_followup_risk(self, test_repositories, sample_deal):
        """Test that WON deals without followup get risk"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup won deal without followup
        deal_dict = sample_deal.to_dict()
        deal_dict['change_to_won_time'] = (datetime.now() - timedelta(days=60)).isoformat()
        deal_dict['Status'] = 'بسته شده'
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [], health_score=80)
        
        assert len(risks) >= 1, f"WON deal without followup should have at least 1 risk, got {len(risks)}"

        assert risks[0]['type'] in ['no_followup_after_close', 'critical_inactivity', 'high_inactivity']

@pytest.mark.unit
class TestRiskIndicatorsLostDeal:
    """Test risk detection for LOST deals"""
    @pytest.mark.unit
    def test_lost_deal_has_loss_risk(self, test_repositories, sample_deal):
        """Test that LOST deals are flagged"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup lost deal
        deal_dict = sample_deal.to_dict()
        deal_dict['change_to_loss_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        deal_dict['Status'] = 'لغو شده'
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [], health_score=20)
        
        assert len(risks) >= 1, f"LOST deal should have risks"
        assert risks[0]['type'] in ['deal_lost', 'low_health_score', 'lost_deal']
    @pytest.mark.unit
    def test_lost_deal_insufficient_effort_risk(self, test_repositories, sample_deal):
        """Test that LOST deals with low effort get warning"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup lost deal with 1 activity
        deal_dict = sample_deal.to_dict()
        deal_dict['change_to_loss_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        deal_dict['Status'] = 'لغو شده'
        
        from models.deal_model import DealActivity
        minimal_activity = DealActivity(id='1', dealid='deal1')
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [minimal_activity], health_score=20)
        
        assert any(r['type'] in ['insufficient_effort', 'no_activity', 'low_health_score'] for r in risks)



@pytest.mark.unit
class TestRiskIndicatorsOpenDeal:
    """Test risk detection for OPEN deals"""
    @pytest.mark.unit
    def test_open_deal_no_activity_critical_risk(self, test_repositories, sample_deal):
        """Test that OPEN deals with no activity get critical risk"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [], health_score=20)
        
        assert any(r['type'] == 'no_activity' and r['severity'] == 'critical' for r in risks), \
            "OPEN deal with no activity should have critical 'no_activity' risk"
    @pytest.mark.unit
    def test_open_deal_critical_inactivity_risk(self, test_repositories, sample_deal, sample_activities_list):
        """Test that OPEN deals with 60+ days inactivity get critical risk"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        # 70 days old activity
        old_activity = sample_activities_list[0]
        old_activity.registerdate = datetime.now() - timedelta(days=70)
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [old_activity], health_score=15)
        
        critical_inactivity = [r for r in risks if r['type'] == 'critical_inactivity']
        assert len(critical_inactivity) > 0, "Should have 'critical_inactivity' risk"
        assert critical_inactivity[0]['severity'] == 'critical'
    @pytest.mark.unit
    def test_open_deal_high_inactivity_risk(self, test_repositories, sample_deal, sample_activities_list):
        """Test that OPEN deals with 30-60 days inactivity get high risk"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        
        # 40 days old activity
        old_activity = sample_activities_list[0]
        old_activity.registerdate = datetime.now() - timedelta(days=40)
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [old_activity], health_score=30)
        
        high_inactivity = [r for r in risks if r['type'] == 'high_inactivity']
        assert len(high_inactivity) > 0, "Should have 'high_inactivity' risk"
        assert high_inactivity[0]['severity'] == 'high'
    @pytest.mark.unit
    def test_open_deal_very_old_deal_risk(self, test_repositories, sample_deal):
        """Test that OPEN deals > 180 days old get risk"""
        analytics_service = AnalyticsService(test_repositories)
        
        # Setup open deal that's very old
        deal_dict = sample_deal.to_dict()
        deal_dict['Status'] = 'در حال پیگیری'
        deal_dict['change_to_won_time'] = None
        deal_dict['change_to_loss_time'] = None
        deal_dict['RegisterTime'] = (datetime.now() - timedelta(days=200)).isoformat()
        
        risks = analytics_service._identify_risk_indicators(deal_dict, [], health_score=30)
        
        assert any(r['type'] in ['very_old_deal', 'deal_aging'] for r in risks)


@pytest.mark.unit
class TestComprehensiveScenarios:
    """Test complete real-world scenarios"""
    @pytest.mark.unit
    def test_scenario_won_deal_from_output(self, test_repositories, sample_deal, sample_activities_list):
        """
        Test the exact scenario that was failing: WON deal should NOT score same as LOST
        """
        analytics_service = AnalyticsService(test_repositories)
        
        # Create WON deal scenario
        won_deal = sample_deal.to_dict()
        won_deal['change_to_won_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        won_deal['change_to_loss_time'] = None
        won_deal['Status'] = 'بسته شده'
        
        # Add some followup activity
        followup = sample_activities_list[0]
        followup.registerdate = datetime.now() - timedelta(days=2)
        
        sentiment_summary = {'sentiment_available': False}
        
        # Analyze WON deal
        won_result = {
            'health_score': analytics_service._calculate_health_score(won_deal, [followup], sentiment_summary),
            'risks': analytics_service._identify_risk_indicators(won_deal, [followup], health_score=85)
        }
        
        # Create LOST deal scenario
        lost_deal = sample_deal.to_dict()
        lost_deal['change_to_won_time'] = None
        lost_deal['change_to_loss_time'] = (datetime.now() - timedelta(days=5)).isoformat()
        lost_deal['Status'] = 'لغو شده'
        
        # Same inactivity as in the bug report (62 days)
        old_activity = sample_activities_list[0]
        old_activity.registerdate = datetime.now() - timedelta(days=62)
        
        lost_result = {
            'health_score': analytics_service._calculate_health_score(lost_deal, [old_activity], sentiment_summary),
            'risks': analytics_service._identify_risk_indicators(lost_deal, [old_activity], health_score=20)
        }
        
        print(f"\n{'='*70}")
        print("TEST: Won vs Lost Deal Scenario")
        print(f"{'='*70}")
        print(f"WON Deal Score: {won_result['health_score']}/100")
        print(f"WON Deal Risks: {len(won_result['risks'])} risks")
        print(f"\nLOST Deal Score: {lost_result['health_score']}/100")
        print(f"LOST Deal Risks: {len(lost_result['risks'])} risks")
        print(f"{'='*70}")
        
        # ASSERTIONS
        assert won_result['health_score'] > 70, f"WON deal should score > 70, got {won_result['health_score']}"
        assert lost_result['health_score'] < 50, f"LOST deal should score < 50, got {lost_result['health_score']}"
        assert won_result['health_score'] > lost_result['health_score'] + 30, \
            f"WON ({won_result['health_score']}) should be much higher than LOST ({lost_result['health_score']})"