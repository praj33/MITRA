# AI Assistant Frontend

A modern, professional frontend interface for the AI Assistant system that provides clear visibility into assistant actions, intents, task creation, and execution status.

## Active Deployment Topology

This frontend is part of the merged two-service setup:

- `backend/` on Render
- `frontend/frontend/` on Vercel

Authentication is now handled by the FastAPI backend, not by the legacy `frontend/Signup/` service.

## Features

### ✅ Core Requirements (Day 1 & 2)

- **Single Assistant Interface**: Clean, focused UI for interacting with the AI assistant
- **Input Box**: User-friendly message input with keyboard shortcuts (Enter to send, Shift+Enter for new line)
- **Output Panel**: Displays:
  - Assistant response text
  - Detected intent classification
  - Action taken (task creation, response generation, etc.)
  - Execution status (executed/pending/failed)
- **Task Cards**: Visual cards showing created tasks with:
  - Task ID and description
  - Status indicators (executed/pending/failed)
  - Creation and update timestamps
- **Error States**: Clear error messages when API calls fail or processing errors occur
- **Loading Indicators**: Visual feedback during API requests
- **Timestamps**: Each message and response includes timestamp for traceability

## Technology Stack

- **React 19** with TypeScript
- **Tailwind CSS** for modern, responsive styling
- **Fetch API** for backend communication

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running (default: http://localhost:8000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your backend URL and API key:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your-api-key-here
```

Optional legacy override:
```
REACT_APP_AUTH_API_URL=http://localhost:8000
```

In the merged architecture, auth uses the same backend URL as assistant traffic.

3. Start the development server:
```bash
npm start
```

The app will open at http://localhost:3000

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## How It Works

### User Interaction Flow

1. **User Types Message**: User enters a message in the input box
2. **API Request**: Frontend sends POST request to `/api/assistant` endpoint
3. **Loading State**: Loading spinner appears while processing
4. **Response Display**: Response panel shows:
   - User's original message
   - Assistant's response
   - Detected intent (e.g., "task", "general", "summarize")
   - Task type (if applicable)
   - Action status and type
   - Created task card (if task was created)
5. **Error Handling**: If API fails, error state is displayed with clear message

### Action Visibility

The UI makes all assistant actions transparent:

- **Intent Display**: Shows what the assistant understood (task creation, question, summarization, etc.)
- **Task Type**: Displays the structured task type (reminder, meeting, email, etc.)
- **Action Status**: Color-coded badges showing:
  - 🟢 **Executed** (green): Action completed successfully
  - 🟡 **Pending/Processing** (yellow): Action in progress
  - 🔴 **Failed** (red): Action failed with error message
- **Task Cards**: When tasks are created, they appear as cards showing:
  - Task ID and description
  - Current status
  - Timestamps

### Error States

The frontend handles multiple error scenarios:

1. **API Connection Errors**: Network failures, timeout errors
2. **API Response Errors**: Backend returns error status
3. **Invalid Responses**: Malformed or unexpected response structure

All errors display in a red-bordered panel with:
- Error indicator badge
- Clear error message
- Timestamp

## Component Structure

```
src/
├── components/
│   ├── MessageInput.tsx      # User input component
│   ├── ResponsePanel.tsx     # Main response display
│   ├── TaskCard.tsx          # Individual task display
│   ├── StatusIndicator.tsx   # Status badge component
│   └── LoadingSpinner.tsx    # Loading animation
├── services/
│   └── api.ts                # API service layer
├── types.ts                  # TypeScript type definitions
├── App.tsx                   # Main application component
└── index.tsx                 # Application entry point
```

## Deployment

### Vercel Deployment

1. Push code to GitHub/GitLab/Bitbucket
2. Import project in Vercel
3. Set the project root directory to `frontend/frontend`
3. Set environment variables in Vercel dashboard:
   - `REACT_APP_API_URL`: Your backend API URL
   - `REACT_APP_API_KEY`: Your API key
4. Deploy

### Other Platforms

The `build` folder contains static files that can be deployed to any static hosting service:
- Netlify
- GitHub Pages
- AWS S3 + CloudFront
- Azure Static Web Apps
- Any web server

## API Integration

### Endpoint Used

**POST `/api/assistant`**

Request:
```json
{
  "version": "3.0.0",
  "input": {
    "message": "Create a task to call John tomorrow",
    "summarized_payload": null
  },
  "context": {
    "platform": "web",
    "device": "desktop",
    "session_id": null,
    "voice_input": false
  }
}
```

Response (Backend v3):
```json
{
  "version": "3.0.0",
  "status": "success",
  "result": {
    "type": "workflow",
    "response": "Task processed successfully",
    "task": {
      "type": "reminder"
    }
  },
  "processed_at": "2025-01-20T10:00:00Z"
}
```
*Note: The frontend automatically maps this backend response to the detailed structure used by the UI components.*

### Authentication

All API requests include the `X-API-Key` header for backend authentication.
After login, the frontend also sends the user's bearer token so the backend can associate assistant requests with the authenticated user.

## UX Design Principles

This frontend follows senior UX designer best practices:

1. **Information Hierarchy**: Clear visual hierarchy with headers, sections, and emphasis
2. **Action Transparency**: Every action is visible and traceable
3. **Feedback**: Immediate visual feedback for all user actions
4. **Error Prevention**: Input validation and clear error messages
5. **Accessibility**: Semantic HTML, keyboard navigation support
6. **Responsive Design**: Works on desktop, tablet, and mobile devices
7. **Performance**: Optimized rendering and efficient state management

## Future Enhancements (Optional)

- Chat history persistence
- Task management panel (view all tasks)
- Voice input support
- Real-time updates via WebSocket
- Dark mode
- Export conversation history

## License

Part of the AI Assistant Phase B Integration project.
