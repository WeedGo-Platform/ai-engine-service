#!/usr/bin/env python3
"""Clear cache for Britane barcode"""

import redis

r = redis.Redis(host='localhost', port=6379, db=0)

barcode = "6528273015278"
cache_key = f"barcode:{barcode}"

if r.exists(cache_key):
    r.delete(cache_key)
    print(f"✅ Cleared cache for {cache_key}")
else:
    print(f"❌ No cache entry found for {cache_key}")

# Check what's in the cache
all_keys = r.keys("barcode:*")
print(f"\nTotal cached barcodes: {len(all_keys)}")
for key in all_keys[:5]:
    print(f"  {key.decode()}")