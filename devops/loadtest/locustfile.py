from locust import HttpUser, task, between
import random
import string


class AnonymousUser(HttpUser):
    """Simulates anonymous users browsing public pages"""
    wait_time = between(1, 3)
    weight = 3

    @task(3)
    def index_page(self):
        self.client.get("/")

    @task(2)
    def login_page(self):
        self.client.get("/accounts/login/")

    @task(1)
    def register_page(self):
        self.client.get("/accounts/register/")

    @task(1)
    def billing_plans(self):
        self.client.get("/billing/plans/")


class AuthenticatedUser(HttpUser):
    """Simulates logged-in users using the dashboard"""
    wait_time = between(2, 5)
    weight = 2

    def on_start(self):
        """Login before starting tasks"""
        # Get login page to get CSRF token
        response = self.client.get("/accounts/login/")
        if response.status_code == 200:
            # Extract CSRF token (simplified - in real scenario you'd parse HTML)
            # For load testing, we'll skip CSRF validation or use a test user
            pass

    @task(5)
    def dashboard(self):
        """Most common action - viewing dashboard"""
        self.client.get("/")

    @task(3)
    def analytics(self):
        """View analytics page"""
        self.client.get("/analytics/")

    @task(2)
    def tenant_list(self):
        """View tenant list"""
        self.client.get("/tenants/")

    @task(1)
    def create_project(self):
        """Attempt to create a project"""
        self.client.get("/create-project/")

    @task(1)
    def export_report(self):
        """Download export report"""
        self.client.get("/export-report/")

    @task(1)
    def system_settings(self):
        """View system settings"""
        self.client.get("/settings/")


class AdminUser(HttpUser):
    """Simulates admin users performing management tasks"""
    wait_time = between(3, 8)
    weight = 1

    @task(3)
    def dashboard(self):
        self.client.get("/")

    @task(2)
    def tenant_management(self):
        """Heavy tenant management operations"""
        # List tenants
        self.client.get("/tenants/")
        
        # View a random tenant detail (simulate clicking on tenant)
        tenant_id = random.randint(1, 10)
        self.client.get(f"/tenants/{tenant_id}/")

    @task(2)
    def analytics_deep_dive(self):
        """Heavy analytics usage"""
        self.client.get("/analytics/")

    @task(1)
    def system_config(self):
        """System administration tasks"""
        self.client.get("/settings/")

    @task(1)
    def billing_overview(self):
        """Check billing and subscriptions"""
        self.client.get("/billing/plans/")


class ApiUser(HttpUser):
    """Simulates API usage (if you have API endpoints)"""
    wait_time = between(0.5, 2)
    weight = 1

    @task
    def health_check(self):
        """Basic health check endpoint"""
        # Assuming you might add a health endpoint
        self.client.get("/health/", name="/health/ (API)")

    @task
    def dashboard_data(self):
        """Simulate AJAX calls for dashboard data"""
        # This would be actual API endpoints in a real app
        self.client.get("/", name="Dashboard AJAX")


# Custom load test scenarios
class BurstTraffic(HttpUser):
    """Simulates sudden traffic spikes"""
    wait_time = between(0.1, 0.5)  # Very short wait times
    weight = 0  # Disabled by default, enable manually

    @task
    def rapid_requests(self):
        endpoints = ["/", "/accounts/login/", "/analytics/", "/tenants/"]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)


class SlowUser(HttpUser):
    """Simulates users with slow connections or who read pages thoroughly"""
    wait_time = between(10, 30)  # Long pauses between requests
    weight = 1

    @task
    def slow_browsing(self):
        # Simulate user reading content thoroughly
        self.client.get("/")
        
    @task
    def deep_analytics_study(self):
        # User spending time analyzing data
        self.client.get("/analytics/")
