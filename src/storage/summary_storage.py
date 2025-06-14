"""
Storage module for Pensieve.
Handles saving meeting summaries to organized files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

from ..processing.ai_processor import ProcessingResult, MeetingMetadata
from ..utils.config import get_config
from ..utils.logger import get_logger, log_performance_metrics


class SummaryStorage:
    """Handles storage and organization of meeting summaries."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("summary_storage")
        self.summaries_folder = Path(self.config.output.summaries_folder)
        
        # Create summaries folder if it doesn't exist
        self._ensure_directories_exist()
    
    def _ensure_directories_exist(self):
        """Create necessary directories for storing summaries."""
        try:
            self.summaries_folder.mkdir(parents=True, exist_ok=True)
            
            # Create year folders for current and next year
            current_year = datetime.now().year
            for year in [current_year, current_year + 1]:
                year_folder = self.summaries_folder / str(year)
                year_folder.mkdir(exist_ok=True)
                
                # Create month folders for current year
                if year == current_year:
                    for month in range(1, 13):
                        month_name = datetime(year, month, 1).strftime("%m-%B")
                        month_folder = year_folder / month_name
                        month_folder.mkdir(exist_ok=True)
            
            self.logger.debug(f"Directory structure created: {self.summaries_folder}")
            
        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")
            raise
    
    def save_summary(self, result: ProcessingResult) -> Optional[Path]:
        """
        Save a processing result to an organized file structure.
        
        Args:
            result: ProcessingResult containing summary and metadata.
            
        Returns:
            Path to the saved summary file, or None if save failed.
        """
        if not result.success or not result.summary or not result.metadata:
            self.logger.warning("Cannot save incomplete processing result")
            return None
        
        start_time = datetime.now()
        
        try:
            # Generate file path
            summary_path = self._generate_file_path(result.metadata)
            
            # Create the summary content
            summary_content = self._format_summary_content(result)
            
            # Save to file
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            # Save metadata separately
            metadata_path = self._save_metadata(result, summary_path)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            log_performance_metrics(
                "summary_storage",
                processing_time,
                success=True,
                file_size=len(summary_content),
                output_path=str(summary_path)
            )
            
            self.logger.info(f"💾 Summary saved: {summary_path.name}")
            return summary_path
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            log_performance_metrics("summary_storage", processing_time, success=False)
            self.logger.error(f"Failed to save summary: {e}")
            return None
    
    def _generate_file_path(self, metadata: MeetingMetadata) -> Path:
        """
        Generate organized file path for a summary.
        
        Args:
            metadata: Meeting metadata.
            
        Returns:
            Path where the summary should be saved.
        """
        try:
            # Parse date from metadata
            if " " in metadata.date:
                date_part = metadata.date.split(" ")[0]
            else:
                date_part = metadata.date
            
            # Try to parse the date
            try:
                parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
            except ValueError:
                # Fallback to current date if parsing fails
                parsed_date = datetime.now()
                self.logger.warning(f"Could not parse date '{date_part}', using current date")
            
            # Create organized path: YYYY/MM-Month/filename
            year = parsed_date.year
            month_name = parsed_date.strftime("%m-%B")
            
            # Generate filename
            filename = self._generate_filename(metadata, parsed_date)
            
            return self.summaries_folder / str(year) / month_name / filename
            
        except Exception as e:
            self.logger.error(f"Error generating file path: {e}")
            # Fallback to current date structure
            now = datetime.now()
            filename = f"{now.strftime('%Y-%m-%d_%H-%M')}_meeting_summary.md"
            return self.summaries_folder / str(now.year) / now.strftime("%m-%B") / filename
    
    def _generate_filename(self, metadata: MeetingMetadata, parsed_date: datetime) -> str:
        """
        Generate a descriptive filename for the summary.
        
        Args:
            metadata: Meeting metadata.
            parsed_date: Parsed meeting date.
            
        Returns:
            Generated filename.
        """
        try:
            # Extract time from metadata if available
            time_part = "unknown"
            if " " in metadata.date:
                time_str = metadata.date.split(" ", 1)[1]
                if ":" in time_str:
                    time_part = time_str.replace(":", "-")[:5]  # HH-MM format
            
            # Clean title for filename
            clean_title = self._clean_filename(metadata.title)
            
            # Format: YYYY-MM-DD_HH-MM_Title_summary.md
            filename = f"{parsed_date.strftime('%Y-%m-%d')}_{time_part}_{clean_title}_summary.md"
            
            # Ensure filename isn't too long
            if len(filename) > 100:
                # Truncate title but keep essential parts
                max_title_len = 100 - len(parsed_date.strftime('%Y-%m-%d')) - len(time_part) - len("_summary.md") - 2
                clean_title = clean_title[:max_title_len]
                filename = f"{parsed_date.strftime('%Y-%m-%d')}_{time_part}_{clean_title}_summary.md"
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error generating filename: {e}")
            # Fallback filename
            return f"{parsed_date.strftime('%Y-%m-%d')}_meeting_summary.md"
    
    def _clean_filename(self, title: str) -> str:
        """Clean a title to be filesystem-safe."""
        # Replace problematic characters
        replacements = {
            '/': '_', '\\': '_', ':': '-', '*': '_', '?': '_',
            '"': '_', '<': '_', '>': '_', '|': '_', ' ': '_'
        }
        
        clean_title = title
        for old, new in replacements.items():
            clean_title = clean_title.replace(old, new)
        
        # Remove consecutive underscores and limit length
        while '__' in clean_title:
            clean_title = clean_title.replace('__', '_')
        
        clean_title = clean_title.strip('_')
        
        # Limit length
        return clean_title[:50] if len(clean_title) > 50 else clean_title
    
    def _format_summary_content(self, result: ProcessingResult) -> str:
        """
        Format the complete summary content including metadata.
        
        Args:
            result: ProcessingResult to format.
            
        Returns:
            Formatted summary content.
        """
        metadata = result.metadata
        
        # Header with metadata
        header = f"""---
# Meeting Summary
**Meeting**: {metadata.title}
**Date**: {metadata.date}
**Duration**: {metadata.duration}
**Participants**: {', '.join(metadata.participants)}
**Type**: {metadata.meeting_type}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Model**: {result.model_used}
**Processing Time**: {result.processing_time:.1f}s
---

"""
        
        # Main summary content
        content = result.summary
        
        # Footer with technical details
        footer = f"""

---
## Technical Details
- **Source File**: `{Path(metadata.file_path).name}`
- **File Size**: {metadata.file_size:,} bytes
- **Participants Count**: {len(metadata.participants)}
- **Generated by**: Pensieve v1.0
- **Timestamp**: {datetime.now().isoformat()}
"""
        
        return header + content + footer
    
    def _save_metadata(self, result: ProcessingResult, summary_path: Path) -> Path:
        """
        Save metadata as a separate JSON file.
        
        Args:
            result: ProcessingResult containing metadata.
            summary_path: Path where the summary was saved.
            
        Returns:
            Path to the metadata file.
        """
        try:
            # Create metadata dictionary
            metadata_dict = {
                "processing_result": {
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "model_used": result.model_used,
                    "error": result.error
                },
                "meeting_metadata": asdict(result.metadata),
                "file_info": {
                    "summary_path": str(summary_path),
                    "created_at": datetime.now().isoformat(),
                    "generator": "Pensieve v1.0"
                }
            }
            
            # Save metadata file alongside summary
            metadata_path = summary_path.with_suffix('.json')
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
            
            return metadata_path
            
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
            # Return a dummy path so the main operation doesn't fail
            return summary_path.with_suffix('.json')
    
    def get_recent_summaries(self, days: int = 7) -> list:
        """
        Get recently created summaries.
        
        Args:
            days: Number of days to look back.
            
        Returns:
            List of summary file paths.
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_summaries = []
        
        try:
            for summary_file in self.summaries_folder.rglob("*_summary.md"):
                if summary_file.stat().st_mtime > cutoff_date:
                    recent_summaries.append(summary_file)
            
            # Sort by modification time (newest first)
            recent_summaries.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting recent summaries: {e}")
        
        return recent_summaries
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored summaries.
        
        Returns:
            Dictionary with storage statistics.
        """
        try:
            summary_files = list(self.summaries_folder.rglob("*_summary.md"))
            metadata_files = list(self.summaries_folder.rglob("*.json"))
            
            total_size = sum(f.stat().st_size for f in summary_files)
            
            # Count by year/month
            by_period = {}
            for file_path in summary_files:
                try:
                    parts = file_path.relative_to(self.summaries_folder).parts
                    if len(parts) >= 2:
                        period = f"{parts[0]}/{parts[1]}"
                        by_period[period] = by_period.get(period, 0) + 1
                except:
                    continue
            
            return {
                "total_summaries": len(summary_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "metadata_files": len(metadata_files),
                "by_period": by_period,
                "storage_path": str(self.summaries_folder),
                "last_summary": max((f.stat().st_mtime for f in summary_files), default=0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {
                "error": str(e),
                "storage_path": str(self.summaries_folder)
            }
    
    def check_duplicate(self, metadata: MeetingMetadata) -> Optional[Path]:
        """
        Check if a summary for this meeting already exists.
        
        Args:
            metadata: Meeting metadata to check.
            
        Returns:
            Path to existing summary if found, None otherwise.
        """
        try:
            expected_path = self._generate_file_path(metadata)
            
            if expected_path.exists():
                return expected_path
            
            # Also check for similar files in the same directory
            if expected_path.parent.exists():
                pattern = f"*{self._clean_filename(metadata.title)}*_summary.md"
                matches = list(expected_path.parent.glob(pattern))
                if matches:
                    return matches[0]
            
        except Exception as e:
            self.logger.debug(f"Error checking for duplicate: {e}")
        
        return None 