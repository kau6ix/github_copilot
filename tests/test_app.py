"""Tests for the activities API endpoints"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    """Reset activities state before each test"""
    # Store the original state
    original_participants = {}
    for activity_name, activity_data in activities.items():
        original_participants[activity_name] = activity_data["participants"].copy()
    
    yield
    
    # Restore the original state
    for activity_name, activity_data in activities.items():
        activity_data["participants"] = original_participants[activity_name].copy()


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_have_initial_participants(self, client):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have at least 2 participants
        assert len(data["Chess Club"]["participants"]) >= 1


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check new count
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        
        assert new_count == initial_count + 1
        assert email in response.json()[activity]["participants"]
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_fails(self, client):
        """Test that signing up twice for the same activity fails"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multiactivity@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregister from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Check new count
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        
        assert new_count == initial_count - 1
        assert email not in response.json()[activity]["participants"]
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered_fails(self, client):
        """Test unregister for someone not registered fails"""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_then_signup_again(self, client):
        """Test that a student can unregister and sign up again"""
        email = "testuser@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up again
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
