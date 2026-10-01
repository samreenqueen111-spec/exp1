import os
import sys
import unittest
import tempfile

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils.database import init_db, seed_demo_data, get_db_connection
from utils.prediction import predict_distress_indicator

class CareBridgeComprehensiveTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['DATABASE_PATH'] = self.db_path
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Initialize DB and seed demo data
        with app.app_context():
            init_db()
            seed_demo_data()

    def tearDown(self):
        os.close(self.db_fd)
        if 'DATABASE_PATH' in os.environ:
            del os.environ['DATABASE_PATH']
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    # 1. PUBLIC PAGES
    def test_landing_page(self):
        """Test public landing page buttons & content."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CareBridge', response.data)
        self.assertIn(b'Start Confidential Check-in', response.data)

    def test_about_page(self):
        """Test About system methodology page."""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About CareBridge', response.data)
        self.assertIn(b'Decision Tree Classifier', response.data)

    def test_privacy_page(self):
        """Test Privacy policy page."""
        response = self.client.get('/privacy')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Privacy & Data Safety Policy', response.data)

    # 2. AUTHENTICATION & REGISTRATION
    def test_survivor_registration(self):
        """Test survivor account creation form."""
        response = self.client.post('/register', data={
            'name': 'New Hope',
            'email': 'newhope@carebridge.org',
            'age_group': '25-34',
            'gender': 'Female',
            'contact_pref': 'App Notification',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, New Hope', response.data)

    def test_login_survivor(self):
        """Test login button & authentication for Survivor."""
        response = self.client.post('/login', data={
            'identifier': 'survivor1@carebridge.org',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, User Alpha (DEMO)', response.data)

    def test_login_counselor(self):
        """Test login button for Counselor role."""
        response = self.client.post('/login', data={
            'identifier': 'counselor@carebridge.org',
            'password': 'counselor123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Counselor Portal', response.data)

    def test_login_admin(self):
        """Test login button for Admin role."""
        response = self.client.post('/login', data={
            'identifier': 'admin@carebridge.org',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Administrator Control Panel', response.data)

    def test_logout(self):
        """Test log out button functionality."""
        self.client.post('/login', data={'identifier': 'survivor1@carebridge.org', 'password': 'password123'})
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been safely logged out.', response.data)

    # 3. SURVIVOR FEATURES
    def test_survivor_checkin_submission(self):
        """Test Daily Check-in form sliders submission & AI prediction result."""
        self.client.post('/login', data={'identifier': 'survivor1@carebridge.org', 'password': 'password123'})
        
        response = self.client.post('/survivor/checkin', data={
            'stress_score': 8,
            'sleep_score': 3,
            'concentration_score': 4,
            'social_support_score': 3,
            'distress_frequency': 8
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Check-in Submitted Successfully', response.data)
        self.assertIn(b'Distress Indicator', response.data)

    def test_survivor_trends_api(self):
        """Test Chart.js trend API endpoint for survivors."""
        self.client.post('/login', data={'identifier': 'survivor1@carebridge.org', 'password': 'password123'})
        response = self.client.get('/api/survivor/trends')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('labels', json_data)
        self.assertIn('stress', json_data)

    def test_survivor_history_and_support(self):
        """Test Survivor History table & Support Resources views."""
        self.client.post('/login', data={'identifier': 'survivor1@carebridge.org', 'password': 'password123'})
        
        res_hist = self.client.get('/survivor/history')
        self.assertEqual(res_hist.status_code, 200)
        self.assertIn(b'Your Check-in History', res_hist.data)

        res_supp = self.client.get('/survivor/support')
        self.assertEqual(res_supp.status_code, 200)
        self.assertIn(b'Support Resources & Helplines', res_supp.data)

    # 4. COUNSELOR FEATURES
    def test_counselor_dashboard_and_filters(self):
        """Test Counselor Dashboard and filter buttons."""
        self.client.post('/login', data={'identifier': 'counselor@carebridge.org', 'password': 'counselor123'})
        
        # Test dashboard main view
        res = self.client.get('/counselor/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Counselor Portal', res.data)

        # Test filter check-ins button (e.g. indicator=High)
        res_filter = self.client.get('/counselor/dashboard?indicator=High&days=14')
        self.assertEqual(res_filter.status_code, 200)
        self.assertIn(b'High', res_filter.data)

    def test_counselor_survivor_roster(self):
        """Test Anonymized Survivor Roster page."""
        self.client.post('/login', data={'identifier': 'counselor@carebridge.org', 'password': 'counselor123'})
        res = self.client.get('/counselor/users')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Anonymized Survivor Roster', res.data)
        self.assertIn(b'CB-7842', res.data)

    def test_counselor_alerts_management(self):
        """Test updating Early-Warning Alert status & notes."""
        self.client.post('/login', data={'identifier': 'counselor@carebridge.org', 'password': 'counselor123'})
        
        # Update alert 1 to Resolved
        res = self.client.post('/counselor/alerts', data={
            'alert_id': 1,
            'status': 'Resolved',
            'notes': 'Followed up via supportive call. User reported resting better.'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Alert status updated successfully.', res.data)

    def test_counselor_distribution_api(self):
        """Test Counselor Distress Distribution Doughnut Chart API endpoint."""
        self.client.post('/login', data={'identifier': 'counselor@carebridge.org', 'password': 'counselor123'})
        res = self.client.get('/api/counselor/distress_distribution')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('Low', json_data)
        self.assertIn('High', json_data)

    def test_counselor_live_alerts_api(self):
        """Test Real-time High Distress Alert API polling endpoint."""
        self.client.post('/login', data={'identifier': 'counselor@carebridge.org', 'password': 'counselor123'})
        res = self.client.get('/api/counselor/live_alerts')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('has_high_alert', json_data)
        self.assertIn('pending_alerts_count', json_data)
        self.assertIn('high_distress_count', json_data)
        self.assertIn('recent_alerts', json_data)

    def test_counselor_dismiss_and_review_api(self):
        """Test Dismiss and Review actions on alerts via JSON API."""
        self.client.post('/login', data={'identifier': 'counselor@carebridge.org', 'password': 'counselor123'})
        
        # Test dismiss
        res_dismiss = self.client.post('/api/counselor/dismiss_alert', json={'alert_id': 1})
        self.assertEqual(res_dismiss.status_code, 200)
        self.assertTrue(res_dismiss.get_json().get('success'))

        # Test review
        res_review = self.client.post('/api/counselor/review_alert', json={'alert_id': 1})
        self.assertEqual(res_review.status_code, 200)
        self.assertTrue(res_review.get_json().get('success'))

    # 5. ADMIN FEATURES & BUTTONS
    def test_admin_add_counselor_and_resources(self):
        """Test Admin buttons: Add Counselor, Add Resource, Delete Resource, Retrain Model."""
        self.client.post('/login', data={'identifier': 'admin@carebridge.org', 'password': 'admin123'})

        # 1. Add Counselor button
        res_couns = self.client.post('/admin/counselors/add', data={
            'name': 'Dr. Marcus Vance',
            'email': 'marcus@carebridge.org',
            'badge_id': '104',
            'password': 'counselor123'
        }, follow_redirects=True)
        self.assertEqual(res_couns.status_code, 200)
        self.assertIn(b'Authorized counselor account created for Dr. Marcus Vance.', res_couns.data)

        # 2. Add Resource button
        res_add = self.client.post('/admin/resources/add', data={
            'name': 'Global Relief Desk',
            'description': '24/7 crisis support line for relocated families.',
            'contact': '1-800-DEMO-RELIEF',
            'location': 'Worldwide',
            'category': 'Crisis Center'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b'Support resource &#39;Global Relief Desk&#39; added successfully.', res_add.data)

        # 3. Retrain Model button
        res_train = self.client.post('/admin/model/retrain', follow_redirects=True)
        self.assertEqual(res_train.status_code, 200)
        self.assertIn(b'ML Model successfully retrained on synthetic dataset!', res_train.data)

    # 6. ERROR HANDLERS & SECURITY
    def test_404_error(self):
        """Test custom 404 page handler."""
        res = self.client.get('/nonexistent-page-url')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'Page Not Found', res.data)

    def test_role_authorization_security(self):
        """Test security barrier: Survivor cannot open admin dashboard."""
        self.client.post('/login', data={'identifier': 'survivor1@carebridge.org', 'password': 'password123'})
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Access denied: insufficient permissions.', res.data)

if __name__ == '__main__':
    unittest.main()
