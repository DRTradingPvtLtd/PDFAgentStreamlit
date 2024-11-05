import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Paper, CircularProgress, Alert } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import axios from 'axios';
import { AnalysisData, ApiError } from '../types';

interface FileUploadProps {
  onAnalysisComplete: (data: AnalysisData, context: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onAnalysisComplete }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<AnalysisData | ApiError>(
        'http://localhost:8000/api/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if ('error' in response.data) {
        throw new Error(response.data.error);
      }

      const reader = new FileReader();
      reader.onload = async (e) => {
        const text = e.target?.result as string;
        onAnalysisComplete(response.data as AnalysisData, text);
      };
      reader.readAsText(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [onAnalysisComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: false,
  });

  return (
    <Box sx={{ mb: 4 }}>
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        {loading ? (
          <CircularProgress />
        ) : (
          <Box>
            {isDragActive ? (
              <p>Drop the PDF file here...</p>
            ) : (
              <p>Drag and drop a PDF file here, or click to select one</p>
            )}
          </Box>
        )}
      </Paper>
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default FileUpload;
