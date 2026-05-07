import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Layout } from './components/layout';
import { WelcomePage, ProjectPage } from './pages';
import { ToastProvider } from './components/ui';
import './index.css';

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <AnimatePresence mode="wait">
          <Routes>
            {/* Welcome / Upload Page */}
            <Route
              path="/"
              element={
                <Layout>
                  <WelcomePage />
                </Layout>
              }
            />

            {/* Project Page - Pipeline & Report */}
            <Route path="/projects/:projectId" element={<ProjectPage />} />

            {/* All Projects (placeholder) */}
            <Route
              path="/all-projects"
              element={
                <Layout>
                  <div className="flex items-center justify-center h-full">
                    <p className="text-slate-500">全部项目页面开发中...</p>
                  </div>
                </Layout>
              }
            />

            {/* Settings (placeholder) */}
            <Route
              path="/settings"
              element={
                <Layout>
                  <div className="flex items-center justify-center h-full">
                    <p className="text-slate-500">设置页面开发中...</p>
                  </div>
                </Layout>
              }
            />

            {/* Guide (placeholder) */}
            <Route
              path="/guide"
              element={
                <Layout>
                  <div className="flex items-center justify-center h-full">
                    <p className="text-slate-500">使用指南开发中...</p>
                  </div>
                </Layout>
              }
            />

            {/* Redirect unknown routes to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
