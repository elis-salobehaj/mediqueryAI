#!/bin/bash

echo "=========================================="
echo "   RUNNING MEDIQUERY AI TEST SUITE"
echo "=========================================="
echo ""

echo -e "\033[36m[1/2] Running Backend Tests (Pytest)...\033[0m"
docker compose -f docker-compose.test.yml run --rm backend-test
if [ $? -eq 0 ]; then
    echo -e "\033[32m✅ Backend Tests Passed!\033[0m"
else
    echo -e "\033[31m❌ Backend Tests Failed!\033[0m"
fi

echo ""
echo -e "\033[36m[2/2] Running Frontend Tests (Playwright)...\033[0m"
echo -e "\033[33mNote: First run will take time to install dependencies inside the container.\033[0m"

docker compose -f docker-compose.test.yml run --rm frontend-test-ct
if [ $? -eq 0 ]; then
    echo -e "\033[32m✅ Frontend Tests Passed!\033[0m"
else
    echo -e "\033[31m❌ Frontend Tests Failed!\033[0m"
fi

echo ""
echo "Test execution complete."
