# 🚀 Multi-Tenant SaaS Boilerplate

## Overview

This is a **production-ready**, Django-based **Multi-Tenant SaaS Boilerplate** designed for developers building scalable, tenant-aware SaaS applications. Each tenant is isolated using **PostgreSQL schemas**, allowing separation of data with shared logic and infrastructure.

Built with a **modular, Google-level backend architecture**, it includes tenant onboarding, isolated schemas, shared public schema, custom user authentication, an admin dashboard, and extensibility hooks for billing, plans, and more.

---

## 🔑 Main Features

- ✅ **True Multi-Tenant Architecture**  
  Isolated PostgreSQL schemas for each tenant, with automatic schema creation and routing.

- 👥 **Custom User Model with Email Login**  
  Email-based authentication with extendable fields, role-based permissions, and admin/staff logic.

- 🧩 **Admin Dashboard**  
  Django admin is enhanced for multi-tenant visibility, user and group management, and CRUD operations.

- 🌐 **Public Schema Management**  
  Common models like users, auth, and plans reside in the `public` schema, separated from tenant-specific data.

- ⚙️ **Tenant Onboarding & Schema Setup**  
  Easily onboard new tenants with one command — schema and domain setup handled automatically.

- 🐘 **PostgreSQL with UUID Support**  
  Uses `uuid-ossp` and `pgcrypto` extensions for secure, unique IDs across schemas.

- 🧪 **Seeded DevOps Bootstrap**  
  Comes with a `devops/` folder including Docker, environment setup, and schema seeding for quick dev.

---

## 📦 Table of Contents

- [Installation](#installation)
- [Functionality](#functionality)
- [Configuration](#configuration)
- [Usage](#usage)
- [Admin Dashboard](#admin-dashboard)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/solo925/Multi-Tenant-SaaS-Boilerplate
cd multi-tenant-saas
```

### 2. Set Up Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure `.env`

```env
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/multi_tenant_saas
SECRET_KEY=your-secret-key
```

---

## 🧠 Functionality

### 🔐 Authentication

- Uses Django's custom user model with email login.
- Integrated role/group/permissions via Django's permission system.

### 🏢 Tenant Isolation

- Tenant schemas created automatically via onboarding commands.
- Supports subdomain and schema-based routing.
- Shared user model in `public` schema; tenant models isolated.

### 🖥️ Admin Panel

- Custom dashboard powered by Django admin.
- Full CRUD for tenants, users, roles, and public schema data.
- Easily extendable to include plans, usage, and billing.

### 🧱 DevOps Structure

- Docker and PostgreSQL config inside `/devops`.
- Seed tenant(s), superuser, and billing plans via SQL.
- Bootstrap shell script for team development.

---

## ⚡ Performance

- DB indexes & constraint for billing (fast queries, single active subscription per user)
- Cached KPIs and analytics (configurable TTLs)
- Query optimization for dashboard feed

See `OPTIMIZATIONS.md` for details.

### 🧪 Development Tips

- Caching
  - Uses in‑memory cache by default. To use Redis locally, set `REDIS_URL=redis://localhost:6379/1`.
  - Clear cache via Makefile: `make cache-clear`.
- Email
  - In `DEBUG=True`, emails print to console (no SMTP needed).

---

## ⚙️ Configuration

Edit database connection in `.env` or `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'multi_tenant_saas',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Ensure `django-tenants` is configured correctly in your settings:

```python
TENANT_MODEL = "clients.Client"
TENANT_DOMAIN_MODEL = "clients.Domain"
```

---

## 💻 Usage

### Start the Server

```bash
python manage.py runserver
```

### Create a Superuser

```bash
python manage.py createsuperuser
```

### Create a Tenant

```bash
python manage.py create_tenant --name "Tenant One" --schema "tenant1"
```

This will:
- Create the tenant's schema
- Link a subdomain/domain
- Migrate tenant-specific models

### Run Migrations

```bash
python manage.py migrate_schemas --shared
```

---

## 🛠 Admin Dashboard

Visit [http://localhost:8000/admin](http://localhost:8000/admin) to access the admin panel.

Manage:
- 🔐 Users
- 🏢 Tenants
- 🛡️ Roles & Groups
- 📦 Billing Plans (optional)

---

## 🧯 Troubleshooting

### 🧨 `relation "users_user" does not exist`

> Run:
```bash
python manage.py migrate_schemas --shared
```

### ❌ `Tenant Schema Not Found`

> Ensure tenant was created and schema exists. Confirm correct domain and schema name.

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

