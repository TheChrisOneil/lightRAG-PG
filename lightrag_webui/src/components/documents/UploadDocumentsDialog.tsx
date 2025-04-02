import { useState, useCallback } from 'react'
import { useSettingsStore } from '@/stores/settings'
import Button from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/Dialog'
import FileUploader from '@/components/ui/FileUploader'
import { toast } from 'sonner'
import { errorMessage } from '@/lib/utils'
import { uploadDocument } from '@/api/lightrag'

import { UploadIcon } from 'lucide-react'

export default function UploadDocumentsDialog() {
  const [open, setOpen] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [progresses, setProgresses] = useState<Record<string, number>>({})
  const [namespace, setNamespace] = useState(() => useSettingsStore.getState().querySettings?.namespace ?? '')

  const handleDocumentsUpload = useCallback(
    async (filesToUpload: File[]) => {
      setIsUploading(true)
      console.log('Initial file list for upload:', filesToUpload)
      try {
        await Promise.all(
          filesToUpload.map(async (file) => {
            console.log('Starting upload for file:', file.name)
            try {
              const result = await uploadDocument(
                file,
                (percentCompleted: number) => {
                  console.debug(`Uploading ${file.name}: ${percentCompleted}%`)
                  setProgresses((pre) => ({
                    ...pre,
                    [file.name]: percentCompleted
                  }))
                }
              )
              if (result.status === 'success') {
                console.log(`Upload result for ${file.name}: Success`)
                toast.success(`Upload Success:\n${file.name} uploaded successfully`)
              } else {
                console.log(`Upload result for ${file.name}: Failed - ${result.message}`)
                toast.error(`Upload Failed:\n${file.name}\n${result.message}`)
              }
            } catch (err) {
              console.error(`Error during upload of ${file.name}:`, err)
              toast.error(`Upload Failed:\n${file.name}\n${errorMessage(err)}`)
            }
          })
        )
      } catch (err) {
        console.error('Error during batch upload:', err)
        toast.error('Upload Failed\n' + errorMessage(err))
      } finally {
        setIsUploading(false)
        // setOpen(false)
      }
    },
    [setIsUploading, setProgresses]
  )

  return (
    <Dialog
      open={open}
      onOpenChange={(open) => {
        if (isUploading && !open) {
          return
        }
        setOpen(open)
      }}
    >
      <DialogTrigger asChild>
        <Button variant="default" side="bottom" tooltip="Upload documents" size="sm">
          <UploadIcon /> Upload
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-xl" onCloseAutoFocus={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle>Upload documents</DialogTitle>
          <DialogDescription>
            Drag and drop your documents here or click to browse.
          </DialogDescription>
        </DialogHeader>
        <div className="mb-4">
          <label htmlFor="namespace-input" className="block text-sm font-medium text-gray-700 mb-1">
            Namespace
          </label>
          <input
            id="namespace-input"
            type="text"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            value={namespace}
            onChange={(e) => {
              const newNamespace = e.target.value
              setNamespace(newNamespace)
              useSettingsStore.setState({
                querySettings: {
                  ...useSettingsStore.getState().querySettings,
                  namespace: newNamespace
                }
              })
            }}
            placeholder="Enter namespace"
          />
        </div>
        <FileUploader
          maxFileCount={Infinity}
          maxSize={200 * 1024 * 1024}
          description="supported types: TXT, MD, DOCX, PDF, PPTX, RTF, ODT, EPUB, HTML, HTM, TEX, JSON, XML, YAML, YML, CSV, LOG, CONF, INI, PROPERTIES, SQL, BAT, SH, C, CPP, PY, JAVA, JS, TS, SWIFT, GO, RB, PHP, CSS, SCSS, LESS"
          onUpload={handleDocumentsUpload}
          progresses={progresses}
          disabled={isUploading}
        />
      </DialogContent>
    </Dialog>
  )
}
