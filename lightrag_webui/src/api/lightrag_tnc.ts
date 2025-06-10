/**
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 *
 * Description: API for TechNexusClarity-specific features.
 * Owner: TechNexusClarity
 */

import { QueryMode, axiosInstance } from './lightrag'

import { errorMessage } from '@/lib/utils'
/**
 * The Reply is focused on the assistant who leverages the AI Agent to create a reply to the user
 * user is the student, patient, the digital twin, etc
 * assistant is the coach, the doctor, the AI, etc
*/
export type Reply = {
    role: 'user' | 'assistant' | 'system'
    content: string
  }


type AISuggestion = {
    text: string
    intent?: string
    sentiment?: string
    topic?: string
    sub_topic?: string
    technique?: string
    level?: string
    confidence?: number
  }
  
export type ReplyRequest = {
    student_name?: string
    speaker: 'student' | 'patient'
    content: string
    timestamp: string
    response_format: string
    prompt: string
    topic?: string
    sub_topic?: string
    intent?: string
    sentiment?: string
    technique?: string
    level?: string
    mode: QueryMode
    only_need_context?: boolean
    only_need_prompt?: boolean
    top_k?: number
    max_token_for_text_unit?: number
    max_token_for_global_context?: number
    max_token_for_local_context?: number
    hl_keywords?: string[]
    ll_keywords?: string[]
    history_turns?: number
    conversation_history?: DialogTurn[]
      /** Namespace for the query. */
  namespace?: string
  }
  
export type ReplyResponse = {
    coachMessage?: CoachMessage
  }
  
export type CoachMessage = {
    speaker: 'coach' | 'doctor'
    content?: string
    aiSuggestions?: AISuggestion[]
    selectedSuggestionIndex?: number
    isFinalized: boolean
    timestamp: string
  }
  
export type UserMessage = {
    speaker: 'student' | 'patient'
    content?: string // student or paitne experiencial, emoutional, skill, knowledge, etc content
    intent?: string
    sentiment?: string
    topic?: string
    sub_topic?: string
    technique?: string
    level?: string
    timestamp: string
  }
  
export type DialogTurn = {
    userMessage?: UserMessage
    coachMessage?: CoachMessage
  }
  

export const coachReplyText = async (request: ReplyRequest): Promise<ReplyResponse> => {
  const response = await axiosInstance.post('/coach_reply', request)
  return response.data
}

export const coachReplyTextStream = async (
  request: ReplyRequest,
  onChunk: (chunk: string) => void,
  onError?: (error: string) => void
) => {
  try {
    let buffer = ''
    await axiosInstance
      .post('/coach_reply/stream', request, {
        responseType: 'text',
        headers: {
          Accept: 'application/x-ndjson'
        },
        transformResponse: [
          (data: string) => {
            buffer += data
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (line.trim()) {
                try {
                  const parsed = JSON.parse(line)
                  if (parsed.response) {
                    onChunk(parsed.response)
                  } else if (parsed.error && onError) {
                    onError(parsed.error)
                  }
                } catch (e) {
                  console.error('Error parsing stream chunk:', e)
                  if (onError) onError('Error parsing server response')
                }
              }
            }
            return data
          }
        ]
      })
      .catch((error) => {
        if (onError) onError(errorMessage(error))
      })

    if (buffer.trim()) {
      try {
        const parsed = JSON.parse(buffer)
        if (parsed.response) {
          onChunk(parsed.response)
        } else if (parsed.error && onError) {
          onError(parsed.error)
        }
      } catch (e) {
        console.error('Error parsing final chunk:', e)
        if (onError) onError('Error parsing server response')
      }
    }
  } catch (error) {
    const message = errorMessage(error)
    console.error('Stream request failed:', message)
    if (onError) onError(message)
  }
}

export const fetchPromptOptions = async (): Promise<{ label: string; value: string }[]> => {
  try {
    // Make an API call to fetch the prompt keys
    const response = await axiosInstance.get('/prompt/keys');
    const promptKeys: string[] = response.data; // API returns a list of strings

    // Format the prompt keys into an array of { label, value } objects
    const formattedOptions = promptKeys.map((key) => ({
      label: key,
      value: key,
    }));

    return formattedOptions;
  } catch (error) {
    console.error('Error fetching prompt options:', error);
    throw new Error('Failed to fetch prompt options');
  }
};