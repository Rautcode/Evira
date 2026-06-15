"""Tests for real-time data flow between components."""

import asyncio
import websockets
import json
import unittest
from datetime import datetime
import aiohttp

class TestRealTimeDataFlow(unittest.TestCase):
    """Test suite for real-time data flow."""
    
    async def test_dashboard_api(self):
        """Test dashboard API endpoints."""
        async with aiohttp.ClientSession() as session:
            # Test dashboard stats endpoint
            async with session.get("http://localhost:8000/dashboard/stats") as resp:
                self.assertEqual(resp.status, 200)
                data = await resp.json()
                
                # Validate structure
                self.assertIn("system_status", data)
                self.assertIn("reports", data)
                self.assertIn("scheduler", data)
                self.assertIn("recent_activity", data)
                self.assertIn("last_updated", data)

    async def test_wincc_websocket(self):
        """Test WinCC WebSocket connection."""
        uri = "ws://localhost:8000/ws/wincc"
        async with websockets.connect(uri) as websocket:
            # Wait for first message
            response = await websocket.recv()
            data = json.loads(response)
            
            # Validate structure
            self.assertEqual(data["type"], "wincc_update")
            self.assertIn("connected", data["data"])
            self.assertIn("total_tags", data["data"])
            self.assertIn("active_tags", data["data"])

    async def test_activity_websocket(self):
        """Test activity log WebSocket connection."""
        uri = "ws://localhost:8000/ws/activity"
        async with websockets.connect(uri) as websocket:
            # Send test event
            await websocket.send("ping")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            # Validate structure
            self.assertEqual(data["type"], "activity_update")
            self.assertIsInstance(data["data"], list)

def run_tests():
    """Run all tests."""
    unittest.main()

if __name__ == "__main__":
    run_tests()
