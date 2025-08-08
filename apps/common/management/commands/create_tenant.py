"""
Django management command to create new tenants with proper schema setup.
Usage: python manage.py create_tenant --name "Company Name" --schema "company" --domain "company.localhost"
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import schema_context
from apps.tenants.models import Client, Domain
import re


class Command(BaseCommand):
    help = 'Create a new tenant with schema and domain setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='The name of the tenant company'
        )
        parser.add_argument(
            '--schema',
            type=str,
            required=True,
            help='The database schema name (must be lowercase, alphanumeric)'
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='The domain for the tenant (default: {schema}.localhost)'
        )
        parser.add_argument(
            '--trial-days',
            type=int,
            default=14,
            help='Number of trial days (default: 14)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if tenant exists'
        )

    def handle(self, *args, **options):
        name = options['name']
        schema_name = options['schema']
        domain_name = options.get('domain') or f"{schema_name}.localhost"
        trial_days = options['trial_days']
        force = options['force']

        # Validate schema name
        if not re.match(r'^[a-z][a-z0-9_]*$', schema_name):
            raise CommandError(
                'Schema name must start with a letter and contain only '
                'lowercase letters, numbers, and underscores'
            )

        # Check if tenant already exists
        if Client.objects.filter(schema_name=schema_name).exists():
            if not force:
                raise CommandError(f'Tenant with schema "{schema_name}" already exists')
            else:
                self.stdout.write(
                    self.style.WARNING(f'Tenant "{schema_name}" exists, updating...')
                )

        # Check if domain already exists
        if Domain.objects.filter(domain=domain_name).exists():
            if not force:
                raise CommandError(f'Domain "{domain_name}" already exists')

        try:
            with transaction.atomic():
                # Create or update tenant
                tenant, created = Client.objects.get_or_create(
                    schema_name=schema_name,
                    defaults={
                        'name': name,
                        'on_trial': True,
                    }
                )
                
                if not created and force:
                    tenant.name = name
                    tenant.on_trial = True
                    tenant.save()

                # Create or update domain
                domain, domain_created = Domain.objects.get_or_create(
                    domain=domain_name,
                    defaults={
                        'tenant': tenant,
                        'is_primary': True,
                    }
                )

                if not domain_created and force:
                    domain.tenant = tenant
                    domain.is_primary = True
                    domain.save()

                # Create the schema and run migrations
                self.stdout.write('Creating database schema...')
                tenant.create_schema(check_if_exists=True)
                
                # Run tenant migrations
                self.stdout.write('Running tenant migrations...')
                with schema_context(schema_name):
                    from django.core.management import call_command
                    call_command('migrate_schemas', schema_name=schema_name, verbosity=0)

                # Success message
                action = 'Updated' if not created else 'Created'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action} tenant successfully:\n'
                        f'  Name: {name}\n'
                        f'  Schema: {schema_name}\n'
                        f'  Domain: {domain_name}\n'
                        f'  Trial: {trial_days} days'
                    )
                )

                # Additional setup instructions
                self.stdout.write(
                    self.style.WARNING(
                        f'\nNext steps:\n'
                        f'1. Add "{domain_name}" to your hosts file for local development\n'
                        f'2. Access tenant at: http://{domain_name}:8000\n'
                        f'3. Create tenant admin user if needed'
                    )
                )

        except Exception as e:
            raise CommandError(f'Failed to create tenant: {str(e)}')

    def validate_schema_name(self, schema_name):
        """Validate that the schema name follows PostgreSQL naming conventions."""
        if len(schema_name) > 63:
            raise CommandError('Schema name must be 63 characters or less')
        
        if not schema_name.islower():
            raise CommandError('Schema name must be lowercase')
        
        reserved_names = [
            'public', 'information_schema', 'pg_catalog', 'pg_toast',
            'pg_temp', 'pg_toast_temp', 'template0', 'template1'
        ]
        
        if schema_name in reserved_names:
            raise CommandError(f'Schema name "{schema_name}" is reserved')

        return True
