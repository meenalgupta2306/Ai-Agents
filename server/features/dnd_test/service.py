"""Drag and Drop Test Automation Service"""
import json
import os
import asyncio
from playwright.async_api import async_playwright, Page
from typing import Dict, List, Any


class DndTestService:
    def __init__(self, config_path: str = None):
        """Initialize the DnD test service"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        self.config_path = config_path
        self.config = None
        self.progress_callback = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            self.config = data.get('config', {})
        return self.config
    
    def set_progress_callback(self, callback):
        """Set callback function for progress updates"""
        self.progress_callback = callback
        
    async def _update_progress(self, message: str, status: str = "info"):
        """Send progress update"""
        if self.progress_callback:
            await self.progress_callback({"message": message, "status": status})
        print(f"[{status.upper()}] {message}")
    
    async def run_test(self, url: str, use_existing_browser: bool = True, cdp_url: str = None) -> Dict[str, Any]:
        """
        Run the drag and drop automation test
        
        Args:
            url: The URL to navigate to (question bank URL)
            use_existing_browser: If True, try to connect to existing Chrome instance
            cdp_url: Chrome DevTools Protocol URL (default: http://localhost:9222)
            
        Returns:
            Dict with test results
        """
        # Load config
        await self._update_progress("Loading configuration...", "info")
        self.load_config()
        
        draggable_items = self.config.get('draggableItems', {}).get('items', [])
        dropzones = self.config.get('dropzones', {}).get('zones', [])
        
        await self._update_progress(f"Config loaded: {len(draggable_items)} draggable items, {len(dropzones)} drop zones", "success")
        
        results = {
            "success": False,
            "total_operations": 0,
            "completed_operations": 0,
            "errors": []
        }
        
        async with async_playwright() as p:
            browser = None
            page = None
            
            # Try to connect to existing browser first
            if use_existing_browser:
                try:
                    if cdp_url is None:
                        cdp_url = "http://localhost:9222"
                    
                    await self._update_progress(f"Connecting to existing Chrome at {cdp_url}...", "info")
                    browser = await p.chromium.connect_over_cdp(cdp_url)
                    
                    # Get the first context (existing browser context with your auth)
                    contexts = browser.contexts
                    if contexts:
                        context = contexts[0]
                        # Create new page in existing context (keeps your auth)
                        page = await context.new_page()
                        await self._update_progress("✓ Connected to existing Chrome! Using your authenticated session.", "success")
                    else:
                        raise Exception("No browser contexts found")
                        
                except Exception as e:
                    await self._update_progress(
                        f"Could not connect to existing Chrome: {str(e)}", 
                        "warning"
                    )
                    await self._update_progress(
                        "💡 To use existing browser: Close Chrome, then run: google-chrome --remote-debugging-port=9222",
                        "info"
                    )
                    browser = None
            
            # Fallback: Launch new browser
            if browser is None:
                await self._update_progress("Launching new Chrome instance...", "info")
                browser = await p.chromium.launch(headless=False, slow_mo=500)
                page = await browser.new_page()
                await self._update_progress("⚠ New browser launched (no authentication)", "warning")
            
            try:
                # Navigate to URL
                await self._update_progress(f"Navigating to {url}...", "info")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await self._update_progress("Page loaded successfully", "success")
                
                # Wait a bit for the page to fully render
                await page.wait_for_timeout(2000)
                
                # Click first question's edit button
                await self._update_progress("Looking for first question edit button...", "info")
                
                # Try multiple possible selectors for edit button
                edit_selectors = [
                    'button:has-text("Edit")',
                    'button[aria-label*="edit" i]',
                    'button[title*="edit" i]',
                    '.edit-button',
                    '[data-action="edit"]',
                    'tr:first-child button',  # First row button
                    'tbody tr:first-child button:last-child',  # Last button in first row
                ]
                
                edit_button = None
                for selector in edit_selectors:
                    try:
                        edit_button = await page.wait_for_selector(selector, timeout=3000)
                        if edit_button:
                            await self._update_progress(f"Found edit button with selector: {selector}", "success")
                            break
                    except:
                        continue
                
                if not edit_button:
                    raise Exception("Could not find edit button. Please check the page structure.")
                
                await edit_button.click()
                await self._update_progress("Clicked edit button", "success")
                await page.wait_for_timeout(2000)
                
                # Click reset button
                await self._update_progress("Looking for reset button...", "info")
                
                reset_selectors = [
                    'button:has-text("Reset")',
                    'button:has-text("reset")',
                    'button[aria-label*="reset" i]',
                    '.reset-button',
                    '[data-action="reset"]',
                ]
                
                reset_button = None
                for selector in reset_selectors:
                    try:
                        reset_button = await page.wait_for_selector(selector, timeout=3000)
                        if reset_button:
                            await self._update_progress(f"Found reset button with selector: {selector}", "success")
                            break
                    except:
                        continue
                
                if not reset_button:
                    raise Exception("Could not find reset button. Please check the page structure.")
                
                await reset_button.click()
                await self._update_progress("Clicked reset button", "success")
                await page.wait_for_timeout(2000)
                
                # Click Hide Config button
                await self._update_progress("Looking for Hide Config button...", "info")
                
                hide_config_selectors = [
                    'button:has-text("Hide Config")',
                    'button:has-text("hide config")',
                    'button[aria-label*="hide config" i]',
                    '.hide-config-button',
                ]
                
                hide_config_button = None
                for selector in hide_config_selectors:
                    try:
                        hide_config_button = await page.wait_for_selector(selector, timeout=3000)
                        if hide_config_button:
                            await self._update_progress(f"Found Hide Config button with selector: {selector}", "success")
                            break
                    except:
                        continue
                
                if hide_config_button:
                    await hide_config_button.click()
                    await self._update_progress("Clicked Hide Config button", "success")
                    await page.wait_for_timeout(1000)
                else:
                    await self._update_progress("Hide Config button not found, continuing...", "warning")
                
                # Now perform drag and drop operations
                await self._update_progress("Starting drag and drop operations...", "info")
                
                # Count total operations
                total_ops = sum(len(zone.get('draggableItems', [])) for zone in dropzones)
                results["total_operations"] = total_ops
                
                completed = 0
                
                # For each dropzone, drag the specified items
                for zone in dropzones:
                    zone_id = zone.get('id')
                    zone_items = zone.get('draggableItems', [])
                    
                    for item_to_drag in zone_items:
                        item_id = item_to_drag.get('id')
                        
                        try:
                            await self._update_progress(
                                f"Dragging item '{item_id}' to zone '{zone_id}' ({completed + 1}/{total_ops})", 
                                "info"
                            )
                            
                            # Find draggable item - try multiple selector strategies
                            draggable_selectors = [
                                f'[data-id="{item_id}"]',
                                f'#{item_id}',
                                f'[id="{item_id}"]',
                                f'.draggable-item[data-id="{item_id}"]',
                                f'.draggable[data-id="{item_id}"]',
                            ]
                            
                            draggable_selector = None
                            for selector in draggable_selectors:
                                try:
                                    if await page.locator(selector).count() > 0:
                                        draggable_selector = selector
                                        break
                                except:
                                    continue
                            
                            if not draggable_selector:
                                raise Exception(f"Could not find draggable item with id: {item_id}")
                            
                            # Find dropzone - try multiple selector strategies
                            dropzone_selectors = [
                                f'[data-id="{zone_id}"]',
                                f'#{zone_id}',
                                f'[id="{zone_id}"]',
                                f'.dropzone[data-id="{zone_id}"]',
                                f'.drop-zone[data-id="{zone_id}"]',
                            ]
                            
                            dropzone_selector = None
                            for selector in dropzone_selectors:
                                try:
                                    if await page.locator(selector).count() > 0:
                                        dropzone_selector = selector
                                        break
                                except:
                                    continue
                            
                            if not dropzone_selector:
                                raise Exception(f"Could not find dropzone with id: {zone_id}")
                            
                            # Get bounding boxes for manual drag
                            draggable_box = await page.locator(draggable_selector).bounding_box()
                            dropzone_box = await page.locator(dropzone_selector).bounding_box()
                            
                            if not draggable_box or not dropzone_box:
                                raise Exception(f"Could not get bounding boxes for drag operation")
                            
                            # Calculate center points
                            drag_x = draggable_box['x'] + draggable_box['width'] / 2
                            drag_y = draggable_box['y'] + draggable_box['height'] / 2
                            drop_x = dropzone_box['x'] + dropzone_box['width'] / 2
                            drop_y = dropzone_box['y'] + dropzone_box['height'] / 2
                            
                            # Perform manual drag and drop using mouse events (for Angular CDK compatibility)
                            # This sequence triggers the proper Angular CDK events
                            
                            # 1. Move to draggable item
                            await page.mouse.move(drag_x, drag_y)
                            await page.wait_for_timeout(100)
                            
                            # 2. Mouse down (start drag)
                            await page.mouse.down()
                            await page.wait_for_timeout(200)
                            
                            # 3. Move slightly to initiate drag (Angular CDK needs this)
                            await page.mouse.move(drag_x + 5, drag_y + 5)
                            await page.wait_for_timeout(100)
                            
                            # 4. Move to drop zone in steps (smoother animation)
                            steps = 10
                            for i in range(1, steps + 1):
                                intermediate_x = drag_x + (drop_x - drag_x) * (i / steps)
                                intermediate_y = drag_y + (drop_y - drag_y) * (i / steps)
                                await page.mouse.move(intermediate_x, intermediate_y)
                                await page.wait_for_timeout(20)
                            
                            # 5. Mouse up (drop)
                            await page.mouse.up()
                            await page.wait_for_timeout(500)  # Wait for UI to update
                            
                            completed += 1
                            results["completed_operations"] = completed
                            
                            await self._update_progress(
                                f"✓ Successfully dragged '{item_id}' to '{zone_id}'", 
                                "success"
                            )
                            
                        except Exception as e:
                            error_msg = f"Error dragging '{item_id}' to '{zone_id}': {str(e)}"
                            await self._update_progress(error_msg, "error")
                            results["errors"].append(error_msg)
                
                # Final results
                if completed == total_ops:
                    results["success"] = True
                    await self._update_progress(
                        f"✓ Test completed successfully! {completed}/{total_ops} operations completed", 
                        "success"
                    )
                else:
                    await self._update_progress(
                        f"Test completed with errors: {completed}/{total_ops} operations completed", 
                        "warning"
                    )
                
                # Keep browser open for 5 seconds so user can see the result
                await self._update_progress("Keeping browser open for 5 seconds...", "info")
                await page.wait_for_timeout(5000)
                
            except Exception as e:
                error_msg = f"Test failed: {str(e)}"
                await self._update_progress(error_msg, "error")
                results["errors"].append(error_msg)
                
                # Take screenshot on error
                try:
                    import os
                    documents_dir = os.getenv('DOCUMENTS_DIR', os.path.join(os.path.dirname(__file__), '../../documents'))
                    os.makedirs(documents_dir, exist_ok=True)
                    
                    # Clean up old test screenshots
                    for file in os.listdir(documents_dir):
                        if file.startswith('dnd_test_') and file.endswith('.png'):
                            try:
                                os.remove(os.path.join(documents_dir, file))
                            except:
                                pass
                    
                    screenshot_path = os.path.join(documents_dir, "dnd_test_error.png")
                    await page.screenshot(path=screenshot_path)
                    await self._update_progress(f"Screenshot saved to {screenshot_path}", "info")
                    results["screenshot"] = screenshot_path
                except Exception as e:
                    await self._update_progress(f"Could not save screenshot: {str(e)}", "warning")
            
            finally:
                await browser.close()
                await self._update_progress("Browser closed", "info")
        
        return results
