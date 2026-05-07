import { useMemo, useCallback, memo, useRef, type ComponentProps, type ReactNode, isValidElement } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion } from 'framer-motion';
import { FileText, Calendar, Cpu, ExternalLink, BarChart3 } from 'lucide-react';
import { CitationLink } from './CitationLink';
import { Card } from '../ui';
import type { ReportContent } from '../../types';
import { formatDateTime, extractCitationId, getCitationType, cn } from '../../lib/utils';
import { fadeInUp } from '../../lib/animations';

// Recursively extract text content from React children
// This prevents [object Object] from appearing when children contains React elements
function getTextContent(children: ReactNode): string {
  if (children === null || children === undefined) {
    return '';
  }
  if (typeof children === 'string' || typeof children === 'number') {
    return String(children);
  }
  if (Array.isArray(children)) {
    return children.map(getTextContent).join('');
  }
  if (isValidElement(children)) {
    const props = children.props as { children?: ReactNode };
    return getTextContent(props.children);
  }
  return '';
}

// Strip outer markdown code fence if LLM wrapped the output
function stripMarkdownCodeFence(content: string): string {
  const trimmed = content.trim();
  // Match ```markdown or ``` at the start and ``` at the end
  const match = trimmed.match(/^```(?:markdown)?\s*\n?([\s\S]*?)\n?```\s*$/);
  if (match) {
    return match[1].trim();
  }
  return content;
}

// Parsed citation data from footnotes
export interface ParsedCitation {
  id: string;
  type: 'document' | 'chart' | 'web';
  title?: string;
  url?: string;
  location?: string;
  source?: string; // Original text excerpt for documents
  imagePath?: string; // For charts
}

// Extract all citation data from footnote definitions in markdown
function extractFootnoteData(content: string): Map<string, ParsedCitation> {
  const citations = new Map<string, ParsedCitation>();

  // Match all footnote definitions
  // Format: [^citation-id]: content
  const footnoteRegex = /\[\^([^\]]+)\]:\s*(.+?)(?=\n\[\^|\n\n|\n---|$)/gs;
  let match;

  while ((match = footnoteRegex.exec(content)) !== null) {
    const citationId = match[1];
    // Normalize to lowercase for case-insensitive lookup
    // (remark-gfm may lowercase the IDs in href)
    const normalizedId = citationId.toLowerCase();
    const footnoteContent = match[2].trim();
    const type = getCitationType(citationId);

    if (type === 'document') {
      // Document format: [章节标题](location) | 原文："..."
      const docMatch = footnoteContent.match(/\[([^\]]*)\]\(([^)]+)\)(?:\s*\|\s*原文[：:]\s*[""]([^""]+)[""])?/);
      if (docMatch) {
        citations.set(normalizedId, {
          id: citationId, // Keep original ID for display
          type: 'document',
          title: docMatch[1],
          location: docMatch[2],
          source: docMatch[3],
        });
      }
    } else if (type === 'chart') {
      // Chart format: [图表标题](image_path)
      const chartMatch = footnoteContent.match(/\[([^\]]*)\]\(([^)]+)\)/);
      if (chartMatch) {
        citations.set(normalizedId, {
          id: citationId,
          type: 'chart',
          title: chartMatch[1],
          imagePath: chartMatch[2],
        });
      }
    } else if (type === 'web') {
      // Web format: [标题](url)
      const webMatch = footnoteContent.match(/\[([^\]]*)\]\((https?:\/\/[^)]+)\)/);
      if (webMatch) {
        citations.set(normalizedId, {
          id: citationId,
          type: 'web',
          title: webMatch[1],
          url: webMatch[2],
        });
      }
    }
  }

  return citations;
}

interface ReportViewerProps {
  report: ReportContent;
  projectId: string;
  onCitationClick: (citationId: string, citation?: ParsedCitation) => void;
}

const ReportViewerComponent = ({
  report,
  projectId,
  onCitationClick,
}: ReportViewerProps) => {
  // Counter for footnotes - use ref to avoid module-level mutable state
  const footnoteCounterRef = useRef(0);

  // Clean content by removing outer markdown code fence if present
  const cleanedContent = useMemo(
    () => stripMarkdownCodeFence(report.content),
    [report.content]
  );

  // Extract all citation data from report footnotes
  const citationData = useMemo(
    () => extractFootnoteData(cleanedContent),
    [cleanedContent]
  );

  // Handle citation click - for web type, open URL directly; for others, show panel
  const handleCitationClick = useCallback((citationId: string) => {
    // Normalize to lowercase for lookup (matches how we store in citationData)
    const citation = citationData.get(citationId.toLowerCase());
    const type = getCitationType(citationId);

    if (type === 'web' && citation?.url) {
      // Web citations open directly in new tab
      window.open(citation.url, '_blank', 'noopener,noreferrer');
      return;
    }

    // For document/chart, enrich with projectId for image URLs
    if (citation && type === 'chart' && citation.imagePath) {
      // Build image URL from project path
      citation.url = `/api/projects/${projectId}/files/${citation.imagePath}`;
    }

    // Pass citation data to panel
    onCitationClick(citationId, citation);
  }, [citationData, projectId, onCitationClick]);

  // Custom components for ReactMarkdown
  const components = useMemo(
    () =>
      ({
        // Intercept sup tags to handle footnote references
        sup: ({ children, ...props }) => {
          // Use getTextContent to safely extract text from children
          const text = getTextContent(children);
          const citationId = extractCitationId(text);

          if (citationId) {
            return (
              <CitationLink citationId={citationId} onClick={handleCitationClick}>
                {text}
              </CitationLink>
            );
          }

          // For remark-gfm rendered footnotes, the sup contains an <a> tag
          // We handle it by making the whole sup clickable
          return <sup {...props}>{children}</sup>;
        },

        // Custom link handling for citation definitions and footnote links
        a: ({ href, children, ...props }) => {
          // Use getTextContent to safely extract text from children
          const text = getTextContent(children);

          // Check if this is a footnote reference link (rendered by remark-gfm)
          // Format: href="#user-content-fn-doc-p2" or href="#fn-doc-p2"
          if (href?.includes('fn-')) {
            const fnMatch = href.match(/fn-(.+)$/);
            if (fnMatch) {
              // Decode URL-encoded characters (Chinese characters, etc.)
              // and restore original case if needed
              const citationId = decodeURIComponent(fnMatch[1]);
              return (
                <CitationLink
                  citationId={citationId}
                  onClick={handleCitationClick}
                >
                  {text}
                </CitationLink>
              );
            }
          }

          // Check if this is a footnote back-reference (↩)
          if (href?.includes('fnref-') || text === '↩') {
            return (
              <span className="text-gold-500 cursor-pointer hover:text-gold-400">
                {text}
              </span>
            );
          }

          // Check if this is a footnote definition link [^xxx]
          const citationMatch = text.match(/\[\^([^\]]+)\]/);
          if (citationMatch) {
            const citationId = citationMatch[1];
            return (
              <CitationLink
                citationId={citationId}
                onClick={handleCitationClick}
              >
                {text}
              </CitationLink>
            );
          }

          // Regular links
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gold-400 hover:text-gold-300 transition-colors underline decoration-gold-500/30 hover:decoration-gold-400"
              {...props}
            >
              {children}
            </a>
          );
        },

        // Handle footnote section (rendered by remark-gfm at bottom of document)
        section: ({ children, ...props }) => {
          // Check if this is the footnotes section
          const dataFootnotes = (props as Record<string, unknown>)['data-footnotes'];
          if (dataFootnotes) {
            // Traditional academic style - simple and understated
            return (
              <section className="mt-12 pt-6 border-t-2 border-gray-200" {...props}>
                <h4 className="text-base font-semibold text-gray-600 mb-4 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-gray-400" />
                  References
                </h4>
                <div className="footnotes-container text-gray-500">
                  {children}
                </div>
              </section>
            );
          }
          return <section {...props}>{children}</section>;
        },

        // Custom heading styles
        h1: ({ children, ...props }) => (
          <h1
            className="text-3xl font-display font-bold text-gray-900 mt-8 mb-4 first:mt-0"
            {...props}
          >
            {children}
          </h1>
        ),
        h2: ({ children, ...props }) => (
          <h2
            className="text-2xl font-display font-semibold text-gray-900 mt-8 mb-3 pb-2 border-b border-gray-200"
            {...props}
          >
            {children}
          </h2>
        ),
        h3: ({ children, ...props }) => (
          <h3
            className="text-xl font-display font-semibold text-gray-800 mt-6 mb-2"
            {...props}
          >
            {children}
          </h3>
        ),
        h4: ({ children, ...props }) => (
          <h4
            className="text-lg font-display font-medium text-gray-800 mt-4 mb-2"
            {...props}
          >
            {children}
          </h4>
        ),

        // Paragraph
        p: ({ children, ...props }) => (
          <p className="text-gray-700 leading-relaxed mb-4" {...props}>
            {children}
          </p>
        ),

        // Lists
        ul: ({ children, ...props }) => (
          <ul
            className="list-disc list-inside space-y-2 mb-4 text-gray-700"
            {...props}
          >
            {children}
          </ul>
        ),
        ol: ({ children, ...props }) => {
          // Check if this is a footnotes list (has data-footnotes parent or specific structure)
          const id = (props as Record<string, unknown>)['id'];
          const isFootnotesList = typeof id === 'string' && id.includes('footnote');

          if (isFootnotesList) {
            // Reset footnote counter for this list
            footnoteCounterRef.current = 0;
            return (
              <ol
                className="space-y-3"
                style={{
                  listStyle: 'none',
                  paddingLeft: 0,
                }}
                {...props}
              >
                {children}
              </ol>
            );
          }
          return (
            <ol
              className="list-decimal list-inside space-y-2 mb-4 text-gray-700"
              {...props}
            >
              {children}
            </ol>
          );
        },
        li: ({ children, ...props }) => {
          // Check if this is a footnote item (has id like "user-content-fn-xxx")
          const id = (props as Record<string, unknown>)['id'];
          const isFootnoteItem = typeof id === 'string' && id.includes('fn-');

          if (isFootnoteItem) {
            // Extract citation ID from the id attribute
            const citationIdMatch = typeof id === 'string' ? id.match(/fn-(.+)$/) : null;
            const citationId = citationIdMatch ? citationIdMatch[1] : null;
            const type = citationId ? getCitationType(citationId) : 'document';

            // Extract text content to parse title and quote
            const textContent = getTextContent(children);

            // Parse footnote format: [Title](url) | 原文："quote" ↩
            const parseFootnote = (text: string) => {
              // Match pattern: [Title](url) | 原文："quote"
              const match = text.match(/\[([^\]]+)\]\([^)]+\)\s*\|\s*原文[：:]\s*["""]([^"""]+)["""]/);
              if (match) {
                return {
                  title: match[1],
                  quote: match[2],
                };
              }
              // Fallback: try to extract at least the title
              const titleMatch = text.match(/\[([^\]]+)\]/);
              return {
                title: titleMatch ? titleMatch[1] : null,
                quote: null,
              };
            };

            const parsed = parseFootnote(textContent);

            // Style based on citation type
            const typeStyles = {
              document: {
                bg: 'bg-electric-500/5',
                border: 'border-electric-500/20',
                icon: <FileText className="w-4 h-4 text-electric-400" />,
                titleColor: 'text-electric-300',
                quoteAccent: 'border-l-electric-500',
              },
              chart: {
                bg: 'bg-mint-500/5',
                border: 'border-mint-500/20',
                icon: <BarChart3 className="w-4 h-4 text-mint-400" />,
                titleColor: 'text-mint-300',
                quoteAccent: 'border-l-mint-500',
              },
              web: {
                bg: 'bg-gold-500/5',
                border: 'border-gold-500/20',
                icon: <ExternalLink className="w-4 h-4 text-gold-400" />,
                titleColor: 'text-gold-300',
                quoteAccent: 'border-l-gold-500',
              },
            };

            const style = typeStyles[type];

            // Increment counter for this footnote
            footnoteCounterRef.current++;
            const currentNumber = footnoteCounterRef.current;

            // Traditional academic style - clean and compact
            return (
              <li
                className="pb-3 mb-3 border-b border-gray-200 last:border-b-0 last:mb-0"
                style={{ listStyle: 'none' }}
                {...props}
              >
                <div className="flex gap-2.5 items-start">
                  {/* Footnote Number - compact style */}
                  <div className="flex-shrink-0 w-6 text-gray-400 text-xs font-medium leading-[1.25rem]">
                    {currentNumber}.
                  </div>

                  {/* Icon - smaller and subtle */}
                  <div className="flex-shrink-0 mt-[0.125rem] opacity-60">
                    {style.icon}
                  </div>

                  {/* Content - compact and traditional */}
                  <div className="flex-1 min-w-0">
                    {/* Title - emphasized but not too bold */}
                    {parsed.title && (
                      <div className={cn('text-sm font-medium leading-tight mb-1', style.titleColor)}>
                        {parsed.title}
                      </div>
                    )}

                    {/* Original Quote - indented, smaller, gray */}
                    {parsed.quote && (
                      <blockquote className="mt-1 pl-4 border-l border-gray-300 text-xs text-gray-500 leading-relaxed font-serif italic">
                        "{parsed.quote}"
                      </blockquote>
                    )}

                    {/* Fallback */}
                    {!parsed.title && !parsed.quote && (
                      <div className="text-xs text-gray-500 leading-relaxed">
                        {children}
                      </div>
                    )}
                  </div>
                </div>
              </li>
            );
          }

          return (
            <li className="text-gray-700" {...props}>
              {children}
            </li>
          );
        },

        // Blockquote
        blockquote: ({ children, ...props }) => (
          <blockquote
            className="border-l-4 border-gold-500 bg-gray-50 px-4 py-3 my-4 rounded-r-lg"
            {...props}
          >
            {children}
          </blockquote>
        ),

        // Code
        code: ({ className, children, ...props }) => {
          const isInline = !className;
          if (isInline) {
            return (
              <code
                className="font-mono text-sm bg-gray-100 px-1.5 py-0.5 rounded text-gold-400"
                {...props}
              >
                {children}
              </code>
            );
          }
          return (
            <code
              className={cn('font-mono text-sm text-gray-700', className)}
              {...props}
            >
              {children}
            </code>
          );
        },
        pre: ({ children, ...props }) => (
          <pre
            className="bg-gray-50 border border-gray-200 rounded-xl p-4 overflow-x-auto my-4"
            {...props}
          >
            {children}
          </pre>
        ),

        // Table - responsive with horizontal scroll on mobile
        table: ({ children, ...props }) => (
          <div className="overflow-x-auto my-6 -mx-4 px-4 lg:mx-0 lg:px-0">
            <table className="min-w-full border-collapse text-sm" {...props}>
              {children}
            </table>
          </div>
        ),
        thead: ({ children, ...props }) => (
          <thead className="bg-gray-100" {...props}>
            {children}
          </thead>
        ),
        th: ({ children, ...props }) => (
          <th
            className="border border-gray-200 px-4 py-2 text-left font-semibold text-gray-800"
            {...props}
          >
            {children}
          </th>
        ),
        td: ({ children, ...props }) => (
          <td className="border border-gray-200 px-4 py-2 text-gray-700" {...props}>
            {children}
          </td>
        ),
        tr: ({ children, ...props }) => (
          <tr className="hover:bg-gray-50" {...props}>
            {children}
          </tr>
        ),

        // Horizontal rule
        hr: () => <hr className="border-gray-200 my-8" />,

        // Strong and emphasis
        strong: ({ children, ...props }) => (
          <strong className="font-semibold text-gray-900" {...props}>
            {children}
          </strong>
        ),
        em: ({ children, ...props }) => (
          <em className="italic text-gray-500" {...props}>
            {children}
          </em>
        ),

        // Images
        img: ({ src, alt, ...props }) => (
          <figure className="my-6">
            <img
              src={src}
              alt={alt}
              className="rounded-lg border border-gray-200 max-w-full"
              {...props}
            />
            {alt && (
              <figcaption className="text-sm text-gray-400 text-center mt-2">
                {alt}
              </figcaption>
            )}
          </figure>
        ),
      } as ComponentProps<typeof ReactMarkdown>['components']),
    [handleCitationClick]
  );

  return (
    <motion.div
      variants={fadeInUp}
      initial="initial"
      animate="animate"
      className="max-w-4xl mx-auto p-6 lg:p-8"
    >
      {/* Report Metadata */}
      <Card variant="default" padding="md" className="mb-8">
        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span className="font-medium text-gray-700">
              {report.metadata.title}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>{formatDateTime(report.metadata.generated_at)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            <span>{report.metadata.model}</span>
          </div>
        </div>
      </Card>

      {/* Report Content */}
      <article className="prose-deepfinance">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
          {cleanedContent}
        </ReactMarkdown>
      </article>
    </motion.div>
  );
};

// Memoize to prevent re-rendering when parent updates unrelated state
export const ReportViewer = memo(ReportViewerComponent);
