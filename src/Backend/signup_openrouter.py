#!/usr/bin/env python3
"""
OpenRouter Automated Signup

Uses Playwright to automate OpenRouter account creation and API key retrieval.
"""

import asyncio
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Test email for WeedGo
TEST_EMAIL = "weedgo.test@gmail.com"  # You can change this
TEST_PASSWORD = "WeedGo2025!Test"     # You can change this


async def signup_openrouter():
    """Automate OpenRouter signup"""
    print("\n" + "="*80)
    print("OPENROUTER AUTOMATED SIGNUP")
    print("="*80)

    async with async_playwright() as p:
        # Launch browser (headless=False to see what's happening)
        print("\n🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Step 1: Go to OpenRouter
            print("\n📍 Navigating to OpenRouter...")
            await page.goto("https://openrouter.ai/", timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Take screenshot
            await page.screenshot(path="openrouter_step1.png")
            print("  ✓ Page loaded (screenshot: openrouter_step1.png)")

            # Step 2: Find and click Sign Up
            print("\n🔍 Looking for Sign Up button...")
            try:
                # Try multiple selectors
                signup_selectors = [
                    "text=Sign up",
                    "text=Sign Up",
                    "text=Create account",
                    "text=Get Started",
                    'a[href*="sign-up"]',
                    'button:has-text("Sign")'
                ]

                clicked = False
                for selector in signup_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            await element.click()
                            print(f"  ✓ Clicked sign up button (selector: {selector})")
                            clicked = True
                            break
                    except:
                        continue

                if not clicked:
                    # Try going directly to signup page
                    print("  ⚠️ Sign up button not found, trying direct URL...")
                    await page.goto("https://openrouter.ai/sign-up", timeout=30000)

                await page.wait_for_load_state("networkidle")
                await page.screenshot(path="openrouter_step2.png")

            except Exception as e:
                print(f"  ⚠️ Error finding signup: {e}")
                await page.screenshot(path="openrouter_error.png")

            # Step 3: Look for Google Sign In
            print("\n🔍 Looking for Google Sign In...")
            try:
                google_selectors = [
                    "text=Sign in with Google",
                    "text=Continue with Google",
                    'button:has-text("Google")',
                    '[aria-label*="Google"]'
                ]

                for selector in google_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            print(f"  ✓ Found Google sign in button")
                            print(f"\n⚠️ MANUAL STEP REQUIRED:")
                            print(f"     Please click the Google sign in button")
                            print(f"     and complete the Google OAuth flow")
                            print(f"     The browser will stay open for 2 minutes")

                            # Wait for manual interaction
                            await asyncio.sleep(120)  # 2 minutes
                            break
                    except:
                        continue

                await page.screenshot(path="openrouter_step3.png")

            except Exception as e:
                print(f"  ⚠️ Error finding Google signin: {e}")

            # Step 4: After login, navigate to API keys
            print("\n🔑 Navigating to API keys page...")
            try:
                await page.goto("https://openrouter.ai/keys", timeout=30000)
                await page.wait_for_load_state("networkidle")
                await page.screenshot(path="openrouter_keys.png")

                # Look for API key
                print("\n🔍 Looking for API key...")

                # Try to find existing key or create button
                key_selectors = [
                    'input[type="password"]',
                    'code',
                    'pre',
                    'text=sk-or-v1',
                    'button:has-text("Create")',
                    'button:has-text("Generate")'
                ]

                for selector in key_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            if 'button' in selector:
                                await element.click()
                                print("  ✓ Clicked create key button")
                                await asyncio.sleep(2)

                            # Try to extract key
                            key_element = page.locator('text=/sk-or-v1-[a-zA-Z0-9-]+/').first
                            if await key_element.is_visible(timeout=2000):
                                key = await key_element.inner_text()
                                print(f"\n✅ SUCCESS! Got API Key:")
                                print(f"  {key}")

                                # Save to file
                                with open("openrouter_key.txt", "w") as f:
                                    f.write(key)
                                print(f"\n💾 Saved to: openrouter_key.txt")

                                return key
                            break
                    except:
                        continue

                print("\n⚠️ Could not automatically extract key")
                print("  Please copy it manually from the browser")
                print("  The browser will stay open for 1 minute")
                await asyncio.sleep(60)

            except Exception as e:
                print(f"  ⚠️ Error accessing keys page: {e}")
                await page.screenshot(path="openrouter_keys_error.png")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await page.screenshot(path="openrouter_final_error.png")
            import traceback
            traceback.print_exc()

        finally:
            print("\n🔄 Closing browser...")
            await browser.close()

    return None


async def main():
    print("\n" + "="*80)
    print(" "*20 + "OPENROUTER AUTOMATION")
    print(" "*15 + "Attempting automated signup")
    print("="*80)

    print("\n⚠️  NOTE: This script will:")
    print("  1. Open a browser window")
    print("  2. Navigate to OpenRouter")
    print("  3. Require manual Google OAuth (cannot automate)")
    print("  4. Attempt to retrieve API key")

    # Skip interactive prompt for automation - check if running in terminal
    if sys.stdin.isatty():
        input("\n Press ENTER to start...")
    else:
        print("\n🤖 Running in automated mode...")
        await asyncio.sleep(2)

    api_key = await signup_openrouter()

    if api_key:
        print("\n" + "="*80)
        print("✅ SIGNUP COMPLETE!")
        print("="*80)
        print(f"\nYour OpenRouter API key: {api_key}")
        print("\nTo use it, run:")
        print(f'  export OPENROUTER_API_KEY="{api_key}"')
    else:
        print("\n" + "="*80)
        print("⚠️ MANUAL COMPLETION REQUIRED")
        print("="*80)
        print("\nPlease:")
        print("  1. Complete the signup manually")
        print("  2. Go to https://openrouter.ai/keys")
        print("  3. Copy your API key")
        print("  4. Run: export OPENROUTER_API_KEY='your_key'")


if __name__ == "__main__":
    asyncio.run(main())
