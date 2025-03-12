import { useCallback } from 'react'
import { QueryRequest } from '@/api/lightrag'
import Text from '@/components/ui/Text'
import Input from '@/components/ui/Input'
import Checkbox from '@/components/ui/Checkbox'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { useSettingsStore } from '@/stores/settings'

export default function ReplySettings() {
  const querySettings = useSettingsStore((state) => state.querySettings)

  const handleChange = useCallback((key: keyof QueryRequest, value: any) => {
    useSettingsStore.getState().updateQuerySettings({ [key]: value })
  }, [])

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
              value={querySettings.student_name ?? ''}
              onChange={(e) => handleChange('student_name', e.target.value)}
              placeholder="Enter student name"
            />

            <Text
              className="ml-1"
              text="Last Message"
              tooltip="The last message sent by the user"
              side="left"
            />

            <div className="flex items-center gap-2">
              <Text
                className="ml-1"
                text="Include History"
                tooltip="Include prior conversation history in the request"
                side="left"
              />
              <div className="grow" />
              <Checkbox
                className="mr-1 cursor-pointer"
                id="include_history"
                checked={querySettings.include_history}
                onCheckedChange={(checked) => handleChange('include_history', checked)}
              />
            </div>

          </div>
        </div>
      </CardContent>
    </Card>
  )
}
