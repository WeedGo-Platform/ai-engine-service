"""
Robots.txt API Endpoint
Serves dynamic robots.txt based on store configuration
"""

from fastapi import APIRouter, Response, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["seo"])


@router.get("/robots.txt")
async def get_robots_txt(
    domain: Optional[str] = Query(None, description="Domain for sitemap URLs"),
    allow_crawling: bool = Query(True, description="Allow search engine crawling")
):
    """
    Generate dynamic robots.txt file
    """
    try:
        # Base domain for sitemap URLs
        base_domain = domain or "https://weedgo.com"

        if allow_crawling:
            # Allow crawling configuration
            robots_content = f"""# Robots.txt for {base_domain}
# Allow search engines to crawl all content

User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Disallow: /checkout/
Disallow: /cart/
Disallow: /profile/
Disallow: /login
Disallow: /register
Disallow: /reset-password
Disallow: /verify-email
Disallow: /*.json$
Disallow: /*?*sort=
Disallow: /*?*filter=
Disallow: /*?*page=

# Allow important pages
Allow: /products
Allow: /dispensary-near-me/
Allow: /cannabis/
Allow: /brands/
Allow: /about
Allow: /contact

# Specific bot rules
User-agent: Googlebot
Allow: /
Crawl-delay: 0

User-agent: Bingbot
Allow: /
Crawl-delay: 1

User-agent: Slurp
Allow: /
Crawl-delay: 1

# Block bad bots
User-agent: MJ12bot
Disallow: /

User-agent: AhrefsBot
Disallow: /

User-agent: SemrushBot
Disallow: /

User-agent: DotBot
Disallow: /

User-agent: Rogerbot
Disallow: /

# Sitemap locations
Sitemap: {base_domain}/api/seo/sitemap.xml
Sitemap: {base_domain}/api/seo/sitemap-index.xml
"""
        else:
            # Disallow all crawling (for staging/dev environments)
            robots_content = f"""# Robots.txt for {base_domain}
# Block all crawlers - staging/development environment

User-agent: *
Disallow: /

# Development/Staging Notice
# This site is not intended for public indexing
"""

        return Response(
            content=robots_content,
            media_type="text/plain",
            headers={
                "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
            }
        )

    except Exception as e:
        logger.error(f"Error generating robots.txt: {str(e)}")
        # Return a safe default that blocks crawling on error
        return Response(
            content="User-agent: *\nDisallow: /",
            media_type="text/plain"
        )