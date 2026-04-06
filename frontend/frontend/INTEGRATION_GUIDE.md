# Frontend Integration Guide

## Quick Start for Demo

### 1. Setup Backend
Ensure your backend is running:
```bash
cd AI_ASSISTANT_Backend
# Follow backend README to start the server
# Default: http://localhost:8000
```

### 2. Setup Frontend
```bash
cd frontend/frontend
npm install
npm start
```

### 3. Configure API Connection

Create `.env` file (or edit existing):
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=localtest
```

Optional:
```
REACT_APP_AUTH_API_URL=http://localhost:8000
```

The merged architecture does not require a separate auth service URL.

### 4. Test the Integration

1. Open http://localhost:3000
2. Try these test messages:
   - "Create a task to call John tomorrow at 3pm"
   - "What is artificial intelligence?"
   - "Summarize the benefits of renewable energy"

## UI/UX Design Decisions

### Information Architecture

**Primary Information (Always Visible)**
- User message
- Assistant response
- Detected intent
- Action status
- Task cards (when created)

**Secondary Information (Available on Demand)**
- Timestamps
- Task metadata
- Confidence scores (hidden, available in API response)

### Visual Hierarchy

1. **Header**: Brand and purpose
2. **User Message**: Blue background, clearly distinguished
3. **Assistant Response**: White background, primary content
4. **Metadata Section**: Separated by border, smaller text
5. **Task Cards**: Distinct cards for created tasks

### Color System

- **Primary (Blue)**: Trust, reliability (buttons, links, user messages)
- **Green**: Success, executed actions
- **Yellow**: Processing, pending states
- **Red**: Errors, failed actions
- **Gray**: Neutral, metadata, disabled states

### Status Indicators

Color-coded badges with icons:
- 🟢 **Executed** - Action completed successfully
- 🟡 **Pending/Processing** - Action in progress (animated pulse)
- 🔴 **Failed** - Action failed with error

### Responsive Design

- **Desktop**: Full-width layout, max-width container (4xl)
- **Tablet**: Same layout, adjusted spacing
- **Mobile**: Stacked layout, optimized touch targets

### Accessibility

- Semantic HTML elements
- Keyboard navigation (Enter to send, Shift+Enter for new line)
- Color contrast meets WCAG AA standards
- Focus states on interactive elements
- ARIA labels where appropriate

## Screen Recording Checklist

When creating the demo screen recording (2-3 minutes), show:

1. **Welcome Screen** (5 seconds)
   - Clean interface
   - Example prompts

2. **Task Creation** (30 seconds)
   - Type: "Create a task to call John tomorrow at 3pm"
   - Show loading state
   - Show response with intent detection
   - Show task card with status

3. **General Question** (20 seconds)
   - Type: "What is artificial intelligence?"
   - Show response
   - Show intent: "general"

4. **Error Handling** (15 seconds)
   - Show what happens if backend is down
   - Clear error message display

5. **Action Visibility** (20 seconds)
   - Highlight how intent, action, and status are shown
   - Point out timestamps

## Deployment Checklist

### Pre-Deployment

- [ ] Test all flows (task creation, questions, errors)
- [ ] Verify environment variables are set
- [ ] Check API endpoint is accessible
- [ ] Test on multiple browsers (Chrome, Firefox, Safari)
- [ ] Verify responsive design on mobile

### Vercel Deployment

1. Push to GitHub/GitLab
2. Import in Vercel
3. Set root directory to `frontend/frontend`
3. Set environment variables:
   - `REACT_APP_API_URL`
   - `REACT_APP_API_KEY`
4. Deploy
5. Test deployed version

### Production Considerations

- Use production API URL
- Secure API key (never commit to repo)
- Enable HTTPS
- Set up error monitoring (optional)
- Configure CORS on backend if needed

## Troubleshooting

### API Connection Issues

**Error: "Failed to communicate with the assistant"**
- Check backend is running
- Verify `REACT_APP_API_URL` in `.env`
- Check browser console for CORS errors
- Verify API key is correct

### Build Issues

**Error: "Module not found"**
- Run `npm install`
- Clear node_modules and reinstall
- Check Node.js version (16+)

### Styling Issues

**Tailwind classes not working**
- Verify `tailwind.config.js` content paths
- Check `postcss.config.js` exists
- Ensure `index.css` has Tailwind directives
- Restart dev server

## Performance Optimizations

- Component lazy loading (for future expansion)
- API response caching (optional)
- Debounced input (if needed)
- Optimized bundle size via React build

## Future Enhancements (Out of Scope)

These are noted for future iterations:

- Chat history persistence (localStorage/backend)
- Real-time task status updates (WebSocket)
- Voice input integration
- Task management panel
- Export conversation history
- Dark mode toggle
- Multi-language support

