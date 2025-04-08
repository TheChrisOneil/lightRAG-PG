/**
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 *
 * Description: Chat for TechNexusClarity-specific features.
 * Owner: TechNexusClarity
 */
import { ReactNode, useCallback, useState } from 'react'
import useTheme from '@/hooks/useTheme'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/utils'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeReact from 'rehype-react'
import remarkMath from 'remark-math'

import type { Element } from 'hast'
import type { DialogTurn } from '@/api/lightrag_tnc'

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight, oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'

import { LoaderIcon, CopyIcon } from 'lucide-react'

export const ChatMessage = ({
  reply,
  isFirstMessage = false,
}: {
  reply: DialogTurn
  isFirstMessage?: boolean
}) => {
  const handleCopyMarkdown = useCallback(async () => {
    const contentToCopy = reply.coachMessage?.content || reply.userMessage?.content
    if (contentToCopy) {
      try {
        await navigator.clipboard.writeText(contentToCopy)
      } catch (err) {
        console.error('Failed to copy:', err)
      }
    }
  }, [reply])

  const contentToDisplay =
    (reply.coachMessage?.content?.trim?.() || reply.userMessage?.content?.trim?.()) ?? ''
  const role = reply.coachMessage?.speaker ?? reply.userMessage?.speaker
  const isError = false

  return (
    <>
      {isFirstMessage && (
        <div className="text-center text-muted-foreground text-xs mb-2">
          New Conversation Started
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          role === 'coach' || role === 'doctor'
            ? isError
              ? 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400'
              : 'bg-muted'
            : 'bg-primary text-primary-foreground'
        }`}
      >
        <pre className="relative break-words whitespace-pre-wrap">
          <ReactMarkdown
            className="dark:prose-invert max-w-none text-sm"
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeReact]}
            skipHtml={false}
            components={{ code: CodeHighlight }}
          >
            {contentToDisplay || ''}
          </ReactMarkdown>
          {(role === 'coach' || role === 'doctor') && contentToDisplay?.length > 0 && (
            <Button
              onClick={handleCopyMarkdown}
              className="absolute right-0 bottom-0 size-6 rounded-md opacity-20 transition-opacity hover:opacity-100"
              tooltip="Copy to clipboard"
              variant="default"
              size="icon"
            >
              <CopyIcon />
            </Button>
          )}
        </pre>
        {contentToDisplay?.length === 0 && <LoaderIcon className="animate-spin duration-2000" />}
      </div>
    </>
  )
}

interface CodeHighlightProps {
  inline?: boolean
  className?: string
  children?: ReactNode
  node?: Element
}

const isInlineCode = (node: Element): boolean => {
  const textContent = (node.children || [])
    .filter((child) => child.type === 'text')
    .map((child) => (child as any).value)
    .join('')

  return !textContent.includes('\n')
}

const CodeHighlight = ({ className, children, node, ...props }: CodeHighlightProps) => {
  const { theme } = useTheme()
  const match = className?.match(/language-(\w+)/)
  const language = match ? match[1] : undefined
  const inline = node ? isInlineCode(node) : false

  return !inline ? (
    <SyntaxHighlighter
      style={theme === 'dark' ? oneDark : oneLight}
      PreTag="div"
      language={language}
      {...props}
    >
      {String(children).replace(/\n$/, '')}
    </SyntaxHighlighter>
  ) : (
    <code
      className={cn(className, 'mx-1 rounded-xs bg-black/10 px-1 dark:bg-gray-100/20')}
      {...props}
    >
      {children}
    </code>
  )
}

export const ConversationStartInstructions = ({
  conversationHistory,
  onSubmit,
}: {
  conversationHistory: DialogTurn[]
  onSubmit: (speaker: 'student' | 'coach', content: string) => void
}) => {
  const [content, setContent] = useState('')
  const [speaker, setSpeaker] = useState<'student' | 'coach' | null>(null)

  if (conversationHistory.length > 0) return null

  console.log('Conversation is empty. Starting a new one.')

  return (
    <div className="mb-4 text-sm text-muted-foreground">
      <p className="mb-2">Conversation history is currently empty.</p>
      <p>You can start the conversation either as a student or a coach by entering a message below.</p>

      <div className="mt-4 space-y-4">
        <div>
          <label htmlFor="studentInput" className="block mb-1 font-medium">Student Message:</label>
          <input
            id="studentInput"
            type="text"
            value={speaker === 'student' ? content : ''}
            onChange={(e) => {
              setSpeaker('student')
              setContent(e.target.value)
            }}
            placeholder="Type student message here..."
            className="w-full rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="coachInput" className="block mb-1 font-medium">Coach Reply:</label>
          <input
            id="coachInput"
            type="text"
            value={speaker === 'coach' ? content : ''}
            onChange={(e) => {
              setSpeaker('coach')
              setContent(e.target.value)
            }}
            placeholder="Type coach reply here..."
            className="w-full rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <div className="mt-2 flex justify-end">
          <button
            type="button"
            onClick={() => {
              if (speaker && content.trim()) {
                onSubmit(speaker, content.trim())
                setContent('')
                setSpeaker(null)
              }
            }}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Start Conversation
          </button>
        </div>
      </div>
    </div>
  )
}

export const ConversationContinueInstructions = ({
  lastSpeaker,
  onSubmit,
}: {
  lastSpeaker: 'student' | 'coach'
  onSubmit: (speaker: 'student' | 'coach', content: string) => void
}) => {
  const [content, setContent] = useState('')

  const nextSpeaker = lastSpeaker === 'student' ? 'coach' : 'student'
  const label = nextSpeaker === 'student' ? 'Student Message' : 'Coach Reply'

  return (
    <div className="mb-4 text-sm text-muted-foreground">
      <p className="mb-2">Continue the conversation by entering a message from the next speaker.</p>

      <div className="mt-4 space-y-4">
        <div>
          <label htmlFor="nextInput" className="block mb-1 font-medium">{label}:</label>
          <input
            id="nextInput"
            type="text"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={`Type ${nextSpeaker} message here...`}
            className="w-full rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <div className="mt-2 flex justify-end">
          <button
            type="button"
            onClick={() => {
              if (content.trim()) {
                onSubmit(nextSpeaker, content.trim())
                setContent('')
              }
            }}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Submit Message
          </button>
        </div>
      </div>
    </div>
  )
}
