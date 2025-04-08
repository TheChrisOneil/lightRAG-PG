/**
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 *
 * Description: Reply feature for coaching via TechNexusClarity-specific features.
 * Owner: TechNexusClarity
 */
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { useCallback, useEffect, useRef, useState } from 'react'
import { coachReplyText,
  coachReplyTextStream,
  ReplyRequest,
  CoachMessage,
  UserMessage
} from '@/api/lightrag_tnc'
import { errorMessage } from '@/lib/utils'
// import { useSettingsStore } from '@/stores/settings'
import { useCustomSettingsStore } from '@/stores/settings_tnc'
import { useDebounce } from '@/hooks/useDebounce'
import ReplySettings from '../components/reply_tnc/ReplySettings_tnc'
import { EraserIcon } from 'lucide-react'
import { 
  ConversationStartInstructions, 
  ConversationContinueInstructions 
} from '@/components/reply_tnc/ChatMessage_tnc'
import { useTranslation } from 'react-i18next'

export default function ReplyTesting() {
  const { t } = useTranslation()
  const messages = useCustomSettingsStore((state) => state.dialogTurns)
  const setMessages = useCustomSettingsStore((state) => state.setDialogTurns)
  const setReplySettings = useCustomSettingsStore((state) => state.updateReplySettings);

  const [isLoading, setIsLoading] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editValue, setEditValue] = useState('')
  const [conversationStarted, setConversationStarted] = useState(messages.length > 0);
  const messagesEndRef = useRef<HTMLDivElement>(null)


  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const handleConversation = async (selectedSpeaker: 'student' | 'coach', initialContent: string) => {
    const state = useCustomSettingsStore.getState()
    setIsLoading(true)
  
    // Always read from store to avoid stale data
    const updatedMessages = [...state.dialogTurns]
    const timestamp = new Date().toISOString()
    console.log('Starting conversation as:', selectedSpeaker)
  
    if (selectedSpeaker === 'coach') {
      // If coach initiates conversation
      const coachMsg: CoachMessage = {
        speaker: 'coach',
        content: initialContent,
        timestamp,
        aiSuggestions: [],
        selectedSuggestionIndex: -1,
        isFinalized: true,
      }
      // Create a brand-new turn with only a coach message
      updatedMessages.push({ coachMessage: coachMsg })
      setMessages(updatedMessages)
      setIsLoading(false)
      return
    }
  
    // Otherwise, student initiates or continues conversation
    const userMsg: UserMessage = {
      speaker: 'student',
      content: initialContent,
      timestamp,
      intent: state.replySettings.intent,
      sentiment: state.replySettings.sentiment,
      topic: state.replySettings.topic,
      sub_topic: state.replySettings.sub_topic,
      technique: state.replySettings.technique,
      level: state.replySettings.level,
    }
  
    // Create a new turn with user message
    updatedMessages.push({ userMessage: userMsg })
    setMessages(updatedMessages)
  
    const replyRequest: ReplyRequest = {
      ...state.replySettings,
      speaker: 'student',
      content: initialContent,
      timestamp,
      conversation_history: updatedMessages,
    }
    console.log('Reply Request:', replyRequest)
    try {
      if (state.replySettings.stream) {
        // Streaming scenario
        await coachReplyTextStream(
          replyRequest,
          (chunk: string) => {
            const response = JSON.parse(chunk) as { coachMessage: CoachMessage }
            const currentMessages = [...useCustomSettingsStore.getState().dialogTurns]
            const lastTurn = currentMessages[currentMessages.length - 1]
            if (!lastTurn) return
            lastTurn.coachMessage = {
              ...response.coachMessage,
              speaker: response.coachMessage.speaker || 'coach',
            }
            setMessages(currentMessages)
          }
        )
      } else {
        // Non-stream scenario
        const response = await coachReplyText(replyRequest)
        console.log('Response:', response)
  
        const currentMessages = [...useCustomSettingsStore.getState().dialogTurns]
        const lastTurn = currentMessages[currentMessages.length - 1]
        if (lastTurn) {
          lastTurn.coachMessage = {
            speaker: response.coachMessage?.speaker || 'coach',
            content: response.coachMessage?.content || '',
            aiSuggestions: response.coachMessage?.aiSuggestions || [],
            selectedSuggestionIndex: response.coachMessage?.selectedSuggestionIndex ?? -1,
            isFinalized: response.coachMessage?.isFinalized ?? false,
            timestamp: response.coachMessage?.timestamp || new Date().toISOString(),
          }
          // Update the reply settings state variables with tooltips
          const bestSuggestion = response.coachMessage?.aiSuggestions?.[0];
          if (bestSuggestion) {
            setReplySettings({
              intent: bestSuggestion.intent?.split(':')[0]?.trim() || 'Unknown',
              sentiment: bestSuggestion.sentiment?.split(':')[0]?.trim() || 'Unknown',
              topic: bestSuggestion.topic?.split(':')[0]?.trim() || 'Unknown',
              sub_topic: bestSuggestion.sub_topic?.split(':')[0]?.trim() || 'Unknown',
              technique: bestSuggestion.technique?.split(':')[0]?.trim() || 'Unknown',
              level: bestSuggestion.level?.split(':')[0]?.trim() || 'Unknown',
              tooltips: {
                intent: bestSuggestion.intent?.split(':')[1]?.trim() || '',
                sentiment: bestSuggestion.sentiment?.split(':')[1]?.trim() || '',
                topic: bestSuggestion.topic?.split(':')[1]?.trim() || '',
                sub_topic: bestSuggestion.sub_topic?.split(':')[1]?.trim() || '',
                technique: bestSuggestion.technique?.split(':')[1]?.trim() || '',
                level: bestSuggestion.level?.split(':')[1]?.trim() || '',
              }
            });
          }
          setMessages(currentMessages)
        }
      }
    } catch (err) {
      // Error scenario
      const currentMessages = [...useCustomSettingsStore.getState().dialogTurns]
      const lastTurn = currentMessages[currentMessages.length - 1]
      if (lastTurn) {
        if (!lastTurn.coachMessage) {
          lastTurn.coachMessage = {
            speaker: 'coach',
            content: `\nError: Failed to get response\n${errorMessage(err)}`,
            aiSuggestions: [],
            selectedSuggestionIndex: -1,
            isFinalized: false,
            timestamp,
          }
        } else {
          lastTurn.coachMessage.content = `\nError: Failed to get response\n${errorMessage(err)}`
        }
        setMessages(currentMessages)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const debouncedMessages = useDebounce(messages, 100)
  useEffect(() => {
    if (messages.length > 0 && !conversationStarted) {
      setConversationStarted(true);
    }
  }, [messages, conversationStarted]);
  useEffect(() => scrollToBottom(), [debouncedMessages, scrollToBottom])

  const clearMessages = useCallback(() => {
    setMessages([])
    setConversationStarted(false)
  }, [setMessages])

  return (
    <div className="flex size-full gap-2 px-2 pb-12">
      <div className="flex grow flex-col gap-4">
        {!conversationStarted ? (
          <ConversationStartInstructions conversationHistory={messages} onSubmit={handleConversation} />
        ) : (
          <ConversationContinueInstructions
            lastSpeaker={messages.length > 0 && messages[messages.length - 1].coachMessage?.content ? 'coach' : 'student'}
            onSubmit={handleConversation}
          />
        )}
        <div className="relative grow">
          <div className="bg-primary-foreground/60 absolute inset-0 flex flex-col overflow-auto rounded-lg border p-2">
            <div className="flex min-h-0 flex-1 flex-col gap-2">
              {messages.length === 0 ? (
                <div className="text-muted-foreground flex h-full items-center justify-center text-lg">
                  You can start the conversation either as a student or a coach by entering a message above.
                </div>
              ) : (
                messages.map((message, idx) => (
                  <div key={idx} className="flex flex-col gap-1 w-full">
                    {message.userMessage?.content && (
                      <>
                        <div className="text-sm font-semibold text-right text-blue-800">
                          {message.userMessage?.speaker?.toUpperCase?.() || 'UNKNOWN'}
                        </div>
                        <div className="rounded p-2 bg-blue-100 self-end">
                          {message.userMessage.content}
                        </div>
                      </>
                    )}

                    {message.coachMessage?.content && (
                      <>
                        <div className="text-sm font-semibold text-left text-green-800">
                          {message.coachMessage.speaker.toUpperCase()}
                        </div>
                        <div className="rounded p-2 bg-gray-100 self-start">
                          {message.coachMessage.content}
                        </div>
                      </>
                    )}

                    {message.coachMessage && !message.coachMessage.content && (
                      <div className="text-xs italic text-muted-foreground ml-2">
                        {message.coachMessage.isFinalized ? (
                          <>Final Reply: {message.coachMessage.content}</>
                        ) : editingIndex === idx ? (
                          <>
                            <Input
                              className="mb-1"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                            />
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => {
                                  const updated = [...messages]
                                  updated[idx].coachMessage!.content = editValue
                                  updated[idx].coachMessage!.isFinalized = true
                                  setMessages(updated)
                                  setEditingIndex(null)
                                  setEditValue('')
                                }}
                              >
                                Approve
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setEditingIndex(null)
                                  setEditValue('')
                                }}
                              >
                                Cancel
                              </Button>
                            </div>
                          </>
                        ) : (
                          <>
                            {message.coachMessage.aiSuggestions?.length ? (
                              <>
                                <div className="mb-1">AI Suggestions:</div>
                                <ul className="ml-4 list-disc text-muted-foreground text-xs">
                                  {message.coachMessage.aiSuggestions.map((option, i) => (
                                    <li key={i}>{option.text}</li>
                                  ))}
                                </ul>
                                <div className="flex gap-2 mt-2">
                                  <Button
                                    size="sm"
                                    onClick={() => {
                                      setEditingIndex(idx)
                                      setEditValue(message.coachMessage?.aiSuggestions?.[0]?.text || '')
                                    }}
                                  >
                                    Edit & Approve
                                  </Button>
                                </div>
                              </>
                            ) : null}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} className="pb-1" />
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={clearMessages}
            disabled={isLoading}
            size="sm"
          >
            <EraserIcon />
            Clear
          </Button>
          {/* Follow-up replies are handled dynamically via AI suggestions. */}
        </div>
      </div>
      <ReplySettings />
    </div>
  )
}
