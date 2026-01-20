#!/bin/bash
# Seed test data for YDTT Backend
# This script drops the existing database, recreates it, runs migrations, and seeds test data

set -e

echo "========================================"
echo "YDTT Backend - Test Data Seeding"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}WARNING: This will drop the existing database and recreate it!${NC}"
echo -e "${YELLOW}All existing data will be lost!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]
then
    echo "Aborted."
    exit 1
fi

echo -e "${GREEN}Step 1: Dropping existing database...${NC}"
docker-compose exec -T db psql -U ydtt_user -d postgres -c "DROP DATABASE IF EXISTS ydtt_core;"

echo -e "${GREEN}Step 2: Creating fresh database...${NC}"
docker-compose exec -T db psql -U ydtt_user -d postgres -c "CREATE DATABASE ydtt_core;"

echo -e "${GREEN}Step 3: Running migrations...${NC}"
docker-compose exec -T app alembic upgrade head

echo -e "${GREEN}Step 4: Seeding test data...${NC}"
docker-compose exec -T app python -m app.seed_test_data

echo ""
echo -e "${GREEN}========================================"
echo "✓ Test data seeding completed!"
echo "========================================${NC}"
echo ""
echo "Test Accounts:"
echo "  Teacher: teacher1@ydtt.uz / password123"
echo "  Student: student1@ydtt.uz / password123"
echo ""
echo "API Documentation: http://localhost:8000/api/v1/docs"
echo ""
