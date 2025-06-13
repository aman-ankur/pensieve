# 🏛️ Architecture Design - Pensieve

## 🎯 Design Principles

### **Core Principles**
1. **Privacy First**: No data leaves the local machine
2. **Fail Gracefully**: System continues working even if individual components fail
3. **Modular Design**: Components can be replaced/upgraded independently
4. **Extensible**: Easy to add new features and integrations
5. **Resource Efficient**: Minimal CPU/RAM usage when idle

## 🧩 Component Architecture

### **1. Monitor Layer**
```python
# File System Watcher
class ZoomMonitor:
    - Watches ~/Documents/Zoom/ for new folders
    - Detects new transcript files
    - Filters out incomplete/empty files
    - Queues files for processing
    
# Smart Detection
class TranscriptDetector:
    - Validates file format and structure
    - Extracts meeting metadata from folder names
    - Prevents duplicate processing
    - Handles file locks and partial writes
```

### **2. Processing Layer**
```python
# Content Parser
class TranscriptParser:
    - Parses Zoom's speaker-timestamp format
    - Extracts participant information
    - Calculates meeting duration
    - Handles malformed entries gracefully
    
# AI Integration
class OllamaSummarizer:
    - Manages connection to local Ollama instance
    - Handles context window limitations
    - Implements retry logic for failed requests
    - Chunks large transcripts intelligently
    
# Content Extraction
class ActionExtractor:
    - Identifies action items using NLP patterns
    - Associates actions with speakers
    - Extracts deadlines and priorities
    - Categorizes meeting decisions
```

### **3. Storage Layer**
```python
# File Organization
class SummaryManager:
    - Creates organized directory structure
    - Generates consistent file naming
    - Manages summary templates
    - Handles file conflicts and versioning
    
# Metadata Handler
class MetadataManager:
    - Tracks processing history
    - Stores meeting classifications
    - Maintains search indexes
    - Manages summary statistics
```

## 🔄 Data Flow Architecture

### **Event-Driven Processing**
```
1. File System Event
   ↓
2. Validation & Queuing
   ↓
3. Metadata Extraction
   ↓
4. Content Processing
   ↓
5. AI Summarization
   ↓
6. Summary Generation
   ↓
7. Storage & Indexing
```

### **Error Recovery Flows**
```
Processing Error → Log Error → Retry (3x) → Manual Queue
AI Service Down → Queue for Later → Notify User
Large File → Chunk Processing → Merge Results
Malformed Input → Best Effort Parse → Flag for Review
```

## 🔧 Configuration Architecture

### **Hierarchical Configuration**
```yaml
# config/settings.yaml
monitoring:
  zoom_folder: "~/Documents/Zoom"
  watch_patterns: ["*/meeting_saved_closed_caption.txt"]
  min_file_size: 1024
  
processing:
  ollama_url: "http://localhost:11434"
  model_name: "llama3.1:8b"
  max_retries: 3
  chunk_size: 4000
  
output:
  summaries_folder: "./summaries"
  template_file: "config/prompts/summary_template.txt"
  date_format: "%Y-%m-%d"
  
features:
  multilingual: true
  action_extraction: true
  priority_detection: true
  calendar_integration: false  # Future feature
```

## 🏗️ Extensibility Points

### **Plugin Architecture (Future)**
```python
# Plugin Interface
class ProcessorPlugin:
    def process_transcript(self, transcript: Dict) -> Dict:
        pass
    
    def generate_summary(self, content: str) -> str:
        pass

# Example Plugins
- NotionIntegration: Export to Notion pages
- SlackNotifier: Send summaries to Slack channels  
- CalendarSync: Pull meeting titles from calendar
- TeamInsights: Generate team communication analytics
```

### **AI Model Flexibility**
```python
# Abstract AI Provider
class AIProvider:
    def summarize(self, content: str, prompt: str) -> str:
        pass

# Implementations
- OllamaProvider: Local Llama models
- OpenAIProvider: GPT-4 API (future)
- ClaudeProvider: Anthropic API (future)
- CustomProvider: Fine-tuned models
```

## 📊 Monitoring & Observability

### **Health Monitoring**
```python
# System Health
class HealthChecker:
    - Monitor Ollama service status
    - Check disk space for summaries
    - Validate configuration integrity
    - Track processing queue length
    
# Performance Metrics
class MetricsCollector:
    - Processing time per meeting
    - Success/failure rates
    - Resource usage patterns
    - Summary quality scores
```

### **Logging Architecture**
```
Application Logs → File (pensieve.log)
Error Logs → File (errors.log) + Console
Processing Stats → JSON (metrics.json)
Debug Info → Conditional verbose logging
```

## 🔐 Security Architecture

### **Data Protection**
- **Isolation**: All processing in local sandbox
- **Access Control**: File permissions match source files
- **Audit Trail**: Complete processing history
- **Cleanup**: Temporary files auto-deleted

### **Privacy Safeguards**
- **No Network**: Only localhost Ollama communication
- **Encryption Ready**: Framework for future encryption
- **Selective Processing**: Exclude sensitive meetings
- **Data Minimization**: Only store necessary metadata

## 🚀 Deployment Architecture

### **Development Mode**
```bash
# Direct Python execution
python src/main.py --config config/dev.yaml --verbose
```

### **Production Mode (Future)**
```bash
# Background service
pensieve start --daemon
pensieve status
pensieve stop
```

### **Containerized Deployment (Future)**
```dockerfile
# Docker container with Ollama + Pensieve
FROM ollama/ollama:latest
COPY . /app/pensieve
RUN pip install -r requirements.txt
CMD ["python", "/app/pensieve/src/main.py"]
```

## 🔄 Upgrade & Migration Strategy

### **Backward Compatibility**
- **Config Migration**: Automatic settings upgrade
- **Data Migration**: Summary format versioning  
- **API Stability**: Stable interfaces for extensions
- **Rollback Support**: Easy downgrade capability

### **Feature Flags**
```yaml
# Gradual feature rollout
features:
  experimental_multilingual: false
  beta_calendar_sync: false
  alpha_team_analytics: false
```

This architecture ensures Pensieve can scale from a simple personal tool to a comprehensive meeting intelligence platform while maintaining privacy and performance. 