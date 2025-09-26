#!/bin/bash

# TrackFlow Local Development Script
set -e

case "$1" in
    "start")
        echo "🚀 Starting TrackFlow development environment..."
        docker-compose up -d mariadb redis
        echo "⏳ Waiting for database to be ready..."
        sleep 10
        docker-compose up frappe
        ;;
    
    "stop")
        echo "🛑 Stopping TrackFlow development environment..."
        docker-compose down
        ;;
        
    "restart")
        echo "🔄 Restarting TrackFlow development environment..."
        docker-compose down
        docker-compose up -d mariadb redis
        sleep 10
        docker-compose up frappe
        ;;
        
    "clean")
        echo "🧹 Cleaning up TrackFlow development environment..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Environment cleaned"
        ;;
        
    "logs")
        echo "📝 Showing TrackFlow logs..."
        docker-compose logs -f frappe
        ;;
        
    "shell")
        echo "🐚 Opening shell in TrackFlow container..."
        docker-compose exec frappe bash
        ;;
        
    "migrate")
        echo "🔄 Running TrackFlow migrations..."
        docker-compose exec frappe bench --site trackflow.localhost migrate
        ;;
        
    "install")
        echo "📦 Installing TrackFlow app..."
        docker-compose exec frappe bench --site trackflow.localhost install-app trackflow
        ;;
        
    *)
        echo "TrackFlow Local Development"
        echo ""
        echo "Usage: ./dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start development environment"
        echo "  stop     - Stop development environment"  
        echo "  restart  - Restart development environment"
        echo "  clean    - Clean up all containers and volumes"
        echo "  logs     - Show application logs"
        echo "  shell    - Open shell in container"
        echo "  migrate  - Run database migrations"
        echo "  install  - Install TrackFlow app"
        echo ""
        echo "🌐 Access: http://localhost:8000"
        echo "👤 Login: Administrator / admin"
        ;;
esac