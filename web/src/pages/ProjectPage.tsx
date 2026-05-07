import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react';
import { Layout } from '../components/layout';
import { CitationPanel, type ParsedCitation } from '../components/report';
import { QAFloatingButton } from '../components/qa';
import { Button, Card } from '../components/ui';
import { getProject, getReport, getCitation } from '../api';
import type { ProjectDetail, ReportContent, PDFHighlight } from '../types';
import { fadeInUp } from '../lib/animations';

// Lazy load heavy components for better code splitting
const PipelineProgress = lazy(() =>
  import('../components/pipeline').then(m => ({ default: m.PipelineProgress }))
);
const ReportViewer = lazy(() =>
  import('../components/report').then(m => ({ default: m.ReportViewer }))
);
const PDFViewer = lazy(() => import('../components/pdf/PDFViewer'));
const QAPanel = lazy(() =>
  import('../components/qa').then(m => ({ default: m.QAPanel }))
);

type ViewState = 'loading' | 'processing' | 'report' | 'error';
type PanelMode = 'citation' | 'qa' | null;

// Loading fallback for lazy loaded components
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-gold-400 mx-auto mb-4" />
        <p className="text-gray-500">加载组件中...</p>
      </div>
    </div>
  );
}

export function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [viewState, setViewState] = useState<ViewState>('loading');
  const [_project, setProject] = useState<ProjectDetail | null>(null);
  const [report, setReport] = useState<ReportContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  // _project is stored for future use (e.g., displaying project metadata)

  // Panel mode state
  const [panelMode, setPanelMode] = useState<PanelMode>(null);

  // Citation panel state
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<ParsedCitation | null>(null);
  const [showCitationPanel, setShowCitationPanel] = useState(false);

  // QA panel state
  const [showQAPanel, setShowQAPanel] = useState(false);

  // PDF viewer state
  const [showPDFViewer, setShowPDFViewer] = useState(false);
  const [pdfHighlight, setPdfHighlight] = useState<PDFHighlight | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  // Load project data
  useEffect(() => {
    if (!projectId) return;

    // Reset all panel/viewer state when project changes
    setShowPDFViewer(false);
    setPdfUrl(null);
    setPdfHighlight(null);
    setShowCitationPanel(false);
    setActiveCitationId(null);
    setActiveCitation(null);
    setShowQAPanel(false);
    setPanelMode(null);

    const loadProject = async () => {
      setViewState('loading');
      setError(null);

      try {
        const projectData = await getProject(projectId);
        setProject(projectData);

        // Determine view state based on project status
        if (projectData.status === 'completed') {
          // Load report
          const reportData = await getReport(projectId, 'markdown');
          setReport(reportData);
          setViewState('report');
        } else if (projectData.status === 'processing') {
          setViewState('processing');
        } else if (projectData.status === 'failed') {
          setError('项目处理失败');
          setViewState('error');
        }
      } catch (err) {
        console.error('Failed to load project:', err);
        setError('加载项目失败');
        setViewState('error');
      }
    };

    loadProject();
  }, [projectId]);

  // Handle pipeline completion
  const handlePipelineComplete = useCallback(async () => {
    if (!projectId) return;

    try {
      const reportData = await getReport(projectId, 'markdown');
      setReport(reportData);
      setViewState('report');
    } catch (err) {
      console.error('Failed to load report:', err);
      setError('加载报告失败');
      setViewState('error');
    }
  }, [projectId]);

  // Handle citation click
  const handleCitationClick = useCallback(async (citationId: string, citation?: ParsedCitation) => {
    if (!projectId) return;

    console.log('🔗 Citation clicked:', citationId);
    setActiveCitationId(citationId);
    setActiveCitation(citation || null);

    try {
      // Fetch full citation data from API
      const fullCitation = await getCitation(projectId, citationId);
      console.log('🔗 Citation API response:', fullCitation);

      // For document/chart citations with PDF highlight, open PDF viewer
      if (
        (fullCitation.type === 'document' || fullCitation.type === 'chart') &&
        fullCitation.pdf_highlight &&
        fullCitation.pdf_url
      ) {
        console.log('🔗 Opening PDF viewer with highlight:', fullCitation.pdf_highlight);
        setPdfHighlight(fullCitation.pdf_highlight);
        setPdfUrl(fullCitation.pdf_url);
        setShowPDFViewer(true);
        setShowCitationPanel(false);
      } else {
        console.log('🔗 Showing citation panel (no PDF highlight)');
        // For web citations or citations without PDF, show citation panel
        setShowCitationPanel(true);
        setPanelMode('citation');
        setShowPDFViewer(false);
      }
    } catch (err) {
      console.error('Failed to fetch citation:', err);
      // Fallback to showing citation panel
      setShowCitationPanel(true);
        setPanelMode('citation');
    }
  }, [projectId]);

  // Open QA panel
  const handleOpenQA = useCallback(() => {
    setShowCitationPanel(false);
    setShowPDFViewer(false);
    setShowQAPanel(true);
    setPanelMode('qa');
  }, []);

  // Close QA panel
  const handleCloseQA = useCallback(() => {
    setShowQAPanel(false);
    setPanelMode(null);
  }, []);

  // Handle QA citation click (switch to citation panel)
  const handleQACitationClick = useCallback(
    async (citationId: string) => {
      setShowQAPanel(false);
      // Use existing citation click handler
      await handleCitationClick(citationId);
    },
    [handleCitationClick]
  );

  // Close citation panel
  const handleCloseCitationPanel = useCallback(() => {
    setShowCitationPanel(false);
    // Delay clearing the data for exit animation
    setTimeout(() => {
      setActiveCitationId(null);
      setActiveCitation(null);
      setPanelMode(null);
    }, 300);
  }, []);

  // Close PDF viewer
  const handleClosePDFViewer = useCallback(() => {
    setShowPDFViewer(false);
    // Delay clearing the data for exit animation
    setTimeout(() => {
      setPdfHighlight(null);
      setPdfUrl(null);
    }, 300);
  }, []);

  // Render content based on view state
  const renderContent = () => {
    switch (viewState) {
      case 'loading':
        return (
          <div className="flex items-center justify-center h-full">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center"
            >
              <Loader2 className="w-8 h-8 animate-spin text-gold-400 mx-auto mb-4" />
              <p className="text-gray-500">加载中...</p>
            </motion.div>
          </div>
        );

      case 'processing':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <PipelineProgress
              projectId={projectId!}
              onComplete={handlePipelineComplete}
            />
          </Suspense>
        );

      case 'report':
        return (
          <Suspense fallback={<LoadingFallback />}>
            <ReportViewer
              report={report!}
              projectId={projectId!}
              onCitationClick={handleCitationClick}
            />
          </Suspense>
        );

      case 'error':
        return (
          <motion.div
            variants={fadeInUp}
            initial="initial"
            animate="animate"
            className="max-w-md mx-auto p-8"
          >
            <Card variant="default" padding="lg" className="text-center">
              <div className="w-16 h-16 rounded-full bg-coral-500/20 flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-coral-400" />
              </div>
              <h2 className="text-xl font-display font-semibold text-gray-900 mb-2">
                出错了
              </h2>
              <p className="text-gray-500 mb-6">{error}</p>
              <div className="flex gap-3 justify-center">
                <Button
                  variant="secondary"
                  onClick={() => navigate('/')}
                  icon={<ArrowLeft className="w-4 h-4" />}
                >
                  返回首页
                </Button>
                <Button
                  variant="gold"
                  onClick={() => window.location.reload()}
                >
                  重试
                </Button>
              </div>
            </Card>
          </motion.div>
        );
    }
  };

  // Determine which panel to show
  const sidePanelContent = panelMode === 'qa' ? (
    <Suspense fallback={<LoadingFallback />}>
      <QAPanel
        projectId={projectId!}
        onClose={handleCloseQA}
        onCitationClick={handleQACitationClick}
      />
    </Suspense>
  ) : panelMode === 'citation' ? (
    <CitationPanel
      citationId={activeCitationId}
      citation={activeCitation}
      projectId={projectId!}
      onClose={handleCloseCitationPanel}
    />
  ) : null;

  return (
    <Layout
      showSidePanel={(showCitationPanel || showQAPanel) && viewState === 'report'}
      sidePanel={sidePanelContent}
      showSplitView={showPDFViewer && viewState === 'report'}
      splitContent={
        pdfUrl && pdfHighlight ? (
          <Suspense fallback={<LoadingFallback />}>
            <PDFViewer
              key={`pdf-${activeCitationId || 'default'}`}
              url={pdfUrl}
              highlight={pdfHighlight}
              onClose={handleClosePDFViewer}
            />
          </Suspense>
        ) : null
      }
      onCloseSplitView={handleClosePDFViewer}
    >
      {renderContent()}

      {/* Floating QA Button */}
      <AnimatePresence>
        {viewState === 'report' && !showQAPanel && (
          <QAFloatingButton onClick={handleOpenQA} />
        )}
      </AnimatePresence>
    </Layout>
  );
}
