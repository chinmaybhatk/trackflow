# 🐳 TrackFlow Local Docker Development

Quickly set up TrackFlow locally with Docker for fast development and testing.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git (for cloning)

### 1. Clone and Setup
```bash
git clone https://github.com/chinmaybhatk/trackflow.git
cd trackflow
```

### 2. Start Development Environment
```bash
./dev.sh start
```

This will:
- 🗄️ Start MariaDB database
- 📦 Start Redis cache
- 🏗️ Build Frappe environment
- 📱 Install Frappe CRM
- 🎯 Install TrackFlow
- 🌐 Start development server

### 3. Access TrackFlow
- **URL**: http://localhost:8000
- **Username**: Administrator  
- **Password**: admin

## 🎯 Test Modern UI

Once the environment is running, test the modern TrackFlow pages:

### Direct URLs
```
http://localhost:8000/campaigns     # Campaigns page
http://localhost:8000/links         # Links page  
http://localhost:8000/analytics     # Analytics dashboard
```

### Through FCRM
1. Go to http://localhost:8000
2. Login with Administrator / admin
3. Navigate to CRM workspace
4. Look for TrackFlow in sidebar or use the dedicated TrackFlow workspace

## 🛠️ Development Commands

```bash
# Start environment
./dev.sh start

# Stop environment
./dev.sh stop

# Restart environment  
./dev.sh restart

# View logs
./dev.sh logs

# Open shell in container
./dev.sh shell

# Run migrations
./dev.sh migrate

# Clean everything (remove all data)
./dev.sh clean
```

## 🔧 Development Workflow

### Making Changes
1. Edit TrackFlow code locally
2. Changes are automatically synced to container
3. Restart if needed: `./dev.sh restart`
4. Test at http://localhost:8000

### Installing Apps
If you need to install additional Frappe apps:
```bash
./dev.sh shell
bench get-app [app-name]
bench --site trackflow.localhost install-app [app-name]
```

### Database Access
```bash
# Access MariaDB
docker-compose exec mariadb mariadb -u frappe -p frappe_db
# Password: frappe
```

## 📂 Project Structure

```
trackflow/
├── docker/                 # Docker configuration
│   ├── Dockerfile.frappe   # Frappe container
│   ├── setup.sh           # Setup script
│   └── mariadb.cnf        # Database config
├── docker-compose.yml     # Docker services
├── dev.sh                # Development helper
└── trackflow/            # TrackFlow app code
    ├── www/             # Modern UI pages
    │   ├── campaigns.*  # Campaigns page
    │   ├── links.*     # Links page
    │   └── analytics.* # Analytics page
    └── ...
```

## 🐛 Troubleshooting

### Port Conflicts
If ports 8000, 3306, or 6379 are in use:
```bash
./dev.sh stop
# Kill processes using those ports
./dev.sh start
```

### Database Issues
```bash
# Reset everything
./dev.sh clean
./dev.sh start
```

### App Installation Issues
```bash
./dev.sh shell
bench --site trackflow.localhost migrate
bench --site trackflow.localhost install-app trackflow --force
```

## 🎉 Ready for Testing!

Once everything is running:
1. ✅ Test campaigns page: http://localhost:8000/campaigns
2. ✅ Test links page: http://localhost:8000/links  
3. ✅ Test analytics: http://localhost:8000/analytics
4. ✅ Create campaigns and links through FCRM
5. ✅ Verify modern UI integration

When everything works locally, deploy to Frappe Cloud with confidence! 🚀