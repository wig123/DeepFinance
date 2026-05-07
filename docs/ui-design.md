# DeepFinance UI/交互设计文档

## 概述

DeepFinance 前端采用类 ChatGPT 的对话式界面，提供直观的文档上传、流程可视化和报告查看体验。

**设计原则**：
- **简洁优先**：减少视觉干扰，聚焦核心功能
- **渐进式展示**：分步骤展开信息，避免信息过载
- **实时反馈**：150秒流程全程提供连续进度更新
- **溯源可见**：引用系统作为核心价值，必须优雅且易用

**技术栈**：
- **框架**：React 18 + TypeScript
- **样式**：Tailwind CSS 3.4+
- **动画**：Framer Motion 11+
- **Markdown**：React Markdown + remark-gfm
- **图标**：Lucide React

---

## 整体布局

### 三栏布局（桌面端）

```
┌──────────────┬────────────────────────────────┬─────────────────┐
│  项目侧边栏   │         主内容区                │  溯源面板*       │
│  (240px)     │         (flex-1)               │  (360px)        │
│              │                                │                 │
│ [+ 新建项目]  │  ┌──────────────────────────┐  │  [可折叠]       │
│              │  │                          │  │                 │
│ 📂 最近项目   │  │   欢迎页 / 流程视图 /     │  │  当前查看引用：  │
│  • Tesla Q3  │  │   报告展示               │  │                 │
│  • NVDA Q4   │  │                          │  │  📄 doc-p5      │
│              │  │                          │  │  位置：第5页     │
│ 📁 全部项目   │  │                          │  │  [查看原文]     │
│ ⚙️  设置      │  │                          │  │                 │
│              │  └──────────────────────────┘  │                 │
└──────────────┴────────────────────────────────┴─────────────────┘
```

*溯源面板：仅在查看报告时显示，可通过按钮折叠

### 响应式布局（移动端）

```
┌──────────────────────┐
│  [≡] DeepFinance     │  ← 汉堡菜单
├──────────────────────┤
│                      │
│   主内容区（全宽）     │
│                      │
│                      │
└──────────────────────┘

点击引用 → 弹出模态框显示溯源信息
```

---

## 页面流程设计

### 阶段 1：欢迎引导页

**布局**：

```
┌─────────────────────────────────────────┐
│                                         │
│         📊 DeepFinance                  │
│       文档智能分析助手                   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │   [拖拽文件到此 或 点击上传]     │   │
│  │                                 │   │
│  │   支持 PDF，最大 50MB            │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ────────── 或者 ──────────            │
│                                         │
│  📝 描述您的分析需求（可选）             │
│  ┌─────────────────────────────────┐   │
│  │ 例如：重点分析利润率变化和       │   │
│  │ 现金流状况...                   │   │
│  └─────────────────────────────────┘   │
│                                         │
│      [快速模式]  [完整分析]             │
│                                         │
└─────────────────────────────────────────┘
```

**交互细节**：

1. **文件上传区域**：
   - 默认状态：虚线边框，灰色背景
   - 悬停状态：蓝色边框，背景色变浅
   - 拖拽悬停：边框加粗，背景色高亮
   - 上传中：显示进度条

2. **用户Query输入框**：
   - 可选，展开/折叠
   - 占位符文本给出示例
   - 字数限制：500字符

3. **模式选择**：
   - 快速模式（minimal）：无图片分析，无外部研究，~115秒
   - 完整分析（full）：含图片分析+外部研究，~200秒
   - 默认选中"完整分析"

**组件代码**：

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
    // 跳转到流程视图
    navigate(`/projects/${data.project_id}`);
  };

  return (
    <div className="welcome-container">
      {/* 文件上传 */}
      <FileUploadZone
        onFileSelect={setFile}
        accept=".pdf"
        maxSize={50 * 1024 * 1024}
      />

      {/* 用户Query */}
      <div className="mt-6">
        <label>📝 描述您的分析需求（可选）</label>
        <textarea
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          placeholder="例如：重点分析利润率变化和现金流状况..."
          maxLength={500}
          className="w-full mt-2 p-3 border rounded-lg"
        />
      </div>

      {/* 模式选择 */}
      <div className="mt-6 flex gap-4">
        <ModeButton
          selected={mode === "minimal"}
          onClick={() => setMode("minimal")}
          label="快速模式"
          description="~2分钟"
        />
        <ModeButton
          selected={mode === "full"}
          onClick={() => setMode("full")}
          label="完整分析"
          description="~3分钟"
        />
      </div>

      {/* 开始按钮 */}
      <button
        onClick={handleSubmit}
        disabled={!file || uploading}
        className="mt-6 btn-primary"
      >
        {uploading ? "上传中..." : "开始分析"}
      </button>
    </div>
  );
}
```

---

### 阶段 2：流程可视化

**布局**：

```
┌────────────────────────────────────────────┐
│  🎬 正在分析您的文档...                     │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ 解析 ━━━━ 分析 ━━━━ 研究 ━━━━ 生成   │ │
│  │  ✅      🔄       ⏳      ⏳          │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ ✅ 1. 文档解析              96.3s    │ │
│  │  ├─ 已提取 42 页内容                │ │
│  │  ├─ 识别 17 个图表                  │ │
│  │  └─ 提取 8 个数据表                 │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ 🔄 2. 智能分析中...       (54/73s)  │ │
│  │  ├─ 财务指标分析 ━━━━━━━━░░ 80%    │ │
│  │  ├─ 运营数据提取 ━━━━━░░░░░ 50%    │ │
│  │  └─ 已发现 12 个关键指标            │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ⏳ 3. 外部研究                            │
│     等待分析完成...                        │
│                                            │
│  ⏳ 4. 报告生成                            │
│     等待研究完成...                        │
│                                            │
└────────────────────────────────────────────┘
```

**动画效果**：

1. **步骤卡片展开**：
   - 使用 stagger animation
   - 从上到下依次展开，延迟 100ms

2. **进度条动画**：
   - 平滑的渐变色（蓝 → 绿）
   - 使用 spring 动画，避免线性运动

3. **状态图标**：
   - 待处理（⏳）：静态灰色
   - 进行中（🔄）：旋转动画，蓝色
   - 已完成（✅）：scale 弹出动画，绿色
   - 错误（❌）：shake 动画，红色

**组件代码**：

```tsx
// components/PipelineProgress.tsx

import { motion } from "framer-motion";

function PipelineProgress({ projectId }: { projectId: string }) {
  const [stages, setStages] = useState<Stage[]>([]);

  useEffect(() => {
    // 连接 WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      // 更新阶段状态
      setStages((prev) => updateStages(prev, message));
    };

    return () => ws.close();
  }, [projectId]);

  return (
    <div className="pipeline-container">
      {/* 顶部进度条 */}
      <StepProgressBar stages={stages} />

      {/* 阶段卡片列表 */}
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

**StageCard 组件**：

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
        {/* 左侧：图标 + 标题 */}
        <div className="flex items-center gap-3">
          <span className="text-2xl">{statusIcon[stage.status]}</span>
          <div>
            <h3 className="font-semibold">{stage.title}</h3>
            <p className="text-sm text-gray-600">{stage.message}</p>
          </div>
        </div>

        {/* 右侧：时长 */}
        {stage.duration && (
          <span className="text-sm text-gray-500">{stage.duration}s</span>
        )}
      </div>

      {/* 进度条（仅进行中） */}
      {stage.status === "in_progress" && stage.progress !== undefined && (
        <div className="mt-3">
          <ProgressBar progress={stage.progress} />
        </div>
      )}

      {/* 详细信息 */}
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

### 阶段 3：报告展示 + 溯源系统

#### 3.1 报告主视图

**布局**：

```
┌─────────────────────────────────┬──────────────────┐
│  报告内容（Markdown渲染）        │  溯源面板         │
├─────────────────────────────────┼──────────────────┤
│                                 │                  │
│ ## 执行摘要                     │  点击引用后显示： │
│                                 │                  │
│ Tesla Q3 2025 实现了创纪录的     │  📄 [^doc-p5]    │
│ 收入和现金流[^doc-p5][^gap-2]   │                  │
│         ↑ 悬停显示预览           │  来源：原始文档   │
│                                 │  位置：第5页 表2  │
│ ## 核心发现                     │                  │
│                                 │  [查看原文]       │
│ ### 1. 财务表现强劲             │                  │
│                                 │  ─────────────   │
│ 总收入达到 $28.1B，同比增长     │                  │
│ 12%[^doc-p5]，但营业利润率      │  🌐 [^gap-2]     │
│ 下降至 8.5%...                  │                  │
│                                 │  来源：外部研究   │
│ [图表：收入趋势][^fig_004]      │  标题：Tesla...  │
│                                 │  [访问链接]       │
│                                 │                  │
└─────────────────────────────────┴──────────────────┘
```

**引用交互**：

1. **悬停预览**：
   ```
   鼠标悬停在 [^doc-p5] 上
         ↓
   显示浮动卡片：
   ┌──────────────────┐
   │ 📄 文档引用       │
   │ 位置：第5页 表2   │
   │ 点击查看详情     │
   └──────────────────┘
   ```

2. **点击展开**：
   - 右侧溯源面板打开
   - 滚动到对应引用
   - 高亮当前查看的引用

3. **引用视觉区分**：
   ```css
   [^doc-p5]      → 📄 蓝色徽章（文档引用）
   [^fig_004.png] → 📊 绿色徽章（图表引用）
   [^gap-001-2]   → 🌐 橙色徽章（外部研究）
   ```

**组件代码**：

```tsx
// components/ReportViewer.tsx

function ReportViewer({ content, projectId }: ReportViewerProps) {
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  return (
    <div className="flex h-full">
      {/* 报告内容 */}
      <div className="flex-1 overflow-auto p-8">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // 拦截脚注渲染
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

      {/* 溯源面板 */}
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

**CitationLink 组件**（带悬停预览）：

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

      {/* 悬停预览卡片 */}
      {showPreview && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute z-10 mt-2 p-3 bg-white shadow-lg rounded-lg border w-48"
        >
          <div className="text-sm">
            {citationType === "document" && "📄 文档引用"}
            {citationType === "chart" && "📊 图表引用"}
            {citationType === "web" && "🌐 外部研究"}
          </div>
          <div className="text-xs text-gray-600 mt-1">点击查看详情</div>
        </motion.div>
      )}
    </span>
  );
}
```

#### 3.2 溯源面板详情

**文档引用展示**：

```tsx
function DocumentCitation({ citation }) {
  return (
    <div className="space-y-3">
      <div className="bg-blue-50 p-3 rounded-lg">
        <div className="text-sm text-gray-600">引用ID</div>
        <div className="font-mono text-blue-700 mt-1">{citation.id}</div>
      </div>

      <div className="bg-gray-50 p-3 rounded-lg">
        <div className="text-sm text-gray-600">文档位置</div>
        <div className="font-medium mt-1">{citation.location}</div>
      </div>

      {citation.source && (
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm text-gray-600">具体引用</div>
          <div className="font-medium mt-1">{citation.source}</div>
        </div>
      )}
    </div>
  );
}
```

**图表引用展示**（直接显示图片）：

```tsx
function ChartCitation({ citation, projectId }) {
  const imageUrl = `/api/projects/${projectId}/files/source/images/${citation.figure_id}`;

  return (
    <div className="space-y-4">
      {/* 图表标题 */}
      {citation.figure_analysis?.title && (
        <h4 className="font-medium text-gray-900">
          {citation.figure_analysis.title}
        </h4>
      )}

      {/* 图片展示 */}
      <div className="border rounded-lg overflow-hidden bg-white">
        <img
          src={imageUrl}
          alt={citation.figure_id}
          className="w-full h-auto"
        />
      </div>

      {/* 图表分析 */}
      {citation.figure_analysis?.analysis && (
        <div className="bg-gray-50 p-4 rounded-lg text-sm space-y-2">
          {Object.entries(citation.figure_analysis.analysis).map(
            ([key, value]) => (
              <div key={key}>
                <span className="font-medium text-gray-700">{key}：</span>
                <span className="text-gray-600">{value}</span>
              </div>
            )
          )}
        </div>
      )}

      {/* 文件名 */}
      <div className="text-xs text-gray-500 font-mono">
        {citation.figure_id}
      </div>
    </div>
  );
}
```

**外部链接引用展示**：

```tsx
function WebCitation({ citation }) {
  return (
    <div className="space-y-3">
      {/* 标题 + 链接 */}
      <a
        href={citation.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
      >
        {citation.title || citation.url}
        <ExternalLink className="w-4 h-4" />
      </a>

      {/* 内容摘要 */}
      {citation.content && (
        <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 leading-relaxed">
          {citation.content}
        </div>
      )}

      {/* 发布日期 */}
      {citation.published_date && (
        <div className="text-xs text-gray-500">
          发布于 {citation.published_date}
        </div>
      )}
    </div>
  );
}
```

---

## 项目管理侧边栏

### 布局

```
┌─────────────────┐
│ DeepFinance     │
├─────────────────┤
│                 │
│ [+ 新建项目]     │
│                 │
│ 📂 最近项目      │
│  ┌────────────┐ │
│  │ Tesla Q3   │ │
│  │ 2小时前    │ │
│  │ ✅ 已完成   │ │
│  └────────────┘ │
│                 │
│  ┌────────────┐ │
│  │ NVDA Q4    │ │
│  │ 昨天       │ │
│  │ 🔄 分析中   │ │
│  └────────────┘ │
│                 │
│ 📁 全部项目      │
│ ⚙️  设置         │
│ 📖 使用指南      │
│                 │
└─────────────────┘
```

### 项目卡片

**悬停效果**：
- 背景色变深
- 显示快捷操作按钮：重新分析、导出、删除

**状态指示**：
- 🔄 处理中（蓝色动画）
- ✅ 已完成（绿色）
- ❌ 失败（红色）

**代码**：

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

      {/* 元数据 */}
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

## 组件库

### 1. FileUploadZone

**功能**：拖拽上传 + 点击上传

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
      <p>拖拽文件到此 或 点击上传</p>
      <p className="text-sm text-gray-500">支持 PDF，最大 50MB</p>
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

**功能**：平滑渐变进度条

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

**功能**：顶部步骤条

```tsx
function StepProgressBar({ stages }: { stages: Stage[] }) {
  const stepNames = ["解析", "分析", "研究", "生成"];

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

            {/* 连接线 */}
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

### 4. CitationModal（移动端）

**功能**：移动端引用弹窗

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
          {/* 标题栏 */}
          <div className="modal-header">
            <h3>
              {citation?.type === "document" && "📄 文档引用"}
              {citation?.type === "chart" && "📊 图表引用"}
              {citation?.type === "web" && "🌐 外部研究"}
            </h3>
            <button onClick={onClose}>✕</button>
          </div>

          {/* 内容 */}
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

## 动画配置

### Framer Motion 预设

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

## 样式配置

### Tailwind 配置

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

## 响应式设计

### 断点策略

```css
/* 移动端：< 768px */
@media (max-width: 767px) {
  .sidebar {
    display: none; /* 隐藏侧边栏 */
  }
  .citation-panel {
    display: none; /* 溯源面板改为模态框 */
  }
}

/* 平板：768px - 1024px */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar {
    width: 200px; /* 缩窄侧边栏 */
  }
  .citation-panel {
    width: 300px; /* 缩窄溯源面板 */
  }
}

/* 桌面：>= 1024px */
@media (min-width: 1024px) {
  /* 默认布局 */
}
```

---

## 性能优化

### 1. 虚拟滚动

对于长报告，使用 `react-window` 实现虚拟滚动。

### 2. 懒加载图片

```tsx
import { LazyLoadImage } from "react-lazy-load-image-component";

<LazyLoadImage
  src={imageUrl}
  alt="Chart"
  placeholder={<Skeleton />}
  effect="blur"
/>;
```

### 3. Markdown 渲染优化

使用 `React.memo` 缓存 Markdown 渲染结果。

```tsx
const MemoizedMarkdown = React.memo(ReactMarkdown);
```

---

## 总结

### 设计亮点

✅ **渐进式展示**：从欢迎页 → 流程可视化 → 报告展示，分步引导
✅ **实时反馈**：WebSocket 推送 + 流畅动画，150秒不枯燥
✅ **溯源可见**：三种引用类型，图表直接展示图片
✅ **响应式**：桌面/移动端自适应布局

### 技术栈

- **React 18** + TypeScript
- **Tailwind CSS** + Framer Motion
- **React Markdown** + remark-gfm
- **WebSocket** 实时通信

### 下一步

1. 创建前端项目脚手架
2. 实现核心组件库
3. 集成 API 和 WebSocket
4. 测试和优化
