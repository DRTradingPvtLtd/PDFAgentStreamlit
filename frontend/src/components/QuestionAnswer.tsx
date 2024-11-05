import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';

interface QuestionAnswerProps {
  pdfContext: string;
}

const QuestionAnswer: React.FC<QuestionAnswerProps> = ({ pdfContext }) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim().length < 3) {
      setError('Please enter a valid question');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/api/ask', {
        question,
        context: pdfContext,
      });

      if ('error' in response.data) {
        throw new Error(response.data.error);
      }

      setAnswer(response.data.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        ❓ Ask Questions
      </Typography>
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Ask a question about the document"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          error={!!error}
          helperText={error}
          disabled={loading}
          sx={{ mb: 2 }}
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Ask'}
        </Button>
      </Box>
      {answer && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6">Answer:</Typography>
          <Typography>{answer}</Typography>
        </Box>
      )}
    </Paper>
  );
};

export default QuestionAnswer;
