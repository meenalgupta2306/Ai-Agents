"""
Frame Capture Service
Captures frames during automation based on scene structure
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from playwright.async_api import Page, async_playwright
from ..models import SceneStructure, Scene, SceneType, FrameSequence


class FrameCaptureService:
    """Captures frames during drag-and-drop automation"""
    
    def __init__(self, documents_dir: str):
        """Initialize frame capture service"""
        self.documents_dir = Path(documents_dir)
    
    async def capture_automation_with_frames(
        self,
        scene_structure: SceneStructure,
        session_id: str,
        url: str = None,
        use_existing_browser: bool = True,
        cdp_url: str = "http://localhost:9222"
    ) -> List[FrameSequence]:
        """
        Run automation and capture frames for each scene
        
        Args:
            url: URL to navigate to
            scene_structure: Scene structure with timing info
            session_id: Content generation session ID
            use_existing_browser: Whether to connect to existing browser
            cdp_url: Chrome DevTools Protocol URL
            
        Returns:
            List of FrameSequence objects
        """
        frame_sequences = []
        
        async with async_playwright() as p:
            browser = None
            page = None
            
            # Connect to browser
            if use_existing_browser:
                try:
                    browser = await p.chromium.connect_over_cdp(cdp_url)
                    contexts = browser.contexts
                    print(f"Found {len(contexts)} browser contexts")
                    
                    # Find first context with pages
                    context = None
                    page = None
                    
                    for i, ctx in enumerate(contexts):
                        print(f"Context {i} has {len(ctx.pages)} pages: {[p.url for p in ctx.pages]}")
                        if ctx.pages and not page:
                            context = ctx
                            page = ctx.pages[0]
                            print(f"Using Context {i}, Page: {page.url}")
                    
                    if not page:
                        if contexts:
                            context = contexts[0]
                            page = await context.new_page()
                            print("Created new page in first context (no existing pages found)")
                        else:
                            print("No contexts found, cannot create page")
                            browser = None
                except Exception as e:
                    print(f"Could not connect to existing browser: {e}")
                    raise Exception(f"Failed to connect to existing browser at {cdp_url}: {e}")
            
            # Launch new browser only if NOT using existing one
            if browser is None and not use_existing_browser:
                browser = await p.chromium.launch(headless=False, slow_mo=500)
                page = await browser.new_page()
            elif browser is None:
                # Should have been raised above, but just in case
                raise Exception("Browser connection failed")
            
            try:
                # Navigate to URL only if not using existing browser or if URL different
                current_url = page.url
                if not use_existing_browser or (url and url not in current_url):
                    print(f"Navigating to {url}")
                    await page.goto(url, wait_until='networkidle')
                    await page.wait_for_timeout(2000)
                else:
                    print(f"Using existing page: {current_url}")
                
                # PREPARE PAGE: Edit -> Hide Config -> Reset
                await self._prepare_page(page)
                
                # Process each scene
                for scene in scene_structure.scenes:
                    if scene.type == SceneType.INTRO or scene.type == SceneType.CONCLUSION:
                        # Static scene - single frame
                        frame_seq = await self._capture_static_scene(page, scene, session_id)
                    else:
                        # Action scene - multiple frames
                        frame_seq = await self._capture_action_scene(page, scene, session_id)
                    
                    frame_sequences.append(frame_seq)
                
                return frame_sequences
                
            finally:
                if page and not use_existing_browser:
                    await page.close()
                if browser and not use_existing_browser:
                    await browser.close()
    
    async def _prepare_page(self, page: Page):
        """Prepare page for recording: Click Edit -> Hide config -> Reset"""
        print("Preparing page...")
        
        if 'question-bank' in page.url:
            print("On question bank list, looking for Edit button...")
            
            # 1. Click Edit Button (using dnd_test selectors)
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
                    if edit_button and await edit_button.is_visible():
                        print(f"Found edit button: {selector}")
                        await edit_button.click()
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            if not edit_button:
                # If we couldn't find it, maybe we are already in editor?
                print("Could not find edit button, assuming already in editor or failed.")
        
        # 2. Click Hide Config (using dnd_test selectors)
        hide_config_selectors = [
            'button:has-text("Hide Config")',
            'button:has-text("hide config")',
            'button[aria-label*="hide config" i]',
            '.hide-config-button',
        ]
        
        hide_btn = None
        for selector in hide_config_selectors:
            try:
                hide_btn = await page.wait_for_selector(selector, timeout=3000)
                if hide_btn and await hide_btn.is_visible():
                    print(f"Found Hide Config button: {selector}")
                    await hide_btn.click()
                    await page.wait_for_timeout(1000)
                    break
            except:
                continue

        # 3. Click Reset (using dnd_test selectors)
        reset_selectors = [
            'button:has-text("Reset")',
            'button:has-text("reset")',
            'button[aria-label*="reset" i]',
            '.reset-button',
            '[data-action="reset"]',
        ]
        
        reset_btn = None
        for selector in reset_selectors:
            try:
                reset_btn = await page.wait_for_selector(selector, timeout=3000)
                if reset_btn and await reset_btn.is_visible():
                    print(f"Found Reset button: {selector}")
                    await reset_btn.click()
                    await page.wait_for_timeout(2000)
                    break
            except:
                continue


    async def _capture_static_scene(
        self,
        page: Page,
        scene: Scene,
        session_id: str
    ) -> FrameSequence:
        """Capture single frame for static scene"""
        
        # Create scene directory
        scene_dir = self.documents_dir / 'content_generation' / session_id / 'frames' / scene.id
        scene_dir.mkdir(parents=True, exist_ok=True)
        
        # Capture single frame
        frame_path = scene_dir / 'frame_000.png'
        await page.screenshot(path=str(frame_path), full_page=False)
        
        return FrameSequence(
            scene_id=scene.id,
            frame_dir=str(scene_dir),
            frame_count=1,
            fps=1,  # Doesn't matter for static
            duration=scene.duration
        )
    
    async def _capture_action_scene(
        self,
        page: Page,
        scene: Scene,
        session_id: str
    ) -> FrameSequence:
        """Capture frames for action scene with drag operation"""
        
        # Create scene directory
        scene_dir = self.documents_dir / 'content_generation' / session_id / 'frames' / scene.id
        scene_dir.mkdir(parents=True, exist_ok=True)
        
        if not scene.action or not scene.timing:
            raise ValueError(f"Action scene {scene.id} missing action or timing info")
            
        item_id = scene.action.item_id
        zone_id = scene.action.zone_id
        
        # Find elements using robust selectors (matching dnd_test)
        item_element, item_selector = await self._find_element(page, item_id, 'item')
        if not item_element:
             # Debug info
            title = await page.title()
            url = page.url
            ids = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('[data-id], .draggable-item')).map(el => el.getAttribute('data-id') || el.id).slice(0, 100);
            }''')
            
            error_path = self.documents_dir / 'content_generation' / session_id / 'error_screenshot.png'
            await page.screenshot(path=str(error_path))
            
            error_msg = f"Could not find item '{item_id}'. Page: {title} ({url}). IDs found: {ids}"
            print(error_msg)
            raise Exception(error_msg)

        zone_element, zone_selector = await self._find_element(page, zone_id, 'zone')
        if not zone_element:
            raise Exception(f"Could not find zone '{zone_id}'")
            
        print(f"Found item {item_id} using {item_selector}")
        print(f"Found zone {zone_id} using {zone_selector}")
        
        # 1. PRE-ACTION: Capture before drag
        # Wait for pre-action duration to let audio play/viewer see initial state
        # We capture ONE frame but wait the duration
        pre_frame_path = scene_dir / 'pre_action.png'
        await page.screenshot(path=str(pre_frame_path), full_page=False)
        
        if scene.timing and scene.timing.pre_action > 0:
            print(f"Waiting pre-action: {scene.timing.pre_action}s")
            await page.wait_for_timeout(scene.timing.pre_action * 1000)
        
        # 2. PERFORM DRAG WITH FRAME CAPTURE
        
        # Get element positions (re-query to ensure freshness)
        item = await page.query_selector(item_selector)
        zone = await page.query_selector(zone_selector)
        
        item_box = await item.bounding_box()
        zone_box = await zone.bounding_box()
        
        if not item_box or not zone_box:
            raise ValueError(f"Could not get bounding boxes for {item_id} or {zone_id}")
        
        # Calculate positions
        item_x = item_box['x'] + item_box['width'] / 2
        item_y = item_box['y'] + item_box['height'] / 2
        zone_x = zone_box['x'] + zone_box['width'] / 2
        zone_y = zone_box['y'] + zone_box['height'] / 2
        
        # Start drag
        await page.mouse.move(item_x, item_y)
        await page.wait_for_timeout(100)
        await page.mouse.down()
        await page.wait_for_timeout(200)
        
        # Move slightly to initiate drag
        await page.mouse.move(item_x + 5, item_y + 5)
        await page.wait_for_timeout(100)
        
        # Capture frames during drag (10 FPS)
        action_duration = scene.timing.action
        num_frames = int(action_duration * 10)  # 10 FPS
        steps = max(10, num_frames)  # At least 10 steps for smooth animation
        
        for i in range(num_frames):
            # Calculate intermediate position
            progress = (i + 1) / steps
            current_x = item_x + (zone_x - item_x) * progress
            current_y = item_y + (zone_y - item_y) * progress
            
            # Move mouse
            await page.mouse.move(current_x, current_y)
            
            # Capture frame
            frame_path = scene_dir / f'drag_{i:03d}.png'
            await page.screenshot(path=str(frame_path), full_page=False)
            
            # Wait for next frame (100ms = 10 FPS)
            await page.wait_for_timeout(100)
        
        # Complete drag
        await page.mouse.move(zone_x, zone_y)
        await page.mouse.up()
        await page.wait_for_timeout(500)  # Wait for UI to update
        
        # 3. POST-ACTION: Capture after drag
        post_frame_path = scene_dir / 'post_action.png'
        await page.screenshot(path=str(post_frame_path), full_page=False)
        
        # Calculate total frames
        total_frames = 1 + num_frames + 1  # pre + drag + post
        
        return FrameSequence(
            scene_id=scene.id,
            frame_dir=str(scene_dir),
            frame_count=total_frames,
            fps=10,
            duration=scene.duration
        )

    async def _find_element(self, page: Page, element_id: str, element_type: str):
        """Find element using multiple selectors (borrowed from dnd_test)"""
        selectors = []
        if element_type == 'item':
            selectors = [
                f'[data-id="{element_id}"]',
                f'[data-item-id="{element_id}"]', # My custom one
                f'#{element_id}',
                f'[id="{element_id}"]',
                f'.draggable-item[data-id="{element_id}"]',
                f'.draggable[data-id="{element_id}"]',
            ]
        else: # zone
            selectors = [
                f'[data-id="{element_id}"]',
                f'[data-zone-id="{element_id}"]', # My custom one
                f'#{element_id}',
                f'[id="{element_id}"]',
                f'.dropzone[data-id="{element_id}"]',
                f'.drop-zone[data-id="{element_id}"]',
            ]
            
        for selector in selectors:
            try:
                if await page.locator(selector).count() > 0:
                    # Wait for it to be visible
                    await page.wait_for_selector(selector, state='visible', timeout=1000)
                    return await page.query_selector(selector), selector
            except:
                continue
                
        return None, None
