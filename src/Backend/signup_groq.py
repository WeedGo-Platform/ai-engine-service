#!/usr/bin/env python3
"""
Groq Automated Signup

Uses Playwright to automate Groq account creation and API key retrieval.
"""

import asyncio
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def signup_groq():
    """Automate Groq signup"""
    print("\n" + "="*80)
    print("GROQ AUTOMATED SIGNUP")
    print("="*80)

    async with async_playwright() as p:
        # Launch browser (headless=False to see what's happening)
        print("\n🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Step 1: Go to Groq Console
            print("\n📍 Navigating to Groq Console...")
            await page.goto("https://console.groq.com/", timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Take screenshot
            await page.screenshot(path="groq_step1.png")
            print("  ✓ Page loaded (screenshot: groq_step1.png)")

            # Step 2: Look for Sign In / Sign Up
            print("\n🔍 Looking for Sign Up/Login...")
            try:
                login_selectors = [
                    "text=Log In",
                    "text=Sign In",
                    "text=Start Building",
                    "text=Get Started",
                    'button:has-text("Log")',
                    'button:has-text("Sign")',
                    'a:has-text("Log")'
                ]

                clicked = False
                for selector in login_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            await element.click()
                            print(f"  ✓ Clicked login button (selector: {selector})")
                            clicked = True
                            break
                    except:
                        continue

                if not clicked:
                    print("  ⚠️ Login button not found, checking if already on login page...")

                await page.wait_for_load_state("networkidle")
                await page.screenshot(path="groq_step2.png")

            except Exception as e:
                print(f"  ⚠️ Error finding login: {e}")
                await page.screenshot(path="groq_error.png")

            # Step 3: Look for Google Sign In
            print("\n🔍 Looking for Google Sign In...")
            try:
                google_selectors = [
                    "text=Sign in with Google",
                    "text=Continue with Google",
                    'button:has-text("Google")',
                    '[aria-label*="Google"]',
                    'text=Google'
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

                await page.screenshot(path="groq_step3.png")

            except Exception as e:
                print(f"  ⚠️ Error finding Google signin: {e}")

            # Step 4: After login, navigate to API keys
            print("\n🔑 Navigating to API keys page...")
            try:
                await page.goto("https://console.groq.com/keys", timeout=30000)
                await page.wait_for_load_state("networkidle")
                await page.screenshot(path="groq_keys.png")

                # Look for Create API Key button
                print("\n🔍 Looking for Create API Key button...")
                create_selectors = [
                    "text=Create API Key",
                    "text=New API Key",
                    'button:has-text("Create")',
                    'button:has-text("New Key")'
                ]

                for selector in create_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            await element.click()
                            print("  ✓ Clicked create API key button")
                            await asyncio.sleep(2)
                            break
                    except:
                        continue

                # Look for key name input
                print("\n📝 Entering key name...")
                try:
                    name_input = page.locator('input[placeholder*="name" i], input[type="text"]').first
                    if await name_input.is_visible(timeout=2000):
                        await name_input.fill("WeedGo Test")
                        print("  ✓ Entered key name: WeedGo Test")

                        # Click submit/create
                        submit_selectors = [
                            "text=Submit",
                            "text=Create",
                            'button[type="submit"]'
                        ]

                        for selector in submit_selectors:
                            try:
                                element = page.locator(selector).first
                                if await element.is_visible(timeout=2000):
                                    await element.click()
                                    print("  ✓ Clicked submit")
                                    await asyncio.sleep(2)
                                    break
                            except:
                                continue

                except:
                    pass

                await page.screenshot(path="groq_keys_created.png")

                # Try to extract key
                print("\n🔍 Looking for API key...")
                key_selectors = [
                    'text=/gsk_[a-zA-Z0-9]+/',
                    'code',
                    'pre',
                    'input[type="password"]',
                    'textarea'
                ]

                for selector in key_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            key = await element.inner_text()
                            if key and key.startswith('gsk_'):
                                print(f"\n✅ SUCCESS! Got API Key:")
                                print(f"  {key}")

                                # Save to file
                                with open("groq_key.txt", "w") as f:
                                    f.write(key)
                                print(f"\n💾 Saved to: groq_key.txt")

                                return key
                    except:
                        continue

                print("\n⚠️ Could not automatically extract key")
                print("  Please copy it manually from the browser")
                print("  The browser will stay open for 1 minute")
                await asyncio.sleep(60)

            except Exception as e:
                print(f"  ⚠️ Error accessing keys page: {e}")
                await page.screenshot(path="groq_keys_error.png")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await page.screenshot(path="groq_final_error.png")
            import traceback
            traceback.print_exc()

        finally:
            print("\n🔄 Closing browser...")
            await browser.close()

    return None


async def main():
    print("\n" + "="*80)
    print(" "*20 + "GROQ AUTOMATION")
    print(" "*15 + "Attempting automated signup")
    print("="*80)

    print("\n⚠️  NOTE: This script will:")
    print("  1. Open a browser window")
    print("  2. Navigate to Groq Console")
    print("  3. Require manual Google OAuth (cannot automate)")
    print("  4. Attempt to retrieve API key")

    # Skip interactive prompt for automation - check if running in terminal
    if sys.stdin.isatty():
        input("\n Press ENTER to start...")
    else:
        print("\n🤖 Running in automated mode...")
        await asyncio.sleep(2)

    api_key = await signup_groq()

    if api_key:
        print("\n" + "="*80)
        print("✅ SIGNUP COMPLETE!")
        print("="*80)
        print(f"\nYour Groq API key: {api_key}")
        print("\nTo use it, run:")
        print(f'  export GROQ_API_KEY="{api_key}"')
    else:
        print("\n" + "="*80)
        print("⚠️ MANUAL COMPLETION REQUIRED")
        print("="*80)
        print("\nPlease:")
        print("  1. Complete the signup manually")
        print("  2. Go to https://console.groq.com/keys")
        print("  3. Click 'Create API Key'")
        print("  4. Copy your API key")
        print("  5. Run: export GROQ_API_KEY='your_key'")


if __name__ == "__main__":
    asyncio.run(main())
