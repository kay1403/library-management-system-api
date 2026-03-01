# 📚 Library Management System

A production-ready library management platform with user authentication, book borrowing, waitlists, and comprehensive admin dashboard. Deployed on Render with PostgreSQL.

## 🚀 Live Demo

- **Application**: [https://libraryms-tfsy.onrender.com](https://libraryms-tfsy.onrender.com)
- **Admin Panel**: [https://libraryms-tfsy.onrender.com/admin](https://libraryms-tfsy.onrender.com/admin)
- **API Documentation**: [https://libraryms-tfsy.onrender.com/api/docs](https://libraryms-tfsy.onrender.com/api/docs)

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Screenshots](#-screenshots)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 👤 User Features
| Feature | Description |
|---------|-------------|
| **User Authentication** | Secure registration and login system |
| **Book Catalog** | Browse all available books with search functionality |
| **Advanced Search** | Filter books by title, author, or ISBN |
| **Borrowing System** | Check out books with automatic 14-day return dates |
| **Waitlist Management** | Join waitlists for unavailable books with queue position tracking |
| **Personal Dashboard** | Real-time stats: current loans, overdue items, waitlist positions |
| **Email Notifications** | Automatic alerts when reserved books become available |
| **Profile Management** | Update personal information and view membership history |

### 👑 Admin Features
| Feature | Description |
|---------|-------------|
| **Book Management** | Full CRUD operations for books (add, edit, delete) |
| **User Administration** | Activate/deactivate member accounts, view all users |
| **Transaction Oversight** | Monitor all borrow/return activities across the library |
| **Waitlist Control** | View and manage waiting queues for popular books |
| **Analytics Dashboard** | Quick overview of library statistics |
| **Bulk Actions** | Mark multiple transactions as returned |

## 🛠 Tech Stack

### Backend
- **Framework**: Django 5.2
- **API Framework**: Django REST Framework 3.15
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: Session-based + Token Authentication
- **Background Tasks**: Email notifications on book returns

### Frontend
- **Templating**: Django Templates
- **Styling**: Tailwind CSS
- **JavaScript**: Vanilla JS for interactive features
- **Icons**: Emoji-based UI elements

### DevOps & Tools
- **Version Control**: Git & GitHub
- **Deployment**: Render (Web Service + PostgreSQL)
- **Environment**: Python 3.14
- **Dependencies**: pip + requirements.txt
- **Static Files**: WhiteNoise for production serving


## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (optional, SQLite works for development)
- Git

### Step-by-Step Setup

1. **Clone the repository**
```bash
git clone https://github.com/kay1403/library-management-system-api.git
cd library-management-system-api
```

2. **Create and activate virtual environment**
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file in the root directory:
```env
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (PostgreSQL)
DB_NAME=library_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Email (Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Start development server**
```bash
python manage.py runserver
```

8. **Access the application**
- Main site: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/
- API docs: http://127.0.0.1:8000/api/docs/

## 🔐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (keep secret!) | Required |
| `DEBUG` | Debug mode (True for development) | False |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | localhost,127.0.0.1 |
| `DB_NAME` | PostgreSQL database name | library_db |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | Required |
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `EMAIL_HOST_USER` | Gmail address for notifications | Required |
| `EMAIL_HOST_PASSWORD` | Gmail app password | Required |

## 📡 API Documentation

### Base URL
- Development: `http://127.0.0.1:8000/api/`
- Production: `https://libraryms-tfsy.onrender.com/api/`

### Authentication
Most endpoints require authentication. Include session cookie or token.

### Endpoints Overview

| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| **Books** |
| GET | `/api/books/` | List all books | Public |
| POST | `/api/books/` | Create new book | Admin |
| GET | `/api/books/{id}/` | Book details | Public |
| PUT | `/api/books/{id}/` | Update book | Admin |
| DELETE | `/api/books/{id}/` | Delete book | Admin |
| **Transactions** |
| POST | `/api/checkout/` | Borrow a book | User |
| POST | `/api/return/` | Return a book | User |
| GET | `/api/my-transactions/` | User's transactions | User |
| GET | `/api/overdue/` | Overdue books | User |
| **Waitlist** |
| GET | `/api/waitlist/` | View waitlist | User |
| POST | `/api/waitlist/join/` | Join waitlist | User |
| DELETE | `/api/waitlist/{id}/cancel/` | Leave waitlist | User |

### Example Requests

**Borrow a book**
```bash
curl -X POST https://libraryms-tfsy.onrender.com/api/checkout/ \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1}'
```

**Join waitlist**
```bash
curl -X POST https://libraryms-tfsy.onrender.com/api/waitlist/join/ \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1}'
```

## 🚢 Deployment

### Deploy to Render

1. **Push code to GitHub**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Create a new Web Service on Render**
- Connect your GitHub repository
- Select Python environment
- Set build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Set start command: `python manage.py runserver 0.0.0.0:$PORT`

3. **Add environment variables** in Render dashboard
- `SECRET_KEY`: (Render can generate)
- `DEBUG`: False
- `ALLOWED_HOSTS`: .onrender.com,localhost,127.0.0.1
- `DATABASE_URL`: (Auto-populated when adding PostgreSQL)

4. **Add PostgreSQL database**
- Go to Dashboard → New → PostgreSQL
- Link it to your web service

5. **Deploy!** 🚀

## 📁 Detailed Project Structure

```
library-management-system-api/
├── books/                          # Main application
│   ├── migrations/                 # Database migrations
│   ├── __init__.py
│   ├── admin.py                    # Admin interface config
│   ├── apps.py                      # App configuration
│   ├── models.py                    # Book, Transaction, Waitlist
│   ├── serializers.py               # DRF serializers
│   ├── urls.py                      # App-specific URLs
│   └── views.py                     # All views (API + HTML)
├── users/                           # User management
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py                     # User admin config
│   ├── apps.py
│   ├── models.py                    # Custom User model
│   ├── serializers.py               # User serializers
│   ├── urls.py                      # User URLs
│   └── views.py                     # Auth views
├── templates/                        # HTML templates
│   ├── base.html                     # Base template
│   ├── home.html                      # Homepage
│   ├── includes/                      # Reusable components
│   │   ├── navbar.html
│   │   └── messages.html
│   ├── books/                         # Book templates
│   │   ├── book_list.html
│   │   ├── book_detail.html
│   │   ├── my_transactions.html
│   │   ├── overdue.html
│   │   └── waitlist.html
│   └── users/                         # User templates
│       ├── login.html
│       ├── register.html
│       └── profile.html
├── static/                            # Static files (CSS, JS)
│   └── css/
│       └── output.css                  # Tailwind output
├── library_management/                 # Project configuration
│   ├── __init__.py
│   ├── settings.py                      # Main settings
│   ├── urls.py                          # Main URLs
│   └── wsgi.py                          # WSGI config
├── .env                                 # Environment variables
├── .gitignore                           # Git ignore rules
├── manage.py                            # Django management
├── requirements.txt                     # Python dependencies
└── README.md                            # This file
```

## 🧪 Testing

Run the test suite:
```bash
python manage.py test books
python manage.py test users
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and well-described


## 👥 Authors

- **Ange KOUMBA** - *Initial work* - [kay1403](https://github.com/kay1403)

## 🙏 Acknowledgments

- Django Software Foundation
- Render for hosting
- Tailwind CSS team
- All contributors and users

## 📬 Contact

- **Project Link**: [https://github.com/kay1403/library-management-system-api](https://github.com/kay1403/library-management-system-api)
- **Live Demo**: [https://libraryms-tfsy.onrender.com](https://libraryms-tfsy.onrender.com)
- **Issues**: [GitHub Issues](https://github.com/kay1403/library-management-system-api/issues)



