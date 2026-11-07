# HealthConnect Document Automation

A local Python application that automates the conversion and re-upload of medical text files in a healthcare system using Claude's computer use capabilities.

## Overview

This application automates the processing of medical documents by:

1. **Downloading** text files from HealthConnect
2. **Extracting** metadata using Claude API
3. **Converting** to PDF format
4. **Uploading** back to HealthConnect with proper metadata
5. **Verifying** successful upload
6. **Deleting** original files after verification

## Architecture

### Hybrid Approach

- **Claude Computer Use** - For all UI interactions (navigation, clicking, form filling)
- **Claude API (standard)** - For document analysis, metadata extraction, and summary generation
- **Local Python** - For file management, PDF conversion, and orchestration

## Features

- ✅ Automated document processing workflow
- ✅ Metadata extraction from Dutch medical documents
- ✅ PDF conversion with proper UTF-8 encoding
- ✅ Screenshot verification for UI actions
- ✅ Checkpoint-based crash recovery
- ✅ Stuck loop detection
- ✅ Safety checks before deletion
- ✅ Simulation app for testing
- ✅ Comprehensive logging

## Prerequisites

- Docker and Docker Compose
- Anthropic API key
- Python 3.11+ (for local development)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Healtconnect
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Start with Simulation

```bash
# Start all services (simulation app + automation)
docker-compose up -d

# View logs
docker-compose logs -f orchestrator
```

### 4. Access Simulation App

Open your browser to: http://localhost:3000

You'll see a HealthConnect simulation with test .txt files ready for processing.

## Project Structure

```
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # Main app container
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── src/
│   ├── main.py                # Entry point and orchestrator
│   ├── config.py              # Configuration
│   ├── exceptions.py          # Custom exceptions
│   ├── computer_use/
│   │   ├── agent.py           # Computer use agent
│   │   ├── prompts.py         # UI interaction prompts
│   │   └── verification.py    # Screenshot verification
│   ├── document_processor/
│   │   ├── extractor.py       # Metadata extraction
│   │   ├── converter.py       # Text to PDF conversion
│   │   └── naming.py          # Naming convention logic
│   ├── workflow/
│   │   ├── state_machine.py   # Workflow states
│   │   └── checkpoints.py     # Recovery checkpoints
│   └── utils/
│       ├── screenshots.py     # Screenshot utilities
│       └── logging.py         # Structured logging
├── simulation/
│   ├── app.py                 # Flask simulation app
│   ├── templates/
│   │   └── index.html         # UI template
│   └── Dockerfile             # Simulation container
├── tests/
│   └── test_with_simulation.py  # Integration tests
├── prompts/
│   └── extraction_prompts.py    # Claude prompts
└── data/
    ├── downloads/             # Downloaded files
    ├── processed/             # Converted PDFs
    ├── checkpoints/           # Recovery checkpoints
    ├── trash/                 # Deleted files
    └── logs/                  # Execution logs
```

## Usage

### Process All Documents

```bash
# Sequential processing (default - one at a time)
python src/main.py --simulation

# Parallel processing (process 3 documents at a time)
python src/main.py --simulation --parallel

# Parallel with custom batch size (process 5 at a time)
python src/main.py --simulation --parallel --batch-size 5

# Against production HealthConnect
python src/main.py --production

# Parallel in production
python src/main.py --production --parallel --batch-size 3
```

### Process Single Document

```bash
python src/main.py --single --file-id document_123
```

### Resume from Checkpoint

```bash
python src/main.py --resume --document-id document_123
```

### Cleanup Trash

```bash
python src/main.py --cleanup-trash
```

## Docker Usage

### Start All Services

```bash
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator
docker-compose logs -f simulation
```

### Stop Services

```bash
docker-compose down
```

### Access Computer Use Interface

- VNC: `vnc://localhost:5900`
- noVNC web: http://localhost:6080
- Combined interface: http://localhost:8080

## Workflow Steps

The application executes these steps for each document:

### Step 1: Navigate to Patient Files

Navigate to the "Bijlage" (attachments) tab and identify .txt files.

### Step 2: Download Text File

Click download button and wait for file to appear in downloads folder.

### Step 3: Extract Metadata

Use Claude API to extract:
- Document type (specialistenbrief, etc.)
- Specialization code (NEU, LON, CAR, etc.)
- Specialist name
- Direction (incoming/outgoing)
- Summary (max 150 chars)
- Logical name (CODE.Name format)

### Step 4: Convert to PDF

Convert text to PDF with proper Dutch character encoding.

### Step 5: Upload PDF

Upload PDF via UI with metadata:
- Logical name field
- Summary field
- Document type selection

### Step 6: Finalize Contact

Select "Geen financiële afhandeling" (No financial processing) and confirm.

### Step 7: Verify Upload

Verify the uploaded PDF appears with correct metadata.

### Step 8: Delete Original

Delete original .txt file (only after verification passes).

## Parallel Processing

### Overview

The system supports processing multiple documents simultaneously in batches:

- **Sequential Mode** (default): Processes one document at a time - safest option
- **Parallel Mode** (`--parallel`): Processes multiple documents concurrently - faster for large batches

### Usage

```bash
# Process 3 documents at a time (recommended)
python src/main.py --parallel --batch-size 3

# Process 5 documents at a time
python src/main.py --parallel --batch-size 5

# Use default batch size (3)
python src/main.py --parallel
```

### Batch Size Recommendations

| Scenario | Recommended Batch Size | Reason |
|----------|----------------------|--------|
| Simulation/Testing | 3-5 | Good balance of speed and monitoring |
| Production (small dataset) | 2-3 | Conservative, easier to troubleshoot |
| Production (large dataset) | 3-5 | Faster processing, still manageable |
| Low resources | 1-2 | Prevents system overload |
| High resources | 5-10 | Maximum throughput (max limit: 10) |

### Considerations

**Advantages**:
- ✅ Faster processing for large batches
- ✅ Better resource utilization
- ✅ Independent document processing

**Trade-offs**:
- ⚠️ More complex error tracking
- ⚠️ Higher memory usage
- ⚠️ Potential rate limit issues with Claude API

**When to use Sequential**:
- First-time testing
- Debugging issues
- Limited system resources
- Small number of documents (< 5)

**When to use Parallel**:
- Large batches (10+ documents)
- Proven stable system
- Adequate resources available
- Time-sensitive processing

## Safety Features

### Iteration Limits

- Max 10 iterations per step
- Max 50 total iterations
- 120 second timeout per step

### Stuck Detection

Automatically detects if the same action is repeated 3 times and stops.

### Screenshot Verification

Every UI action is verified using screenshot analysis to confirm expected results.

### Recovery Checkpoints

Checkpoints saved after:
- download_complete
- metadata_extracted
- pdf_converted
- upload_complete
- verification_passed
- original_deleted

### Safety Checks Before Deletion

- Verification must be "VERIFIED"
- PDF must exist in processed folder
- Checkpoint must show upload_completed=True
- Files moved to trash first, permanent delete after 24 hours

## Metadata Extraction

The Claude API extracts metadata using structured prompts:

### Document Types

- specialistenbrief
- patiëntbrief
- verwijsbrief
- afspraakbericht
- aanvraagformulier

### Specialization Codes

| Specialty | Code |
|-----------|------|
| Neurologie | NEU |
| Longarts/Pulmonologie | LON |
| Urologie | URO |
| Psychiatrie/Psychologie | PSY |
| Cardiologie | CAR |
| Dermatologie | DER |
| Gynaecologie | GYN |
| Interne geneeskunde | INT |
| Oogheelkunde | OOG |
| Orthopedie | ORT |
| Keel-neus-oorheelkunde | KNO |
| Chirurgie | CHI |
| Reumatologie | REU |
| Geriatrie | GER |
| Kindergeneeskunde | KIN |
| Maag-darm-lever | MDL |
| Radiologie | RAD |
| Anesthesiologie | ANA |
| Oncologie | ONC |
| Nefrologie | NEF |
| Hematologie | HEM |

### Logical Name Format

| Scenario | Format | Example |
|----------|--------|---------|
| Incoming specialist letter | `[CODE].[SpecialistLastName]` | `NEU.Stam` |
| Incoming from hospital | `[CODE].[Hospital]` | `LON.BovenIJ` |
| Outgoing referral | `[CODE].Huisarts` | `NEU.Huisarts` |
| Follow-up letter | `[CODE].[Name] follow-up` | `NEU.Stam follow-up` |

### Summary Guidelines

- Maximum 150 characters
- In Dutch
- Focus on:
  - Clinical status (stabiel/progressief/verbeterd)
  - Key diagnosis or finding
  - Treatment recommendation

## Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
# Metadata extraction tests
pytest tests/test_with_simulation.py::TestMetadataExtraction -v

# PDF conversion tests
pytest tests/test_with_simulation.py::TestPDFConversion -v

# Checkpoint tests
pytest tests/test_with_simulation.py::TestCheckpointManager -v
```

### Skip Integration Tests

```bash
pytest tests/ -m "not integration" -v
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `USE_SIMULATION` | Use simulation app | `true` |
| `SIMULATION_APP_URL` | Simulation app URL | `http://localhost:3000` |
| `HEALTHCONNECT_URL` | Production URL | - |
| `COMPUTER_USE_HOST` | Computer use host | `localhost` |
| `COMPUTER_USE_PORT` | Computer use port | `8080` |

### Application Settings

Edit `src/config.py` to customize:

- Iteration limits
- Timeout values
- Screen resolution
- File paths
- Safety settings

## Logging

All actions are logged with:

- Timestamp
- Step name
- Action taken
- Result (success/fail)
- Screenshot reference (for UI actions)

### Log Format

```
2024-01-15 14:32:01 | download | START | document_id=abc123
2024-01-15 14:32:05 | download | ACTION | clicked_download_button
2024-01-15 14:32:08 | download | VERIFY | file_exists=/tmp/downloads/abc123.txt
2024-01-15 14:32:08 | download | COMPLETE | success=True
```

### Log Locations

- Application logs: `data/logs/app_YYYYMMDD_HHMMSS.log`
- Document logs: `data/logs/{document_id}_YYYYMMDD_HHMMSS.log`
- Screenshots: `data/logs/screenshots/`

## Error Handling

### Workflow Errors

- `WorkflowError` - Base exception
- `VerificationError` - UI verification fails
- `StuckLoopError` - Agent stuck in loop
- `SafetyError` - Safety check fails
- `ExtractionError` - Metadata extraction fails
- `ConversionError` - PDF conversion fails
- `UploadError` - Upload fails

### Error Recovery

1. Error is logged with screenshot
2. Checkpoint saved with error details
3. State transitions to ERROR
4. Can resume from last successful checkpoint

## Production Deployment

### Before Production

1. ✅ Test with simulation app
2. ✅ Verify all safety checks work
3. ✅ Test checkpoint recovery
4. ✅ Review all logs
5. ✅ Set `USE_SIMULATION=false`
6. ✅ Configure production URL

### Production Checklist

- [ ] Computer use prompts are explicit and numbered
- [ ] Every UI action has verification
- [ ] Iteration limits enforced
- [ ] Stuck loop detection active
- [ ] Checkpoints save after major steps
- [ ] Originals deleted only after verification
- [ ] "Geen financiële afhandeling" always selected
- [ ] All logs include screenshots
- [ ] Simulation testing passes 100%
- [ ] Error handling covers all failure modes

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# Set API key
export ANTHROPIC_API_KEY=your_key_here
```

### Container Issues

```bash
# Rebuild containers
docker-compose build --no-cache

# Check container status
docker-compose ps

# View container logs
docker-compose logs orchestrator
```

### Checkpoint Recovery

```bash
# List checkpoints
ls data/checkpoints/

# Resume from checkpoint
python src/main.py --resume --document-id document_123
```

### Clear All Data

```bash
# Stop containers
docker-compose down

# Clear data
rm -rf data/downloads/*
rm -rf data/processed/*
rm -rf data/checkpoints/*
rm -rf data/trash/*

# Keep logs for analysis
```

## Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run application
python -m src.main --simulation
```

### Adding New Features

1. Create feature branch
2. Add implementation
3. Add tests
4. Update documentation
5. Test with simulation
6. Create pull request

## License

[Add your license here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: This README
- Simulation Testing: http://localhost:3000

## Acknowledgments

- Built with Claude API by Anthropic
- Uses Claude Computer Use capabilities
- PDF generation with ReportLab
- Web simulation with Flask
