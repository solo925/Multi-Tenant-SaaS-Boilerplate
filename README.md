# Multi-Tenant SaaS Boilerplate

## Overview

This is a Django-based multi-tenant SaaS boilerplate designed to provide a scalable backend solution for SaaS applications. The boilerplate is built with best practices for multi-tenancy, allowing each tenant to have its own isolated schema within the same database. The app includes features like user management, admin dashboard, public schema handling, tenant onboarding, and more.

### Key Features:
- **Multi-Tenant Architecture**: Support for multiple tenants, each with its own isolated schema.
- **Custom User Management**: Extends Django's `AbstractBaseUser` for custom user models with email authentication.
- **Admin Dashboard**: Fully functional admin dashboard with CRUD operations for managing tenants and users.
- **Shared Database**: All tenant data is stored in a single database, with separate schemas for each tenant.
- **Onboarding and Tenant Creation**: Automated onboarding for new tenants with schema creation.

---

## Table of Contents

- [Installation](#installation)
- [Features](#features)
- [Configuration](#configuration)
- [Usage](#usage)
- [Running Migrations](#running-migrations)
- [Admin Dashboard](#admin-dashboard)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/solo925/Multi-Tenant-SaaS-Boilerplate
   cd multi-tenant-saas
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Database**:
   Create a PostgreSQL database and configure your `.env` or `settings.py` to point to it.

   Example configuration in `.env`:
   ```env
   DATABASE_URL=postgres://user:password@localhost:5432/multi_tenant_saas
   ```

---

## Features

### Multi-Tenant Support

- **Tenant Isolation**: Each tenant has a separate schema within the same database.
- **Shared Database**: Public models (like user management) are stored in the `public` schema, while tenant-specific data is in each tenant’s own schema.
- **Tenant Creation**: New tenants are onboarded with automatic schema creation.

### Custom User Model

- **Email Authentication**: The custom user model uses email as the unique identifier instead of the default username.
- **Permissions**: Each user has roles (e.g., admin, staff) and permissions through Django's `Groups` and `Permissions` system.
- **Extensibility**: You can easily extend the user model to include additional fields.

### Admin Dashboard

- **Tenant Management**: Admins can manage tenant data and onboard new tenants.
- **User Management**: Admins can manage user roles, permissions, and groups through the dashboard.
- **CRUD Operations**: Full Create, Read, Update, Delete functionality for managing tenants and users.

### Public Schema

- The public schema stores shared data such as authentication models and user permissions.
  
### Migrations

- Migrations are handled across both public and tenant schemas, ensuring each tenant’s schema is kept in sync with your codebase.

---

## Configuration

1. **Database Configuration**: Set up your database in `.env` or directly in `settings.py`.
   
   Example:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

2. **Tenant Configuration**: In your settings, specify how tenants are handled. Use `django-tenants` for multi-tenant support.

---

## Usage

### Starting the Server

To start the development server, run:
```bash
python manage.py runserver
```

### Creating a Superuser

To create an admin superuser for your application, run:
```bash
python manage.py createsuperuser
```

### Onboarding New Tenants

To add a new tenant, run the following command:
```bash
python manage.py create_tenant --name "tenant_name" --schema "tenant_schema"
```

This will create a new tenant with the specified schema and a public user set up.

### Running Migrations

For regular migrations (both public and tenant schemas):
```bash
python manage.py migrate_schemas --shared
```

This command ensures that migrations are applied across all tenant schemas as well as the public schema.

---

## Admin Dashboard

Access the admin dashboard at:

```
http://localhost:8000/admin
```

Log in with the superuser credentials and use the admin panel to manage:

- **Users**: Add, edit, and delete users.
- **Groups and Permissions**: Assign users to different groups and manage their permissions.
- **Tenants**: View tenant data, onboard new tenants, and delete tenants.

---

## Troubleshooting

If you encounter any issues, try the following:

### `ProgrammingError: relation "users_user" does not exist`
- Ensure that migrations have been applied correctly. Try running:
  ```bash
  python manage.py migrate_schemas --shared
  ```

### `Tenant Schema Not Found`
- Check that the schema for the tenant was created successfully during onboarding. Ensure the correct database URL and schema name are set.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

