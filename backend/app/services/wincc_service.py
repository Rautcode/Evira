"""Service for interfacing with WinCC OA system via OPC UA."""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from asyncua import Client
from app.utils.db import add_activity_log, get_db_connection
from app.utils.config_manager import config_manager

logger = logging.getLogger(__name__)

class OPCSubHandler:
    """Subscription Handler for OPC UA Data Change Notifications."""
    
    def __init__(self, monitor):
        self.monitor = monitor

    def datachange_notification(self, node, val, data):
        """Callback received from OPC UA Server when a tag value changes."""
        asyncio.create_task(self.monitor.handle_tag_change(node, val, data))

class WinCCMonitor:
    """Monitors WinCC OA system via OPC UA and provides real-time tag updates and logging."""
    
    def __init__(self):
        self._connected = False
        self._active_tags = 0
        self._total_tags = 0
        self._last_update = None
        self._monitor_task = None
        self.client = None
        self.subscription = None
        
        self.load_config()
        
        # Store auto-discovered tags: {"node": Node, "id": str, "display_name": str, "machine_id": str, "parameter": str, "unit": str}
        self.discovered_nodes = []

    def load_config(self):
        """Load connection settings dynamically."""
        config = config_manager.load_config()
        self.server_url = config.get("opcua_url", os.getenv("OPC_UA_SERVER_URL", "opc.tcp://localhost:4840/freeopcua/server/"))
        self.username = config.get("opcua_username", os.getenv("OPC_UA_USERNAME"))
        self.password = config.get("opcua_password", os.getenv("OPC_UA_PASSWORD"))

    async def start(self):
        """Start the WinCC monitoring background task."""
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("WinCC OPC UA monitoring service started")

    async def stop(self):
        """Stop the WinCC monitoring background task."""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            self._connected = False
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            logger.info("WinCC OPC UA monitoring service stopped")

    async def reconnect(self):
        """Cleanly tear down the existing connection and start a new one with updated config."""
        logger.info("Hot-reloading WinCC OPC UA connection...")
        await self.stop()
        self.load_config()
        await self.start()

    async def _connect(self):
        """Establish client connection to the WinCC OPC UA Server."""
        try:
            logger.info(f"Connecting to OPC UA Server at {self.server_url}...")
            self.client = Client(self.server_url)
            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)
            
            await self.client.connect()
            self._connected = True
            logger.info("OPC UA Connection established successfully!")
            
            await self._log_event(
                "connection",
                "Connected to Siemens WinCC OPC UA Server",
                "success"
            )
            
            # Start tag auto-discovery
            await self._auto_discover_tags()
            
            # Start subscription
            await self._subscribe_tags()
            
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA Server: {e}")
            self._connected = False
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            await self._log_event(
                "connection_error",
                f"Failed to connect to OPC UA Server: {str(e)}",
                "error"
            )

    async def _auto_discover_tags(self):
        """Recursively browse OPC UA server to auto-discover SCADA tags and map to machines."""
        try:
            logger.info("Starting OPC UA Node Auto-Discovery...")
            root = self.client.get_objects_node()
            discovered = []
            
            async def browse_recursive(node):
                try:
                    children = await node.get_children()
                    for child in children:
                        node_class = await child.read_node_class()
                        if node_class.name == "Variable":
                            display_name_obj = await child.read_display_name()
                            display_name = display_name_obj.Text if display_name_obj else ""
                            node_id_str = str(child.nodeid)
                            
                            # Match using heuristics
                            machine_id = self._match_machine(display_name, node_id_str)
                            param_info = self._match_parameter(display_name, node_id_str)
                            
                            if machine_id and param_info:
                                discovered.append({
                                    "node": child,
                                    "id": node_id_str,
                                    "display_name": display_name,
                                    "machine_id": machine_id,
                                    "parameter": param_info["parameter"],
                                    "unit": param_info["unit"]
                                })
                        elif node_class.name == "Object":
                            await browse_recursive(child)
                except Exception as e:
                    logger.debug(f"Error browsing node: {e}")
            
            await browse_recursive(root)
            self.discovered_nodes = discovered
            self._total_tags = len(discovered)
            self._active_tags = len(discovered)
            self._last_update = datetime.now()
            logger.info(f"Discovered {len(discovered)} SCADA tags on OPC UA Server.")
            
            # Sync discovered tags to database wincc_tags
            await self._sync_discovered_tags_to_db()
            
        except Exception as e:
            logger.error(f"Error during tag auto-discovery: {e}")

    def _match_machine(self, display_name: str, node_id: str) -> Optional[str]:
        """Heuristics to map OPC UA tags to machine IDs based on names."""
        text = (display_name + " " + node_id).lower()
        if "extruder" in text or "m001" in text:
            return "M001"
        if "molding" in text or "m002" in text:
            return "M002"
        if "cooling" in text or "chiller" in text or "m003" in text:
            return "M003"
        if "packaging" in text or "m004" in text:
            return "M004"
        if "mixer" in text or "blending" in text or "m005" in text:
            return "M005"
        return None

    def _match_parameter(self, display_name: str, node_id: str) -> Optional[dict]:
        """Heuristics to map OPC UA tags to report parameter variables and units."""
        text = (display_name + " " + node_id).lower()
        if "temp" in text or "temperature" in text:
            return {"parameter": "Temperature", "unit": "C"}
        if "press" in text or "pressure" in text:
            return {"parameter": "Pressure", "unit": "bar"}
        if "speed" in text or "rpm" in text:
            return {"parameter": "Speed", "unit": "RPM"}
        if "force" in text or "clamp" in text:
            return {"parameter": "Clamping Force", "unit": "kN"}
        if "time" in text or "cycle" in text:
            return {"parameter": "Cycle Time", "unit": "s"}
        if "flow" in text:
            return {"parameter": "Flow Rate", "unit": "L/min"}
        if "count" in text or "pack" in text:
            return {"parameter": "Pack Count", "unit": "pcs"}
        if "error" in text:
            return {"parameter": "Error Rate", "unit": "%"}
        return None

    async def _sync_discovered_tags_to_db(self):
        """Insert or update discovered tags in the database wincc_tags table."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for tag in self.discovered_nodes:
                    cursor.execute("SELECT COUNT(*) FROM wincc_tags WHERE tag_name = ?", (tag["id"],))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO wincc_tags (tag_name, tag_type, description, machine_id, active)
                            VALUES (?, ?, ?, ?, 1)
                        """, (tag["id"], tag["parameter"], f"Auto-discovered: {tag['display_name']}", tag["machine_id"]))
                conn.commit()
                cursor.close()
            logger.info("Synced auto-discovered SCADA tags to wincc_tags table.")
        except Exception as e:
            logger.error(f"Failed to sync tags to database: {e}")

    async def _subscribe_tags(self):
        """Subscribe to live data changes for all auto-discovered nodes."""
        try:
            if not self.client or not self.discovered_nodes:
                return
            handler = OPCSubHandler(self)
            self.subscription = await self.client.create_subscription(500, handler)
            
            nodes_to_subscribe = [tag["node"] for tag in self.discovered_nodes]
            await self.subscription.subscribe_data_change(nodes_to_subscribe)
            logger.info(f"OPC UA subscription setup complete for {len(nodes_to_subscribe)} tags.")
        except Exception as e:
            logger.error(f"Failed to setup OPC UA subscription: {e}")

    async def handle_tag_change(self, node, val, data):
        """Process real-time OPC UA tag change notifications."""
        node_id_str = str(node.nodeid)
        tag_info = next((t for t in self.discovered_nodes if t["id"] == node_id_str), None)
        if not tag_info:
            return
            
        self._last_update = datetime.now()
        
        # 1. Update tag values table
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE wincc_tags
                    SET value = ?, quality = 'Good', last_update = GETDATE()
                    WHERE tag_name = ?
                """, (float(val), node_id_str))
                conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"DB tag update failed: {e}")

        # 2. Append telemetry log snapshots for reporting
        try:
            hour = datetime.now().hour
            if 6 <= hour < 14:
                shift = "Morning"
            elif 14 <= hour < 22:
                shift = "Evening"
            else:
                shift = "Night"
                
            status = "Normal"
            if tag_info["parameter"] == "Temperature" and (val > 220 or val < 180):
                status = "Warning"
            elif tag_info["parameter"] == "Pressure" and (val > 120 or val < 80):
                status = "Warning"

            with get_db_connection() as conn:
                cursor = conn.cursor()
                # Insert logs for all report types
                for report_type in ['production_summary', 'downtime_analysis', 'quality_metrics']:
                    cursor.execute("""
                        INSERT INTO logs (machine_id, shift, timestamp, report_type, parameter, value, unit, status)
                        VALUES (?, ?, GETDATE(), ?, ?, ?, ?, ?)
                    """, (tag_info["machine_id"], shift, report_type, tag_info["parameter"], float(val), tag_info["unit"], status))
                conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"DB telemetry logging failed: {e}")

        # 3. Broadcast to frontend WebSockets
        try:
            from app.core.websocket import manager
            await manager.broadcast_wincc_update({
                "connected": True,
                "total_tags": self._total_tags,
                "active_tags": self._active_tags,
                "last_update": self._last_update.isoformat(),
                "tag_event": {
                    "node_id": node_id_str,
                    "parameter": tag_info["parameter"],
                    "value": float(val),
                    "machine_id": tag_info["machine_id"]
                }
            })
        except Exception:
            pass

    async def _monitor_loop(self):
        """Resilient background thread loop for managing OPC UA connection and recovery."""
        while True:
            try:
                if not self._connected:
                    await self._connect()
                
                # Check server connection health status
                if self._connected and self.client:
                    try:
                        # Call check server time to verify server heartbeat
                        await self.client.get_node("i=2258").read_value()
                    except Exception:
                        logger.warning("OPC UA Server heartbeat lost. Disconnecting and starting recovery loop.")
                        self._connected = False
                        if self.client:
                            try:
                                await self.client.disconnect()
                            except:
                                pass
                            self.client = None
                        await self._log_event(
                            "disconnection",
                            "Disconnected from WinCC OPC UA Server (Heartbeat Lost)",
                            "warning"
                        )
                
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WinCC monitor loop: {e}")
                await asyncio.sleep(5)

    async def _log_event(self, event_type: str, description: str, severity: str):
        """Write SCADA monitor lifecycle events into activity log database."""
        try:
            add_activity_log(
                event_type=f"wincc_{event_type}",
                description=description,
                severity=severity,
                source="WinCCMonitor"
            )
        except Exception as e:
            logger.error(f"Failed to log WinCC lifecycle event: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get live WinCC status statistics."""
        return {
            "connected": self._connected,
            "total_tags": self._total_tags,
            "active_tags": self._active_tags,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "server_url": self.server_url
        }

# Global wincc_monitor instance
wincc_monitor = WinCCMonitor()
