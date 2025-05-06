/**
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 *
 * Description: Custom persistent settings store for TechNexusClarity-specific features.
 * Owner: TechNexusClarity
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { DialogTurn} from '@/api/lightrag_tnc'


export interface ReplyParams {
    topic: string
    sub_topic: string
    intent: string
    sentiment: string
    technique: string
    level: string
    mode: 'local' | 'global' | 'hybrid' | 'naive' | 'mix'
    only_need_context?: boolean
    only_need_prompt?: boolean
    top_k?: number
    max_token_for_text_unit?: number
    max_token_for_global_context?: number
    max_token_for_local_context?: number
    hl_keywords?: string[]
    ll_keywords?: string[]
    stream?: boolean
    history_turns?: number
    student_name?: string
    speaker: 'student' | 'patient'
    content: string
    namespace: string | undefined
    response_format: 'HS Text' | 'Professional Text' // Added response_format
    prompt: 'Default' | 'Tim' 
    tooltips?: {
      topic?: string
      sub_topic?: string
      intent?: string
      sentiment?: string
      technique?: string
      level?: string
    }
}


interface CustomSettingsState {
  // Reply settings
  replyLabel: string
  setReplyLabel: (replyLabel: string) => void

  dialogTurns: DialogTurn[]
  setDialogTurns: (turns: DialogTurn[]) => void

  replySettings: ReplyParams
  updateReplySettings: (settings: Partial<ReplyParams>) => void
}

export const useCustomSettingsStore = create<CustomSettingsState>()(
  persist(
    (set) => ({
      replyLabel: '*',
      dialogTurns: [],
      setDialogTurns: (turns: DialogTurn[]) => set({ dialogTurns: turns }),
      replySettings: {
        mode: 'hybrid',
        response_format: 'HS Text',
        prompt: 'Default',
        only_need_context: false,
        only_need_prompt: false,
        topic: 'Unknown',
        sub_topic: 'Unknown',
        intent: 'Unknown',
        sentiment: 'Unknown',
        technique: 'Unknown',
        level: 'Unknown',
        top_k: 10,
        max_token_for_text_unit: 4000,
        max_token_for_global_context: 4000,
        max_token_for_local_context: 4000,
        hl_keywords: [],
        stream: false,
        history_turns: 3,
        student_name: '',
        speaker: 'student',
        content: '',
        tooltips: {},
        namespace: undefined
      },
      setReplyLabel: (replyLabel: string) =>
        set({
          replyLabel
        }),
      updateReplySettings: (settings: Partial<ReplyParams>) =>
        set((state) => ({
          replySettings: { ...state.replySettings, ...settings }
        }))
    }),
    {
      name: 'custom-settings-storage',
      storage: createJSONStorage(() => localStorage),
      version: 1,
    }
  )
)
