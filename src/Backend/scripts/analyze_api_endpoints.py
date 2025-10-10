#!/usr/bin/env python3
"""
API Endpoint Analysis Script
Analyzes all API endpoints and maps them to DDD bounded contexts
"""

import re
import ast
from pathlib import Path
from collections import defaultdict
import json

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def extract_routes_from_file(file_path):
    """Extract FastAPI routes from a Python file"""
    routes = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find router definitions
        router_match = re.search(r'router\s*=\s*APIRouter\([^)]*\)', content)
        prefix = ""
        tags = []

        if router_match:
            router_def = router_match.group(0)
            prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', router_def)
            tags_match = re.search(r'tags\s*=\s*\[([^\]]+)\]', router_def)

            if prefix_match:
                prefix = prefix_match.group(1)
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [t.strip(' "\'') for t in tags_str.split(',')]

        # Find all route decorators
        route_patterns = [
            r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
            r'@app\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
        ]

        for pattern in route_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                full_path = prefix + path if prefix and not path.startswith('/') else path

                # Try to find the function name
                func_match = re.search(r'async\s+def\s+(\w+)\s*\(', content[match.end():match.end()+200])
                func_name = func_match.group(1) if func_match else "unknown"

                routes.append({
                    'method': method,
                    'path': full_path,
                    'function': func_name,
                    'tags': tags
                })

        # Find imported services
        service_imports = re.findall(r'from\s+services\.(\w+)\s+import|import\s+services\.(\w+)', content)
        services = set()
        for match in service_imports:
            service = match[0] or match[1]
            services.add(service)

        return {
            'routes': routes,
            'services': list(services),
            'has_router': bool(router_match),
            'prefix': prefix,
            'tags': tags
        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def map_to_ddd_context(filename, routes, services):
    """Map an endpoint file to a DDD bounded context"""

    filename_lower = filename.lower()

    # Identity & Access Context
    if any(x in filename_lower for x in ['auth', 'user', 'admin', 'registration', 'customer_auth']):
        return 'Identity & Access'

    # Tenant Management Context
    if any(x in filename_lower for x in ['tenant', 'store_endpoints', 'store_hours']):
        return 'Tenant Management'

    # Product Catalog Context
    if any(x in filename_lower for x in ['product', 'accessories', 'catalog', 'ocs']):
        return 'Product Catalog'

    # Inventory Management Context
    if any(x in filename_lower for x in ['inventory', 'shelf_location']):
        return 'Inventory Management'

    # Purchase Order Context
    if any(x in filename_lower for x in ['supplier', 'provincial_catalog']):
        return 'Purchase Order'

    # Order Management Context
    if any(x in filename_lower for x in ['order', 'cart', 'checkout', 'guest_checkout']):
        return 'Order Management'

    # Pricing & Promotions Context
    if any(x in filename_lower for x in ['promotion', 'pricing']):
        return 'Pricing & Promotions'

    # Payment Processing Context
    if any(x in filename_lower for x in ['payment']):
        return 'Payment Processing'

    # Delivery Management Context
    if any(x in filename_lower for x in ['delivery', 'geocoding']):
        return 'Delivery Management'

    # Customer Engagement Context
    if any(x in filename_lower for x in ['review', 'wishlist']):
        return 'Customer Engagement'

    # Communication Context
    if any(x in filename_lower for x in ['communication']):
        return 'Communication'

    # AI & Conversation Context
    if any(x in filename_lower for x in ['chat', 'voice', 'agent_pool']):
        return 'AI & Conversation'

    # Localization Context
    if any(x in filename_lower for x in ['translation']):
        return 'Localization'

    # Infrastructure / Cross-cutting
    if any(x in filename_lower for x in ['database', 'logs', 'analytics', 'file_upload', 'sitemap', 'robots', 'search']):
        return 'Infrastructure'

    # POS / Kiosk (could be Order Management)
    if any(x in filename_lower for x in ['pos', 'kiosk', 'device', 'hardware']):
        return 'POS/Kiosk (Order Management)'

    # API Gateway
    if 'gateway' in filename_lower:
        return 'API Gateway'

    return 'Uncategorized'

def analyze_all_endpoints():
    """Analyze all API endpoint files"""

    api_dir = Path('api')

    if not api_dir.exists():
        print(f"{Colors.FAIL}Error: api/ directory not found{Colors.ENDC}")
        return

    endpoint_files = sorted(api_dir.glob('*.py'))

    # Exclude __init__.py and backup files
    endpoint_files = [f for f in endpoint_files if f.name != '__init__.py' and 'backup' not in f.name.lower()]

    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}API Endpoint Analysis{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    print(f"Found {Colors.BOLD}{len(endpoint_files)}{Colors.ENDC} API endpoint files\n")

    all_data = {}
    context_mapping = defaultdict(list)
    all_routes = []
    duplicate_routes = defaultdict(list)

    # Analyze each file
    for file_path in endpoint_files:
        print(f"Analyzing: {Colors.OKBLUE}{file_path.name}{Colors.ENDC}")

        data = extract_routes_from_file(file_path)

        if data:
            context = map_to_ddd_context(file_path.name, data['routes'], data['services'])
            data['ddd_context'] = context
            data['filename'] = file_path.name
            data['line_count'] = sum(1 for _ in open(file_path))

            all_data[file_path.name] = data
            context_mapping[context].append(file_path.name)

            # Track all routes for duplicate detection
            for route in data['routes']:
                route_key = f"{route['method']} {route['path']}"
                all_routes.append(route_key)
                duplicate_routes[route_key].append(file_path.name)

            print(f"  → {len(data['routes'])} routes, {len(data['services'])} services, Context: {Colors.OKCYAN}{context}{Colors.ENDC}")
        else:
            print(f"  → {Colors.WARNING}Failed to analyze{Colors.ENDC}")

    # Generate report
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}Analysis Results{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    # Summary by DDD context
    print(f"{Colors.BOLD}Endpoints by DDD Bounded Context:{Colors.ENDC}\n")

    for context in sorted(context_mapping.keys()):
        files = context_mapping[context]
        total_routes = sum(len(all_data[f]['routes']) for f in files if f in all_data)
        total_lines = sum(all_data[f]['line_count'] for f in files if f in all_data)

        print(f"{Colors.OKCYAN}{context}{Colors.ENDC}")
        print(f"  Files: {len(files)}, Routes: {total_routes}, Lines: {total_lines}")
        for filename in sorted(files):
            if filename in all_data:
                routes = len(all_data[filename]['routes'])
                services = ', '.join(all_data[filename]['services'][:3]) + ('...' if len(all_data[filename]['services']) > 3 else '')
                print(f"    • {filename} ({routes} routes)")
                if services:
                    print(f"      Services: {services}")
        print()

    # Find duplicates
    print(f"{Colors.BOLD}Duplicate/Overlapping Routes:{Colors.ENDC}\n")

    duplicates_found = False
    for route_key, files in sorted(duplicate_routes.items()):
        if len(files) > 1:
            duplicates_found = True
            print(f"{Colors.WARNING}{route_key}{Colors.ENDC}")
            for file in files:
                print(f"  • {file}")
            print()

    if not duplicates_found:
        print(f"{Colors.OKGREEN}No duplicate routes found!{Colors.ENDC}\n")

    # Save detailed report
    report_data = {
        'summary': {
            'total_files': len(endpoint_files),
            'total_routes': len(all_routes),
            'contexts': {ctx: len(files) for ctx, files in context_mapping.items()}
        },
        'by_context': {ctx: {
            'files': files,
            'routes': sum(len(all_data[f]['routes']) for f in files if f in all_data),
            'lines': sum(all_data[f]['line_count'] for f in files if f in all_data)
        } for ctx, files in context_mapping.items()},
        'endpoints': all_data,
        'duplicates': {k: v for k, v in duplicate_routes.items() if len(v) > 1}
    }

    with open('API_ENDPOINT_ANALYSIS.json', 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"{Colors.OKGREEN}Detailed report saved to: API_ENDPOINT_ANALYSIS.json{Colors.ENDC}")

    return report_data

if __name__ == '__main__':
    try:
        analyze_all_endpoints()
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        raise
