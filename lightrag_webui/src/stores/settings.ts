import { defaultQueryLabel, defaultReplyLabel } from './../lib/constants';
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { createSelectors } from '@/lib/utils'
import { Message, QueryRequest } from '@/api/lightrag'
import type { DialogTurn} from '@/api/lightrag'

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
  tooltips?: {
    topic?: string
    sub_topic?: string
    intent?: string
    sentiment?: string
    technique?: string
    level?: string
  }
}

type Theme = 'dark' | 'light' | 'system'
type Tab = 'documents' | 'knowledge-graph' | 'retrieval' | 'reply' | 'api'

interface SettingsState {
  // Graph viewer settings
  showPropertyPanel: boolean
  showNodeSearchBar: boolean

  showNodeLabel: boolean
  enableNodeDrag: boolean

  showEdgeLabel: boolean
  enableHideUnselectedEdges: boolean
  enableEdgeEvents: boolean

  graphQueryMaxDepth: number
  setGraphQueryMaxDepth: (depth: number) => void

  graphLayoutMaxIterations: number
  setGraphLayoutMaxIterations: (iterations: number) => void

  // Retrieval settings
  queryLabel: string
  setQueryLabel: (queryLabel: string) => void

  retrievalHistory: Message[]
  setRetrievalHistory: (history: Message[]) => void

  querySettings: Omit<QueryRequest, 'query'>
  updateQuerySettings: (settings: Partial<QueryRequest>) => void

  // Reply settings
  replyLabel: string
  setReplyLabel: (replyLabel: string) => void

  dialogTurns: DialogTurn[]
  setDialogTurns: (turns: DialogTurn[]) => void

  replySettings: ReplyParams
  updateReplySettings: (settings: Partial<ReplyParams>) => void

  // Auth settings
  apiKey: string | null
  setApiKey: (key: string | null) => void

  // App settings
  theme: Theme
  setTheme: (theme: Theme) => void

  enableHealthCheck: boolean
  setEnableHealthCheck: (enable: boolean) => void

  currentTab: Tab
  setCurrentTab: (tab: Tab) => void
}

const useSettingsStoreBase = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'system',

      showPropertyPanel: true,
      showNodeSearchBar: true,

      showNodeLabel: true,
      enableNodeDrag: true,

      showEdgeLabel: false,
      enableHideUnselectedEdges: true,
      enableEdgeEvents: false,

      graphQueryMaxDepth: 3,
      graphLayoutMaxIterations: 10,

      queryLabel: defaultQueryLabel,

      replyLabel: defaultReplyLabel,

      enableHealthCheck: true,

      apiKey: null,

      currentTab: 'reply',

      retrievalHistory: [],
      dialogTurns: [],

      querySettings: {
        mode: 'global',
        response_type: 'Multiple Paragraphs',
        top_k: 10,
        max_token_for_text_unit: 4000,
        max_token_for_global_context: 4000,
        max_token_for_local_context: 4000,
        only_need_context: false,
        only_need_prompt: false,
        stream: true,
        history_turns: 3,
        hl_keywords: [],
        ll_keywords: [],
        namespace: undefined
      },

      replySettings: {
        mode: 'hybrid',
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
        tooltips: {}
      },

      setTheme: (theme: Theme) => set({ theme }),

      setEnableHealthCheck: (enable: boolean) => set({ enableHealthCheck: enable }),

      setGraphLayoutMaxIterations: (iterations: number) =>
        set({
          graphLayoutMaxIterations: iterations
        }),

      setQueryLabel: (queryLabel: string) =>
        set({
          queryLabel
        }),

      setReplyLabel: (replyLabel: string) =>
        set({
          replyLabel
        }),

      setGraphQueryMaxDepth: (depth: number) => set({ graphQueryMaxDepth: depth }),

      setApiKey: (apiKey: string | null) => set({ apiKey }),

      setCurrentTab: (tab: Tab) => set({ currentTab: tab }),

      setRetrievalHistory: (history: Message[]) => set({ retrievalHistory: history }),

      setDialogTurns: (turns: DialogTurn[]) => set({ dialogTurns: turns }),

      updateQuerySettings: (settings: Partial<QueryRequest>) =>
        set((state) => ({
          querySettings: { ...state.querySettings, ...settings }
        })),

      updateReplySettings: (settings: Partial<ReplyParams>) =>
        set((state) => ({
          replySettings: { ...state.replySettings, ...settings }
        }))
    }),
    {
      name: 'settings-storage',
      storage: createJSONStorage(() => localStorage),
      version: 7,
      migrate: (state: any, version: number) => {
        if (version < 2) {
          state.showEdgeLabel = false
        }
        if (version < 3) {
          state.queryLabel = defaultQueryLabel
        }
        if (version < 4) {
          state.showPropertyPanel = true
          state.showNodeSearchBar = true
          state.showNodeLabel = true
          state.enableHealthCheck = true
          state.apiKey = null
        }
        if (version < 5) {
          state.currentTab = 'reply'
        }
        if (version < 6) {
          state.querySettings = {
            mode: 'global',
            response_type: 'Multiple Paragraphs',
            top_k: 10,
            max_token_for_text_unit: 4000,
            max_token_for_global_context: 4000,
            max_token_for_local_context: 4000,
            only_need_context: false,
            only_need_prompt: false,
            stream: true,
            history_turns: 3,
            hl_keywords: [],
            ll_keywords: []
          }
          state.retrievalHistory = []
          state.dialogTurns = []
          state.replyLabel = defaultReplyLabel
        }
        if (version < 7) {
          state.graphQueryMaxDepth = 3
          state.graphLayoutMaxIterations = 10
        }
        return state
      }
    }
  )
)

const useSettingsStore = createSelectors(useSettingsStoreBase)

export { useSettingsStore, type Theme }
