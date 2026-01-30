# Technology Stack

## Overview

Video Splitter is a web application for downloading and splitting videos from Facebook, YouTube, and Instagram. It uses a Python backend for video processing and a static HTML/CSS/JS frontend.

---

## Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance async API framework |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | Lightning-fast ASGI server |
| **Video Extraction** | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Extract video URLs from 1000+ sites |
| **Video Processing** | [FFmpeg](https://ffmpeg.org/) | Encode, trim, merge video/audio |
| **FFmpeg Wrapper** | [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) | Pythonic interface to FFmpeg |

### Key Features
- **Streaming Response**: Videos are encoded and streamed in real-time (no temp files)
- **Audio Merging**: Automatically merges separate video+audio tracks for 1080p+
- **Multi-Platform**: Supports Facebook, YouTube, Instagram, TikTok, and more
- **Format Selection**: Users can choose specific resolutions (144p to 4K)

### Dependencies (`requirements.txt`)
```
fastapi
uvicorn
yt-dlp
ffmpeg-python
python-multipart
```

---

## Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Structure** | HTML5 | Semantic markup |
| **Styling** | Vanilla CSS | Custom design system with CSS variables |
| **Logic** | Vanilla JavaScript | No frameworks, lightweight |
| **Icons** | [Font Awesome](https://fontawesome.com/) | UI icons |
| **Fonts** | [Google Fonts](https://fonts.google.com/) | Roboto typeface |

### Design Features
- **Responsive**: Works on mobile and desktop
- **Modern UI**: Rounded corners, shadows, smooth animations
- **Direct Download**: Uses browser's native download manager (no buffering)

---

## Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend Host** | Mac Mini (self-hosted) | Runs Python backend 24/7 |
| **Secure Tunnel** | [Tailscale](https://tailscale.com/) | Zero-config VPN with auto-HTTPS |
| **Frontend Host** | [Netlify](https://www.netlify.com/) | Free static site hosting |
| **Version Control** | Git + GitHub | Source code management |

### Network Architecture
```
┌─────────────┐     HTTPS      ┌─────────────┐
│   Browser   │ ─────────────► │   Netlify   │  (Frontend)
└─────────────┘                └─────────────┘
       │
       │ HTTPS (Tailscale)
       ▼
┌─────────────────────────────────────────────┐
│              Mac Mini (Backend)             │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │
│  │ Uvicorn │──│ FastAPI │──│ FFmpeg/yt-dlp│ │
│  └─────────┘  └─────────┘  └─────────────┘  │
└─────────────────────────────────────────────┘
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/analyze` | POST | Extract video metadata and available formats |
| `/stream-segment` | GET | Download/stream a video segment |
| `/process-segment` | POST | Process and stream a video segment |
| `/process` | POST | Split video into multiple segments (ZIP) |

---

## System Requirements

### Backend Server
- Python 3.10+
- FFmpeg installed and in PATH
- 4GB+ RAM recommended
- Stable internet connection

### Frontend
- Any modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled

---

## Future Considerations

- [ ] Add Redis for caching extracted URLs
- [ ] Implement job queue for concurrent downloads
- [ ] Add progress WebSocket for real-time status
- [ ] Docker containerization
- [ ] Rate limiting and authentication
