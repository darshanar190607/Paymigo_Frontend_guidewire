#!/usr/bin/env python3
"""
PayMigo System Validation Script
Verifies all components are properly integrated and ready for testing
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"{GREEN}✓{RESET} {description}: {filepath}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {filepath} NOT FOUND")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    if Path(dirpath).is_dir():
        print(f"{GREEN}✓{RESET} {description}: {dirpath}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {dirpath} NOT FOUND")
        return False

def check_string_in_file(filepath, search_string, description):
    """Check if a string exists in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string in content:
                print(f"{GREEN}✓{RESET} {description}")
                return True
            else:
                print(f"{RED}✗{RESET} {description} - NOT FOUND")
                return False
    except Exception as e:
        print(f"{RED}✗{RESET} {description} - ERROR: {e}")
        return False

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}PayMigo System Validation{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    results = []
    
    # Section 1: Core Structure
    print(f"\n{YELLOW}[1] Core Project Structure{RESET}")
    results.append(check_directory_exists("backend", "Backend directory"))
    results.append(check_directory_exists("ml-services/ML-Service", "ML Service directory"))
    results.append(check_directory_exists("Paymigo_Frontend/web", "Frontend directory"))
    
    # Section 2: Backend Files
    print(f"\n{YELLOW}[2] Backend Integration{RESET}")
    results.append(check_file_exists("backend/server.js", "Backend server"))
    results.append(check_file_exists("backend/routes/geotruth.js", "GeoTruth route"))
    results.append(check_file_exists("backend/routes/analytics.js", "Analytics route"))
    results.append(check_file_exists("backend/routes/pricing.js", "Pricing route"))
    results.append(check_file_exists("backend/routes/dashboard.js", "Dashboard route"))
    results.append(check_file_exists("backend/routes/fraud.js", "Fraud route"))
    
    # Section 3: ML Service Files
    print(f"\n{YELLOW}[3] ML Service Integration{RESET}")
    results.append(check_file_exists("ml-services/ML-Service/app/main.py", "ML Service main"))
    results.append(check_file_exists("ml-services/ML-Service/app/adapters/geotruth_adapter.py", "GeoTruth adapter"))
    results.append(check_file_exists("ml-services/ML-Service/app/api/geotruth.py", "GeoTruth API"))
    results.append(check_file_exists("ml-services/ML-Service/app/api/fraud.py", "Fraud API"))
    results.append(check_file_exists("ml-services/ML-Service/app/api/forecast.py", "Forecast API"))
    
    # Section 4: GeoTruth Package
    print(f"\n{YELLOW}[4] GeoTruth Package{RESET}")
    results.append(check_file_exists("ml-services/ML-Service/Geotruth/geotruth/__init__.py", "GeoTruth package"))
    results.append(check_file_exists("ml-services/ML-Service/Geotruth/geotruth/engine.py", "GeoTruth engine"))
    results.append(check_file_exists("ml-services/ML-Service/Geotruth/geotruth/schemas.py", "GeoTruth schemas"))
    
    # Section 5: Frontend Files
    print(f"\n{YELLOW}[5] Frontend Integration{RESET}")
    results.append(check_file_exists("Paymigo_Frontend/web/src/App.tsx", "Frontend App"))
    results.append(check_file_exists("Paymigo_Frontend/web/src/pages/RiskAnalytics.tsx", "RiskAnalytics page"))
    results.append(check_file_exists("Paymigo_Frontend/web/src/pages/Dashboard.tsx", "Dashboard page"))
    results.append(check_file_exists("Paymigo_Frontend/web/src/pages/Plans.tsx", "Plans page"))
    results.append(check_file_exists("Paymigo_Frontend/web/src/pages/ClaimVerification.tsx", "ClaimVerification page"))
    
    # Section 6: Database
    print(f"\n{YELLOW}[6] Database Configuration{RESET}")
    results.append(check_file_exists("backend/prisma/schema.prisma", "Prisma schema"))
    results.append(check_file_exists("backend/lib/prisma.js", "Prisma client"))
    
    # Section 7: Documentation
    print(f"\n{YELLOW}[7] Documentation{RESET}")
    results.append(check_file_exists("SYSTEM_ARCHITECTURE.md", "System architecture doc"))
    results.append(check_file_exists("TESTING_CHECKLIST.md", "Testing checklist"))
    results.append(check_file_exists("QUICKSTART.md", "Quick start guide"))
    results.append(check_file_exists("STEP6_SUMMARY.md", "Step 6 summary"))
    
    # Section 8: Code Verification
    print(f"\n{YELLOW}[8] Code Integration Verification{RESET}")
    
    # Check RiskAnalytics import in App.tsx
    results.append(check_string_in_file(
        "Paymigo_Frontend/web/src/App.tsx",
        "import RiskAnalytics from './pages/RiskAnalytics'",
        "RiskAnalytics imported in App.tsx"
    ))
    
    # Check RiskAnalytics routing
    results.append(check_string_in_file(
        "Paymigo_Frontend/web/src/App.tsx",
        "/admin/analytics",
        "RiskAnalytics routed at /admin/analytics"
    ))
    
    # Check currency symbol fix
    results.append(check_string_in_file(
        "Paymigo_Frontend/web/src/pages/RiskAnalytics.tsx",
        "₹{(forecastData.global.projectedPayout",
        "Currency symbol fixed to ₹"
    ))
    
    # Check analytics.js fix (no self-referencing)
    results.append(check_string_in_file(
        "backend/routes/analytics.js",
        "http://127.0.0.1:8000/orchestrator/pipeline/forecast",
        "Analytics calls ML forecast endpoint"
    ))
    
    # Check GeoTruth router in main.py
    results.append(check_string_in_file(
        "ml-services/ML-Service/app/main.py",
        "from app.api import cluster, premium, trigger, curfew, fraud, forecast, health, payout_manager, testing_framework, geotruth",
        "GeoTruth imported in main.py"
    ))
    
    results.append(check_string_in_file(
        "ml-services/ML-Service/app/main.py",
        'app.include_router(geotruth.router, prefix="/geotruth"',
        "GeoTruth router registered"
    ))
    
    # Section 9: Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Validation Summary{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    if failed > 0:
        print(f"{RED}Failed: {failed}{RESET}")
    else:
        print(f"Failed: {failed}")
    
    percentage = (passed / total) * 100
    print(f"\nSuccess Rate: {percentage:.1f}%")
    
    if percentage == 100:
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✓ ALL CHECKS PASSED - SYSTEM READY FOR TESTING{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        return 0
    elif percentage >= 90:
        print(f"\n{YELLOW}{'='*70}{RESET}")
        print(f"{YELLOW}⚠ MOSTLY COMPLETE - MINOR ISSUES DETECTED{RESET}")
        print(f"{YELLOW}{'='*70}{RESET}\n")
        return 1
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}✗ CRITICAL ISSUES DETECTED - REVIEW REQUIRED{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 2

if __name__ == "__main__":
    sys.exit(main())
