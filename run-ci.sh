#!/bin/bash

echo "=========================================="
echo "   RUNNING MEDIQUERY AI - CI SUITE"
echo "   (Unit & Component Tests - Isolated)"
echo "=========================================="
echo ""

# 1. Backend Unit
echo -e "\033[36m[1/2] Backend Unit Tests...\033[0m"
docker compose -f docker-compose.test.yml run --rm backend-unit
BACKEND_EXIT=$?

# 2. Frontend Component
echo -e "\033[36m[2/2] Frontend Component Tests...\033[0m"
echo -e "\033[33mNote: First run will take time to install dependencies inside the container if not cached\033[0m"
docker compose -f docker-compose.test.yml run --rm frontend-component
FRONTEND_EXIT=$?

if [ $BACKEND_EXIT -eq 0 ] && [ $FRONTEND_EXIT -eq 0 ]; then
    echo -e "\033[32m✅ All CI Tests Passed!\033[0m"
    exit 0
else
    echo -e "\033[31m❌ Some CI Tests Failed!\033[0m"
    exit 1
fi
