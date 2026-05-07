import { useState, useEffect, memo, useCallback, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Folder,
  Settings,
  BookOpen,
  ChevronDown,
  Loader2,
  CheckCircle2,
  XCircle,
  Menu,
  X,
} from 'lucide-react';
import { getProjects } from '../../api';
import type { Project } from '../../types';
import { cn } from '../../lib/utils';
import { staggerContainer, staggerItem } from '../../lib/animations';
import { ProjectListSkeleton, EmptyState } from '../ui';

export const Sidebar = memo(function Sidebar() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      const data = await getProjects(10, 0);
      setProjects(data.items);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleNewProject = useCallback(() => {
    navigate('/');
    setMobileOpen(false);
  }, [navigate]);

  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  const closeMobile = useCallback(() => {
    setMobileOpen(false);
  }, []);

  const toggleMobile = useCallback(() => {
    setMobileOpen(prev => !prev);
  }, []);

  // Memoize the current path to avoid unnecessary re-renders
  const currentPath = location.pathname;

  const SidebarContent = useMemo(() => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b border-gray-100">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center shadow-md shadow-gold-500/20">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          <div>
            <h1 className="font-display font-semibold text-gray-900 group-hover:text-gold-600 transition-colors">
              DeepFinance
            </h1>
            <p className="text-xs text-gray-400">文档智能分析</p>
          </div>
        </Link>
      </div>

      {/* New Project Button */}
      <div className="p-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleNewProject}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-gold-500 to-gold-600 rounded-xl text-white font-medium hover:from-gold-600 hover:to-gold-700 transition-all duration-300 shadow-sm shadow-gold-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>新建项目</span>
        </motion.button>
      </div>

      {/* Recent Projects */}
      <div className="flex-1 overflow-auto px-3">
        <button
          onClick={toggleExpanded}
          className="flex items-center gap-2 w-full px-2 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          <motion.span
            animate={{ rotate: isExpanded ? 0 : -90 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4" />
          </motion.span>
          <Folder className="w-4 h-4" />
          <span>最近项目</span>
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-1"
            >
              {loading ? (
                <ProjectListSkeleton count={4} />
              ) : projects.length === 0 ? (
                <EmptyState
                  icon={<Folder className="w-full h-full" />}
                  title="暂无项目"
                  description="点击上方按钮创建新项目"
                  compact
                />
              ) : (
                projects.map((project) => (
                  <motion.div key={project.project_id} variants={staggerItem}>
                    <ProjectItem
                      project={project}
                      isActive={currentPath.includes(project.project_id)}
                      onClick={closeMobile}
                    />
                  </motion.div>
                ))
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Actions */}
      <div className="p-3 border-t border-gray-100 space-y-1">
        <Link
          to="/all-projects"
          className="flex items-center gap-3 px-3 py-2 text-sm text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-all"
        >
          <Folder className="w-4 h-4" />
          <span>全部项目</span>
        </Link>
        <Link
          to="/settings"
          className="flex items-center gap-3 px-3 py-2 text-sm text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-all"
        >
          <Settings className="w-4 h-4" />
          <span>设置</span>
        </Link>
        <Link
          to="/guide"
          className="flex items-center gap-3 px-3 py-2 text-sm text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-all"
        >
          <BookOpen className="w-4 h-4" />
          <span>使用指南</span>
        </Link>
      </div>
    </div>
  ), [projects, loading, isExpanded, currentPath, handleNewProject, toggleExpanded, closeMobile]);

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-60 h-screen bg-white border-r border-gray-200 flex-col shadow-sm">
        {SidebarContent}
      </aside>

      {/* Mobile Menu Button */}
      <button
        onClick={toggleMobile}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 bg-white border border-gray-200 rounded-lg text-gray-600 hover:text-gray-900 transition-colors shadow-sm"
      >
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile Sidebar */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeMobile}
              className="fixed inset-0 bg-black/40 z-40 lg:hidden"
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed left-0 top-0 w-72 h-full bg-white border-r border-gray-200 z-50 lg:hidden shadow-xl"
            >
              {SidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
});

// Project Item Component - memoized to prevent unnecessary re-renders
interface ProjectItemProps {
  project: Project;
  isActive: boolean;
  onClick?: () => void;
}

const ProjectItem = memo(function ProjectItem({ project, isActive, onClick }: ProjectItemProps) {
  const statusIcon = useMemo(() => ({
    processing: <Loader2 className="w-3.5 h-3.5 animate-spin text-gold-500" />,
    completed: <CheckCircle2 className="w-3.5 h-3.5 text-mint-500" />,
    failed: <XCircle className="w-3.5 h-3.5 text-coral-500" />,
  }), []);

  return (
    <Link
      to={`/projects/${project.project_id}`}
      onClick={onClick}
      className={cn(
        'block px-3 py-2.5 rounded-lg transition-all duration-200',
        isActive
          ? 'bg-gold-50 border border-gold-200'
          : 'hover:bg-gray-100 border border-transparent'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h4
            className={cn(
              'text-sm font-medium truncate',
              isActive ? 'text-gold-700' : 'text-gray-800'
            )}
          >
            {project.title || '未命名项目'}
          </h4>
          {project.metadata?.company && (
            <div className="mt-1">
              <span className="text-xs text-gray-400 truncate">
                {project.metadata.company}
              </span>
            </div>
          )}
        </div>
        <div className="flex-shrink-0 mt-0.5">
          {statusIcon[project.status]}
        </div>
      </div>
    </Link>
  );
});
