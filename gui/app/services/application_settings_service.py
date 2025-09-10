"""
Application Settings Service

Manages application-level settings including logging, update checking,
diagnostics, performance tuning, and system configuration.
"""

import json
import logging
import os
import platform
import sys
import subprocess
from pathlib import Path
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Available logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class UpdateChannel(Enum):
    """Update channels"""
    STABLE = "stable"
    BETA = "beta"
    DEVELOPMENT = "development"


@dataclass
class LoggingSettings:
    """Logging configuration settings"""
    level: LogLevel = LogLevel.INFO
    enable_file_logging: bool = True
    log_file_path: str = ""
    max_log_file_size: int = 10  # MB
    max_log_files: int = 5
    enable_console_logging: bool = True
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class UpdateSettings:
    """Update checking settings"""
    auto_check_enabled: bool = True
    check_interval_hours: int = 24
    update_channel: UpdateChannel = UpdateChannel.STABLE
    last_check_time: str = ""
    notify_on_updates: bool = True
    auto_download: bool = False
    include_prereleases: bool = False


@dataclass
class PerformanceSettings:
    """Performance tuning settings"""
    max_memory_usage_mb: int = 2048
    max_cpu_threads: int = 0  # 0 = auto-detect
    enable_hardware_acceleration: bool = True
    cache_size_mb: int = 512
    enable_background_processing: bool = True
    max_concurrent_operations: int = 3
    process_priority: str = "normal"  # low, normal, high


@dataclass
class DiagnosticsSettings:
    """Diagnostic and telemetry settings"""
    enable_crash_reporting: bool = True
    enable_usage_analytics: bool = False
    enable_performance_monitoring: bool = True
    collect_system_info: bool = True
    send_diagnostic_data: bool = False
    diagnostic_level: str = "basic"  # basic, detailed, full


@dataclass
class SecuritySettings:
    """Security and privacy settings"""
    enable_secure_connections: bool = True
    verify_ssl_certificates: bool = True
    enable_local_encryption: bool = True
    clear_sensitive_data_on_exit: bool = False
    session_timeout_minutes: int = 60
    require_confirmation_for_sensitive_ops: bool = True


@dataclass
class ApplicationSettings:
    """Complete application settings"""
    logging: LoggingSettings
    updates: UpdateSettings
    performance: PerformanceSettings
    diagnostics: DiagnosticsSettings
    security: SecuritySettings
    version: str = "1.0"
    last_updated: str = ""


class ApplicationSettingsService:
    """Service for managing application-level settings
    
    Provides configuration management for logging, updates, performance,
    diagnostics, and other system-level application settings.
    """
    
    def __init__(self):
        """Initialize the application settings service"""
        self.config_dir = Path.home() / ".auto-grader"
        self.settings_file = self.config_dir / "app_settings.json"
        self.log_dir = self.config_dir / "logs"
        self.config_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        # Load current settings
        self.settings = self._load_settings()
        
        # Set up logging based on current settings
        self._configure_logging()
        
        # Update check task
        self._update_check_task = None
        
        # System information cache
        self._system_info_cache = None
        self._system_info_cache_time = None
    
    def get_settings(self) -> ApplicationSettings:
        """Get current application settings
        
        Returns:
            Current ApplicationSettings object
        """
        return self.settings
    
    def update_logging_settings(self, **updates) -> bool:
        """Update logging settings
        
        Args:
            **updates: Logging setting updates
            
        Returns:
            True if update was successful
        """
        try:
            logging_dict = asdict(self.settings.logging)
            
            for key, value in updates.items():
                if key in logging_dict:
                    if key == "level" and isinstance(value, str):
                        # Convert string to LogLevel enum
                        for level in LogLevel:
                            if level.value == value:
                                logging_dict[key] = level
                                break
                    else:
                        logging_dict[key] = value
            
            # Create new logging settings
            self.settings.logging = LoggingSettings(**logging_dict)
            
            # Reconfigure logging
            self._configure_logging()
            
            # Save settings
            return self._save_settings()
            
        except Exception as e:
            logger.error(f"Failed to update logging settings: {e}")
            return False
    
    def update_update_settings(self, **updates) -> bool:
        """Update update checking settings
        
        Args:
            **updates: Update setting updates
            
        Returns:
            True if update was successful
        """
        try:
            update_dict = asdict(self.settings.updates)
            
            for key, value in updates.items():
                if key in update_dict:
                    if key == "update_channel" and isinstance(value, str):
                        # Convert string to UpdateChannel enum
                        for channel in UpdateChannel:
                            if channel.value == value:
                                update_dict[key] = channel
                                break
                    else:
                        update_dict[key] = value
            
            self.settings.updates = UpdateSettings(**update_dict)
            return self._save_settings()
            
        except Exception as e:
            logger.error(f"Failed to update update settings: {e}")
            return False
    
    def update_performance_settings(self, **updates) -> bool:
        """Update performance settings
        
        Args:
            **updates: Performance setting updates
            
        Returns:
            True if update was successful
        """
        try:
            perf_dict = asdict(self.settings.performance)
            
            for key, value in updates.items():
                if key in perf_dict:
                    perf_dict[key] = value
            
            self.settings.performance = PerformanceSettings(**perf_dict)
            
            # Apply performance settings
            self._apply_performance_settings()
            
            return self._save_settings()
            
        except Exception as e:
            logger.error(f"Failed to update performance settings: {e}")
            return False
    
    def update_diagnostics_settings(self, **updates) -> bool:
        """Update diagnostics settings
        
        Args:
            **updates: Diagnostics setting updates
            
        Returns:
            True if update was successful
        """
        try:
            diag_dict = asdict(self.settings.diagnostics)
            
            for key, value in updates.items():
                if key in diag_dict:
                    diag_dict[key] = value
            
            self.settings.diagnostics = DiagnosticsSettings(**diag_dict)
            return self._save_settings()
            
        except Exception as e:
            logger.error(f"Failed to update diagnostics settings: {e}")
            return False
    
    def update_security_settings(self, **updates) -> bool:
        """Update security settings
        
        Args:
            **updates: Security setting updates
            
        Returns:
            True if update was successful
        """
        try:
            sec_dict = asdict(self.settings.security)
            
            for key, value in updates.items():
                if key in sec_dict:
                    sec_dict[key] = value
            
            self.settings.security = SecuritySettings(**sec_dict)
            return self._save_settings()
            
        except Exception as e:
            logger.error(f"Failed to update security settings: {e}")
            return False
    
    async def check_for_updates(self, force: bool = False) -> Dict[str, Any]:
        """Check for application updates
        
        Args:
            force: Force check even if recently checked
            
        Returns:
            Dictionary with update information
        """
        try:
            # Check if we should skip based on last check time
            if not force and self.settings.updates.last_check_time:
                last_check = datetime.fromisoformat(self.settings.updates.last_check_time)
                check_interval = timedelta(hours=self.settings.updates.check_interval_hours)
                
                if datetime.now() - last_check < check_interval:
                    return {
                        "update_available": False,
                        "message": "Check skipped - too recent",
                        "last_check": self.settings.updates.last_check_time
                    }
            
            # Simulate update check (in real implementation, this would check GitHub releases)
            await asyncio.sleep(1)  # Simulate network delay
            
            # Update last check time
            self.settings.updates.last_check_time = datetime.now().isoformat()
            self._save_settings()
            
            # Mock update check result
            current_version = "1.0.0"
            latest_version = "1.0.1"  # Mock newer version
            
            if latest_version > current_version:
                return {
                    "update_available": True,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "release_notes": "Bug fixes and performance improvements",
                    "download_url": "https://github.com/michael-borck/academic-auto-grader/releases/latest",
                    "release_date": "2024-01-15",
                    "size_mb": 45.2
                }
            else:
                return {
                    "update_available": False,
                    "current_version": current_version,
                    "message": "You are running the latest version"
                }
        
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return {
                "update_available": False,
                "error": str(e),
                "message": "Update check failed"
            }
    
    def get_system_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostic information
        
        Returns:
            Dictionary with diagnostic information
        """
        try:
            # Use cached info if recent (less than 5 minutes old)
            if (self._system_info_cache and self._system_info_cache_time and 
                datetime.now() - self._system_info_cache_time < timedelta(minutes=5)):
                return self._system_info_cache
            
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "application": self._get_application_info(),
                "system": self._get_system_info(),
                "performance": self._get_performance_info(),
                "network": self._get_network_info(),
                "storage": self._get_storage_info(),
                "environment": self._get_environment_info()
            }
            
            # Cache the results
            self._system_info_cache = diagnostics
            self._system_info_cache_time = datetime.now()
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Failed to collect diagnostics: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "message": "Diagnostic collection failed"
            }
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """Get information about available log files
        
        Returns:
            List of log file information
        """
        log_files = []
        
        try:
            for log_file in self.log_dir.glob("*.log"):
                stat = log_file.stat()
                log_files.append({
                    "name": log_file.name,
                    "path": str(log_file),
                    "size_bytes": stat.st_size,
                    "size_mb": stat.st_size / (1024 * 1024),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get log files: {e}")
        
        return log_files
    
    def clear_log_files(self, older_than_days: int = 30) -> int:
        """Clear old log files
        
        Args:
            older_than_days: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        try:
            for log_file in self.log_dir.glob("*.log"):
                stat = log_file.stat()
                file_date = datetime.fromtimestamp(stat.st_mtime)
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file.name}")
        
        except Exception as e:
            logger.error(f"Failed to clear log files: {e}")
        
        return deleted_count
    
    def export_settings(self) -> Dict[str, Any]:
        """Export all application settings
        
        Returns:
            Dictionary with all settings for backup
        """
        return {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "settings": asdict(self.settings)
        }
    
    def import_settings(self, settings_data: Dict[str, Any]) -> bool:
        """Import application settings from backup
        
        Args:
            settings_data: Exported settings data
            
        Returns:
            True if import was successful
        """
        try:
            if "settings" not in settings_data:
                return False
            
            imported_settings = settings_data["settings"]
            
            # Validate and convert enums
            if "logging" in imported_settings and "level" in imported_settings["logging"]:
                level_str = imported_settings["logging"]["level"]
                if isinstance(level_str, str):
                    for level in LogLevel:
                        if level.value == level_str:
                            imported_settings["logging"]["level"] = level
                            break
            
            if "updates" in imported_settings and "update_channel" in imported_settings["updates"]:
                channel_str = imported_settings["updates"]["update_channel"]
                if isinstance(channel_str, str):
                    for channel in UpdateChannel:
                        if channel.value == channel_str:
                            imported_settings["updates"]["update_channel"] = channel
                            break
            
            # Create settings objects
            logging_settings = LoggingSettings(**imported_settings.get("logging", {}))
            update_settings = UpdateSettings(**imported_settings.get("updates", {}))
            performance_settings = PerformanceSettings(**imported_settings.get("performance", {}))
            diagnostics_settings = DiagnosticsSettings(**imported_settings.get("diagnostics", {}))
            security_settings = SecuritySettings(**imported_settings.get("security", {}))
            
            self.settings = ApplicationSettings(
                logging=logging_settings,
                updates=update_settings,
                performance=performance_settings,
                diagnostics=diagnostics_settings,
                security=security_settings,
                last_updated=datetime.now().isoformat()
            )
            
            # Apply imported settings
            self._configure_logging()
            self._apply_performance_settings()
            
            # Save imported settings
            success = self._save_settings()
            
            if success:
                logger.info("Imported application settings successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults
        
        Returns:
            True if reset was successful
        """
        try:
            self.settings = ApplicationSettings(
                logging=LoggingSettings(),
                updates=UpdateSettings(),
                performance=PerformanceSettings(),
                diagnostics=DiagnosticsSettings(),
                security=SecuritySettings(),
                last_updated=datetime.now().isoformat()
            )
            
            # Apply default settings
            self._configure_logging()
            self._apply_performance_settings()
            
            # Save defaults
            success = self._save_settings()
            
            if success:
                logger.info("Reset application settings to defaults")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False
    
    def start_automatic_update_checking(self):
        """Start automatic update checking background task"""
        if self.settings.updates.auto_check_enabled and not self._update_check_task:
            self._update_check_task = asyncio.create_task(self._update_check_loop())
    
    def stop_automatic_update_checking(self):
        """Stop automatic update checking background task"""
        if self._update_check_task:
            self._update_check_task.cancel()
            self._update_check_task = None
    
    async def _update_check_loop(self):
        """Background task for automatic update checking"""
        while True:
            try:
                await asyncio.sleep(self.settings.updates.check_interval_hours * 3600)
                await self.check_for_updates()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Update check loop error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    def _load_settings(self) -> ApplicationSettings:
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return self._dict_to_settings(data)
        except Exception as e:
            logger.warning(f"Failed to load settings, using defaults: {e}")
        
        # Return default settings
        return ApplicationSettings(
            logging=LoggingSettings(log_file_path=str(self.log_dir / "app.log")),
            updates=UpdateSettings(),
            performance=PerformanceSettings(),
            diagnostics=DiagnosticsSettings(),
            security=SecuritySettings(),
            last_updated=datetime.now().isoformat()
        )
    
    def _save_settings(self) -> bool:
        """Save settings to file"""
        try:
            self.settings.last_updated = datetime.now().isoformat()
            settings_dict = asdict(self.settings)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def _dict_to_settings(self, data: Dict[str, Any]) -> ApplicationSettings:
        """Convert dictionary to ApplicationSettings object"""
        try:
            # Handle enum conversions
            logging_data = data.get("logging", {})
            if "level" in logging_data and isinstance(logging_data["level"], str):
                for level in LogLevel:
                    if level.value == logging_data["level"]:
                        logging_data["level"] = level
                        break
                else:
                    logging_data["level"] = LogLevel.INFO
            
            updates_data = data.get("updates", {})
            if "update_channel" in updates_data and isinstance(updates_data["update_channel"], str):
                for channel in UpdateChannel:
                    if channel.value == updates_data["update_channel"]:
                        updates_data["update_channel"] = channel
                        break
                else:
                    updates_data["update_channel"] = UpdateChannel.STABLE
            
            # Create objects
            logging_settings = LoggingSettings(**logging_data)
            update_settings = UpdateSettings(**updates_data)
            performance_settings = PerformanceSettings(**data.get("performance", {}))
            diagnostics_settings = DiagnosticsSettings(**data.get("diagnostics", {}))
            security_settings = SecuritySettings(**data.get("security", {}))
            
            return ApplicationSettings(
                logging=logging_settings,
                updates=update_settings,
                performance=performance_settings,
                diagnostics=diagnostics_settings,
                security=security_settings,
                version=data.get("version", "1.0"),
                last_updated=data.get("last_updated", datetime.now().isoformat())
            )
            
        except Exception as e:
            logger.error(f"Failed to parse settings data: {e}")
            return ApplicationSettings(
                logging=LoggingSettings(),
                updates=UpdateSettings(),
                performance=PerformanceSettings(),
                diagnostics=DiagnosticsSettings(),
                security=SecuritySettings(),
                last_updated=datetime.now().isoformat()
            )
    
    def _configure_logging(self):
        """Configure logging based on current settings"""
        try:
            log_settings = self.settings.logging
            
            # Set logging level
            logging_level = getattr(logging, log_settings.level.value)
            logging.getLogger().setLevel(logging_level)
            
            # Clear existing handlers
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Create formatter
            formatter = logging.Formatter(log_settings.log_format)
            
            # Console handler
            if log_settings.enable_console_logging:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)
            
            # File handler
            if log_settings.enable_file_logging and log_settings.log_file_path:
                log_file = Path(log_settings.log_file_path)
                log_file.parent.mkdir(parents=True, exist_ok=True)
                
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=log_settings.max_log_file_size * 1024 * 1024,
                    backupCount=log_settings.max_log_files
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            
            logger.info("Logging configuration updated")
            
        except Exception as e:
            print(f"Failed to configure logging: {e}")
    
    def _apply_performance_settings(self):
        """Apply performance settings to the application"""
        try:
            perf_settings = self.settings.performance
            
            # Set process priority (platform-specific)
            if PSUTIL_AVAILABLE and hasattr(psutil, "Process"):
                try:
                    process = psutil.Process()
                    if perf_settings.process_priority == "high":
                        process.nice(-10 if platform.system() != "Windows" else psutil.HIGH_PRIORITY_CLASS)
                    elif perf_settings.process_priority == "low":
                        process.nice(10 if platform.system() != "Windows" else psutil.IDLE_PRIORITY_CLASS)
                    # normal priority is default, no change needed
                except:
                    pass  # Ignore permission errors
            
            logger.info("Performance settings applied")
            
        except Exception as e:
            logger.error(f"Failed to apply performance settings: {e}")
    
    def _get_application_info(self) -> Dict[str, Any]:
        """Get application information"""
        return {
            "name": "Academic Auto Grader",
            "version": "1.0.0",
            "python_version": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
            "startup_time": "2024-01-01T00:00:00",  # Would be actual startup time
            "uptime_seconds": 3600,  # Would be actual uptime
            "pid": os.getpid()
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            info = {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "hostname": platform.node(),
                "username": os.getenv("USER") or os.getenv("USERNAME", "unknown")
            }
            
            if PSUTIL_AVAILABLE:
                info.update({
                    "cpu_count": psutil.cpu_count(),
                    "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                    "memory": {
                        "total": psutil.virtual_memory().total,
                        "available": psutil.virtual_memory().available,
                        "percent": psutil.virtual_memory().percent
                    },
                    "disk": {
                        "total": psutil.disk_usage('/').total,
                        "free": psutil.disk_usage('/').free,
                        "percent": psutil.disk_usage('/').percent
                    }
                })
            else:
                info["psutil_available"] = False
            
            return info
        except Exception as e:
            return {"error": str(e)}
    
    def _get_performance_info(self) -> Dict[str, Any]:
        """Get performance information"""
        try:
            info = {
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            if PSUTIL_AVAILABLE:
                info.update({
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_usage": psutil.Process().memory_info()._asdict(),
                    "memory_percent": psutil.Process().memory_percent(),
                    "open_files": len(psutil.Process().open_files()),
                    "threads": psutil.Process().num_threads()
                })
            else:
                info["psutil_available"] = False
            
            return info
        except Exception as e:
            return {"error": str(e)}
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            if PSUTIL_AVAILABLE:
                return {
                    "interfaces": list(psutil.net_if_addrs().keys()),
                    "connections": len(psutil.net_connections()),
                    "io_counters": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None
                }
            else:
                return {"psutil_available": False}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_storage_info(self) -> Dict[str, Any]:
        """Get storage information"""
        try:
            if PSUTIL_AVAILABLE:
                partitions = []
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        partitions.append({
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": (usage.used / usage.total) * 100
                        })
                    except:
                        continue
                
                return {
                    "partitions": partitions,
                    "io_counters": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
                }
            else:
                return {"psutil_available": False}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        try:
            return {
                "python_path": sys.path,
                "environment_variables": dict(os.environ),
                "working_directory": os.getcwd(),
                "temp_directory": os.path.expanduser("~/.auto-grader")
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Test the application settings service"""
    async def test_service():
        service = ApplicationSettingsService()
        
        print("Testing application settings service...")
        
        # Test getting settings
        settings = service.get_settings()
        print(f"Current log level: {settings.logging.level}")
        print(f"Auto-update enabled: {settings.updates.auto_check_enabled}")
        
        # Test update check
        update_result = await service.check_for_updates(force=True)
        print(f"Update check result: {update_result}")
        
        # Test diagnostics
        diagnostics = service.get_system_diagnostics()
        print(f"System info collected: {len(diagnostics)} categories")
        
        print("Application settings service test completed!")
    
    asyncio.run(test_service())


if __name__ == "__main__":
    main()