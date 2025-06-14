"""
Configuration management for Pensieve.
Loads and manages settings from YAML configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MonitoringConfig:
    """Configuration for file monitoring."""
    zoom_folder: str
    watch_patterns: list = None
    min_file_size: int = 1024
    check_interval: int = 5
    file_stable_time: int = 2
    file_extensions: list = None
    ignored_folders: list = None
    poll_interval: float = 2.0


@dataclass
class ProcessingConfig:
    """Configuration for AI processing."""
    ollama_url: str
    model_name: str
    max_retries: int = 3
    retry_delay: int = 5
    request_timeout: int = 120
    chunk_size: int = 4000
    max_chunk_overlap: int = 200
    chunk_model: str = "llama3.2:1b"
    synthesis_model: str = "llama3.1:8b"
    chunking: dict = None


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    summaries_folder: str
    template_file: str
    date_format: str
    filename_format: str
    include_metadata: bool = True
    create_backups: bool = False
    time_format: str = "%H-%M"
    organize_by_date: bool = True
    create_monthly_folders: bool = True


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str
    log_file: str = "./logs/pensieve.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    console_output: bool = True
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_rotation: bool = True


@dataclass
class PensieveConfig:
    """Main configuration class for Pensieve."""
    monitoring: MonitoringConfig
    processing: ProcessingConfig
    output: OutputConfig
    logging: LoggingConfig
    features: Dict[str, bool]
    performance: Dict[str, Any]
    meeting_types: Dict[str, Dict[str, Any]]


class ConfigManager:
    """Manages loading and accessing configuration settings."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/settings.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "settings.yaml"
        
        self.config_path = Path(config_path)
        self._config: Optional[PensieveConfig] = None
        
    def load_config(self) -> PensieveConfig:
        """
        Load configuration from YAML file.
        
        Returns:
            Loaded configuration object.
            
        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
            ValueError: If required configuration keys are missing.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in config file: {e}")
        
        # Validate and create config objects
        try:
            monitoring_config = MonitoringConfig(**raw_config['monitoring'])
            processing_config = ProcessingConfig(**raw_config['processing'])
            output_config = OutputConfig(**raw_config['output'])
            logging_config = LoggingConfig(**raw_config['logging'])
            
            self._config = PensieveConfig(
                monitoring=monitoring_config,
                processing=processing_config,
                output=output_config,
                logging=logging_config,
                features=raw_config.get('features', {}),
                performance=raw_config.get('performance', {}),
                meeting_types=raw_config.get('meeting_types', {})
            )
            
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid configuration format: {e}")
        
        # Expand paths
        self._expand_paths()
        
        return self._config
    
    def _expand_paths(self):
        """Expand relative and user paths in configuration."""
        if self._config is None:
            return
            
        # Expand zoom folder path
        self._config.monitoring.zoom_folder = os.path.expanduser(
            self._config.monitoring.zoom_folder
        )
        
        # Expand output folder path
        self._config.output.summaries_folder = os.path.expanduser(
            self._config.output.summaries_folder
        )
        
        # Expand template file path (relative to project root)
        template_path = Path(self._config.output.template_file)
        if not template_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            template_path = project_root / template_path
        self._config.output.template_file = str(template_path)
        
        # Expand log file path
        log_path = Path(self._config.logging.log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            log_path = project_root / log_path
        self._config.logging.log_file = str(log_path)
    
    @property
    def config(self) -> PensieveConfig:
        """
        Get current configuration, loading it if necessary.
        
        Returns:
            Current configuration object.
        """
        if self._config is None:
            self.load_config()
        return self._config
    
    def reload_config(self) -> PensieveConfig:
        """
        Reload configuration from file.
        
        Returns:
            Reloaded configuration object.
        """
        self._config = None
        return self.load_config()
    
    def get_zoom_folder(self) -> str:
        """Get expanded Zoom folder path."""
        return self.config.monitoring.zoom_folder
    
    def get_summaries_folder(self) -> str:
        """Get expanded summaries folder path."""
        return self.config.output.summaries_folder
    
    def get_template_path(self) -> str:
        """Get expanded template file path."""
        return self.config.output.template_file
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature to check.
            
        Returns:
            True if feature is enabled, False otherwise.
        """
        return self.config.features.get(feature_name, False)
    
    def get_meeting_type_keywords(self, meeting_type: str) -> list:
        """
        Get keywords for a specific meeting type.
        
        Args:
            meeting_type: Type of meeting (e.g., 'one_on_one', 'standup').
            
        Returns:
            List of keywords for the meeting type.
        """
        meeting_config = self.config.meeting_types.get(meeting_type, {})
        return meeting_config.get('keywords', [])


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> PensieveConfig:
    """Get the global configuration instance."""
    return config_manager.config


def reload_config() -> PensieveConfig:
    """Reload the global configuration."""
    return config_manager.reload_config() 