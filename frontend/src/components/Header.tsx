import React from 'react';
import { Box, Typography } from '@mui/material';

const Header: React.FC = () => {
  return (
    <Box sx={{ my: 4, textAlign: 'center' }}>
      <Typography variant="h2" component="h1" gutterBottom>
        🍫 Chocolate PDF Q&A Assistant
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Upload a PDF document to analyze chocolate-related content, get summaries, and ask questions.
      </Typography>
    </Box>
  );
};

export default Header;
