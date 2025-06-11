/**
 * ┌─────────────────────────────────────────────┐
 * │ TechNexusClarity Custom Module              │
 * │ Not part of upstream open source repo       │
 * └─────────────────────────────────────────────┘
 *
 * Description: Reply for TechNexusClarity-specific features.
 * Owner: TechNexusClarity
 */

import { useCallback, useEffect, useState } from 'react'
import { ReplyRequest, fetchPromptOptions } from '@/api/lightrag_tnc'
import Text from '@/components/ui/Text'
import Input from '@/components/ui/Input'
import Select from 'react-select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { useCustomSettingsStore } from '@/stores/settings_tnc'

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

// const techniqueOptions = [
//   'Plow', 'Open', 'Role', 'Stacking', 'Callback', 'Assign', 'Polling', 'Pushpull', 'Unknown'
// ];

const levelOptions = [
  'Attraction', 'Relate', 'Trust', 'Unknown'
];


const queryModeOptions = [
  'Mix', 'Hybrid', 'Global', 'Local', 'Naive', 'Unknown'
];

const responseFormatOptions = [
  'Text Short Hand', 'Professional'
];

const promptOptions = [
  'Default'
];

const formattedQueryModeOptions = queryModeOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedResponseFormatOptions = responseFormatOptions.map(option => ({ label: option.trim(), value: option.trim() }));
let formattedPromptOptions = promptOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedTopicOptions = topicOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedIntentOptions = intentOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedSentimentOptions = sentimentOptions.map(option => ({ label: option.trim(), value: option.trim() }));
// const formattedTechniqueOptions = techniqueOptions.map(option => ({ label: option.trim(), value: option.trim() }));
const formattedLevelOptions = levelOptions.map(option => ({ label: option.trim(), value: option.trim() }));

export default function ReplySettings() {
  // Update reply settings
  const replySettings = useCustomSettingsStore((state) => state.replySettings)
  console.log('replySettings', replySettings)

  const handleChange = useCallback((key: keyof ReplyRequest, value: any) => {
    useCustomSettingsStore.getState().updateReplySettings({ [key]: value })
  }, [])
  
  // Update getTooltip to only return tooltips for the specified keys
  const getTooltip = (key: TooltipKeys) => {
    return replySettings?.tooltips?.[key] || '';
  };
  // State for dynamically fetched prompt options
  const [promptOptions, setPromptOptions] = useState<{ label: string; value: string }[]>([]);
  formattedPromptOptions = promptOptions;
  useEffect(() => {
    const loadPromptOptions = async () => {
      try {
        const options = await fetchPromptOptions();

        // Filter options to only include names matching the pattern "school_counselor_*_reply"
        const filteredOptions = options
          .filter((option) => /^school_counselor_.*_reply$/.test(option.value.trim()))
          .map((option) => {
            // Extract the middle portion (.*) using a capturing group
            const match = option.value.trim().match(/^school_counselor_(.*)_reply$/);
            return match
              ? { label: match[1], value: match[1] } // Use the captured group for label and value
              : null;
          })
          .filter((option) => option !== null); // Remove any null values

        // Debugging: Log the filtered options to verify the transformation
        console.log('Filtered options:', filteredOptions);

        setPromptOptions(filteredOptions as { label: string; value: string }[]); // Update state with filtered options
      } catch (error) {
        console.error('Failed to load prompt options:', error);
      }
    };

    loadPromptOptions();
  }, []);

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
              value={replySettings.namespace ?? ''}
              onChange={(e) => handleChange('namespace', e.target.value)}
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


            {/* New Query Mode Setting */}
            <Text className="ml-1" text="Query Mode" tooltip="Select the query mode for the reply" side="left" />
            <Select
              id="query-mode-select"
              value={formattedQueryModeOptions.find(option => option.value === replySettings.mode) || formattedQueryModeOptions[0]}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('mode', newValue.value);
                }
              }}
              options={formattedQueryModeOptions}
            />

            {/* New Response Format Setting */}
            <Text className="ml-1" text="Response Format" tooltip="Select the format of the AI's response" side="left" />
            <Select
              id="response-format-select"
              value={formattedResponseFormatOptions.find(option => option.value === replySettings.response_format) || formattedResponseFormatOptions[0]}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('response_format', newValue.value);
                }
              }}
              options={formattedResponseFormatOptions}
            />

            {/* New Prompt Dropdown Setting */}
            <Text className="ml-1" text="Prompt" tooltip="Select a predefined prompt for the reply" side="left" />
            <Select
              id="prompt-select"
              value={formattedPromptOptions.find(option => option.value === replySettings.prompt) || formattedPromptOptions[0]}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('prompt', newValue.value);
                }
              }}
              options={formattedPromptOptions}
            />

            <Text className="ml-1" text="Topic" tooltip={getTooltip('topic')} side="left" />
            <Select
              id="topic"
              value={formattedTopicOptions.find(option => option.value === replySettings.topic) || formattedTopicOptions[0]}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('topic', newValue.value);
                }
              }}
              options={formattedTopicOptions}
            />

            <Text className="ml-1" text="Intent" tooltip={getTooltip('intent')} side="left" />
            <Select
              id="intent-select"
              value={formattedIntentOptions.find(option => option.value === replySettings.intent) || formattedIntentOptions[0]}
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
              value={formattedSentimentOptions.find(option => option.value === replySettings.sentiment) || formattedSentimentOptions[0]}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('sentiment', newValue.value);
                }
              }}
              options={formattedSentimentOptions}
            />
            {/*
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
            */}
            <Text className="ml-1" text="Level" tooltip={getTooltip('level')} side="left" />
            <Select
              id="level-select"
              value={formattedLevelOptions.find(option => option.value === replySettings.level) || formattedLevelOptions[0]}
              onChange={(newValue) => {
                if (newValue) {
                  handleChange('level', newValue.value);
                }
              }}
              options={formattedLevelOptions}
            />
            {/*
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
*/}
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