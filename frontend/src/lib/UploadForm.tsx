import { useState } from "react";

const sanitizeFileName = (fileName: string): string => {
  return fileName
    .replace(/[^a-zA-Z0-9.-_]/g, '_')
    .toLowerCase();
};

const UploadForm: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);

  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
  ];

  const handleFileSelection = (selectedFile: File | null) => {
    if (!selectedFile) return;

    // Sanitize the file name
    const sanitizedFileName = sanitizeFileName(selectedFile.name);

    // Update the file state with sanitized name
    const sanitizedFile = new File([selectedFile], sanitizedFileName, { type: selectedFile.type });

    if (allowedTypes.includes(sanitizedFile.type)) {
      setFile(sanitizedFile);
    } else {
      alert("Please select a valid PDF.");
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);

    const droppedFile = event.dataTransfer.files?.[0] || null;
    handleFileSelection(droppedFile);
  };

  const getPresignedUrl = async (file: File): Promise<string> => {
    const response = await fetch("https://wyspfmmxrk.execute-api.us-east-1.amazonaws.com/prod/get-presigned-url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fileName: file.name }),
    });

    if (!response.ok) throw new Error("Failed to get presigned URL");
    const data = await response.json();
    console.log("Presigned URL Response:", data);
    return data.url;

    // return response.json();
  };

  const uploadFileToS3 = async (file: File, presignedUrl: string): Promise<string> => {
    const response = await fetch(presignedUrl, {
      method: "PUT",
      body: file,
      headers: { "Content-Type": file.type },
    });

    if (!response.ok) throw new Error("Upload failed");

    return presignedUrl.split("?")[0];
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    setUploading(true);

    try {
      const url = await getPresignedUrl(file);
      const fileUrl = await uploadFileToS3(file, url);
      console.log("File uploaded successfully:", fileUrl);
      alert(`File uploaded! URL: ${fileUrl}`);
    } catch (e) {
      console.error(e);
      alert("Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-10">
      <label
        className={`flex flex-col justify-center items-center w-full h-32 px-4 transition border-2 border-dashed rounded-md cursor-pointer focus:outline-none 
          ${dragging ? "bg-gray-600 border-gray-400" : "bg-gray-700 border-gray-800 hover:border-gray-400"}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <span className="flex items-center space-x-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-gray-200" fill="none" viewBox="0 0 24 24"
            stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="font-medium text-gray-200">
            {file ? file.name : "Drop files to Attach, or"}
            <span className="text-white underline pl-2">browse</span>
          </span>
        </span>
        <input type="file" name="file_upload" className="hidden" onChange={(e) => handleFileSelection(e.target.files?.[0] || null)} />
      </label>

      {file && (
        <p className="text-center text-gray-300 mt-2">Selected file: {file.name}</p>
      )}

      <button
        onClick={handleUpload}
        className="px-4 py-2 mt-4 text-white bg-blue-600 rounded disabled:bg-gray-400"
        disabled={!file || uploading}
      >
        {uploading ? "Uploading..." : "Upload"}
      </button>
    </div>
  );
};

export default UploadForm;

