# Makefile for Multi-Tenant SaaS Boilerplate

# Define Python and environment variables
PYTHON=python3
VENV_DIR=venv
ACTIVATE=$(VENV_DIR)/bin/activate
DATABASE_URL=postgres://user:password@localhost:5432/multi_tenant_saas

# Install dependencies
install: 
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	. $(ACTIVATE) && pip install -r requirements.txt
	@echo "Dependencies installed."

# Set up the database (replace this with your specific database setup process)
setup-db:
	@echo "Setting up the database..."
	# Add database setup commands here (e.g., creating the PostgreSQL DB)
	# Example:
	# createdb $(DATABASE_URL)

# Create superuser
createsuperuser:
	@echo "Creating superuser..."
	. $(ACTIVATE) && python manage.py createsuperuser

# Run migrations for the shared schema and tenants
migrate:
	@echo "Running migrations..."
	. $(ACTIVATE) && python manage.py migrate_schemas --shared

# Run migrations only for a specific tenant
migrate-tenant:
	@echo "Running tenant migrations..."
	. $(ACTIVATE) && python manage.py migrate_schemas

# Run the development server
runserver:
	@echo "Starting the development server..."
	. $(ACTIVATE) && python manage.py runserver

# Run tests
test:
	@echo "Running tests..."
	. $(ACTIVATE) && python manage.py test

# Clear cache (dev helper)
cache-clear:
	@echo "Clearing cache..."
	. $(ACTIVATE) && python - <<'PY'
from django.conf import settings
from django.core.cache import cache
print('Cache backend:', settings.CACHES['default']['BACKEND'])
cache.clear()
print('Cache cleared')
PY

# Clean up pycache files and other temporary files
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__
	rm -rf $(VENV_DIR)

# Show Django migrations status
showmigrations:
	@echo "Showing migrations..."
	. $(ACTIVATE) && python manage.py showmigrations

# Collect static files
collectstatic:
	@echo "Collecting static files..."
	. $(ACTIVATE) && python manage.py collectstatic --noinput

# Check for potential issues
check:
	@echo "Checking for issues..."
	. $(ACTIVATE) && python manage.py check

# Print help
help:
	@echo "Makefile for Multi-Tenant SaaS Boilerplate"
	@echo "Usage:"
	@echo "  make install        Install dependencies and create virtual environment"
	@echo "  make setup-db       Set up the database"
	@echo "  make createsuperuser Create a superuser"
	@echo "  make migrate        Run all migrations for shared and tenant schemas"
	@echo "  make migrate-tenant Run migrations for tenant schemas"
	@echo "  make runserver      Run the development server"
	@echo "  make test           Run tests"
	@echo "  make clean          Clean up temporary files"
	@echo "  make showmigrations Show migrations"
	@echo "  make collectstatic  Collect static files"
	@echo "  make check          Check for potential issues"
	@echo "  make help           Show this help message"

