import { useState, useCallback, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  UploadCloud,
  FileText,
  File,
  Trash2,
  CheckCircle2,
  Loader2,
  AlertCircle,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STEPS = ["Parsing", "Chunking", "Indexing"];

export default function KnowledgePanel({
  documents = [],
  setDocuments,
  onDocumentUploaded,
  onDocumentDeleted,
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState(-1);
  const [uploadProgress, setUploadProgress] = useState(0);

  const documentList = Array.isArray(documents)
    ? documents
    : Array.isArray(documents?.documents)
    ? documents.documents
    : [];

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await axios.get(`${API}/documents`);
      setDocuments(res.data);
    } catch (e) {
      console.error("Failed to fetch documents", e);
    }
  };

  const handleUpload = useCallback(
    async (files) => {
      for (const file of files) {
        const ext = file.name.split(".").pop().toLowerCase();
        if (!["pdf", "md", "txt"].includes(ext)) {
          toast.error(`Unsupported file: ${file.name}. Use PDF, MD, or TXT.`);
          continue;
        }

        setUploading(true);
        setUploadStep(0);
        setUploadProgress(15);

        const formData = new FormData();
        formData.append("file", file);

        try {
          // Simulate stepper progress
          await new Promise((r) => setTimeout(r, 400));
          setUploadStep(1);
          setUploadProgress(50);

          await new Promise((r) => setTimeout(r, 300));
          setUploadStep(2);
          setUploadProgress(80);

          const res = await axios.post(`${API}/upload`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });

          setUploadProgress(100);
          await new Promise((r) => setTimeout(r, 200));

          onDocumentUploaded(res.data);
          toast.success(`Indexed ${file.name} (${res.data.chunks} chunks)`);
          fetchDocuments();
        } catch (e) {
          toast.error(
            `Upload failed: ${e.response?.data?.detail || e.message}`
          );
        } finally {
          setUploading(false);
          setUploadStep(-1);
          setUploadProgress(0);
        }
      }
    },
    [onDocumentUploaded]
  );

  const handleDelete = async (docId, filename) => {
    try {
      await axios.delete(`${API}/documents/${docId}`);
      onDocumentDeleted(docId);
      toast.success(`Removed ${filename}`);
      fetchDocuments();
    } catch (e) {
      toast.error("Failed to delete document");
    }
  };

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) handleUpload(files);
    },
    [handleUpload]
  );

  const onFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) handleUpload(files);
  };

  const getFileIcon = (type) => {
    if (type === "pdf") return <FileText className="w-4 h-4 text-red-500" strokeWidth={1.5} />;
    if (type === "md") return <File className="w-4 h-4 text-blue-500" strokeWidth={1.5} />;
    return <File className="w-4 h-4 text-slate-500" strokeWidth={1.5} />;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-slate-100">
        <h2 className="font-heading text-sm font-bold text-slate-900 tracking-tight">
          Knowledge Manager
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Upload docs to build your knowledge base
        </p>
      </div>

      {/* Upload Zone */}
      <div className="px-4 pt-3">
        <div
          data-testid="upload-dropzone"
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => document.getElementById("file-input").click()}
          className={`
            border-2 border-dashed rounded-xl p-6 text-center cursor-pointer
            transition-all duration-200 group
            ${
              isDragging
                ? "border-blue-500 bg-blue-50/60 shadow-[0_0_16px_rgba(37,99,235,0.12)]"
                : "border-slate-300 hover:border-blue-400 hover:bg-blue-50/30"
            }
            ${uploading ? "pointer-events-none opacity-60" : ""}
          `}
        >
          <input
            id="file-input"
            data-testid="file-input"
            type="file"
            multiple
            accept=".pdf,.md,.txt"
            onChange={onFileSelect}
            className="hidden"
          />
          <UploadCloud
            className={`w-8 h-8 mx-auto mb-2 transition-colors duration-200 ${
              isDragging
                ? "text-blue-600"
                : "text-slate-400 group-hover:text-blue-500"
            }`}
            strokeWidth={1.5}
          />
          <p className="text-sm font-medium text-slate-700">
            Drop files here
          </p>
          <p className="text-xs text-slate-400 mt-1">PDF, MD, TXT</p>
        </div>

        {/* Progress Stepper */}
        {uploading && (
          <div className="mt-3 animate-fade-in-up" data-testid="upload-stepper">
            <div className="flex items-center gap-1 mb-2">
              {STEPS.map((step, i) => (
                <div key={step} className="flex items-center gap-1 flex-1">
                  <div
                    className={`flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold transition-colors duration-200 ${
                      uploadStep > i
                        ? "bg-emerald-500 text-white"
                        : uploadStep === i
                        ? "bg-blue-600 text-white"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {uploadStep > i ? (
                      <CheckCircle2 className="w-3 h-3" />
                    ) : (
                      i + 1
                    )}
                  </div>
                  <span
                    className={`text-[10px] font-medium ${
                      uploadStep >= i ? "text-slate-700" : "text-slate-400"
                    }`}
                  >
                    {step}
                  </span>
                  {i < STEPS.length - 1 && (
                    <div
                      className={`stepper-line flex-1 ${
                        uploadStep > i ? "bg-emerald-400" : "bg-slate-200"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
            <Progress value={uploadProgress} className="h-1.5" />
          </div>
        )}
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-hidden mt-3">
        <div className="px-4 pb-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Indexed Documents ({documentList.length})
          </p>
        </div>
        <ScrollArea className="h-[calc(100%-1.5rem)] px-4">
          {documentList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <AlertCircle className="w-8 h-8 text-slate-300 mb-2" strokeWidth={1.5} />
              <p className="text-sm text-slate-400">No documents yet</p>
              <p className="text-xs text-slate-400">
                Upload files to get started
              </p>
            </div>
          ) : (
            <div className="space-y-2 pb-4">
              {documentList.map((doc) => (
                <div
                  key={doc.id}
                  data-testid={`document-item-${doc.id}`}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] hover:border-blue-200 transition-all duration-200 group"
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    {getFileIcon(doc.file_type)}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-slate-800 truncate">
                        {doc.filename}
                      </p>
                      <p className="text-[10px] text-slate-400">
                        {doc.chunks} chunks
                      </p>
                    </div>
                  </div>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        data-testid={`delete-doc-${doc.id}`}
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="p-1.5 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors duration-200 opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 className="w-3.5 h-3.5" strokeWidth={1.5} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Remove document</TooltipContent>
                  </Tooltip>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}
