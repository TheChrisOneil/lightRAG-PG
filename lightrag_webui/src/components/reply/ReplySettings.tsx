import { useCallback } from 'react'
import { ReplyRequest, QueryRequest } from '@/api/lightrag'
import Text from '@/components/ui/Text'
import Input from '@/components/ui/Input'
import Checkbox from '@/components/ui/Checkbox'
import Select from 'react-select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { useSettingsStore } from '@/stores/settings'
import { SingleValue } from 'react-select';

// Define a type that includes only the keys that support tooltips
type TooltipKeys = 'topic' | 'sub_topic' | 'intent' | 'sentiment' | 'technique' | 'level';

const topicOptions = [
  'Social', 'Collab', 'Friendship', 'Thinking', 'English', 'Diet', 'Fitness',
  'Coping', 'Learning', 'Financial', 'Practical', 'Problem-solving', 
  'Self-aware', 'Self-care', 'Reflection', 'Stress', 'Time', 'Unknown'
];

const intentOptions = [
  'Experience', 'Emotion', 'Guidance', 'Unknown'
];

const sentimentOptions = [
  'Positive', 'Neutral', 'Negative', 'Unknown'
];

const techniqueOptions = [
  'Plow', 'Open', 'Role', 'Stacking', 'Callback', 'Assign', 'Polling', 'Pushpull', 'Unknown'
];

const levelOptions = [
  'Attraction', 'Relate', 'Trust', 'Unknown'
];

const formattedTopicOptions = topicOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedIntentOptions = intentOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedSentimentOptions = sentimentOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedTechniqueOptions = techniqueOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedLevelOptions = levelOptions.map(option => ({ label: option.trim(), value: option.trim() }));

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

            <Text className="ml-1" text="Topic" tooltip={getTooltip('topic')} side="left" />
            <Select
              id="topic"
              value={formattedTopicOptions.find(option => option.value === replySettings.topic) || { label: 'Unknown', value: 'Unknown' }}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('topic', newValue.value);
                }
              }}
              options={formattedTopicOptions}
            />

            <Text className="ml-1" text="Sub Topic" tooltip={getTooltip('sub_topic')} side="left" />
            <Input
              id="sub_topic"
              type="text"
              value={enforceValue(replySettings.sub_topic)}
              onChange={(e) => handleChange('sub_topic', e.target.value)}
              placeholder="Enter sub topic"
            />

            <Text className="ml-1" text="Intent" tooltip={getTooltip('intent')} side="left" />
            <Select
              id="intent-select"
              value={formattedIntentOptions.find(option => option.value === replySettings.intent) || { label: 'Unknown', value: 'Unknown' }}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('intent', newValue.value);
                }
              }}
              options={formattedIntentOptions}
            />

            <Text className="ml-1" text="Sentiment" tooltip={getTooltip('sentiment')} side="left" />
            <Select
              id="sentiment-select"
              value={formattedSentimentOptions.find(option => option.value === replySettings.sentiment) || { label: 'Unknown', value: 'Unknown' }}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('sentiment', newValue.value);
                }
              }}
              options={formattedSentimentOptions}
            />

            <Text className="ml-1" text="Technique" tooltip={getTooltip('technique')} side="left" />
            <Select
              id="technique-select"
              value={formattedTechniqueOptions.find(option => option.value === replySettings.technique) || { label: 'Unknown', value: 'Unknown' }}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('technique', newValue.value);
                }
              }}
              options={formattedTechniqueOptions}
            />

            <Text className="ml-1" text="Level" tooltip={getTooltip('level')} side="left" />
            <Select
              id="level-select"
              value={formattedLevelOptions.find(option => option.value === replySettings.level) || { label: 'Unknown', value: 'Unknown' }}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('level', newValue.value);
                }
              }}
              options={formattedLevelOptions}
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