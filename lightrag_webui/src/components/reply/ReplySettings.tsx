import { useCallback } from 'react'
import { ReplyRequest, QueryRequest } from '@/api/lightrag'
import Text from '@/components/ui/Text'
import Input from '@/components/ui/Input'
import Checkbox from '@/components/ui/Checkbox'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { useSettingsStore } from '@/stores/settings'

// Define a type that includes only the keys that support tooltips
type TooltipKeys = 'topic' | 'sub_topic' | 'intent' | 'sentiment' | 'technique' | 'level';

export default function ReplySettings() {
  // Update namespace in query settings
  const querySettings = useSettingsStore((state) => state.querySettings)

  const handleQueryChange = useCallback((key: keyof QueryRequest, value: any) => {
    useSettingsStore.getState().updateQuerySettings({ [key]: value })
  }, [])  

  // Update reply settings
  const replySettings = useSettingsStore((state) => state.replySettings)
  console.log('replySettings', replySettings)

  const handleChange = useCallback((key: keyof ReplyRequest, value: any) => {
    useSettingsStore.getState().updateReplySettings({ [key]: value })
  }, [])
  // Update getTooltip to only return tooltips for the specified keys
  const getTooltip = (key: TooltipKeys) => {
    return replySettings?.tooltips?.[key] || '';
  };

  const enforceValue = (value: string | undefined | null) => {
    return value && value.trim() !== '' ? value : 'Unknown';
  };

  return (
    <Card className="flex shrink-0 flex-col">
      <CardHeader className="px-4 pt-4 pb-2">
        <CardTitle>Reply Settings</CardTitle>
        <CardDescription>Configure settings for coach reply endpoint</CardDescription>
      </CardHeader>
      <CardContent className="m-0 flex grow flex-col p-0 text-xs">
        <div className="relative size-full">
          <div className="absolute inset-0 flex flex-col gap-2 overflow-auto px-2">

            <Text
              className="ml-1"
              text="Namespace"
              tooltip="This will be passed as the x-namespace header in query requests"
              side="left"
            />
            <Input
              id="namespace"
              type="text"
              value={querySettings.namespace ?? ''}
              onChange={(e) => handleQueryChange('namespace', e.target.value)}
              placeholder="Enter namespace"
            />

            <Text
              className="ml-1"
              text="Student Name"
              tooltip="The name of the student that will appear in the conversation context"
              side="left"
            />
            <Input
              id="student_name"
              type="text"
              value={replySettings.student_name ?? ''}
              onChange={(e) => handleChange('student_name', e.target.value)}
              placeholder="Enter student name"
            />

            <Text
              className="ml-1"
              text="Last Message"
              tooltip="The last message sent by the user"
              side="left"
            />

            <Text
              className="ml-1"
              text="Mode"
              tooltip="Query mode (local, global, hybrid, naive, mix)"
              side="left"
            />
            <Input
              id="mode"
              type="text"
              value={replySettings.mode ?? ''}
              onChange={(e) => handleChange('mode', e.target.value)}
              placeholder="Enter mode"
            />

            <Text
              className="ml-1"
              text="Only Need Context"
              tooltip="Only return retrieved context"
              side="left"
            />
            <Checkbox
              className="mr-1 cursor-pointer"
              id="only_need_context"
              checked={replySettings.only_need_context}
              onCheckedChange={(checked) => handleChange('only_need_context', checked)}
            />

            <Text
              className="ml-1"
              text="Only Need Prompt"
              tooltip="Only return generated prompt"
              side="left"
            />
            <Checkbox
              className="mr-1 cursor-pointer"
              id="only_need_prompt"
              checked={replySettings.only_need_prompt}
              onCheckedChange={(checked) => handleChange('only_need_prompt', checked)}
            />

            <Text
              className="ml-1"
              text="Topic"
              tooltip={getTooltip('topic')}
              side="left"
            />
            <Input
              id="topic"
              type="text"
              value={enforceValue(replySettings.topic)}
              onChange={(e) => handleChange('topic', e.target.value)}
              placeholder="Enter topic"
            />

            <Text
              className="ml-1"
              text="Sub Topic"
              tooltip={getTooltip('sub_topic')}
              side="left"
            />
            <Input
              id="sub_topic"
              type="text"
              value={enforceValue(replySettings.sub_topic)}
              onChange={(e) => handleChange('sub_topic', e.target.value)}
              placeholder="Enter sub topic"
            />

            <Text
              className="ml-1"
              text="Intent"
              tooltip={getTooltip('intent')}
              side="left"
            />
            <Input
              id="intent"
              type="text"
              value={enforceValue(replySettings.intent)}
              onChange={(e) => handleChange('intent', e.target.value)}
              placeholder="Enter intent"
            />

            <Text
              className="ml-1"
              text="Sentiment"
              tooltip={getTooltip('sentiment')}
              side="left"
            />
            <Input
              id="sentiment"
              type="text"
              value={enforceValue(replySettings.sentiment)}
              onChange={(e) => handleChange('sentiment', e.target.value)}
              placeholder="Enter sentiment"
            />

            <Text
              className="ml-1"
              text="Technique"
              tooltip={getTooltip('technique')}
              side="left"
            />
            <Input
              id="technique"
              type="text"
              value={enforceValue(replySettings.technique)}
              onChange={(e) => handleChange('technique', e.target.value)}
              placeholder="Enter technique"
            />

            <Text
              className="ml-1"
              text="Level"
              tooltip={getTooltip('level')}
              side="left"
            />
            <Input
              id="level"
              type="text"
              value={enforceValue(replySettings.level)}
              onChange={(e) => handleChange('level', e.target.value)}
              placeholder="Enter level"
            />

            <Text className="ml-1" text="Top K" side="left" />
            <Input
              id="top_k"
              type="number"
              value={replySettings.top_k ?? ''}
              onChange={(e) => handleChange('top_k', Number(e.target.value))}
              placeholder="Enter top_k"
            />

            <Text className="ml-1" text="Max Tokens Text Unit" side="left" />
            <Input
              id="max_token_for_text_unit"
              type="number"
              value={replySettings.max_token_for_text_unit ?? ''}
              onChange={(e) => handleChange('max_token_for_text_unit', Number(e.target.value))}
              placeholder="Enter max tokens for text unit"
            />

            <Text className="ml-1" text="Max Tokens Global Context" side="left" />
            <Input
              id="max_token_for_global_context"
              type="number"
              value={replySettings.max_token_for_global_context ?? ''}
              onChange={(e) => handleChange('max_token_for_global_context', Number(e.target.value))}
              placeholder="Enter max tokens for global context"
            />

            <Text className="ml-1" text="Max Tokens Local Context" side="left" />
            <Input
              id="max_token_for_local_context"
              type="number"
              value={replySettings.max_token_for_local_context ?? ''}
              onChange={(e) => handleChange('max_token_for_local_context', Number(e.target.value))}
              placeholder="Enter max tokens for local context"
            />

            <Text className="ml-1" text="High-Level Keywords" side="left" />
            <Input
              id="hl_keywords"
              type="text"
              value={replySettings.hl_keywords?.join(', ') ?? ''}
              onChange={(e) => handleChange('hl_keywords', e.target.value.split(',').map((k) => k.trim()))}
              placeholder="Comma-separated keywords"
            />

            <Text className="ml-1" text="Low-Level Keywords" side="left" />
            <Input
              id="ll_keywords"
              type="text"
              value={replySettings.ll_keywords?.join(', ') ?? ''}
              onChange={(e) => handleChange('ll_keywords', e.target.value.split(',').map((k) => k.trim()))}
              placeholder="Comma-separated keywords"
            />

            <Text className="ml-1" text="History Turns" side="left" />
            <Input
              id="history_turns"
              type="number"
              value={replySettings.history_turns ?? ''}
              onChange={(e) => handleChange('history_turns', Number(e.target.value))}
              placeholder="Enter number of turns"
            />

          </div>
        </div>
      </CardContent>
    </Card>
  )
}