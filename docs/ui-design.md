# DeepFinance UI/Interaction Design Document

## Overview

DeepFinance frontend adopts a ChatGPT-like conversational interface, providing an intuitive experience for document upload, process visualization, and report viewing.

**Design Principles**:
- **Simplicity First**: Reduce visual clutter, focus on core functionality
- **Progressive Disclosure**: Unfold information step-by-step to avoid information overload
- **Real-time Feedback**: Provide continuous progress updates throughout the 150-second process
- **Traceable Sources**: Citation system as core value, must be elegant and user-friendly

**Tech Stack**:
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS 3.4+
- **Animation**: Framer Motion 11+
- **Markdown**: React Markdown + remark-gfm
- **Icons**: Lucide React

---

## Overall Layout

### Three-Column Layout (Desktop)

```
┌──────────────┬────────────────────────────────┬─────────────────┐
│  Project     │         Main Content           │  Source Panel*  │
│  Sidebar     │         (flex-1)               │  (360px)        │
│  (240px)     │                                │                 │
│              │                                │                 │
│ [+ New       │  ┌──────────────────────────┐  │  [Collapsible]  │
│    Project]  │  │                          │  │                 │
│              │  │   Welcome / Pipeline /   │  │  Current        │
│ 📂 Recent    │  │   Report View            │  │  Citation:      │
│  • Tesla Q3  │  │                          │  │                 │
│  • NVDA Q4   │  │                          │  │  📄 doc-p5      │
│              │  │                          │  │  Location: p5   │
│ 📁 All       │  │                          │  │  [View Source]  │
│ ⚙️  Settings │  │                          │  │                 │
│              │  └──────────────────────────┘  │                 │
└──────────────┴────────────────────────────────┴─────────────────┘
```

*Source Panel: Only displayed when viewing reports, collapsible via button

### Responsive Layout (Mobile)

```
┌──────────────────────┐
│  [≡] DeepFinance     │  ← Hamburger menu
├──────────────────────┤
│                      │
│   Main Content       │
│   (full width)       │
│                      │
│                      │
└──────────────────────┘

Click citation → Modal shows source info
```

---

## Page Flow Design

### Stage 1: Welcome Onboarding Page

**Layout**:

```
┌─────────────────────────────────────────┐
│                                         │
│         📊 DeepFinance                  │
│       Intelligent Document Analysis     │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │   [Drag file here or click]    │   │
│  │                                 │   │
│  │   PDF supported, max 50MB      │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ────────── or ──────────              │
│                                         │
│  📝 Describe your analysis needs        │
│     (optional)                          │
│  ┌─────────────────────────────────┐   │
│  │ e.g., Focus on profit margin    │   │
│  │ changes and cash flow...        │   │
│  └─────────────────────────────────┘   │
│                                         │
│      [Quick Mode]  [Full Analysis]     │
│                                         │
└─────────────────────────────────────────┘
```

**Interaction Details**:

1. **File Upload Area**:
   - Default state: Dashed border, gray background
   - Hover state: Blue border, lighter background
   - Drag hover: Thicker border, highlighted background
   - Uploading: Display progress bar

2. **User Query Input**:
   - Optional, expandable/collapsible
   - Placeholder text provides examples
   - Character limit: 500 characters

3. **Mode Selection**:
   - Quick mode (minimal): No image analysis, no external research, ~115s
   - Full analysis (full): With image analysis + external research, ~200s
   - Default selection: "Full Analysis"

**Component Code**:

```tsx
// components/WelcomePage.tsx

function WelcomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [userQuery, setUserQuery] = useState("");
  const [mode, setMode] = useState<"minimal" | "full">("full");
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async () => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_query", userQuery);
    formData.append("mode", mode);

    const response = await fetch("/api/projects", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    // Navigate to pipeline view
    navigate(`/projects/${data.project_id}`);
  };

  return (
    <div className="welcome-container">
      {/* File upload */}
      <FileUploadZone
        onFileSelect={setFile}
        accept=".pdf"
        maxSize={50 * 1024 * 1024}
      />

      {/* User query */}
      <div className="mt-6">
        <label>📝 Describe your analysis needs (optional)</label>
        <textarea
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          placeholder="e.g., Focus on profit margin changes and cash flow..."
          maxLength={500}
          className="w-full mt-2 p-3 border rounded-lg"
        />
      </div>

      {/* Mode selection */}
      <div className="mt-6 flex gap-4">
        <ModeButton
          selected={mode === "minimal"}
          onClick={() => setMode("minimal")}
          label="Quick Mode"
          description="~2 minutes"
        />
        <ModeButton
          selected={mode === "full"}
          onClick={() => setMode("full")}
          label="Full Analysis"
          description="~3 minutes"
        />
      </div>

      {/* Start button */}
      <button
        onClick={handleSubmit}
        disabled={!file || uploading}
        className="mt-6 btn-primary"
      >
        {uploading ? "Uploading..." : "Start Analysis"}
      </button>
    </div>
  );
}
```

---

### Stage 2: Process Visualization

**Layout**:

```
┌────────────────────────────────────────────┐
│  🎬 Analyzing your document...             │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ Parse ━━━━ Analyze ━━━━ Research ━━━━│ │
│  │  ✅      🔄       ⏳      ⏳  Generate│ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ ✅ 1. Document Parsing      96.3s    │ │
│  │  ├─ Extracted 42 pages               │ │
│  │  ├─ Identified 17 charts             │ │
│  │  └─ Extracted 8 data tables          │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ 🔄 2. Analyzing...        (54/73s)   │ │
│  │  ├─ Financial metrics ━━━━━━━━░░ 80% │ │
│  │  ├─ Operational data ━━━━━░░░░░ 50%  │ │
│  │  └─ Found 12 key metrics             │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ⏳ 3. External Research                   │
│     Waiting for analysis to complete...   │
│                                            │
│  ⏳ 4. Report Generation                   │
│     Waiting for research to complete...   │
│                                            │
└────────────────────────────────────────────┘
```

**Animation Effects**:

1. **Step Card Expansion**:
   - Use stagger animation
   - Expand from top to bottom with 100ms delay

2. **Progress Bar Animation**:
   - Smooth gradient (blue → green)
   - Use spring animation, avoid linear motion

3. **Status Icons**:
   - Pending (⏳): Static gray
   - In Progress (🔄): Rotation animation, blue
   - Completed (✅): Scale pop animation, green
   - Error (❌): Shake animation, red

**Component Code**:

```tsx
// components/PipelineProgress.tsx

import { motion } from "framer-motion";

function PipelineProgress({ projectId }: { projectId: string }) {
  const [stages, setStages] = useState<Stage[]>([]);

  useEffect(() => {
    // Connect WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      // Update stage status
      setStages((prev) => updateStages(prev, message));
    };

    return () => ws.close();
  }, [projectId]);

  return (
    <div className="pipeline-container">
      {/* Top progress bar */}
      <StepProgressBar stages={stages} />

      {/* Stage card list */}
      <div className="mt-8 space-y-4">
        {stages.map((stage, index) => (
          <motion.div
            key={stage.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <StageCard stage={stage} />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
```

**StageCard Component**:

```tsx
function StageCard({ stage }: { stage: Stage }) {
  const statusIcon = {
    pending: "⏳",
    in_progress: <Loader2 className="animate-spin" />,
    completed: "✅",
    failed: "❌",
  };

  const statusColor = {
    pending: "text-gray-400",
    in_progress: "text-blue-600",
    completed: "text-green-600",
    failed: "text-red-600",
  };

  return (
    <div className={`stage-card ${statusColor[stage.status]}`}>
      <div className="flex items-start justify-between">
        {/* Left: icon + title */}
        <div className="flex items-center gap-3">
          <span className="text-2xl">{statusIcon[stage.status]}</span>
          <div>
            <h3 className="font-semibold">{stage.title}</h3>
            <p className="text-sm text-gray-600">{stage.message}</p>
          </div>
        </div>

        {/* Right: duration */}
        {stage.duration && (
          <span className="text-sm text-gray-500">{stage.duration}s</span>
        )}
      </div>

      {/* Progress bar (in progress only) */}
      {stage.status === "in_progress" && stage.progress !== undefined && (
        <div className="mt-3">
          <ProgressBar progress={stage.progress} />
        </div>
      )}

      {/* Details */}
      {stage.details && (
        <div className="mt-3 text-sm text-gray-600">
          {Object.entries(stage.details).map(([key, value]) => (
            <div key={key}>
              ├─ {key}: {value}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

### Stage 3: Report Display + Citation System

#### 3.1 Report Main View

**Layout**:

```
┌─────────────────────────────────┬──────────────────┐
│  Report Content (Markdown)      │  Source Panel    │
├─────────────────────────────────┼──────────────────┤
│                                 │                  │
│ ## Executive Summary            │  After clicking  │
│                                 │  citation:       │
│ Tesla Q3 2025 achieved record   │                  │
│ revenue and cash flow[^doc-p5]  │  📄 [^doc-p5]    │
│ [^gap-2]    ↑ Hover for preview │                  │
│                                 │  Source: Doc     │
│ ## Key Findings                 │  Location: p5    │
│                                 │                  │
│ ### 1. Strong Financial         │  [View Source]   │
│        Performance              │                  │
│                                 │  ─────────────   │
│ Total revenue reached $28.1B,   │                  │
│ up 12% YoY[^doc-p5], but        │  🌐 [^gap-2]     │
│ operating margin declined to    │                  │
│ 8.5%...                         │  Source: Web     │
│                                 │  Title: Tesla... │
│ [Chart: Revenue Trend][^fig_004]│  [Visit Link]    │
│                                 │                  │
└─────────────────────────────────┴──────────────────┘
```

**Citation Interaction**:

1. **Hover Preview**:
   ```
   Mouse hover on [^doc-p5]
         ↓
   Show floating card:
   ┌──────────────────┐
   │ 📄 Document      │
   │ Location: p5     │
   │ Click for detail │
   └──────────────────┘
   ```

2. **Click to Expand**:
   - Right source panel opens
   - Scroll to corresponding citation
   - Highlight currently viewed citation

3. **Citation Visual Differentiation**:
   ```css
   [^doc-p5]      → 📄 Blue badge (document)
   [^fig_004.png] → 📊 Green badge (chart)
   [^gap-001-2]   → 🌐 Orange badge (web)
   ```

**Component Code**:

```tsx
// components/ReportViewer.tsx

function ReportViewer({ content, projectId }: ReportViewerProps) {
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  return (
    <div className="flex h-full">
      {/* Report content */}
      <div className="flex-1 overflow-auto p-8">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Intercept footnote rendering
            sup: ({ children }) => {
              const citationId = extractCitationId(children);
              if (!citationId) return <sup>{children}</sup>;

              return (
                <CitationLink
                  citationId={citationId}
                  onClick={() => {
                    setActiveCitation(citationId);
                    setSidePanelOpen(true);
                  }}
                >
                  {children}
                </CitationLink>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>

      {/* Source panel */}
      <AnimatePresence>
        {sidePanelOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 360, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="border-l bg-gray-50"
          >
            <CitationPanel
              citationId={activeCitation}
              projectId={projectId}
              onClose={() => setSidePanelOpen(false)}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**CitationLink Component** (with hover preview):

```tsx
function CitationLink({ citationId, onClick, children }) {
  const [showPreview, setShowPreview] = useState(false);

  const citationType = getCitationType(citationId);
  const badgeColor = {
    document: "bg-blue-100 text-blue-700",
    chart: "bg-green-100 text-green-700",
    web: "bg-orange-100 text-orange-700",
  };

  return (
    <span
      className="relative inline-block"
      onMouseEnter={() => setShowPreview(true)}
      onMouseLeave={() => setShowPreview(false)}
    >
      <sup
        className={`citation-link cursor-pointer px-1.5 py-0.5 rounded text-xs font-medium ${badgeColor[citationType]}`}
        onClick={onClick}
      >
        {children}
      </sup>

      {/* Hover preview card */}
      {showPreview && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute z-10 mt-2 p-3 bg-white shadow-lg rounded-lg border w-48"
        >
          <div className="text-sm">
            {citationType === "document" && "📄 Document Citation"}
            {citationType === "chart" && "📊 Chart Citation"}
            {citationType === "web" && "🌐 External Research"}
          </div>
          <div className="text-xs text-gray-600 mt-1">Click for details</div>
        </motion.div>
      )}
    </span>
  );
}
```

#### 3.2 Source Panel Details

**Document Citation Display**:

```tsx
function DocumentCitation({ citation }) {
  return (
    <div className="space-y-3">
      <div className="bg-blue-50 p-3 rounded-lg">
        <div className="text-sm text-gray-600">Citation ID</div>
        <div className="font-mono text-blue-700 mt-1">{citation.id}</div>
      </div>

      <div className="bg-gray-50 p-3 rounded-lg">
        <div className="text-sm text-gray-600">Document Location</div>
        <div className="font-medium mt-1">{citation.location}</div>
      </div>

      {citation.source && (
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-600">Specific Citation</div>
          <div className="font-medium mt-1">{citation.source}</div>
        </div>
      )}
    </div>
  );
}
```

**Chart Citation Display** (directly display image):

```tsx
function ChartCitation({ citation, projectId }) {
  const imageUrl = `/api/projects/${projectId}/files/source/images/${citation.figure_id}`;

  return (
    <div className="space-y-4">
      {/* Chart title */}
      {citation.figure_analysis?.title && (
        <h4 className="font-medium text-gray-900">
          {citation.figure_analysis.title}
        </h4>
      )}

      {/* Image display */}
      <div className="border rounded-lg overflow-hidden bg-white">
        <img
          src={imageUrl}
          alt={citation.figure_id}
          className="w-full h-auto"
        />
      </div>

      {/* Chart analysis */}
      {citation.figure_analysis?.analysis && (
        <div className="bg-gray-50 p-4 rounded-lg text-sm space-y-2">
          {Object.entries(citation.figure_analysis.analysis).map(
            ([key, value]) => (
              <div key={key}>
                <span className="font-medium text-gray-700">{key}:</span>
                <span className="text-gray-600">{value}</span>
              </div>
            )
          )}
        </div>
      )}

      {/* Filename */}
      <div className="text-xs text-gray-500 font-mono">
        {citation.figure_id}
      </div>
    </div>
  );
}
```

**External Link Citation Display**:

```tsx
function WebCitation({ citation }) {
  return (
    <div className="space-y-3">
      {/* Title + link */}
      <a
        href={citation.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
      >
        {citation.title || citation.url}
        <ExternalLink className="w-4 h-4" />
      </a>

      {/* Content summary */}
      {citation.content && (
        <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 leading-relaxed">
          {citation.content}
        </div>
      )}

      {/* Published date */}
      {citation.published_date && (
        <div className="text-xs text-gray-500">
          Published on {citation.published_date}
        </div>
      )}
    </div>
  );
}
```

---

## Project Management Sidebar

### Layout

```
┌─────────────────┐
│ DeepFinance     │
├─────────────────┤
│                 │
│ [+ New Project] │
│                 │
│ 📂 Recent       │
│  ┌────────────┐ │
│  │ Tesla Q3   │ │
│  │ 2 hours ago│ │
│  │ ✅ Complete │ │
│  └────────────┘ │
│                 │
│  ┌────────────┐ │
│  │ NVDA Q4    │ │
│  │ Yesterday  │ │
│  │ 🔄 Running  │ │
│  └────────────┘ │
│                 │
│ 📁 All Projects │
│ ⚙️  Settings    │
│ 📖 Guide        │
│                 │
└─────────────────┘
```

### Project Card

**Hover Effects**:
- Darker background
- Show quick action buttons: Re-analyze, Export, Delete

**Status Indicators**:
- 🔄 Processing (blue animation)
- ✅ Completed (green)
- ❌ Failed (red)

**Code**:

```tsx
function ProjectCard({ project }: { project: Project }) {
  const statusIcon = {
    processing: <Loader2 className="w-4 h-4 animate-spin text-blue-600" />,
    completed: <CheckCircle className="w-4 h-4 text-green-600" />,
    failed: <XCircle className="w-4 h-4 text-red-600" />,
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="project-card p-3 rounded-lg hover:bg-gray-100 cursor-pointer"
      onClick={() => navigate(`/projects/${project.project_id}`)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium text-sm truncate">{project.title}</h4>
          <p className="text-xs text-gray-500 mt-1">
            {formatTimeAgo(project.created_at)}
          </p>
        </div>
        <div>{statusIcon[project.status]}</div>
      </div>

      {/* Metadata */}
      <div className="mt-2 flex items-center gap-2 text-xs text-gray-600">
        <span>{project.metadata?.company}</span>
        <span>•</span>
        <span>{project.metadata?.period}</span>
      </div>
    </motion.div>
  );
}
```

---

## Component Library

### 1. FileUploadZone

**Functionality**: Drag-and-drop upload + click upload

```tsx
function FileUploadZone({ onFileSelect, accept, maxSize }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (validateFile(file, accept, maxSize)) {
      onFileSelect(file);
    }
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`upload-zone ${isDragging ? "dragging" : ""}`}
    >
      <Upload className="w-12 h-12 text-gray-400" />
      <p>Drag file here or click to upload</p>
      <p className="text-sm text-gray-500">PDF supported, max 50MB</p>
      <input
        type="file"
        accept={accept}
        onChange={(e) => onFileSelect(e.target.files?.[0])}
        className="hidden"
      />
    </div>
  );
}
```

### 2. ProgressBar

**Functionality**: Smooth gradient progress bar

```tsx
function ProgressBar({ progress }: { progress: number }) {
  return (
    <div className="progress-bar-container">
      <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 to-green-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress * 100}%` }}
          transition={{ type: "spring", stiffness: 50 }}
        />
      </div>
      <div className="text-xs text-gray-600 mt-1 text-right">
        {Math.round(progress * 100)}%
      </div>
    </div>
  );
}
```

### 3. StepProgressBar

**Functionality**: Top step indicator

```tsx
function StepProgressBar({ stages }: { stages: Stage[] }) {
  const stepNames = ["Parse", "Analyze", "Research", "Generate"];

  return (
    <div className="flex items-center justify-between">
      {stepNames.map((name, index) => {
        const stage = stages[index];
        const isActive = stage?.status === "in_progress";
        const isCompleted = stage?.status === "completed";

        return (
          <React.Fragment key={name}>
            <div className="flex flex-col items-center">
              <motion.div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  isCompleted
                    ? "bg-green-500 text-white"
                    : isActive
                    ? "bg-blue-500 text-white"
                    : "bg-gray-300 text-gray-600"
                }`}
                animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                {isCompleted ? "✓" : index + 1}
              </motion.div>
              <div className="text-xs mt-1">{name}</div>
            </div>

            {/* Connecting line */}
            {index < stepNames.length - 1 && (
              <div className="flex-1 h-0.5 bg-gray-300 mx-2" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
```

### 4. CitationModal (Mobile)

**Functionality**: Mobile citation modal

```tsx
function CitationModal({ citationId, projectId, onClose }) {
  const { data: citation } = useCitation(projectId, citationId);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="modal-overlay"
        onClick={onClose}
      >
        <motion.div
          initial={{ y: "100%" }}
          animate={{ y: 0 }}
          exit={{ y: "100%" }}
          className="modal-content"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="modal-header">
            <h3>
              {citation?.type === "document" && "📄 Document Citation"}
              {citation?.type === "chart" && "📊 Chart Citation"}
              {citation?.type === "web" && "🌐 External Research"}
            </h3>
            <button onClick={onClose}>✕</button>
          </div>

          {/* Content */}
          <div className="modal-body">
            {citation?.type === "document" && (
              <DocumentCitation citation={citation} />
            )}
            {citation?.type === "chart" && (
              <ChartCitation citation={citation} projectId={projectId} />
            )}
            {citation?.type === "web" && <WebCitation citation={citation} />}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
```

---

## Animation Configuration

### Framer Motion Presets

```tsx
// lib/animations.ts

export const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.3 },
};

export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const scaleIn = {
  initial: { scale: 0 },
  animate: { scale: 1 },
  transition: { type: "spring", stiffness: 200, damping: 15 },
};

export const slideInFromRight = {
  initial: { x: "100%" },
  animate: { x: 0 },
  exit: { x: "100%" },
  transition: { type: "spring", stiffness: 300, damping: 30 },
};
```

---

## Style Configuration

### Tailwind Configuration

```js
// tailwind.config.js

module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        success: {
          500: "#10b981",
          600: "#059669",
        },
        warning: {
          500: "#f59e0b",
          600: "#d97706",
        },
      },
      animation: {
        "spin-slow": "spin 3s linear infinite",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
};
```

---

## Responsive Design

### Breakpoint Strategy

```css
/* Mobile: < 768px */
@media (max-width: 767px) {
  .sidebar {
    display: none; /* Hide sidebar */
  }
  .citation-panel {
    display: none; /* Source panel becomes modal */
  }
}

/* Tablet: 768px - 1024px */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar {
    width: 200px; /* Narrow sidebar */
  }
  .citation-panel {
    width: 300px; /* Narrow source panel */
  }
}

/* Desktop: >= 1024px */
@media (min-width: 1024px) {
  /* Default layout */
}
```

---

## Performance Optimization

### 1. Virtual Scrolling

For long reports, use `react-window` to implement virtual scrolling.

### 2. Lazy Load Images

```tsx
import { LazyLoadImage } from "react-lazy-load-image-component";

<LazyLoadImage
  src={imageUrl}
  alt="Chart"
  placeholder={<Skeleton />}
  effect="blur"
/>;
```

### 3. Markdown Rendering Optimization

Use `React.memo` to cache Markdown rendering results.

```tsx
const MemoizedMarkdown = React.memo(ReactMarkdown);
```

---

## Summary

### Design Highlights

✅ **Progressive Disclosure**: From welcome page → process visualization → report display, step-by-step guidance
✅ **Real-time Feedback**: WebSocket push + smooth animations, 150 seconds without boredom
✅ **Traceable Sources**: Three citation types, charts directly display images
✅ **Responsive**: Desktop/mobile adaptive layout

### Tech Stack

- **React 18** + TypeScript
- **Tailwind CSS** + Framer Motion
- **React Markdown** + remark-gfm
- **WebSocket** real-time communication

### Next Steps

1. Create frontend project scaffold
2. Implement core component library
3. Integrate API and WebSocket
4. Testing and optimization
